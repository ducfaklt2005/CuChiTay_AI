"""
Module Quản lý Cấu hình & Ánh xạ Cử chỉ (Config Manager)
Hỗ trợ lưu/tải cài đặt JSON và các Preset định sẵn cho YouTube và TikTok/Shorts.
"""

import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gesture_config.json")

DEFAULT_CONFIG = {
    "current_preset": "youtube",
    "camera_index": 0,
    "flip_mirror": True,
    "detection_confidence": 0.75,
    "tracking_confidence": 0.75,
    "cooldown": 0.8,
    "lock_hold_time": 1.5,
    "swipe_threshold": 0.12,  # Tỷ lệ so với chiều rộng/cao khung hình
    "lock_gesture": "PEACE_SIGN",
    "show_skeleton": True,
    "enable_toast": True,
    "enable_sound_beep": False,
    "presets": {
        "youtube": {
            "name": "YouTube (Video Dài)",
            "mappings": {
                "OPEN_PALM": {"action": "Play / Pause", "key": "space", "icon": "⏯️", "desc": "Xòe bàn tay: Bật/Tắt video"},
                "FIST": {"action": "Tắt / Mở Tiếng", "key": "m", "icon": "🔇", "desc": "Nắm đấm: Bật/Tắt tiếng"},
                "POINTING_UP": {"action": "Tăng Âm Lượng", "key": "volumeup", "icon": "🔊", "desc": "Ngón trỏ lên: Tăng âm"},
                "POINTING_DOWN": {"action": "Giảm Âm Lượng", "key": "volumedown", "icon": "🔉", "desc": "Ngón trỏ xuống: Giảm âm"},
                "THUMBS_UP": {"action": "Tăng Âm Lượng", "key": "volumeup", "icon": "🔊", "desc": "Ngón cái lên: Tăng âm"},
                "THUMBS_DOWN": {"action": "Giảm Âm Lượng", "key": "volumedown", "icon": "🔉", "desc": "Ngón cái xuống: Giảm âm"},
                "SWIPE_RIGHT": {"action": "Tua Tới (+10s)", "key": "right", "icon": "⏩", "desc": "Gạt tay phải: Tua tới 10s"},
                "SWIPE_LEFT": {"action": "Tua Lùi (-10s)", "key": "left", "icon": "⏪", "desc": "Gạt tay trái: Tua lùi 10s"},
                "SWIPE_UP": {"action": "Video Tiếp Theo", "key": "shift+n", "icon": "⏭️", "desc": "Vuốt lên: Chuyển video kế tiếp"},
                "OK_PINCH": {"action": "Toàn Màn Hình", "key": "f", "icon": "⛶", "desc": "Chắp 2 ngón (OK): Bật/Tắt toàn màn hình"},
                "SHH_GESTURE": {"action": "Tắt / Mở Tiếng", "key": "m", "icon": "🔇", "desc": "Ký hiệu Suỵt: Tắt/Bật tiếng"},
                "PINKY_UP": {"action": "Thả Tim / Like", "key": "l", "icon": "💖", "desc": "Ngón út giơ lên: Thả tim/Like"}
            }
        },
        "tiktok": {
            "name": "TikTok / YouTube Shorts (Cuộn)",
            "mappings": {
                "SWIPE_UP": {"action": "Video Tiếp Theo", "key": "down", "icon": "⬇️", "desc": "Vuốt tay lên: Cuộn video tiếp"},
                "SWIPE_DOWN": {"action": "Video Trước Đó", "key": "up", "icon": "⬆️", "desc": "Vuốt tay xuống: Quay lại video trước"},
                "THUMBS_UP": {"action": "Thả Tim / Like", "key": "l", "icon": "💖", "desc": "Thành công / Like: Thả tim video"},
                "PINKY_UP": {"action": "Thả Tim / Like", "key": "l", "icon": "💖", "desc": "Ngón út: Thả tim video"},
                "OPEN_PALM": {"action": "Play / Pause", "key": "space", "icon": "⏯️", "desc": "Xòe bàn tay: Bật/Tắt video"},
                "FIST": {"action": "Tắt / Mở Tiếng", "key": "m", "icon": "🔇", "desc": "Nắm đấm: Mute tiếng"},
                "POINTING_UP": {"action": "Tăng Âm Lượng", "key": "volumeup", "icon": "🔊", "desc": "Ngón trỏ lên: Tăng âm"},
                "POINTING_DOWN": {"action": "Giảm Âm Lượng", "key": "volumedown", "icon": "🔉", "desc": "Ngón trỏ xuống: Giảm âm"},
                "SHH_GESTURE": {"action": "Tắt / Mở Tiếng", "key": "m", "icon": "🔇", "desc": "Ký hiệu Suỵt: Mute tiếng"},
                "OK_PINCH": {"action": "Toàn Màn Hình", "key": "f", "icon": "⛶", "desc": "OK Sign: Toàn màn hình"}
            }
        },
        "custom": {
            "name": "Tùy biến (Custom)",
            "mappings": {
                "OPEN_PALM": {"action": "Play / Pause", "key": "space", "icon": "⏯️", "desc": "Xòe bàn tay: Play/Pause"},
                "FIST": {"action": "Tắt / Mở Tiếng", "key": "m", "icon": "🔇", "desc": "Nắm đấm: Mute"},
                "POINTING_UP": {"action": "Tăng Âm Lượng", "key": "volumeup", "icon": "🔊", "desc": "Ngón trỏ lên: Tăng âm"},
                "POINTING_DOWN": {"action": "Giảm Âm Lượng", "key": "volumedown", "icon": "🔉", "desc": "Ngón trỏ xuống: Giảm âm"},
                "THUMBS_UP": {"action": "Thả Tim / Like", "key": "l", "icon": "💖", "desc": "Thumbs Up: Like"},
                "THUMBS_DOWN": {"action": "Giảm Âm Lượng", "key": "volumedown", "icon": "🔉", "desc": "Thumbs Down: Giảm âm"},
                "SWIPE_RIGHT": {"action": "Tua Tới", "key": "right", "icon": "⏩", "desc": "Gạt phải: Tua tới"},
                "SWIPE_LEFT": {"action": "Tua Lùi", "key": "left", "icon": "⏪", "desc": "Gạt trái: Tua lùi"},
                "SWIPE_UP": {"action": "Video Tiếp Theo", "key": "down", "icon": "⏭️", "desc": "Vuốt lên: Tiếp theo"},
                "SWIPE_DOWN": {"action": "Video Trước", "key": "up", "icon": "⏮️", "desc": "Vuốt xuống: Video trước"},
                "OK_PINCH": {"action": "Toàn Màn Hình", "key": "f", "icon": "⛶", "desc": "Pinch/OK: Fullscreen"},
                "SHH_GESTURE": {"action": "Tắt / Mở Tiếng", "key": "m", "icon": "🔇", "desc": "Suỵt: Mute"}
            }
        }
    }
}

GESTURE_NAMES_VI = {
    "OPEN_PALM": "Xòe bàn tay (5 ngón)",
    "FIST": "Nắm đấm (0 ngón)",
    "POINTING_UP": "Ngón trỏ chỉ lên",
    "POINTING_DOWN": "Ngón trỏ chỉ xuống",
    "THUMBS_UP": "Ngón cái giơ lên (Thumbs Up)",
    "THUMBS_DOWN": "Ngón cái chúc xuống (Thumbs Down)",
    "PEACE_SIGN": "Chữ V (2 ngón tay - Peace)",
    "OK_PINCH": "Chắp 2 ngón (OK / Pinch)",
    "PINKY_UP": "Ngón út giơ lên",
    "SHH_GESTURE": "Ngón trỏ trước môi (Suỵt)",
    "SWIPE_RIGHT": "Gạt tay sang phải (Swipe Right)",
    "SWIPE_LEFT": "Gạt tay sang trái (Swipe Left)",
    "SWIPE_UP": "Vuốt tay lên trên (Swipe Up)",
    "SWIPE_DOWN": "Vuốt tay xuống dưới (Swipe Down)"
}

AVAILABLE_KEYS = [
    ("space", "Phím Space (Play / Pause)"),
    ("volumeup", "Tăng âm lượng hệ thống (Volume Up)"),
    ("volumedown", "Giảm âm lượng hệ thống (Volume Down)"),
    ("right", "Mũi tên phải (Tua tới 5s / Next)"),
    ("left", "Mũi tên trái (Tua lùi 5s / Prev)"),
    ("up", "Mũi tên lên (Video trước / Vol Up)"),
    ("down", "Mũi tên xuống (Video tiếp / Vol Down)"),
    ("f", "Phím F (Toàn màn hình)"),
    ("m", "Phím M (Tắt / Mở tiếng)"),
    ("l", "Phím L (Thả tim / Tua tới 10s)"),
    ("j", "Phím J (Tua lùi 10s)"),
    ("k", "Phím K (Play / Pause YouTube)"),
    ("shift+n", "Shift + N (Video tiếp theo YouTube)"),
    ("pagedown", "Page Down (Cuộn trang xuống)"),
    ("pageup", "Page Up (Cuộn trang lên)")
]

def load_config():
    """Đọc file cấu hình hoặc tạo mới cấu hình mặc định."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception as e:
            print(f"Lỗi khi tải config: {e}. Dùng cấu hình mặc định.")
    return json.loads(json.dumps(DEFAULT_CONFIG))

def save_config(config_data):
    """Lưu cấu hình ra file JSON."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Lỗi khi lưu config: {e}")
        return False
