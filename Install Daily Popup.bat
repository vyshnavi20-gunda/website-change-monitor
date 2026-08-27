@echo off
setlocal
set "PROJECT=%~dp0"
set "RUNNER=%PROJECT%Background Monitor.vbs"
set "WSCRIPT=%SystemRoot%\System32\wscript.exe"

schtasks /Delete /TN "Website Change Monitor Popup" /F >nul 2>&1
schtasks /Create /TN "Website Change Monitor Notification" /TR "\"%WSCRIPT%\" \"%RUNNER%\"" /SC HOURLY /MO 1 /RL LIMITED /IT /F

if errorlevel 1 (
    echo.
    echo Could not create the daily task. Right-click this file and choose Run as administrator, then try again.
) else (
    echo.
    echo Done. The monitor will check once every hour and show a Windows notification when updates are found.
)

pause
