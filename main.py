"""
=============================================================================
           ỨNG DỤNG ĐIỀU KHIỂN ĐA PHƯƠNG TIỆN BẰNG CỬ CHỈ TAY AI
                     (AI GESTURE MEDIA CONTROLLER)
=============================================================================
Tự động kích hoạt DPI sắc nét trên Windows, khởi tạo giao diện Desktop GUI,
kết nối MediaPipe Hands và hệ thống phím tắt đa nền tảng (YouTube & TikTok).
"""

import sys
import os
import ctypes
import tkinter as tk
from app_gui import ModernGestureApp

def enable_windows_dpi_awareness():
    """Kích hoạt độ phân giải cao High-DPI trên Windows để chữ và icon sắc nét."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

def main():
    enable_windows_dpi_awareness()
    
    root = tk.Tk()
    
    # Thiết lập icon cửa sổ nếu có hoặc dùng tiêu đề
    root.title("AI Gesture Media Controller - Trợ Lý Điều Khiển Cử Chỉ")
    
    # Khởi chạy ứng dụng
    app = ModernGestureApp(root)
    
    # Vòng lặp giao diện
    root.mainloop()

if __name__ == "__main__":
    main()