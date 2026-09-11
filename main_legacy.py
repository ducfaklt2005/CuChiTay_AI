"""
Phiên bản thuật toán gốc trước khi nâng cấp lên GUI Desktop App.
Lưu lại để bạn tham khảo hoặc đối chiếu khi cần.
"""

import cv2
import mediapipe as mp
import pyautogui
import time
import math

# Khởi tạo MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.75,
    min_tracking_confidence=0.75
)
mp_draw = mp.solutions.drawing_utils

WINDOW_NAME = "Full Media Controller - AI"
cv2.namedWindow(WINDOW_NAME)

cap = cv2.VideoCapture(0)
last_action_time = 0
cooldown = 0.8  # Giảm cooldown xuống 0.8s để chỉnh âm lượng mượt hơn

def get_fingers_status(landmarks):
    fingers = []
    # Ngón cái (so sánh tọa độ X)
    fingers.append(1 if landmarks[4].x < landmarks[3].x else 0)
    # 4 ngón còn lại (so sánh tọa độ Y)
    for tip_id in [8, 12, 16, 20]:
        fingers.append(1 if landmarks[tip_id].y < landmarks[tip_id - 2].y else 0)
    return fingers

def is_ok_gesture(landmarks):
    distance = math.hypot(landmarks[4].x - landmarks[8].x, landmarks[4].y - landmarks[8].y)
    others_open = (landmarks[12].y < landmarks[10].y and 
                   landmarks[16].y < landmarks[14].y and 
                   landmarks[20].y < landmarks[18].y)
    return distance < 0.05 and others_open

def is_thumbs_up(landmarks):
    thumb_up = landmarks[4].y < landmarks[3].y
    others_closed = (landmarks[8].y > landmarks[6].y and
                     landmarks[12].y > landmarks[10].y and
                     landmarks[16].y > landmarks[14].y and
                     landmarks[20].y > landmarks[18].y)
    return thumb_up and others_closed

def is_thumbs_down(landmarks):
    thumb_down = landmarks[4].y > landmarks[3].y
    others_closed = (landmarks[8].y > landmarks[6].y and
                     landmarks[12].y > landmarks[10].y and
                     landmarks[16].y > landmarks[14].y and
                     landmarks[20].y > landmarks[18].y)
    return thumb_down and others_closed

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
        
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    current_action = "Dang cho cu chi..."
    key_to_press = None

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            landmarks = hand_landmarks.landmark
            
            fingers = get_fingers_status(landmarks)
            total_fingers = sum(fingers)
            now = time.time()

            # 1. Âm lượng (Thumbs Up / Thumbs Down)
            if is_thumbs_up(landmarks):
                current_action = "TANG AM LUONG (+)"
                key_to_press = 'volumeup'
            elif is_thumbs_down(landmarks):
                current_action = "GIAM AM LUONG (-)"
                key_to_press = 'volumedown'
            
            # 2. Toàn màn hình (OK Sign)
            elif is_ok_gesture(landmarks):
                current_action = "TOAN MAN HINH (F)"
                key_to_press = 'f'
                
            # 3. Điều khiển theo ngón tay
            elif total_fingers == 5:
                current_action = "PLAY / PAUSE (Space)"
                key_to_press = 'space'
            elif total_fingers == 0:
                current_action = "MUTE / UNMUTE (M)"
                key_to_press = 'm'
            elif total_fingers == 1 and fingers[1] == 1:
                current_action = "NEXT VIDEO (Down)"
                key_to_press = 'down'
            elif total_fingers == 1 and fingers[4] == 1:  # Ngón út
                current_action = "THA TIM / LIKE (L)"
                key_to_press = 'l'
            elif total_fingers == 2 and fingers[1] == 1 and fingers[2] == 1:
                current_action = "PREV VIDEO (Up)"
                key_to_press = 'up'

            # Bắn phím điều khiển
            if key_to_press and (now - last_action_time > cooldown):
                pyautogui.press(key_to_press)
                last_action_time = now

    cv2.putText(frame, f"Action: {current_action}", (20, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.imshow(WINDOW_NAME, frame)

    # Thoát an toàn
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:
        break

    try:
        if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
            break
    except Exception:
        break

cap.release()
cv2.destroyAllWindows()
