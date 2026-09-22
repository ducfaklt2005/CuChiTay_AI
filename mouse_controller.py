"""
Module Điều khiển Chuột Ảo Bằng Cử Chỉ Tay (Air Mouse Controller)
Tích hợp:
- Bộ lọc làm mượt chuyển động thích ứng (Adaptive Smoothing) triệt tiêu rung giật (Jitter-free)
- Khóa cứng vị trí (Position Freeze) khi Click để chống trượt và không bị nhầm thành kéo thả
- Hộp tương tác ảo (Virtual Active ROI Box) chống mỏi cơ vai (Gorilla Arm)
- Trạng thái phân tách rõ ràng: Move, Left Click, Drag & Drop, Right Click, Scroll, Idle
"""

import time
import math
from collections import deque
import pyautogui
import cv2

# Tắt failsafe của pyautogui
pyautogui.FAILSAFE = False


class AirMouseController:
    def __init__(self, config=None):
        self.config = config or {}
        
        # Lấy kích thước màn hình máy tính
        try:
            self.screen_w, self.screen_h = pyautogui.size()
        except Exception:
            self.screen_w, self.screen_h = 1920, 1080

        # Trạng thái bật/tắt chuột ảo
        self.is_enabled = self.config.get("enable_air_mouse", False)

        # Cấu hình độ nhạy và vùng hoạt động
        self.speed_multiplier = float(self.config.get("mouse_speed", 1.25))
        self.smooth_factor = float(self.config.get("mouse_smooth", 0.65))  # 0.1 (chậm mượt) -> 0.9 (nhạy tức thì)
        self.scroll_speed = int(self.config.get("mouse_scroll_speed", 45))
        
        # Tỷ lệ biên của Hộp tương tác ảo (Active ROI Box) trên khung hình camera
        # 18% lề trái/phải, 18% lề trên/dưới -> vùng giữa chiếm ~64% khung hình
        self.roi_margin_x = 0.18
        self.roi_margin_y = 0.18

        # Bộ lọc chuyển động EMA (Exponential Moving Average)
        self.curr_x = self.screen_w / 2.0
        self.curr_y = self.screen_h / 2.0
        self.prev_target_x = self.curr_x
        self.prev_target_y = self.curr_y

        # Ngưỡng Deadband (Vùng chết vi mô chống rung camera noise)
        self.deadband_px = 3.5

        # Lịch sử vị trí để thực hiện Anchor Rollback khi Click:
        # Lưu các tuple: (target_x, target_y, dist_thumb_index, timestamp)
        self.pos_history = deque(maxlen=15)

        # Cơ chế Khóa vị trí (Position Freeze) khi Click
        self.freeze_until = 0.0
        self.frozen_x = self.curr_x
        self.frozen_y = self.curr_y

        # Quản lý Click & Drag
        self.pinch_left_start = None
        self.is_dragging = False
        self.last_left_click_time = 0.0
        self.last_right_click_time = 0.0
        self.last_scroll_time = 0.0
        self.prev_scroll_y = None

        # Trạng thái hiển thị OSD
        self.current_state_text = "IDLE"
        self.current_state_color = (148, 163, 184)  # Slate 400

    def update_settings(self, config):
        """Cập nhật các tham số cấu hình."""
        self.config = config
        self.is_enabled = self.config.get("enable_air_mouse", False)
        self.speed_multiplier = float(self.config.get("mouse_speed", 1.25))
        self.smooth_factor = float(self.config.get("mouse_smooth", 0.65))
        self.scroll_speed = int(self.config.get("mouse_scroll_speed", 45))

    def _dist_2d(self, p1, p2):
        """Khoảng cách Euclid 2D giữa 2 điểm landmarks chuẩn hóa."""
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def _get_palm_size(self, landmarks):
        """Kích thước bàn tay chuẩn hóa làm thước đo quy đổi."""
        return max(0.01, self._dist_2d(landmarks[0], landmarks[9]))

    def process(self, frame, landmarks, fingers):
        """
        Xử lý 1 khung hình với landmarks bàn tay:
        - Điều khiển chuột desktop
        - Vẽ hộp ROI và visual reticle lên frame
        - Trả về frame đã vẽ và trạng thái
        """
        h, w, _ = frame.shape
        now = time.time()

        # 1. Vẽ Hộp tương tác ảo (Virtual Active ROI Box)
        roi_x1 = int(w * self.roi_margin_x)
        roi_y1 = int(h * self.roi_margin_y)
        roi_x2 = int(w * (1.0 - self.roi_margin_x))
        roi_y2 = int(h * (1.0 - self.roi_margin_y))

        # Khung viền mỏng tinh tế cho vùng hoạt động
        cv2.rectangle(frame, (roi_x1, roi_y1), (roi_x2, roi_y2), (230, 230, 230), 1)
        # 4 góc nhấn (Corner Accents)
        corner_len = 16
        # Góc trên-trái
        cv2.line(frame, (roi_x1, roi_y1), (roi_x1 + corner_len, roi_y1), (37, 99, 235), 2)
        cv2.line(frame, (roi_x1, roi_y1), (roi_x1, roi_y1 + corner_len), (37, 99, 235), 2)
        # Góc trên-phải
        cv2.line(frame, (roi_x2, roi_y1), (roi_x2 - corner_len, roi_y1), (37, 99, 235), 2)
        cv2.line(frame, (roi_x2, roi_y1), (roi_x2, roi_y1 + corner_len), (37, 99, 235), 2)
        # Góc dưới-trái
        cv2.line(frame, (roi_x1, roi_y2), (roi_x1 + corner_len, roi_y2), (37, 99, 235), 2)
        cv2.line(frame, (roi_x1, roi_y2), (roi_x1, roi_y2 - corner_len), (37, 99, 235), 2)
        # Góc dưới-phải
        cv2.line(frame, (roi_x2, roi_y2), (roi_x2 - corner_len, roi_y2), (37, 99, 235), 2)
        cv2.line(frame, (roi_x2, roi_y2), (roi_x2, roi_y2 - corner_len), (37, 99, 235), 2)

        if not self.is_enabled:
            return frame, "DISABLED"

        if landmarks is None or fingers is None:
            # Nếu đang kéo thả mà mất dấu tay -> tự động nhả chuột để không kẹt
            if self.is_dragging:
                try:
                    pyautogui.mouseUp(button="left")
                except Exception:
                    pass
                self.is_dragging = False
            self.current_state_text = "CHO TAY"
            self.current_state_color = (148, 163, 184)
            return frame, "NO_HAND"

        palm_size = self._get_palm_size(landmarks)
        index_tip = landmarks[8]
        index_dip = landmarks[7]
        thumb_tip = landmarks[4]
        middle_tip = landmarks[12]

        # Tọa độ ổn định kết hợp đầu ngón (8) và khớp đốt 2 (7) để giảm rung tự nhiên
        track_norm_x = index_tip.x * 0.70 + index_dip.x * 0.30
        track_norm_y = index_tip.y * 0.70 + index_dip.y * 0.30
        pt_x = int(track_norm_x * w)
        pt_y = int(track_norm_y * h)

        # 2. Phân tích các khoảng cách Pinch
        dist_thumb_index = self._dist_2d(thumb_tip, index_tip) / palm_size
        dist_thumb_middle = self._dist_2d(thumb_tip, middle_tip) / palm_size

        is_pinch_left = dist_thumb_index < 0.23
        is_pinch_right = (dist_thumb_middle < 0.23) and (not is_pinch_left)
        is_pre_pinch = (0.23 <= dist_thumb_index < 0.36)  # Vùng chuẩn bị bấm

        # 3. Phân loại trạng thái cử chỉ
        total_open = sum(fingers)
        # Ngón trỏ mở, ngón nhẫn & út gập
        is_pointing = (fingers[1] == 1 and fingers[3] == 0 and fingers[4] == 0)
        # Chế độ cuộn: ngón trỏ & giữa cùng mở song song, ngón nhẫn & út gập
        is_scroll_pose = (fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0)

        # ==================== LOGIC XỬ LÝ ====================

        # A. CHẾ ĐỘ CUỘN TRANG (Scroll Mode)
        if is_scroll_pose and not is_pinch_left and not is_pinch_right:
            self.current_state_text = "CUON TRANG (SCROLL)"
            self.current_state_color = (22, 163, 74)  # Green

            mid_y = (index_tip.y + middle_tip.y) / 2.0
            if self.prev_scroll_y is not None:
                dy = mid_y - self.prev_scroll_y
                if abs(dy) > 0.012 and (now - self.last_scroll_time > 0.04):
                    scroll_amount = int(-dy * self.scroll_speed * 12)
                    if scroll_amount != 0:
                        try:
                            pyautogui.scroll(scroll_amount)
                        except Exception:
                            pass
                    self.last_scroll_time = now
            self.prev_scroll_y = mid_y

            if self.is_dragging:
                pyautogui.mouseUp(button="left")
                self.is_dragging = False
            self.pinch_left_start = None

        # B. CHẾ ĐỘ CLICK PHẢI (Right Click)
        elif is_pinch_right:
            self.current_state_text = "CLICK PHAI (RIGHT CLICK)"
            self.current_state_color = (168, 85, 247)  # Purple

            self.freeze_until = now + 0.25

            if now - self.last_right_click_time > 0.45:
                try:
                    pyautogui.click(button="right")
                except Exception:
                    pass
                self.last_right_click_time = now

            self.prev_scroll_y = None

        # C. CHẾ ĐỘ CLICK TRÁI & KÉO THẢ (Left Click / Drag & Drop)
        elif is_pinch_left:
            self.prev_scroll_y = None

            if self.pinch_left_start is None:
                self.pinch_left_start = now
                
                # --- ANCHOR ROLLBACK: Quay về tọa độ ổn định lúc vừa rê tới nút ---
                # Tránh trường hợp khi hai ngón tay co lại làm con trỏ bị xô lệch
                anchor_pos = None
                for hist_x, hist_y, hist_dist, hist_t in reversed(self.pos_history):
                    if (now - hist_t >= 0.08) and hist_dist >= 0.30:
                        anchor_pos = (hist_x, hist_y)
                        break

                if anchor_pos is not None:
                    self.curr_x, self.curr_y = anchor_pos
                    try:
                        pyautogui.moveTo(int(self.curr_x), int(self.curr_y))
                    except Exception:
                        pass

                # Khóa cứng tọa độ trong 260ms đầu tiên của cú pinch
                self.freeze_until = now + 0.26

            hold_time = now - self.pinch_left_start

            if hold_time >= 0.35:
                # Giữ quá 0.35s -> Chuyển sang chế độ Kéo thả (Drag)
                if not self.is_dragging:
                    try:
                        pyautogui.mouseDown(button="left")
                    except Exception:
                        pass
                    self.is_dragging = True

                self.current_state_text = "DANG KEO THA (DRAGGING)"
                self.current_state_color = (220, 38, 38)  # Red
            else:
                self.current_state_text = "CHAM CHUOT (PINCH)"
                self.current_state_color = (217, 119, 6)  # Amber

        # D. KHI NHẢ PINCH TRÁI
        elif self.pinch_left_start is not None:
            hold_time = now - self.pinch_left_start
            self.pinch_left_start = None

            if self.is_dragging:
                try:
                    pyautogui.mouseUp(button="left")
                except Exception:
                    pass
                self.is_dragging = False
                self.current_state_text = "THA CHUOT (DROP)"
                self.current_state_color = (37, 99, 235)
            elif hold_time < 0.35:
                # Nhả nhanh -> Một cú Left Click chuẩn xác ngay tại điểm neo
                if now - self.last_left_click_time > 0.18:
                    try:
                        pyautogui.click(button="left")
                    except Exception:
                        pass
                    self.last_left_click_time = now
                self.current_state_text = "CLICK TRAI (LEFT CLICK)"
                self.current_state_color = (37, 99, 235)

            self.prev_scroll_y = None

        # E. CHẾ ĐỘ DI CHUYỂN CHUỘT (Move Mode)
        elif is_pointing and total_open <= 2:
            self.current_state_text = "DI CHUOT (MOVING)"
            self.current_state_color = (37, 99, 235)  # Blue
            self.prev_scroll_y = None

            # Tính toán vị trí trong Virtual ROI
            norm_x = (track_norm_x - self.roi_margin_x) / max(0.01, (1.0 - 2 * self.roi_margin_x))
            norm_y = (track_norm_y - self.roi_margin_y) / max(0.01, (1.0 - 2 * self.roi_margin_y))

            clamped_x = max(0.0, min(1.0, norm_x))
            clamped_y = max(0.0, min(1.0, norm_y))

            target_x = clamped_x * self.screen_w
            target_y = clamped_y * self.screen_h

            # Kiểm tra xem có đang trong thời gian Freeze (đóng băng) không
            if now >= self.freeze_until:
                # 1. PRE-PINCH DAMPENING: Nếu đang khép ngón chuẩn bị click -> Hãm phanh con trỏ
                if is_pre_pinch:
                    if dist_thumb_index < 0.28:
                        damp_factor = 0.0  # Đóng băng khi ngón tay cực gần nhau
                    else:
                        damp_factor = 0.15  # Giảm 85% tốc độ để không bị trượt khỏi button
                    self.current_state_text = "CHUAN BI CLICK (LOCKING)"
                    self.current_state_color = (217, 119, 6)
                else:
                    damp_factor = 1.0

                # 2. DEADBAND: Chống rung giật vi mô do camera noise
                delta_dist = math.hypot(target_x - self.prev_target_x, target_y - self.prev_target_y)
                if delta_dist >= self.deadband_px:
                    speed_boost = min(0.35, delta_dist / 600.0)
                    base_alpha = min(0.85, max(0.15, self.smooth_factor + speed_boost))
                    alpha = base_alpha * damp_factor

                    if alpha > 0:
                        self.curr_x = self.curr_x + alpha * (target_x - self.curr_x)
                        self.curr_y = self.curr_y + alpha * (target_y - self.curr_y)
                        self.prev_target_x = target_x
                        self.prev_target_y = target_y

                        try:
                            pyautogui.moveTo(int(self.curr_x), int(self.curr_y))
                        except Exception:
                            pass

                # Lưu vào lịch sử khi ngón tay đang ở trạng thái mở ổn định
                if dist_thumb_index >= 0.32:
                    self.pos_history.append((self.curr_x, self.curr_y, dist_thumb_index, now))

        # F. NGHỈ / DỪNG CHUỘT (Idle Mode - Xòe tay hoặc Nắm đấm)
        else:
            self.current_state_text = "NGHI CHUOT (IDLE)"
            self.current_state_color = (148, 163, 184)
            self.prev_scroll_y = None

            # Nếu đang drag mà xòe tay ra -> nhả chuột an toàn
            if self.is_dragging:
                try:
                    pyautogui.mouseUp(button="left")
                except Exception:
                    pass
                self.is_dragging = False

        # 4. Vẽ con trỏ ảo (Virtual Crosshair Reticle) trực tiếp lên khung hình
        cv2.circle(frame, (pt_x, pt_y), 9, self.current_state_color, -1)
        cv2.circle(frame, (pt_x, pt_y), 15, self.current_state_color, 2)

        # Đường nối ngón cái và ngón trỏ để người dùng quan sát khoảng cách Pinch
        thumb_pt = (int(thumb_tip.x * w), int(thumb_tip.y * h))
        cv2.line(frame, (pt_x, pt_y), thumb_pt, (200, 200, 200), 1)

        # Vẽ nhãn trạng thái OSD của Chuột
        cv2.putText(
            frame,
            f"MOUSE: {self.current_state_text}",
            (roi_x1 + 6, roi_y2 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            self.current_state_color,
            2
        )

        return frame, self.current_state_text
