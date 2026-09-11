# 🖐️ AI Gesture Media Controller (Desktop App)

Ứng dụng Desktop điều khiển đa phương tiện máy tính không chạm bằng **Cử chỉ tay AI (Hand Gestures)** sử dụng **MediaPipe Hands**, **OpenCV** và giao diện đồ họa hiện đại **Tkinter GUI**.

---

## 🌟 1. Nhóm Chức Năng Điều Khiển Nền Tảng (Media Controls)

Ứng dụng hỗ trợ 3 chế độ cấu hình linh hoạt (Preset):
- **YouTube (Video dài)**
- **TikTok / YouTube Shorts (Video ngắn / Dạng cuộn)**
- **Custom (Tùy biến tự do)**

### 🎥 Dành cho YouTube (Video Dài)
| Cử chỉ | Hành động mô phỏng | Phím tắt hệ thống |
| :--- | :--- | :--- |
| ✋ **Xòe bàn tay (5 ngón)** | Phát / Tạm dừng (Play / Pause) | `Space` |
| ✊ **Nắm đấm (0 ngón)** | Tắt tiếng / Mở tiếng (Mute / Unmute) | `M` |
| ☝️ **Ngón trỏ chỉ lên** | Tăng âm lượng hệ thống | `Volume Up` |
| 👇 **Ngón trỏ chỉ xuống** | Giảm âm lượng hệ thống | `Volume Down` |
| 👍 **Thumbs Up (Ngón cái lên)** | Tăng âm lượng | `Volume Up` |
| 👎 **Thumbs Down (Ngón cái xuống)** | Giảm âm lượng | `Volume Down` |
| 👉 **Gạt tay sang phải (Swipe Right)** | Tua tới 10 giây | `Right Arrow` |
| 👈 **Gạt tay sang trái (Swipe Left)** | Tua lùi 10 giây | `Left Arrow` |
| 👆 **Vuốt tay lên trên (Swipe Up)** | Chuyển video kế tiếp | `Shift + N` |
| 👌 **Chắp 2 ngón (OK / Pinch)** | Bật / Tắt Toàn màn hình | `F` |
| 🤫 **Ngón trỏ trước môi (Suỵt)** | Tắt / Mở tiếng | `M` |
| 💖 **Ngón út giơ lên (Pinky)** | Thả tim / Like video | `L` |

---

### 📱 Dành cho TikTok / YouTube Shorts (Video Dạng Cuộn)
| Cử chỉ | Hành động mô phỏng | Phím tắt hệ thống |
| :--- | :--- | :--- |
| 👆 **Vuốt tay lên trên (Swipe Up)** | Lướt sang video kế tiếp (Cuộn xuống) | `Down Arrow` |
| 👇 **Vuốt tay xuống dưới (Swipe Down)** | Xem lại video trước đó (Cuộn lên) | `Up Arrow` |
| 👍 **Thumbs Up / 💖 Ngón út** | Thả tim / Like video | `L` |
| 🤫 **Ký hiệu Suỵt / ✊ Nắm đấm** | Tắt / Bật tiếng video | `M` |
| ✋ **Xòe bàn tay** | Tạm dừng / Tiếp tục phát | `Space` |
| ☝️ **Ngón trỏ lên / 👇 xuống** | Tăng / Giảm âm lượng | `Volume Up / Down` |
| 👌 **Chắp 2 ngón (OK / Pinch)** | Toàn màn hình | `F` |

---

## 🛡️ 2. Chức Năng Hệ Thống & Trải Nghiệm Người Dùng (System & UX)

1. **Chế độ Chờ / Khóa Cử Chỉ (Hold to Lock/Unlock - Anti-accidental Trigger)**:
   - **Mục đích**: Chống trường hợp bạn vô tình đưa tay lên uống nước, gãi đầu hay nói chuyện làm ứng dụng nhận nhầm lệnh.
   - **Cách kích hoạt**: Giơ biểu tượng chữ V (**Peace sign ✌️**) giữ nguyên trong **1.5 giây**. 
   - Trên màn hình camera sẽ xuất hiện **vòng tròn tiến trình đếm 0% -> 100%**. Khi đủ thời gian, ứng dụng sẽ chuyển sang trạng thái:
     - 🔒 **ĐÃ KHÓA (CHẾ ĐỘ CHỜ)**: Không bắn phím tắt ra ngoài máy tính.
     - Giữ tiếp 1.5 giây để 🔓 **MỞ KHÓA (SẴN SÀNG NHẬN LỆNH)**.
   - Bạn cũng có thể bấm nút **Khóa/Mở khóa nhanh** trực tiếp trên thanh Header của GUI.

2. **Cơ chế Chống Lặp Lệnh (Cooldown / Debounce Delay)**:
   - Thiết lập thời gian nghỉ giữa 2 lần nhận lệnh (mặc định **0.8 giây**, có thể tùy chỉnh từ 0.3s đến 2.5s) để tránh bị tua quá đà hoặc nhảy video liên tục.
   - Có thanh đếm ngược Cooldown trực quan trên Camera và Dashboard.

3. **Cửa Sổ Xem Trước Camera Mini Luôn Nổi (Mini Live Preview Overlay)**:
   - Bấm nút **"📺 Cửa Sổ Mini Luôn Nổi"** trên giao diện để mở một cửa sổ camera nhỏ ở góc màn hình.
   - Luôn hiển thị trên các ứng dụng khác (**Always on Top**), cho phép bạn vừa xem video full-screen vừa nhìn thấy phản hồi khung xương tay của mình.
   - Có thể **nhấp giữ chuột kéo thả** đến bất cứ vị trí nào trên màn hình desktop.

4. **Thông Báo Phản Hồi Trực Quan (Visual Feedback Toast / HUD)**:
   - Khi một cử chỉ được kích hoạt thành công, một cửa sổ OSD/Toast bán trong suốt bo góc phong cách Glassmorphism sẽ xuất hiện nhẹ nhàng ở góc màn hình (VD: `🔊 Tăng Âm Lượng`, `⏯️ Play / Pause`, `⏩ Tua Tới`) rồi tự động mờ dần và biến mất sau 1.2 giây mà không làm mất focus của trình duyệt.

---

## ⚙️ 3. Cài Đặt & Tùy Biến (Configuration & Settings)

- **Tùy biến Ánh xạ (Gesture Mapping)**: Tab "Ánh Xạ Cử Chỉ" cho phép bạn tùy ý đổi cử chỉ sang hành động và phím bấm bất kỳ theo thói quen cá nhân.
- **Chọn Camera đầu vào (Camera Device)**: Dễ dàng chuyển đổi giữa Webcam tích hợp laptop và Webcam rời qua cổng USB (Index 0, 1, 2...).
- **Điều chỉnh độ nhạy (Sensitivity Sliders)**:
  - Detection Confidence & Tracking Confidence (0.50 - 0.95).
  - Cooldown time (0.3s - 2.5s).
  - Thời gian giữ khóa Hold Lock (1.0s - 3.0s).
  - Ngưỡng gạt tay Swipe Threshold (0.08 - 0.25).
- **Tự động lưu file cấu hình `gesture_config.json`**: Mọi cài đặt của bạn được lưu lại vĩnh viễn và tự động nạp lại ở lần mở tiếp theo.

---

## 🚀 4. Hướng Dẫn Cài Đặt & Khởi Chạy

### 📦 Bước 1: Cài đặt môi trường (Khi mới clone về)
- **Cách 1 (Khuyên dùng)**: Nhấp đúp vào file **`setup_env.bat`** để tự động tạo môi trường ảo và cài đặt tất cả thư viện cần thiết từ `requirements.txt`.
- **Cách 2 (Thủ công)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\pip install -r requirements.txt
  ```

---

### ▶️ Bước 2: Khởi chạy ứng dụng
- **Cách 1**: Nhấp đúp vào file **`run_app.bat`** trong thư mục dự án.
- **Cách 2**: Chạy qua dòng lệnh (Terminal / PowerShell):
  ```powershell
  .\venv\Scripts\python.exe main.py
  ```

