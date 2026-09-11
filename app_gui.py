"""
Module Giao diện Ứng dụng Desktop Chính (AI Gesture Controller GUI)
Xây dựng trên nền tảng Tkinter/ttk với phong cách Clean Tech Modern Light Theme,
tích hợp đầy đủ điều khiển YouTube & TikTok, tùy biến cử chỉ, độ nhạy, camera, HUD toast, và mini overlay.
"""

import time
import threading
import json
import copy
import cv2
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from config import (
    load_config, save_config, DEFAULT_CONFIG,
    GESTURE_NAMES_VI, AVAILABLE_KEYS
)
from gestures import GestureDetector
from action_executor import ActionExecutor
from hud import HUDToast
from overlay import MiniOverlayWindow

class ModernGestureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Gesture Media Controller - Trợ Lý Điều Khiển Cử Chỉ")
        self.root.geometry("1180x760")
        self.root.minsize(1050, 680)
        self.root.configure(bg="#F8FAFC")

        # Tải cấu hình
        self.config = load_config()
        
        # Khởi tạo các module
        self.gesture_detector = GestureDetector(self.config)
        self.action_executor = ActionExecutor(on_action_callback=self._on_action_executed)
        self.hud_toast = HUDToast(self.root)
        self.mini_overlay = MiniOverlayWindow(self.root, on_close_callback=self._on_mini_overlay_closed)

        # Biến trạng thái Camera Thread
        self.cap = None
        self.is_camera_running = False
        self.camera_thread = None
        self.current_photo = None
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 0

        # Áp dụng Theme
        self._setup_styles()
        
        # Xây dựng giao diện
        self._create_header()
        self._create_main_content()
        self._create_status_bar()

        # Tự động khởi động camera
        self.root.after(300, self.start_camera)

        # Bắt sự kiện đóng ứng dụng an toàn
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_styles(self):
        """Thiết lập màu sắc và font chữ cho ttk theo phong cách Modern Light Theme."""
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Bảng màu sắc chủ đạo Light Theme (Clean Tech Style)
        self.bg_main = "#F8FAFC"       # Slate 50 - Nền chính dịu mắt
        self.bg_card = "#FFFFFF"       # Trắng tinh khiết cho thẻ / bề mặt
        self.bg_panel = "#F1F5F9"      # Slate 100 - Nền sub-panel / input
        self.border_color = "#E2E8F0"  # Slate 200 - Viền và phân tách
        self.fg_text = "#0F172A"       # Slate 900 - Chữ chính tương phản cao
        self.fg_sub = "#64748B"        # Slate 500 - Chữ phụ mờ nhẹ
        self.accent_blue = "#2563EB"   # Blue 600 - Màu nhấn thao tác chính
        self.accent_green = "#16A34A"  # Green 600 - Trạng thái hoạt động
        self.accent_red = "#DC2626"    # Red 600 - Trạng thái khóa / dừng
        self.accent_amber = "#D97706"  # Amber 600 - Cảnh báo / nổi bật
        self.accent_peach = self.accent_amber  # Tương thích ngược

        # Cấu hình Notebook (Tabs)
        self.style.configure("TNotebook", background=self.bg_card, borderwidth=0)
        self.style.configure(
            "TNotebook.Tab",
            background=self.bg_panel,
            foreground=self.fg_sub,
            padding=[16, 10],
            font=("Segoe UI", 10, "bold"),
            borderwidth=0
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", "#DBEAFE"), ("active", self.border_color)],
            foreground=[("selected", self.accent_blue), ("active", self.fg_text)]
        )

        # Cấu hình Combobox
        self.style.configure(
            "TCombobox",
            fieldbackground="#FFFFFF",
            background=self.bg_panel,
            foreground=self.fg_text,
            darkcolor=self.border_color,
            lightcolor=self.border_color,
            bordercolor=self.border_color,
            arrowcolor="#334155"
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#FFFFFF")],
            selectbackground=[("readonly", "#E0F2FE")],
            selectforeground=[("readonly", self.fg_text)]
        )

        # Cấu hình Checkbutton
        self.style.configure(
            "TCheckbutton",
            background=self.bg_card,
            foreground=self.fg_text,
            font=("Segoe UI", 9)
        )
        self.style.map("TCheckbutton", background=[("active", self.bg_card)])

        # Cấu hình Treeview
        self.style.configure(
            "Treeview",
            background="#FFFFFF",
            foreground=self.fg_text,
            fieldbackground="#FFFFFF",
            rowheight=28,
            font=("Segoe UI", 9),
            borderwidth=0
        )
        self.style.configure(
            "Treeview.Heading",
            background=self.bg_panel,
            foreground="#334155",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padding=[6, 6]
        )
        self.style.map(
            "Treeview",
            background=[("selected", "#E0F2FE")],
            foreground=[("selected", "#0369A1")]
        )
        self.style.map(
            "Treeview.Heading",
            background=[("active", self.border_color)]
        )

    def _create_header(self):
        """Tạo thanh điều hướng Header trên cùng với phong cách Pure White và viền tinh tế."""
        header_frame = tk.Frame(
            self.root,
            bg=self.bg_card,
            highlightbackground=self.border_color,
            highlightthickness=1,
            height=66
        )
        header_frame.pack(fill="x", side="top", padx=12, pady=(10, 8))
        header_frame.pack_propagate(False)

        # Logo & Tiêu đề
        title_box = tk.Frame(header_frame, bg=self.bg_card)
        title_box.pack(side="left", padx=16, pady=8)

        lbl_icon = tk.Label(title_box, text="🖐️", font=("Segoe UI Emoji", 20), bg=self.bg_card)
        lbl_icon.pack(side="left", padx=(0, 10))

        text_box = tk.Frame(title_box, bg=self.bg_card)
        text_box.pack(side="left")
        lbl_title = tk.Label(
            text_box,
            text="AI GESTURE CONTROLLER",
            font=("Segoe UI", 13, "bold"),
            bg=self.bg_card,
            fg=self.fg_text
        )
        lbl_title.pack(anchor="w")
        lbl_desc = tk.Label(
            text_box,
            text="Điều khiển YouTube & TikTok không chạm qua Camera AI",
            font=("Segoe UI", 9),
            bg=self.bg_card,
            fg=self.fg_sub
        )
        lbl_desc.pack(anchor="w")

        # Khối Preset Selector
        preset_box = tk.Frame(header_frame, bg=self.bg_card)
        preset_box.pack(side="left", padx=24, pady=12)

        tk.Label(
            preset_box,
            text="Chế độ:",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_card,
            fg="#334155"
        ).pack(side="left", padx=(0, 6))

        self.preset_var = tk.StringVar(value=self.config.get("current_preset", "youtube"))
        self.preset_combo = ttk.Combobox(
            preset_box,
            textvariable=self.preset_var,
            values=["youtube", "tiktok", "custom"],
            state="readonly",
            width=14,
            font=("Segoe UI", 9, "bold")
        )
        self.preset_combo.pack(side="left")
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_change)

        # Nút Bật / Khóa Cử Chỉ Nhanh
        is_locked_now = getattr(self.gesture_detector, "is_locked", False)
        lock_bg = "#FEE2E2" if is_locked_now else "#DCFCE7"
        lock_fg = "#B91C1C" if is_locked_now else "#15803D"
        lock_text = "🔒 ĐÃ KHÓA (CHẾ ĐỘ CHỜ)" if is_locked_now else "🔓 ĐANG NHẬN DIỆN"

        self.btn_lock_toggle = tk.Button(
            header_frame,
            text=lock_text,
            font=("Segoe UI", 9, "bold"),
            bg=lock_bg,
            fg=lock_fg,
            activebackground="#BBF7D0",
            activeforeground="#15803D",
            bd=0,
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._toggle_lock_state
        )
        self.btn_lock_toggle.pack(side="right", padx=(10, 16), pady=14)

        # Nút Bật / Tắt Camera (Neutral slate style)
        self.btn_camera_toggle = tk.Button(
            header_frame,
            text="⏹️ Dừng Camera",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_panel,
            fg="#334155",
            activebackground=self.border_color,
            activeforeground=self.fg_text,
            bd=0,
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.toggle_camera
        )
        self.btn_camera_toggle.pack(side="right", padx=6, pady=14)

    def _create_main_content(self):
        """Tạo thân chính chia làm 2 cột: Cột xem Camera và Cột Tab điều khiển."""
        main_box = tk.Frame(self.root, bg=self.bg_main)
        main_box.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        # ================= CỘT TRÁI: CAMERA PREVIEW =================
        left_frame = tk.Frame(
            main_box,
            bg=self.bg_card,
            highlightbackground=self.border_color,
            highlightthickness=1,
            width=540
        )
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        # Tiêu đề Camera
        cam_header = tk.Frame(left_frame, bg=self.bg_card)
        cam_header.pack(fill="x", padx=14, pady=(12, 6))
        
        tk.Label(
            cam_header,
            text="📹 Xem trước Camera Trực tiếp",
            font=("Segoe UI", 11, "bold"),
            bg=self.bg_card,
            fg=self.fg_text
        ).pack(side="left")

        # Pill-badge style cho FPS Indicator
        self.lbl_fps = tk.Label(
            cam_header,
            text="FPS: 0",
            font=("Segoe UI", 9, "bold"),
            bg="#DCFCE7",
            fg="#15803D",
            padx=10,
            pady=2
        )
        self.lbl_fps.pack(side="right")

        # Khung chứa hình ảnh Camera với nền tối trung tính (#0F172A)
        self.cam_canvas_frame = tk.Frame(
            left_frame,
            bg="#0F172A",
            bd=0,
            highlightbackground=self.border_color,
            highlightthickness=1
        )
        self.cam_canvas_frame.pack(fill="both", expand=True, padx=14, pady=4)

        self.lbl_video = tk.Label(
            self.cam_canvas_frame,
            bg="#0F172A",
            text="Đang khởi động Camera...",
            font=("Segoe UI", 11),
            fg="#94A3B8"
        )
        self.lbl_video.pack(fill="both", expand=True)

        # Thanh nút tiện ích dưới Camera
        cam_tools = tk.Frame(left_frame, bg=self.bg_card)
        cam_tools.pack(fill="x", padx=14, pady=(8, 14))

        # Nút Bật / Tắt Mini Overlay
        self.btn_mini_overlay = tk.Button(
            cam_tools,
            text="📺 Cửa Sổ Mini Luôn Nổi",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_panel,
            fg=self.accent_blue,
            activebackground="#DBEAFE",
            bd=0,
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._toggle_mini_overlay
        )
        self.btn_mini_overlay.pack(side="left")

        # Checkbox Flip Mirror
        self.var_flip = tk.BooleanVar(value=self.config.get("flip_mirror", True))
        chk_flip = tk.Checkbutton(
            cam_tools,
            text="Lật gương (Mirror)",
            variable=self.var_flip,
            bg=self.bg_card,
            fg=self.fg_text,
            selectcolor=self.bg_panel,
            activebackground=self.bg_card,
            activeforeground=self.fg_text,
            font=("Segoe UI", 9),
            command=self._on_flip_change
        )
        chk_flip.pack(side="left", padx=12)

        # Checkbox Skeleton
        self.var_skeleton = tk.BooleanVar(value=self.config.get("show_skeleton", True))
        chk_skel = tk.Checkbutton(
            cam_tools,
            text="Hiện khung xương tay",
            variable=self.var_skeleton,
            bg=self.bg_card,
            fg=self.fg_text,
            selectcolor=self.bg_panel,
            activebackground=self.bg_card,
            activeforeground=self.fg_text,
            font=("Segoe UI", 9),
            command=self._on_skeleton_change
        )
        chk_skel.pack(side="left")

        # ================= CỘT PHẢI: TABS CONTROL =================
        right_frame = tk.Frame(
            main_box,
            bg=self.bg_card,
            highlightbackground=self.border_color,
            highlightthickness=1,
            width=540
        )
        right_frame.pack(side="right", fill="both", expand=True, padx=(6, 0))

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=6)

        # 3 Tabs
        self.tab_dashboard = tk.Frame(self.notebook, bg=self.bg_card)
        self.tab_mappings = tk.Frame(self.notebook, bg=self.bg_card)
        self.tab_settings = tk.Frame(self.notebook, bg=self.bg_card)

        self.notebook.add(self.tab_dashboard, text="  📊 Bảng Điều Khiển  ")
        self.notebook.add(self.tab_mappings, text="  🎮 Ánh Xạ Cử Chỉ  ")
        self.notebook.add(self.tab_settings, text="  ⚙️ Cài Đặt Hệ Thống  ")

        self._build_dashboard_tab()
        self._build_mappings_tab()
        self._build_settings_tab()

    # -------------------------------------------------------------
    # TAB 1: BẢNG ĐIỀU KHIỂN & NHẬT KÝ
    # -------------------------------------------------------------
    def _build_dashboard_tab(self):
        # Khối thẻ trạng thái thời gian thực
        status_cards = tk.Frame(self.tab_dashboard, bg=self.bg_card)
        status_cards.pack(fill="x", padx=14, pady=10)

        # Card 1: Cử chỉ nhận diện tức thời (Modern Rounded Look Card)
        card1 = tk.Frame(
            status_cards,
            bg="#F8FAFC",
            highlightbackground=self.border_color,
            highlightthickness=1,
            bd=0,
            padx=14,
            pady=10
        )
        card1.pack(side="left", fill="both", expand=True, padx=(0, 6))

        tk.Label(
            card1,
            text="CỬ CHỈ ĐANG BẮT ĐƯỢC",
            font=("Segoe UI", 8, "bold"),
            bg="#F8FAFC",
            fg=self.fg_sub
        ).pack(anchor="w")
        self.lbl_current_gesture = tk.Label(
            card1,
            text="Đang đợi tay...",
            font=("Segoe UI", 12, "bold"),
            bg="#F8FAFC",
            fg=self.accent_blue
        )
        self.lbl_current_gesture.pack(anchor="w", pady=(4, 0))

        # Card 2: Lệnh thực thi gần nhất (Modern Rounded Look Card)
        card2 = tk.Frame(
            status_cards,
            bg="#F8FAFC",
            highlightbackground=self.border_color,
            highlightthickness=1,
            bd=0,
            padx=14,
            pady=10
        )
        card2.pack(side="right", fill="both", expand=True, padx=(6, 0))

        tk.Label(
            card2,
            text="LỆNH ĐÃ GỬI GẦN NHẤT",
            font=("Segoe UI", 8, "bold"),
            bg="#F8FAFC",
            fg=self.fg_sub
        ).pack(anchor="w")
        self.lbl_last_action = tk.Label(
            card2,
            text="Chưa có lệnh nào",
            font=("Segoe UI", 12, "bold"),
            bg="#F8FAFC",
            fg=self.accent_green
        )
        self.lbl_last_action.pack(anchor="w", pady=(4, 0))

        # Thanh Cooldown trực quan
        cd_box = tk.Frame(self.tab_dashboard, bg=self.bg_card)
        cd_box.pack(fill="x", padx=14, pady=(2, 8))
        self.lbl_cd_status = tk.Label(
            cd_box,
            text="⚡ Trạng thái: Sẵn sàng nhận lệnh",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_card,
            fg=self.accent_green
        )
        self.lbl_cd_status.pack(anchor="w")

        # Bảng Hướng dẫn Cử chỉ Nhanh của Mode hiện tại
        guide_frame = tk.LabelFrame(
            self.tab_dashboard,
            text=" 💡 Cử Chỉ Nổi Bật Chế Độ Này ",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_card,
            fg=self.accent_amber,
            highlightbackground=self.border_color,
            highlightthickness=1,
            padx=12,
            pady=8
        )
        guide_frame.pack(fill="x", padx=14, pady=4)

        self.lbl_mode_guide = tk.Label(
            guide_frame,
            text="",
            font=("Segoe UI", 9),
            bg=self.bg_card,
            fg="#334155",
            justify="left"
        )
        self.lbl_mode_guide.pack(anchor="w")
        self._update_guide_text()

        # Nhật ký Lệnh (Action Log) phong cách Light
        log_frame = tk.LabelFrame(
            self.tab_dashboard,
            text=" 📝 Lịch Sử Nhận Lệnh Thời Gian Thực ",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_card,
            fg=self.fg_sub,
            highlightbackground=self.border_color,
            highlightthickness=1,
            padx=8,
            pady=6
        )
        log_frame.pack(fill="both", expand=True, padx=14, pady=(8, 12))

        log_inner = tk.Frame(log_frame, bg=self.border_color, padx=1, pady=1)
        log_inner.pack(fill="both", expand=True)

        self.log_listbox = tk.Listbox(
            log_inner,
            bg="#FFFFFF",
            fg="#334155",
            font=("Consolas", 9),
            bd=0,
            highlightthickness=0,
            selectbackground="#E0F2FE",
            selectforeground="#0369A1"
        )
        scrollbar = ttk.Scrollbar(log_inner, orient="vertical", command=self.log_listbox.yview)
        self.log_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log_listbox.pack(side="left", fill="both", expand=True)

    def _update_guide_text(self):
        """Cập nhật văn bản hướng dẫn nhanh theo preset."""
        preset = self.preset_var.get()
        if preset == "youtube":
            guide = (
                "• ✋ Xòe tay / ✊ Nắm đấm : Play / Pause video (Phím Space)\n"
                "• ☝️ Trỏ lên / 👇 Trỏ xuống : Tăng / Giảm âm lượng (+ / -)\n"
                "• 👉 Gạt phải / 👈 Gạt trái : Tua tới 10s / Tua lùi 10s (Right / Left)\n"
                "• 👆 Vuốt lên : Chuyển video kế tiếp (Shift + N)\n"
                "• 👌 Chắp 2 ngón (OK) : Bật/Tắt toàn màn hình (Phím F)\n"
                "• ✌️ Giữ Peace 1.5s : Bật / Khóa cử chỉ (Chống kích hoạt nhầm khi uống nước)"
            )
        elif preset == "tiktok":
            guide = (
                "• 👆 Vuốt lên (Swipe Up) : Lướt video tiếp theo (Down / Cuộn trang)\n"
                "• 👇 Vuốt xuống (Swipe Down) : Xem lại video trước (Up)\n"
                "• 👍 Thumbs Up / 🤙 Ngón út : Thả tim video (Phím L)\n"
                "• 🤫 Đặt ngón trỏ lên môi / ✊ Nắm đấm : Tắt / Bật tiếng (Phím M)\n"
                "• ✋ Xòe bàn tay : Tạm dừng / Phát video (Space)\n"
                "• ✌️ Giữ Peace 1.5s : Bật / Khóa cử chỉ an toàn"
            )
        else:
            guide = "Chế độ Tùy biến: Tự do gán cử chỉ sang phím tắt mong muốn ở tab 'Ánh Xạ Cử Chỉ'."
        self.lbl_mode_guide.config(text=guide)

    # -------------------------------------------------------------
    # TAB 2: ÁNH XẠ CỬ CHỈ (MAPPING CUSTOMIZATION)
    # -------------------------------------------------------------
    def _build_mappings_tab(self):
        top_bar = tk.Frame(self.tab_mappings, bg=self.bg_card)
        top_bar.pack(fill="x", padx=14, pady=10)

        tk.Label(
            top_bar,
            text="Tùy biến hành động và phím tắt cho từng cử chỉ:",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_card,
            fg=self.fg_text
        ).pack(side="left")

        btn_reset_map = tk.Button(
            top_bar,
            text="🔄 Khôi phục Preset",
            font=("Segoe UI", 8, "bold"),
            bg=self.bg_panel,
            fg=self.accent_amber,
            activebackground=self.border_color,
            bd=0,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._reset_current_preset_mappings
        )
        btn_reset_map.pack(side="right")

        # Treeview danh sách cử chỉ với viền nhẹ và màu xen kẽ
        tree_frame = tk.Frame(
            self.tab_mappings,
            bg=self.border_color,
            bd=0,
            padx=1,
            pady=1
        )
        tree_frame.pack(fill="both", expand=True, padx=14, pady=4)

        columns = ("gesture", "action", "key", "desc")
        self.map_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        self.map_tree.heading("gesture", text="Cử chỉ nhận diện")
        self.map_tree.heading("action", text="Hành động mô phỏng")
        self.map_tree.heading("key", text="Phím tắt hệ thống")
        self.map_tree.heading("desc", text="Mô tả chi tiết")

        self.map_tree.column("gesture", width=140, anchor="w")
        self.map_tree.column("action", width=130, anchor="w")
        self.map_tree.column("key", width=90, anchor="center")
        self.map_tree.column("desc", width=180, anchor="w")

        # Cấu hình màu sắc hàng xen kẽ (Zebra Striping)
        self.map_tree.tag_configure("even", background="#FFFFFF")
        self.map_tree.tag_configure("odd", background="#F8FAFC")

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.map_tree.yview)
        self.map_tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y")
        self.map_tree.pack(side="left", fill="both", expand=True)

        self.map_tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Khung chỉnh sửa (Edit Box) với nền sáng và viền #CBD5E1
        edit_frame = tk.LabelFrame(
            self.tab_mappings,
            text=" ✏️ Chỉnh Sửa Cử Chỉ Đang Chọn ",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_card,
            fg=self.accent_blue,
            highlightbackground=self.border_color,
            highlightthickness=1,
            padx=12,
            pady=10
        )
        edit_frame.pack(fill="x", padx=14, pady=(8, 12))

        # Dòng 1: Chọn cử chỉ & Tên hành động
        row1 = tk.Frame(edit_frame, bg=self.bg_card)
        row1.pack(fill="x", pady=4)

        tk.Label(row1, text="Cử chỉ:", font=("Segoe UI", 9), bg=self.bg_card, fg=self.fg_text).pack(side="left")
        self.edit_gesture_lbl = tk.Label(
            row1,
            text="(Chưa chọn)",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_card,
            fg=self.accent_blue
        )
        self.edit_gesture_lbl.pack(side="left", padx=(6, 20))

        tk.Label(row1, text="Hành động:", font=("Segoe UI", 9), bg=self.bg_card, fg=self.fg_text).pack(side="left")
        self.entry_action_name = tk.Entry(
            row1,
            font=("Segoe UI", 9),
            bg="#FFFFFF",
            fg=self.fg_text,
            insertbackground=self.fg_text,
            highlightbackground="#CBD5E1",
            highlightcolor=self.accent_blue,
            highlightthickness=1,
            bd=0,
            width=22
        )
        self.entry_action_name.pack(side="left", padx=(6, 20))

        # Dòng 2: Chọn phím tắt & Icon & Nút Lưu
        row2 = tk.Frame(edit_frame, bg=self.bg_card)
        row2.pack(fill="x", pady=4)

        tk.Label(row2, text="Phím tắt:", font=("Segoe UI", 9), bg=self.bg_card, fg=self.fg_text).pack(side="left")
        self.edit_key_var = tk.StringVar()
        key_choices = [k[0] for k in AVAILABLE_KEYS]
        self.key_combo = ttk.Combobox(
            row2,
            textvariable=self.edit_key_var,
            values=key_choices,
            width=14,
            font=("Segoe UI", 9)
        )
        self.key_combo.pack(side="left", padx=(6, 15))

        tk.Label(row2, text="Icon:", font=("Segoe UI", 9), bg=self.bg_card, fg=self.fg_text).pack(side="left")
        self.entry_icon = tk.Entry(
            row2,
            font=("Segoe UI Emoji", 10),
            bg="#FFFFFF",
            fg=self.fg_text,
            insertbackground=self.fg_text,
            highlightbackground="#CBD5E1",
            highlightcolor=self.accent_blue,
            highlightthickness=1,
            bd=0,
            width=6
        )
        self.entry_icon.pack(side="left", padx=(6, 20))

        btn_save_mapping = tk.Button(
            row2,
            text="💾 Cập Nhật Ánh Xạ",
            font=("Segoe UI", 9, "bold"),
            bg=self.accent_blue,
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            bd=0,
            relief="flat",
            padx=14,
            pady=5,
            cursor="hand2",
            command=self._save_selected_mapping
        )
        btn_save_mapping.pack(side="right")

        self._populate_mappings_tree()

    def _populate_mappings_tree(self):
        """Đổ dữ liệu ánh xạ cử chỉ vào Treeview với màu hàng xen kẽ."""
        for item in self.map_tree.get_children():
            self.map_tree.delete(item)

        preset_key = self.preset_var.get()
        preset_data = self.config.get("presets", {}).get(preset_key, {})
        mappings = preset_data.get("mappings", {})

        row_index = 0
        for g_code, g_name in GESTURE_NAMES_VI.items():
            if g_code in mappings:
                m = mappings[g_code]
                row_tag = "even" if row_index % 2 == 0 else "odd"
                self.map_tree.insert(
                    "",
                    "end",
                    iid=g_code,
                    values=(
                        f"{m.get('icon', '⚡')} {g_name}",
                        m.get("action", ""),
                        m.get("key", ""),
                        m.get("desc", "")
                    ),
                    tags=(row_tag,)
                )
                row_index += 1

    def _on_tree_select(self, event):
        selected = self.map_tree.selection()
        if not selected:
            return
        g_code = selected[0]
        preset_key = self.preset_var.get()
        m = self.config.get("presets", {}).get(preset_key, {}).get("mappings", {}).get(g_code, {})
        
        self.edit_gesture_lbl.config(text=GESTURE_NAMES_VI.get(g_code, g_code))
        self.entry_action_name.delete(0, "end")
        self.entry_action_name.insert(0, m.get("action", ""))
        self.edit_key_var.set(m.get("key", ""))
        self.entry_icon.delete(0, "end")
        self.entry_icon.insert(0, m.get("icon", "⚡"))

    def _save_selected_mapping(self):
        selected = self.map_tree.selection()
        if not selected:
            messagebox.showinfo("Thông báo", "Vui lòng chọn một cử chỉ trong bảng để chỉnh sửa.")
            return

        g_code = selected[0]
        action_name = self.entry_action_name.get().strip()
        key_press = self.edit_key_var.get().strip()
        icon = self.entry_icon.get().strip() or "⚡"

        if not action_name or not key_press:
            messagebox.showwarning("Cảnh báo", "Tên hành động và phím tắt không được để trống.")
            return

        preset_key = self.preset_var.get()
        self.config["presets"][preset_key]["mappings"][g_code] = {
            "action": action_name,
            "key": key_press,
            "icon": icon,
            "desc": f"{GESTURE_NAMES_VI.get(g_code, g_code)}: {action_name}"
        }

        save_config(self.config)
        self.gesture_detector.update_settings(self.config)
        self._populate_mappings_tree()
        messagebox.showinfo("Thành công", f"Đã cập nhật cử chỉ '{GESTURE_NAMES_VI.get(g_code, g_code)}'!")

    def _reset_current_preset_mappings(self):
        preset_key = self.preset_var.get()
        if preset_key in DEFAULT_CONFIG["presets"]:
            self.config["presets"][preset_key] = json.loads(json.dumps(DEFAULT_CONFIG["presets"][preset_key]))
            save_config(self.config)
            self.gesture_detector.update_settings(self.config)
            self._populate_mappings_tree()
            messagebox.showinfo("Thông báo", f"Đã khôi phục cài đặt mặc định cho chế độ '{preset_key}'.")

    # -------------------------------------------------------------
    # TAB 3: CÀI ĐẶT HỆ THỐNG & ĐỘ NHẠY
    # -------------------------------------------------------------
    def _build_settings_tab(self):
        container = tk.Frame(self.tab_settings, bg=self.bg_card)
        container.pack(fill="both", expand=True, padx=16, pady=12)

        # 1. Chọn Camera đầu vào
        cam_group = tk.LabelFrame(
            container,
            text=" 📷 Thiết Bị Camera Đầu Vào ",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_card,
            fg=self.fg_text,
            highlightbackground=self.border_color,
            highlightthickness=1,
            padx=12,
            pady=10
        )
        cam_group.pack(fill="x", pady=5)

        tk.Label(
            cam_group,
            text="Cổng Camera (Index):",
            font=("Segoe UI", 9),
            bg=self.bg_card,
            fg=self.fg_text
        ).pack(side="left")
        
        self.cam_index_var = tk.IntVar(value=self.config.get("camera_index", 0))
        self.combo_cam = ttk.Combobox(
            cam_group,
            textvariable=self.cam_index_var,
            values=[0, 1, 2, 3],
            width=6,
            state="readonly"
        )
        self.combo_cam.pack(side="left", padx=10)

        btn_apply_cam = tk.Button(
            cam_group,
            text="Áp dụng & Khởi động lại Camera",
            font=("Segoe UI", 8, "bold"),
            bg=self.bg_panel,
            fg=self.accent_blue,
            activebackground=self.border_color,
            bd=0,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._change_camera_index
        )
        btn_apply_cam.pack(side="left", padx=10)

        # 2. Độ nhạy & Ngưỡng nhận diện (Sliders)
        slider_group = tk.LabelFrame(
            container,
            text=" 🎚️ Tinh Chỉnh Độ Nhạy & Cooldown ",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_card,
            fg=self.fg_text,
            highlightbackground=self.border_color,
            highlightthickness=1,
            padx=12,
            pady=10
        )
        slider_group.pack(fill="x", pady=6)

        # Slider Cooldown
        self.scale_cooldown = self._create_slider_row(
            slider_group, "Thời gian Cooldown (giữa 2 lệnh):",
            from_=0.3, to=2.5, resolution=0.1, default=self.config.get("cooldown", 0.8), unit="giây"
        )

        # Slider Lock Hold Time
        self.scale_lock_hold = self._create_slider_row(
            slider_group, "Thời gian giữ để Khóa/Mở (Hold Lock):",
            from_=1.0, to=3.0, resolution=0.1, default=self.config.get("lock_hold_time", 1.5), unit="giây"
        )

        # Slider Confidence
        self.scale_confidence = self._create_slider_row(
            slider_group, "Độ tin cậy nhận diện (Confidence):",
            from_=0.5, to=0.95, resolution=0.05, default=self.config.get("detection_confidence", 0.75), unit=""
        )

        # Slider Swipe Threshold
        self.scale_swipe = self._create_slider_row(
            slider_group, "Ngưỡng gạt tay (Swipe Sensitivity):",
            from_=0.08, to=0.25, resolution=0.01, default=self.config.get("swipe_threshold", 0.12), unit=""
        )

        # 3. Tùy chọn Visual Feedback Toast
        ux_group = tk.LabelFrame(
            container,
            text=" 🔔 Trải Nghiệm Người Dùng (UX) ",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_card,
            fg=self.fg_text,
            highlightbackground=self.border_color,
            highlightthickness=1,
            padx=12,
            pady=10
        )
        ux_group.pack(fill="x", pady=6)

        self.var_toast = tk.BooleanVar(value=self.config.get("enable_toast", True))
        chk_toast = tk.Checkbutton(
            ux_group,
            text="Bật cửa sổ thông báo Visual Toast (HUD bán trong suốt góc màn hình)",
            variable=self.var_toast,
            bg=self.bg_card,
            fg=self.fg_text,
            selectcolor=self.bg_panel,
            activebackground=self.bg_card,
            activeforeground=self.fg_text,
            font=("Segoe UI", 9)
        )
        chk_toast.pack(anchor="w")

        # Nút Lưu tất cả cài đặt
        btn_box = tk.Frame(container, bg=self.bg_card)
        btn_box.pack(fill="x", pady=12)

        btn_save_all = tk.Button(
            btn_box,
            text="💾 LƯU TOÀN BỘ CÀI ĐẶT",
            font=("Segoe UI", 10, "bold"),
            bg=self.accent_green,
            fg="#FFFFFF",
            activebackground="#15803D",
            activeforeground="#FFFFFF",
            bd=0,
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
            command=self._save_all_settings
        )
        btn_save_all.pack(side="left", padx=(0, 10))

        btn_restore_all = tk.Button(
            btn_box,
            text="🔄 Khôi Phục Mặc Định Gốc",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_panel,
            fg=self.accent_red,
            activebackground="#FEE2E2",
            activeforeground=self.accent_red,
            bd=0,
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._restore_full_defaults
        )
        btn_restore_all.pack(side="left")

    def _create_slider_row(self, parent, label_text, from_, to, resolution, default, unit):
        row = tk.Frame(parent, bg=self.bg_card)
        row.pack(fill="x", pady=3)

        lbl = tk.Label(
            row,
            text=label_text,
            font=("Segoe UI", 9),
            bg=self.bg_card,
            fg=self.fg_text,
            width=32,
            anchor="w"
        )
        lbl.pack(side="left")

        val_lbl = tk.Label(
            row,
            text=f"{default:.2f} {unit}",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_card,
            fg=self.accent_blue,
            width=10,
            anchor="w"
        )

        def _on_val_change(val):
            val_lbl.config(text=f"{float(val):.2f} {unit}")

        scale = tk.Scale(
            row,
            from_=from_,
            to=to,
            resolution=resolution,
            orient="horizontal",
            bg=self.bg_card,
            fg=self.fg_text,
            highlightthickness=0,
            bd=0,
            troughcolor=self.border_color,
            activebackground=self.accent_blue,
            command=_on_val_change,
            showvalue=0,
            length=180
        )
        scale.set(default)
        scale.pack(side="left", padx=10)
        val_lbl.pack(side="left")
        return scale

    def _create_status_bar(self):
        """Thanh trạng thái dưới đáy với phong cách Light Slate 100 và viền trên nhẹ."""
        self.status_bar = tk.Frame(
            self.root,
            bg=self.bg_panel,
            height=26,
            highlightbackground=self.border_color,
            highlightthickness=1
        )
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)

        self.lbl_status_main = tk.Label(
            self.status_bar,
            text="● Hệ thống AI sẵn sàng",
            font=("Segoe UI", 8, "bold"),
            bg=self.bg_panel,
            fg=self.accent_green
        )
        self.lbl_status_main.pack(side="left", padx=12)

        lbl_author = tk.Label(
            self.status_bar,
            text="MediaPipe Hands + PyAutoGUI Controller",
            font=("Segoe UI", 8),
            bg=self.bg_panel,
            fg=self.fg_sub
        )
        lbl_author.pack(side="right", padx=12)

    # -------------------------------------------------------------
    # CAMERA THREAD & CAPTURE LOGIC
    # -------------------------------------------------------------
    def start_camera(self):
        """Khởi chạy luồng đọc Camera."""
        if self.is_camera_running:
            return

        cam_idx = self.config.get("camera_index", 0)
        try:
            self.cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(cam_idx)
        except Exception:
            self.cap = cv2.VideoCapture(cam_idx)

        if not self.cap or not self.cap.isOpened():
            self.lbl_video.config(text=f"❌ Không thể mở Camera {cam_idx}.\nVui lòng kiểm tra cáp hoặc chọn camera khác.")
            return

        self.is_camera_running = True
        self.btn_camera_toggle.config(text="⏹️ Dừng Camera", bg=self.bg_panel, fg="#334155")
        self.lbl_status_main.config(text=f"● Camera {cam_idx} đang hoạt động bình thường", fg=self.accent_green)

        self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
        self.camera_thread.start()

    def stop_camera(self):
        """Dừng camera và giải phóng tài nguyên."""
        self.is_camera_running = False
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        self.btn_camera_toggle.config(text="▶️ Bật Camera", bg=self.bg_panel, fg="#334155")
        self.lbl_video.config(image="", text="Camera đã tạm dừng.")
        self.lbl_status_main.config(text="○ Camera đang dừng", fg=self.fg_sub)

    def toggle_camera(self):
        if self.is_camera_running:
            self.stop_camera()
        else:
            self.start_camera()

    def _camera_loop(self):
        """Vòng lặp đọc khung hình từ Camera và xử lý AI."""
        while self.is_camera_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.02)
                continue

            # Tính toán FPS
            self.fps_counter += 1
            now = time.time()
            if now - self.fps_timer >= 1.0:
                self.current_fps = self.fps_counter
                self.fps_counter = 0
                self.fps_timer = now
                self.root.after(0, self._update_fps_display)

            # Xử lý cử chỉ qua GestureDetector
            processed_frame, detected_gesture, action_info, is_locked = self.gesture_detector.process_frame(frame)

            # Nếu có lệnh kích hoạt -> Gửi tới ActionExecutor
            if action_info:
                if action_info.get("is_lock_event"):
                    # Sự kiện đổi trạng thái khóa/mở
                    self.root.after(0, self._sync_lock_button, is_locked)
                    if self.config.get("enable_toast", True):
                        self.hud_toast.show(action_info.get("icon"), action_info.get("action"))
                else:
                    self.action_executor.execute(action_info)

            # Đẩy frame đã xử lý lên giao diện chính và Mini Overlay
            self.root.after(0, self._render_camera_frame, processed_frame, detected_gesture, is_locked)

            time.sleep(0.01)

    def _update_fps_display(self):
        self.lbl_fps.config(text=f"FPS: {self.current_fps}")

    def _render_camera_frame(self, frame, detected_gesture, is_locked):
        """Hiển thị frame OpenCV lên Tkinter Label."""
        try:
            # Cập nhật thông tin cử chỉ lên thẻ trạng thái
            if is_locked:
                self.lbl_current_gesture.config(text="🔒 ĐÃ KHÓA (CHẾ ĐỘ CHỜ)", fg=self.accent_red)
                self.lbl_cd_status.config(text="💤 Hệ thống đang chờ mở khóa (Giữ chữ V ✌️ 1.5s)", fg=self.accent_amber)
            elif detected_gesture:
                g_vi = GESTURE_NAMES_VI.get(detected_gesture, detected_gesture)
                self.lbl_current_gesture.config(text=f"✨ {g_vi}", fg=self.accent_blue)
                self.lbl_cd_status.config(text="⚡ Sẵn sàng nhận lệnh", fg=self.accent_green)
            else:
                self.lbl_current_gesture.config(text="Đang đợi tay...", fg=self.fg_sub)

            # Lấy kích thước khung hiển thị
            canvas_w = max(320, self.cam_canvas_frame.winfo_width())
            canvas_h = max(240, self.cam_canvas_frame.winfo_height())
            
            # Resize giữ nguyên tỷ lệ
            h, w, _ = frame.shape
            scale = min(canvas_w / w, canvas_h / h)
            new_w = max(10, int(w * scale))
            new_h = max(10, int(h * scale))

            resized = cv2.resize(frame, (new_w, new_h))
            rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            self.current_photo = ImageTk.PhotoImage(image=img)
            self.lbl_video.configure(image=self.current_photo, text="")

            # Đồng thời cập nhật mini overlay nếu đang hiển thị
            if self.mini_overlay.is_visible:
                self.mini_overlay.update_frame(frame)
        except Exception:
            pass

    # -------------------------------------------------------------
    # SỰ KIỆN & ĐIỀU KHIỂN
    # -------------------------------------------------------------
    def _on_action_executed(self, action_data):
        """Được gọi khi một lệnh được bắn ra bàn phím."""
        act_name = action_data.get("action", "")
        icon = action_data.get("icon", "⚡")
        key = action_data.get("key", "")

        # Cập nhật Card lệnh gần nhất
        self.root.after(0, lambda: self.lbl_last_action.config(text=f"{icon} {act_name} ({key})"))

        # Ghi log vào Listbox
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {icon} {act_name} -> Key: '{key}'"
        def _add_log():
            self.log_listbox.insert(0, log_entry)
            if self.log_listbox.size() > 80:
                self.log_listbox.delete("end")
        self.root.after(0, _add_log)

        # Hiển thị HUD Toast nếu được bật
        if self.config.get("enable_toast", True):
            self.hud_toast.show(icon, act_name, f"Phím bấm: {key.upper()}")

    def _toggle_lock_state(self):
        """Toggle Khóa / Mở khóa cử chỉ qua nút bấm trên GUI."""
        self.gesture_detector.is_locked = not self.gesture_detector.is_locked
        self._sync_lock_button(self.gesture_detector.is_locked)

    def _sync_lock_button(self, is_locked):
        if is_locked:
            self.btn_lock_toggle.config(
                text="🔒 ĐÃ KHÓA (CHẾ ĐỘ CHỜ)",
                bg="#FEE2E2",
                fg="#B91C1C",
                activebackground="#FECACA",
                activeforeground="#B91C1C"
            )
        else:
            self.btn_lock_toggle.config(
                text="🔓 ĐANG NHẬN DIỆN",
                bg="#DCFCE7",
                fg="#15803D",
                activebackground="#BBF7D0",
                activeforeground="#15803D"
            )

    def _toggle_mini_overlay(self):
        self.mini_overlay.toggle()
        if self.mini_overlay.is_visible:
            self.btn_mini_overlay.config(bg=self.accent_blue, fg="#FFFFFF")
        else:
            self.btn_mini_overlay.config(bg=self.bg_panel, fg=self.accent_blue)

    def _on_mini_overlay_closed(self):
        self.btn_mini_overlay.config(bg=self.bg_panel, fg=self.accent_blue)

    def _on_preset_change(self, event=None):
        new_preset = self.preset_var.get()
        self.config["current_preset"] = new_preset
        save_config(self.config)
        self.gesture_detector.update_settings(self.config)
        self._populate_mappings_tree()
        self._update_guide_text()
        if self.config.get("enable_toast", True):
            self.hud_toast.show("🔄", f"Chế độ: {new_preset.upper()}", "Đã áp dụng bộ cử chỉ mới")

    def _on_flip_change(self):
        self.config["flip_mirror"] = self.var_flip.get()
        save_config(self.config)
        self.gesture_detector.update_settings(self.config)

    def _on_skeleton_change(self):
        self.config["show_skeleton"] = self.var_skeleton.get()
        save_config(self.config)
        self.gesture_detector.update_settings(self.config)

    def _change_camera_index(self):
        new_idx = self.cam_index_var.get()
        self.config["camera_index"] = new_idx
        save_config(self.config)
        self.stop_camera()
        time.sleep(0.3)
        self.start_camera()
        messagebox.showinfo("Camera", f"Đã chuyển sang cổng Camera {new_idx}.")

    def _save_all_settings(self):
        self.config["cooldown"] = float(self.scale_cooldown.get())
        self.config["lock_hold_time"] = float(self.scale_lock_hold.get())
        self.config["detection_confidence"] = float(self.scale_confidence.get())
        self.config["tracking_confidence"] = float(self.scale_confidence.get())
        self.config["swipe_threshold"] = float(self.scale_swipe.get())
        self.config["enable_toast"] = self.var_toast.get()
        self.config["flip_mirror"] = self.var_flip.get()
        self.config["show_skeleton"] = self.var_skeleton.get()

        save_config(self.config)
        self.gesture_detector.update_settings(self.config)
        messagebox.showinfo("Thành công", "Đã lưu toàn bộ cài đặt hệ thống thành công!")

    def _restore_full_defaults(self):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn khôi phục toàn bộ cài đặt gốc?"):
            self.config = json.loads(json.dumps(DEFAULT_CONFIG))
            save_config(self.config)
            self.gesture_detector.update_settings(self.config)
            self.preset_var.set(self.config.get("current_preset", "youtube"))
            self.var_flip.set(self.config.get("flip_mirror", True))
            self.var_skeleton.set(self.config.get("show_skeleton", True))
            self.var_toast.set(self.config.get("enable_toast", True))
            self.scale_cooldown.set(self.config.get("cooldown", 0.8))
            self.scale_lock_hold.set(self.config.get("lock_hold_time", 1.5))
            self.scale_confidence.set(self.config.get("detection_confidence", 0.75))
            self.scale_swipe.set(self.config.get("swipe_threshold", 0.12))
            self._populate_mappings_tree()
            self._update_guide_text()
            messagebox.showinfo("Đã khôi phục", "Hệ thống đã trở về cài đặt ban đầu.")

    def on_closing(self):
        """Dọn dẹp và thoát an toàn."""
        self.stop_camera()
        self.mini_overlay.hide()
        self.root.destroy()
