# AGENT DIRECTIVE: Python Tkinter Modern UI/UX Refactoring

## 1. OBJECTIVE & DESIGN VISION
Refactor the Python Tkinter GUI in `app_gui.py`, `hud.py`, and `overlay.py` to transform the current dark interface into a **Pristine, Modern Light Theme (Clean Tech Style)** inspired by modern desktop applications (e.g., macOS Sonoma, Linear, Notion, Vercel).

The new interface must focus on:
- **High Readability & Visual Clarity:** Crisp contrast, clear typography hierarchy, generous padding, and breathing room.
- **Modern Light Color Palette:** Clean off-white/slate backgrounds with vibrant accent colors for status indicators.
- **Intuitive Visual Hierarchy:** Rounded-corner card containers, subtle borders, and smooth status indicators instead of heavy solid panels.

---

## 2. COLOR PALETTE SPECIFICATION (Light Modern Theme)
Replace all existing Catppuccin dark colors (`#1e1e2e`, `#181825`, `#313244`) with this curated Light Palette:

- **Primary Background (`bg_main`):** `#F8FAFC` (Slate 50 - Very soft off-white)
- **Card / Surface Background (`bg_card`):** `#FFFFFF` (Pure White)
- **Sub-panel / Input Background (`bg_panel`):** `#F1F5F9` (Slate 100)
- **Borders & Dividers (`border_color`):** `#E2E8F0` (Slate 200)
- **Primary Text (`fg_text`):** `#0F172A` (Slate 900 - Deep, crisp charcoal)
- **Secondary / Muted Text (`fg_sub`):** `#64748B` (Slate 500)
- **Accent Blue (Primary Action):** `#2563EB` (Blue 600 - High clarity)
- **Accent Green (Active / Ready):** `#16A34A` (Green 600)
- **Accent Red (Locked / Stop):** `#DC2626` (Red 600)
- **Accent Amber/Peach (Warnings / Highlights):** `#D97706` (Amber 600)

---

## 3. COMPONENT & LAYOUT REFACTORING RULES

### A. Header Bar
- **Background:** Pure White (`#FFFFFF`) with a subtle bottom border (`#E2E8F0`).
- **Logo & Title:** Use crisp, bold typography for "AI GESTURE CONTROLLER" (`fg_text`: `#0F172A`, font size `13`, bold). Subtitle should use `#64748B` (font size `9`).
- **Control Buttons:**
    - Lock Button when ACTIVE: Soft green background (`#DCFCE7`) with bold green text (`#15803D`).
    - Lock Button when LOCKED: Soft red background (`#FEE2E2`) with bold red text (`#B91C1C`).
    - Camera Toggle Button: Neutral slate style (`#F1F5F9` background with `#334155` text).

### B. Camera Preview Column (Left)
- **Card Container:** Clean white frame with 1px border (`#E2E8F0`).
- **Camera Canvas Background:** Soft dark/neutral placeholder (`#0F172A`) when camera is starting, seamlessly embedded inside a white card margin.
- **FPS Indicator:** Pill-badge style with soft green tint (`#DCFCE7` background, `#15803D` text).
- **Utility Checkboxes:** Clean, modern styling with light background and clear focus states.

### C. Right Column & Tab Control (`ttk.Notebook`)
- **Tabs Styling:**
    - Tab Background (Unselected): Transparent or `#F1F5F9`.
    - Tab Background (Selected): Active Blue accent indicator with `#0F172A` bold text.
    - Padding: `[16, 10]` for larger, touch/click-friendly targets.
- **Dashboard Cards (Tab 1):**
    - Transform status cards into rounded-look cards with light `#F8FAFC` or `#FFFFFF` fill and `#E2E8F0` border.
    - Large, readable status labels: Current gesture in `#2563EB` (Blue), Last action in `#16A34A` (Green).
    - **Action Log (Listbox):** Set background to `#FFFFFF` (or light `#F8FAFC`), text to `#334155`, with a clean border, eliminating the old black background.
- **Mapping Customization (Tab 2 - Treeview):**
    - Set Treeview row colors: Background `#FFFFFF`, Alternating rows `#F8FAFC`, Selection `#E0F2FE` with `#0369A1` text.
    - Treeview Headers: Flat, clean header styling with `#F1F5F9` background and `#334155` text.
    - Edit Box: Light inputs (`#FFFFFF` background, `#CBD5E1` border).
- **Settings Sliders (Tab 3):**
    - Modern slider tracks (`troughcolor`: `#E2E8F0`, `activebackground`: `#2563EB`).
    - Values highlighted in bold accent colors (`#2563EB` or `#D97706`).

### D. Visual HUD Toast (`hud.py`) & Mini Overlay (`overlay.py`)
- **HUD Toast:** Light Glassmorphism design (`#FFFFFF` background with `0.95` alpha, soft drop shadow feel, border `#2563EB` or `#E2E8F0`, text `#0F172A`).
- **Mini Overlay:** Header in light `#F1F5F9`, title in `#0F172A`, close button with red hover effect.

---

## 4. INSTRUCTIONS FOR CODE GENERATION
1. Update `app_gui.py`, `hud.py`, and `overlay.py` with these light mode colors and improved layouts.
2. Ensure all text contrasts strictly meet accessibility guidelines (high contrast on light backgrounds).
3. Keep all underlying logic, thread safety, MediaPipe frame processing, and PyAutoGUI event execution completely intact.
4. Output clean, fully functional Python code without breaking existing callbacks or configurations.