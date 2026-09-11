"""
Module Thực thi Lệnh Phím tắt (Action Executor)
Mô phỏng các phím bấm và tổ hợp phím hệ thống (Media keys, hotkeys YouTube, TikTok).
"""

import pyautogui
import threading

# Tắt failsafe của pyautogui để tránh exception ngoài ý muốn khi trỏ chuột vào góc màn hình
pyautogui.FAILSAFE = False

class ActionExecutor:
    def __init__(self, on_action_callback=None):
        self.on_action_callback = on_action_callback

    def execute(self, action_data):
        """
        Thực thi phím bấm an toàn trong background thread
        action_data: dict gồm {"action": str, "key": str, "icon": str}
        """
        if not action_data:
            return

        key = action_data.get("key")
        action_name = action_data.get("action", "")
        icon = action_data.get("icon", "⚡")

        # Gọi callback thông báo ra giao diện và HUD
        if self.on_action_callback:
            try:
                self.on_action_callback(action_data)
            except Exception as e:
                print(f"Lỗi callback action: {e}")

        if not key:
            return

        def _run_press():
            try:
                # Xử lý tổ hợp phím có dấu cộng (ví dụ: shift+n)
                if "+" in key:
                    parts = [p.strip().lower() for p in key.split("+")]
                    pyautogui.hotkey(*parts)
                else:
                    pyautogui.press(key.lower())
            except Exception as e:
                print(f"Lỗi khi bấm phím '{key}': {e}")

        # Chạy trong luồng riêng để không làm khựng luồng nhận diện camera
        thread = threading.Thread(target=_run_press, daemon=True)
        thread.start()
