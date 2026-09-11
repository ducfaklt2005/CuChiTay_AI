@echo off
title AI Gesture Media Controller
echo =======================================================
echo    DANG KHOI DONG AI GESTURE MEDIA CONTROLLER...
echo =======================================================

if exist ".\venv\Scripts\python.exe" (
    start "" ".\venv\Scripts\python.exe" "main.py"
) else (
    start "" python "main.py"
)

exit
