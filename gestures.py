"""
Module Nhận diện Cử chỉ Tay Nâng cao (Advanced Gesture Detector)
Sử dụng MediaPipe Hands để phát hiện cử chỉ tĩnh (Fist, Palm, Thumbs Up/Down, Peace, OK, Pinky, Shh)
và cử chỉ động (Swipe Left, Right, Up, Down), kèm cơ chế Hold to Lock/Unlock.
"""

import math
import time
from collections import deque
import cv2
import mediapipe as mp

from mouse_controller import AirMouseController

class GestureDetector:
    def __init__(self, config):
        self.config = config
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Khởi tạo mô hình Hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=self.config.get("detection_confidence", 0.75),
            min_tracking_confidence=self.config.get("tracking_confidence", 0.75)
        )
        
        # Bộ điều khiển Chuột Ảo
        self.mouse_controller = AirMouseController(self.config)

        # Lịch sử vị trí bàn tay để nhận diện Swipe
        # Lưu trữ các tuple: (x, y, timestamp)
        self.motion_history = deque(maxlen=25)
        
        # Biến trạng thái Khóa / Chờ
        self.is_locked = False
        self.hold_start_time = None
        self.hold_progress = 0.0  # 0.0 -> 1.0
        self.last_lock_toggle_time = 0
        
        # Cooldown giữa các lệnh điều khiển
        self.last_action_time = 0
        self.last_executed_gesture = None
        self.last_executed_action = None

        # Bộ lọc ổn định cử chỉ tĩnh & chống xung đột với cử chỉ vuốt
        self.candidate_static_gesture = None
        self.static_gesture_frame_count = 0
        self.STATIC_CONFIRM_FRAMES = 3  # Cần ổn định ít nhất 3 khung hình (~90ms)
        self.post_swipe_suppress_until = 0.0  # Khóa cử chỉ tĩnh tạm thời sau khi vừa vuốt xong

    def update_settings(self, config):
        """Cập nhật cấu hình khi người dùng thay đổi trên GUI."""
        self.config = config
        # Tái khởi tạo nếu cần thay đổi confidence
        new_det = self.config.get("detection_confidence", 0.75)
        new_track = self.config.get("tracking_confidence", 0.75)
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=new_det,
            min_tracking_confidence=new_track
        )
        self.mouse_controller.update_settings(self.config)

    def dist(self, p1, p2):
        """Khoảng cách Euclid 2D giữa 2 landmarks."""
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def get_palm_size(self, landmarks):
        """Đo kích thước bàn tay chuẩn hóa (từ cổ tay 0 tới gốc ngón giữa 9)."""
        return max(0.01, self.dist(landmarks[0], landmarks[9]))

    def get_fingers_status(self, landmarks):
        """
        Xác định trạng thái mở (1) hay cụp (0) của 5 ngón tay:
        [thumb, index, middle, ring, pinky]
        Sử dụng khoảng cách hình học tương đối giữa các khớp để chuẩn xác
        cho mọi hướng nghiêng, ngửa, hoặc chúc xuống.
        """
        fingers = [0, 0, 0, 0, 0]
        palm_size = self.get_palm_size(landmarks)
        wrist = landmarks[0]
        
        # 1. Ngón cái (Thumb - id 4):
        # Đo khoảng cách từ đầu ngón cái (4) đến gốc ngón út (17) so sánh với khớp đốt 2 (3) đến (17)
        dist_thumb_pinky_tip = self.dist(landmarks[4], landmarks[17])
        dist_thumb_pinky_base = self.dist(landmarks[2], landmarks[17])
        dist_thumb_wrist = self.dist(landmarks[4], wrist)
        dist_thumb_mcp = self.dist(landmarks[2], wrist)
        
        if dist_thumb_pinky_tip > dist_thumb_pinky_base * 1.12 and dist_thumb_wrist > dist_thumb_mcp:
            fingers[0] = 1
            
        # 2. Bốn ngón còn lại (Index: 8, Middle: 12, Ring: 16, Pinky: 20)
        # So sánh khoảng cách từ đầu ngón đến cổ tay với khớp PIP đến cổ tay,
        # và khoảng cách từ đầu ngón đến MCP so với PIP đến MCP.
        # Nhờ vậy, ngón tay chúc xuống (pointing down) vẫn được nhận diện chính xác là mở.
        finger_ids = [(8, 6, 5), (12, 10, 9), (16, 14, 13), (20, 18, 17)]
        for idx, (tip_id, pip_id, mcp_id) in enumerate(finger_ids, start=1):
            d_tip_wrist = self.dist(landmarks[tip_id], wrist)
            d_pip_wrist = self.dist(landmarks[pip_id], wrist)
            d_tip_mcp = self.dist(landmarks[tip_id], landmarks[mcp_id])
            d_pip_mcp = self.dist(landmarks[pip_id], landmarks[mcp_id])
            
            # Ngón tay mở khi đầu ngón vươn xa hơn khớp giữa (PIP) so với cổ tay và gốc ngón (MCP)
            if d_tip_wrist > d_pip_wrist * 1.06 and d_tip_mcp > d_pip_mcp * 1.12:
                fingers[idx] = 1
            else:
                fingers[idx] = 0
                
        return fingers

    def detect_static_gesture(self, landmarks, fingers):
        """Nhận diện các cử chỉ tĩnh dựa vào hình học khớp xương."""
        palm_size = self.get_palm_size(landmarks)
        total_open = sum(fingers)
        
        # 1. OK / PINCH Sign: Ngón cái và ngón trỏ chụm lại, ít nhất 2 ngón khác mở
        dist_thumb_index = self.dist(landmarks[4], landmarks[8])
        if dist_thumb_index / palm_size < 0.28:
            # Ngón giữa, áp út hoặc út mở
            if fingers[2] == 1 or fingers[3] == 1 or fingers[4] == 1:
                return "OK_PINCH"l      

        # 2. THUMBS UP / THUMBS DOWN: Chỉ ngón cái mở, 4 ngón còn lại gập
        if fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
            # Ngón cái hướng lên trên
            if landmarks[4].y < landmarks[3].y - 0.02 and landmarks[4].y < landmarks[5].y:
                return "THUMBS_UP"
            # Ngón cái chúc xuống dưới
            elif landmarks[4].y > landmarks[3].y + 0.02 and landmarks[4].y > landmarks[5].y:
                return "THUMBS_DOWN"

        # 3. POINTING UP / POINTING DOWN (Chỉ 1 ngón trỏ mở)
        if fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
            # Vector từ MCP ngón trỏ (5) tới TIP (8)
            dx = landmarks[8].x - landmarks[5].x
            dy = landmarks[8].y - landmarks[5].y
            
            # Ngón trỏ phải thẳng đứng rõ ràng (độ chênh lệch dọc lớn hơn đáng kể so với ngang)
            vertical_ratio = abs(dy) / max(0.001, abs(dx))
            finger_length = abs(dy) / palm_size
            
            if vertical_ratio > 1.30 and finger_length > 0.35:
                if dy < 0:  # Đầu ngón trỏ cao hơn gốc ngón -> Chỉ lên
                    return "POINTING_UP"
                else:       # Đầu ngón trỏ thấp hơn gốc ngón -> Chỉ xuống
                    return "POINTING_DOWN"
            # Nếu ngón trỏ chỉ ngang hoặc chéo -> Trả về None (chống nhận diện nhầm sang Tăng Âm Lượng)
            return None

        # 4. PEACE SIGN (Chữ V: ngón trỏ và ngón giữa mở, 2 ngón kia gập)
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
            return "PEACE_SIGN"

        # 5. PINKY UP (Chỉ ngón út mở - biểu tượng thả tim nhỏ hoặc thề/like)
        if fingers[4] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0:
            return "PINKY_UP"

        # 6. OPEN PALM (Xòe 5 ngón)
        if total_open >= 4:
            return "OPEN_PALM"

        # 7. FIST (Nắm đấm - 0 ngón)
        if total_open == 0:
            return "FIST"

        # 8. SHH GESTURE (Ngón trỏ đặt thẳng đứng trước mặt, các ngón nắm lại)
        if fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
            dy = landmarks[8].y - landmarks[5].y
            if dy < 0 and landmarks[8].y < 0.45:
                return "SHH_GESTURE"

        return None

    def detect_swipe(self, current_time, palm_size):
        """
        Nhận diện cử chỉ gạt tay / vuốt tay:
        SWIPE_LEFT, SWIPE_RIGHT, SWIPE_UP, SWIPE_DOWN.
        Dựa vào lịch sử di chuyển tâm bàn tay trong khoảng 0.08s - 0.40s.
        """
        if len(self.motion_history) < 4:
            return None

        now_point = self.motion_history[-1]
        now_x, now_y, now_t = now_point

        threshold = float(self.config.get("swipe_threshold", 0.10))
        # Thích ứng tự nhiên theo kích thước bàn tay
        effective_thresh = max(0.065, min(threshold, palm_size * 0.70))

        # Tìm trong lịch sử các điểm cách thời điểm hiện tại từ 0.08s đến 0.40s
        # Tìm điểm có độ dịch chuyển lớn nhất
        best_candidate = None
        max_disp = 0.0

        for pt in self.motion_history:
            dt = now_t - pt[2]
            if 0.08 <= dt <= 0.40:
                dx = now_x - pt[0]
                dy = now_y - pt[1]
                disp = math.hypot(dx, dy)
                if disp > max_disp:
                    max_disp = disp
                    best_candidate = (dx, dy, dt)

        if not best_candidate:
            return None

        dx, dy, dt = best_candidate
        speed = max_disp / max(0.001, dt)

        # Cú vuốt cần có vận tốc tối thiểu (tránh dịch chuyển tay chậm chạp)
        if speed < 0.35:
            return None

        # 1. Kiểm tra Vuốt Ngang (Swipe Horizontal: Tua video trên YouTube / Cuộn ngang)
        # Tỷ lệ 1.25 tự nhiên hơn 1.7 rất nhiều vì khớp tay di chuyển theo hình vòng cung
        if abs(dx) > effective_thresh and abs(dx) > 1.25 * abs(dy):
            self.motion_history.clear()
            self.post_swipe_suppress_until = current_time + 0.40
            self.candidate_static_gesture = None
            self.static_gesture_frame_count = 0
            if dx > 0:
                return "SWIPE_RIGHT"
            else:
                return "SWIPE_LEFT"

        # 2. Kiểm tra Vuốt Dọc (Swipe Vertical: Lướt video TikTok / Shorts)
        if abs(dy) > effective_thresh and abs(dy) > 1.25 * abs(dx):
            self.motion_history.clear()
            self.post_swipe_suppress_until = current_time + 0.40
            self.candidate_static_gesture = None
            self.static_gesture_frame_count = 0
            # Trục y của MediaPipe: 0 ở trên, 1 ở dưới
            # Vuốt lên: tọa độ y giảm dần -> dy < 0
            if dy < 0:
                return "SWIPE_UP"
            else:
                return "SWIPE_DOWN"

        return None

    def process_frame(self, frame):
        """
        Xử lý 1 khung hình từ Camera:
        - Lật gương (nếu config bật)
        - Chạy MediaPipe Hands
        - Nhận diện cử chỉ tĩnh / động
        - Xử lý Hold to Lock / Unlock
        - Vẽ landmarks và Visual Overlay HUD trực tiếp lên frame
        - Trả về: (processed_frame, detected_gesture, action_info, is_locked)
        """
        if self.config.get("flip_mirror", True):
            frame = cv2.flip(frame, 1)

        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        now = time.time()
        detected_gesture = None
        action_triggered = None
        
        lock_gesture_target = self.config.get("lock_gesture", "PEACE_SIGN")
        lock_hold_time = self.config.get("lock_hold_time", 1.5)
        cooldown = self.config.get("cooldown", 0.8)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                landmarks = hand_landmarks.landmark
                
                # 1. Vẽ Skeleton Khung xương tay (nếu bật)
                if self.config.get("show_skeleton", True):
                    self.mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing_styles.get_default_hand_landmarks_style(),
                        self.mp_drawing_styles.get_default_hand_connections_style()
                    )

                # 2. Cập nhật lịch sử tâm bàn tay (Landmark 9 - đốt giữa)
                center_x = landmarks[9].x
                center_y = landmarks[9].y
                self.motion_history.append((center_x, center_y, now))

                palm_size = self.get_palm_size(landmarks)

                # Tính vận tốc di chuyển tức thời của bàn tay trong 0.06s - 0.15s gần nhất
                hand_speed = 0.0
                if len(self.motion_history) >= 2:
                    for pt in reversed(self.motion_history):
                        dt_hist = now - pt[2]
                        if dt_hist >= 0.06:
                            dist_moved = math.hypot(center_x - pt[0], center_y - pt[1])
                            hand_speed = dist_moved / max(0.001, dt_hist)
                            break

                is_hand_moving_fast = (hand_speed > 0.40)

                # 3. Lấy trạng thái ngón tay & nhận diện cử chỉ tĩnh
                fingers = self.get_fingers_status(landmarks)
                raw_static_gesture = self.detect_static_gesture(landmarks, fingers)
                
                # 4. Nhận diện cử chỉ vuốt (Swipe)
                swipe_gesture = self.detect_swipe(now, palm_size)

                # 5. Phân tách và chống nhầm lẫn giữa cử chỉ vuốt và cử chỉ tĩnh:
                if swipe_gesture:
                    # Ưu tiên cử chỉ vuốt động cao nhất
                    detected_gesture = swipe_gesture
                    self.candidate_static_gesture = None
                    self.static_gesture_frame_count = 0
                elif is_hand_moving_fast or (now < self.post_swipe_suppress_until):
                    # Bàn tay đang chuyển động nhanh (đang vung tay vuốt) hoặc vừa vuốt xong:
                    # Chặn hoàn toàn cử chỉ tĩnh để không bị kích hoạt nhầm Tăng/Giảm âm lượng!
                    detected_gesture = None
                    self.candidate_static_gesture = None
                    self.static_gesture_frame_count = 0
                else:
                    # Bàn tay đứng yên ổn định: Áp dụng cơ chế lọc rung (Debounce)
                    if raw_static_gesture and (raw_static_gesture == self.candidate_static_gesture):
                        self.static_gesture_frame_count += 1
                    else:
                        self.candidate_static_gesture = raw_static_gesture
                        self.static_gesture_frame_count = 1 if raw_static_gesture else 0

                    # Chỉ công nhận cử chỉ tĩnh nếu đã giữ ổn định ít nhất STATIC_CONFIRM_FRAMES
                    if self.static_gesture_frame_count >= self.STATIC_CONFIRM_FRAMES:
                        detected_gesture = raw_static_gesture
                    else:
                        detected_gesture = None

                # Kiểm tra xem có đang bật chế độ CHUỘT ẢO (Air Mouse) không
                is_air_mouse = self.config.get("enable_air_mouse", False)
                if is_air_mouse and not self.is_locked:
                    # Ưu tiên điều khiển chuột mượt mà, triệt tiêu xung đột với phím tắt Media
                    frame, mouse_state = self.mouse_controller.process(frame, landmarks, fingers)
                    detected_gesture = f"MOUSE: {mouse_state}"
                    action_triggered = None
                else:
                    # 6. Xử lý Logic KHÓA / MỞ KHÓA (Hold to Lock/Unlock)
                    if raw_static_gesture == lock_gesture_target:
                        if self.hold_start_time is None:
                            self.hold_start_time = now
                        
                        elapsed = now - self.hold_start_time
                        self.hold_progress = min(1.0, elapsed / lock_hold_time)

                        # Vẽ vòng tròn tiến trình Hold trực tiếp quanh cổ tay
                        wrist_px = int(landmarks[0].x * w)
                        wrist_py = int(landmarks[0].y * h)
                        radius = int(35 * (w / 640.0))
                        
                        # Vòng nền mờ
                        cv2.circle(frame, (wrist_px, wrist_py), radius, (80, 80, 80), 3)
                        # Góc quét cung tiến độ
                        angle = int(self.hold_progress * 360)
                        if angle > 0:
                            cv2.ellipse(frame, (wrist_px, wrist_py), (radius, radius),
                                        -90, 0, angle, (0, 255, 255), 4)

                        # Hiển thị chữ đếm %
                        percent_txt = f"{int(self.hold_progress * 100)}%"
                        cv2.putText(frame, percent_txt, (wrist_px - 18, wrist_py + 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

                        # Đã giữ đủ thời gian -> Toggle Khóa / Mở khóa
                        if elapsed >= lock_hold_time and (now - self.last_lock_toggle_time > 1.0):
                            self.is_locked = not self.is_locked
                            self.last_lock_toggle_time = now
                            self.hold_start_time = None
                            self.hold_progress = 0.0
                            
                            # Tạo action đặc biệt cho HUD
                            action_triggered = {
                                "action": "ĐÃ KHÓA CỬ CHỈ" if self.is_locked else "ĐÃ MỞ KHÓA CỬ CHỈ",
                                "key": None,
                                "icon": "🔒" if self.is_locked else "🔓",
                                "is_lock_event": True
                            }
                    else:
                        self.hold_start_time = None
                        self.hold_progress = 0.0

                    # 7. Nếu KHÔNG bị khóa -> Khớp lệnh hành động (Media Controls)
                    if not self.is_locked and detected_gesture and not action_triggered:
                        # Tra cứu ánh xạ theo Preset hiện tại
                        preset_key = self.config.get("current_preset", "youtube")
                        preset_data = self.config.get("presets", {}).get(preset_key, {})
                        mappings = preset_data.get("mappings", {})

                        if detected_gesture in mappings:
                            candidate_action = mappings[detected_gesture]
                            # Kiểm tra Cooldown
                            if now - self.last_action_time >= cooldown:
                                action_triggered = candidate_action
                                self.last_action_time = now
                                self.last_executed_gesture = detected_gesture
                                self.last_executed_action = candidate_action
        else:
            # Không phát hiện bàn tay
            self.motion_history.clear()
            self.hold_start_time = None
            self.hold_progress = 0.0
            self.candidate_static_gesture = None
            self.static_gesture_frame_count = 0
            if self.config.get("enable_air_mouse", False):
                frame, _ = self.mouse_controller.process(frame, None, None)

        # 7. Vẽ HUD thông tin lên Frame
        self._draw_hud(frame, detected_gesture, now, cooldown)

        return frame, detected_gesture, action_triggered, self.is_locked

    def _draw_hud(self, frame, detected_gesture, now, cooldown):
        """Vẽ thanh trạng thái OSD hiện đại ở góc trên khung hình camera."""
        h, w, _ = frame.shape
        
        # Banner nền mờ trên cùng
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (w - 10, 75), (20, 20, 25), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Trạng thái Lock / Air Mouse / Media Active
        is_air_mouse = self.config.get("enable_air_mouse", False)
        if self.is_locked:
            status_text = "LOCK: DANG CHO (KHOA CU CHI)"
            status_color = (0, 0, 255)  # Đỏ
            sub_text = "Giu cu chi Peace 2s de Mo khoa"
        elif is_air_mouse:
            status_text = "AIR MOUSE: DANG DIEU KHIEN CHUOT"
            status_color = (255, 165, 0)  # Cam/Xanh
            sub_text = f"Trang thai: {detected_gesture}"
        else:
            status_text = "ACTIVE: DANG NHAN DIEN"
            status_color = (0, 255, 0)  # Xanh lá
            sub_text = f"Cu chi: {detected_gesture if detected_gesture else 'Dang cho tay...'}"

        cv2.circle(frame, (30, 32), 8, status_color, -1)
        cv2.putText(frame, status_text, (48, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.65, status_color, 2)
        cv2.putText(frame, sub_text, (48, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)

        # Thanh Cooldown trực quan ở góc phải
        time_since_last = now - self.last_action_time
        if time_since_last < cooldown:
            cd_ratio = 1.0 - (time_since_last / cooldown)
            bar_w = 100
            bar_h = 10
            bar_x = w - 120
            bar_y = 30
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (80, 80, 80), -1)
            fill_w = int(bar_w * cd_ratio)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), (0, 165, 255), -1)
            cv2.putText(frame, "Cooldown", (bar_x, bar_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 165, 255), 1)
