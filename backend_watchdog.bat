@echo off
title Power Trading Backend Monitor
color 0E
cd /d "%~dp0"
if not exist logs mkdir logs

echo ==========================================
echo   BACKEND WATCHDOG
echo ==========================================
echo.
echo Backend will restart automatically if it crashes.
echo Logs: logs\backend.log
echo.

:RESTART
echo [%date% %time%] Starting backend... >> logs\backend.log
cd /d "%~dp0backend"
call ..\.venv\Scripts\activate.bat
python main.py 1>> ..\logs\backend.log 2>>&1
cd /d "%~dp0"
echo [%date% %time%] Backend stopped or crashed. Restarting in 5 seconds... >> logs\backend.log
echo Backend stopped or crashed. Restarting in 5 seconds...
timeout /t 5 >nul
goto RESTART
