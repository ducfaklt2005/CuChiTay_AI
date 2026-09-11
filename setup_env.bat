@echo off
title Cai dat moi truong AI Gesture Media Controller
echo =======================================================
echo    DANG CAI DAT MOI TRUONG CHO AI GESTURE CONTROLLER...
echo =======================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay Python tren may cua ban!
    echo Vui long cai dat Python 3.10 tro len tai https://www.python.org/
    echo Nho tich chon "Add Python to PATH" khi cai dat.
    pause
    exit /b 1
)

if not exist "venv" (
    echo [1/3] Dang tao moi truong ao Python (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [LOI] Khong the tao virtual environment!
        pause
        exit /b 1
    )
) else (
    echo [1/3] Da tim thay thu muc venv san co.
)

echo.
echo [2/3] Dang nang cap pip...
.\venv\Scripts\python.exe -m pip install --upgrade pip

echo.
echo [3/3] Dang cai dat cac thu vien tu requirements.txt...
.\venv\Scripts\pip.exe install -r requirements.txt
if %errorlevel% neq 0 (
    echo [LOI] Qua trinh cai dat thu vien gap loi!
    pause
    exit /b 1
)

echo.
echo =======================================================
echo    CAI DAT THANH CONG!
echo    Bay gio ban co the chay "run_app.bat" de su dung.
echo =======================================================
pause
