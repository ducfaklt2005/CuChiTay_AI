"""
Module Cửa sổ Xem trước Mini Thu nhỏ (Mini Live Preview Overlay)
Cửa sổ camera thu nhỏ luôn nổi trên các ứng dụng khác (Always on Top),
cho phép kéo thả tự do tới bất kỳ góc nào của màn hình.
Phong cách Light Modern Theme tinh tế với Header màu sáng và nút đóng hover đỏ.
"""

import tkinter as tk
from PIL import Image, ImageTk
import cv2

class MiniOverlayWindow:
    def __init__(self, root, on_close_callback=None):
        self.root = root
        self.on_close_callback = on_close_callback
        self.window = None
        self.label_video = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_visible = False
        self.current_photo = None

    def show(self):
        """Mở cửa sổ overlay mini."""
        if self.window is not None and self.window.winfo_exists():
            self.window.deiconify()
            self.is_visible = True
            return

        self.window = tk.Toplevel(self.root)
        self.window.title("AI Gesture - Mini Camera")
        self.window.attributes("-topmost", True)
        self.window.overrideredirect(True)  # Không viền hệ thống, tự vẽ thanh kéo
        self.window.configure(bg="#E2E8F0")

        # Kích thước cửa sổ thu nhỏ
        win_w = 262
        win_h = 210
        # Mặc định góc dưới bên phải màn hình
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = screen_w - win_w - 24
        pos_y = screen_h - win_h - 60
        self.window.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")

        # Khung viền thanh điều khiển kéo thả (Draggable header)
        self.header = tk.Frame(self.window, bg="#F1F5F9", height=30)
        self.header.pack(fill="x", side="top", padx=1, pady=(1, 0))
        self.header.pack_propagate(False)

        self.title_lbl = tk.Label(
            self.header,
            text="📷 Mini Camera Preview",
            font=("Segoe UI", 9, "bold"),
            bg="#F1F5F9",
            fg="#0F172A"
        )
        self.title_lbl.pack(side="left", padx=10)

        # Nút đóng với hiệu ứng hover màu đỏ
        self.btn_close = tk.Label(
            self.header,
            text="✕",
            font=("Segoe UI", 10, "bold"),
            bg="#F1F5F9",
            fg="#64748B",
            cursor="hand2",
            padx=8
        )
        self.btn_close.pack(side="right")
        self.btn_close.bind("<Button-1>", lambda e: self.hide())

        def _on_enter_close(e):
            self.btn_close.config(bg="#FEE2E2", fg="#DC2626")

        def _on_leave_close(e):
            self.btn_close.config(bg="#F1F5F9", fg="#64748B")

        self.btn_close.bind("<Enter>", _on_enter_close)
        self.btn_close.bind("<Leave>", _on_leave_close)

        # Gắn sự kiện kéo thả cửa sổ
        self.header.bind("<Button-1>", self._start_drag)
        self.header.bind("<B1-Motion>", self._on_drag)
        self.title_lbl.bind("<Button-1>", self._start_drag)
        self.title_lbl.bind("<B1-Motion>", self._on_drag)

        # Khung hiển thị video
        self.video_frame = tk.Frame(self.window, bg="#0F172A", bd=0)
        self.video_frame.pack(fill="both", expand=True, padx=1, pady=(1, 1))

        self.label_video = tk.Label(self.video_frame, bg="#0F172A")
        self.label_video.pack(fill="both", expand=True)

        self.is_visible = True

    def _start_drag(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def _on_drag(self, event):
        x = self.window.winfo_x() + (event.x - self.drag_start_x)
        y = self.window.winfo_y() + (event.y - self.drag_start_y)
        self.window.geometry(f"+{x}+{y}")

    def update_frame(self, cv_frame):
        """Nhận frame OpenCV từ camera thread và hiển thị lên mini overlay."""
        if not self.is_visible or self.window is None or not self.window.winfo_exists():
            return

        try:
            # Resize frame vừa với kích thước mini
            resized = cv2.resize(cv_frame, (260, 178))
            rgb_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_image)
            self.current_photo = ImageTk.PhotoImage(image=img)
            self.label_video.configure(image=self.current_photo)
        except Exception:
            pass

    def hide(self):
        """Ẩn cửa sổ mini overlay."""
        self.is_visible = False
        if self.window and self.window.winfo_exists():
            self.window.withdraw()
        if self.on_close_callback:
            self.on_close_callback()

    def toggle(self):
        """Bật/Tắt mini overlay."""
        if self.is_visible:
            self.hide()
        else:
            self.show()
