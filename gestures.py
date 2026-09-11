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
        
        # Lịch sử vị trí bàn tay để nhận diện Swipe
        # Lưu trữ các tuple: (x, y, timestamp)
        self.motion_history = deque(maxlen=15)
        
        # Biến trạng thái Khóa / Chờ
        self.is_locked = False
        self.hold_start_time = None
        self.hold_progress = 0.0  # 0.0 -> 1.0
        self.last_lock_toggle_time = 0
        
        # Cooldown giữa các lệnh điều khiển
        self.last_action_time = 0
        self.last_executed_gesture = None
        self.last_executed_action = None

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
        Sử dụng cả khoảng cách góc và vị trí tương đối để chuẩn xác cho mọi góc nghiêng.
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
        # So sánh khoảng cách từ đầu ngón đến cổ tay với khớp PIP đến cổ tay
        finger_ids = [(8, 6), (12, 10), (16, 14), (20, 18)]
        for idx, (tip_id, pip_id) in enumerate(finger_ids, start=1):
            d_tip = self.dist(landmarks[tip_id], wrist)
            d_pip = self.dist(landmarks[pip_id], wrist)
            # Nếu đầu ngón xa cổ tay hơn khớp giữa rõ rệt
            if d_tip > d_pip * 1.10 and landmarks[tip_id].y < landmarks[pip_id].y + (0.05 * palm_size):
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
                return "OK_PINCH"

        # 2. THUMBS UP: Ngón cái giơ thẳng lên, 4 ngón còn lại gập
        if fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
            # Ngón cái hướng lên trên
            if landmarks[4].y < landmarks[3].y - 0.03 and landmarks[4].y < landmarks[5].y:
                return "THUMBS_UP"
            # THUMBS DOWN: Ngón cái chúc xuống dưới
            elif landmarks[4].y > landmarks[3].y + 0.03 and landmarks[4].y > landmarks[5].y:
                return "THUMBS_DOWN"

        # 3. POINTING UP / POINTING DOWN (Chỉ 1 ngón trỏ mở)
        if fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
            # Vector từ MCP ngón trỏ (5) tới TIP (8)
            dx = landmarks[8].x - landmarks[5].x
            dy = landmarks[8].y - landmarks[5].y
            
            # Nếu ngón trỏ gần như thẳng đứng
            if abs(dy) > abs(dx) * 1.1:
                if dy < -0.05:  # Hướng lên
                    # Kiểm tra cử chỉ Shh (Suỵt - ngón trỏ đặt trước mặt/môi)
                    # Hoặc phân loại ngón trỏ chỉ lên
                    return "POINTING_UP"
                elif dy > 0.05:  # Hướng xuống
                    return "POINTING_DOWN"
            return "POINTING_UP"

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

        # 8. SHH GESTURE (Ngón trỏ đặt thẳng đứng, các ngón nắm lại)
        if fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0:
            return "SHH_GESTURE"

        return None

    def detect_swipe(self, current_time):
        """
        Nhận diện cử chỉ gạt tay / vuốt tay:
        SWIPE_LEFT, SWIPE_RIGHT, SWIPE_UP, SWIPE_DOWN.
        Dựa vào lịch sử di chuyển tâm bàn tay trong khoảng 0.15s - 0.35s.
        """
        if len(self.motion_history) < 6:
            return None

        # Lấy điểm cũ nhất cách đây khoảng 0.2s - 0.35s
        now_point = self.motion_history[-1]
        start_point = None
        for pt in self.motion_history:
            dt = now_point[2] - pt[2]
            if 0.15 <= dt <= 0.35:
                start_point = pt
                break

        if not start_point:
            return None

        dx = now_point[0] - start_point[0]
        dy = now_point[1] - start_point[1]
        dt = now_point[2] - start_point[2]
        
        threshold = self.config.get("swipe_threshold", 0.12)
        
        # Kiểm tra di chuyển ngang (Swipe Horizontal)
        if abs(dx) > threshold and abs(dx) > 1.7 * abs(dy):
            self.motion_history.clear()  # Xóa buffer để tránh kích hoạt lặp
            if dx > 0:
                return "SWIPE_RIGHT"
            else:
                return "SWIPE_LEFT"

        # Kiểm tra di chuyển dọc (Swipe Vertical)
        if abs(dy) > threshold and abs(dy) > 1.7 * abs(dx):
            self.motion_history.clear()
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

                # 3. Lấy trạng thái ngón tay & nhận diện cử chỉ tĩnh
                fingers = self.get_fingers_status(landmarks)
                static_gesture = self.detect_static_gesture(landmarks, fingers)
                
                # 4. Nhận diện cử chỉ vuốt (Swipe)
                swipe_gesture = self.detect_swipe(now)

                # Ưu tiên cử chỉ vuốt nếu có, nếu không thì lấy cử chỉ tĩnh
                detected_gesture = swipe_gesture if swipe_gesture else static_gesture

                # 5. Xử lý Logic KHÓA / MỞ KHÓA (Hold to Lock/Unlock)
                if static_gesture == lock_gesture_target:
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

                # 6. Nếu KHÔNG bị khóa -> Khớp lệnh hành động (Media Controls)
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

        # Trạng thái Lock
        if self.is_locked:
            status_text = "LOCK: DANG CHO (KHOA CU CHI)"
            status_color = (0, 0, 255)  # Đỏ
            sub_text = "Giu cu chi Peace 2s de Mo khoa"
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
