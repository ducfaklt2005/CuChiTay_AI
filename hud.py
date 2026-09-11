"""
Module Cửa sổ Phản hồi Trực quan (Visual Feedback Toast / HUD)
Hiển thị popup thông báo bán trong suốt, bo góc, luôn nổi trên màn hình (Topmost)
khi có lệnh cử chỉ kích hoạt mà không làm mất tiêu điểm (Focus) của trình duyệt/video.
Phong cách Light Glassmorphism hiện đại (macOS / Clean Tech Style).
"""

import tkinter as tk
from tkinter import ttk

class HUDToast:
    def __init__(self, root):
        self.root = root
        self.toast_window = None
        self.hide_timer = None
        self.alpha = 0.0
        self.target_alpha = 0.95
        self.fade_step = 0.15

    def show(self, icon, action_name, subtext=""):
        """Hiển thị toast với icon và mô tả."""
        # Chạy trong luồng chính của Tkinter
        self.root.after(0, self._render_toast, icon, action_name, subtext)

    def _render_toast(self, icon, action_name, subtext):
        if self.hide_timer:
            self.root.after_cancel(self.hide_timer)
            self.hide_timer = None

        if self.toast_window is None or not self.toast_window.winfo_exists():
            self.toast_window = tk.Toplevel(self.root)
            self.toast_window.overrideredirect(True)
            self.toast_window.attributes("-topmost", True)
            self.toast_window.configure(bg="#E2E8F0")
            
            # Khung viền ngoài phong cách Glassmorphism sáng với viền điểm nhấn
            self.card = tk.Frame(
                self.toast_window,
                bg="#FFFFFF",
                bd=0,
                relief="flat",
                highlightbackground="#2563EB",
                highlightthickness=1.5
            )
            self.card.pack(fill="both", expand=True, padx=1, pady=1)

            # Icon lớn
            self.icon_label = tk.Label(
                self.card,
                text="",
                font=("Segoe UI Emoji", 24),
                bg="#FFFFFF",
                fg="#2563EB"
            )
            self.icon_label.pack(side="left", padx=(16, 12), pady=12)

            # Khung chữ
            text_frame = tk.Frame(self.card, bg="#FFFFFF")
            text_frame.pack(side="left", padx=(0, 20), pady=10)

            self.title_label = tk.Label(
                text_frame,
                text="",
                font=("Segoe UI", 12, "bold"),
                bg="#FFFFFF",
                fg="#0F172A"
            )
            self.title_label.pack(anchor="w")

            self.sub_label = tk.Label(
                text_frame,
                text="",
                font=("Segoe UI", 9),
                bg="#FFFFFF",
                fg="#64748B"
            )
            self.sub_label.pack(anchor="w")

        # Cập nhật nội dung
        self.icon_label.config(text=icon or "✨")
        self.title_label.config(text=action_name)
        self.sub_label.config(text=subtext or "Cử chỉ AI thực thi")

        # Căn vị trí ở góc trên bên phải màn hình desktop
        self.toast_window.update_idletasks()
        req_w = max(260, self.toast_window.winfo_reqwidth())
        req_h = max(68, self.toast_window.winfo_reqheight())
        screen_w = self.root.winfo_screenwidth()
        pos_x = screen_w - req_w - 30
        pos_y = 40
        self.toast_window.geometry(f"{req_w}x{req_h}+{pos_x}+{pos_y}")

        # Hiển thị và đặt độ mờ
        self.toast_window.attributes("-alpha", self.target_alpha)
        self.toast_window.deiconify()

        # Tự động ẩn sau 1.2 giây
        self.hide_timer = self.root.after(1200, self._hide_toast)

    def _hide_toast(self):
        if self.toast_window and self.toast_window.winfo_exists():
            self.toast_window.withdraw()
            self.hide_timer = None
