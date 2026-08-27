@echo off
setlocal
set "PROJECT=%~dp0"
set "RUNNER=%PROJECT%Background Monitor.vbs"
set "WSCRIPT=%SystemRoot%\System32\wscript.exe"

echo Choose how often the monitor should check:
echo   1. Daily at 9:00 AM ^(recommended for the challenge^)
echo   2. Every hour
set /p "CHOICE=Type 1 or 2, then press Enter: "

schtasks /Delete /TN "Website Change Monitor Popup" /F >nul 2>&1
schtasks /Delete /TN "Website Change Monitor Notification" /F >nul 2>&1

if "%CHOICE%"=="2" (
    schtasks /Create /TN "Website Change Monitor Notification" /TR "\"%WSCRIPT%\" \"%RUNNER%\"" /SC HOURLY /MO 1 /RL LIMITED /IT /F
    set "MESSAGE=every hour"
) else (
    schtasks /Create /TN "Website Change Monitor Notification" /TR "\"%WSCRIPT%\" \"%RUNNER%\"" /SC DAILY /ST 09:00 /RL LIMITED /IT /F
    set "MESSAGE=daily at 9:00 AM"
)

if errorlevel 1 (
    echo.
    echo Could not create the task. Right-click this file and choose Run as administrator, then try again.
) else (
    echo.
    echo Done. The monitor will check %MESSAGE% and show a Windows notification when updates are found.
)

pause
