@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" main.py --demo-toast
echo.
echo If no Windows notification appeared, read the message above and check Windows Settings - System - Notifications.
pause
.\.venv\Scripts\python.exe .\main.py --demo-toast