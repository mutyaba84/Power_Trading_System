@echo off
title Power Trading System Control Center
color 0A
cd /d "%~dp0"
if not exist logs mkdir logs

echo ==========================================
echo   POWER TRADING SYSTEM - CONTROL CENTER
echo ==========================================
echo.
echo Choose launch mode:
echo.
echo [1] Paper Trading      Recommended
echo [2] Live Trading       Use carefully
echo [3] Diagnostics Only
echo [4] Start Backend + Frontend
echo [5] Exit
echo.
set /p MODE=Select option: 

if "%MODE%"=="1" goto PAPER
if "%MODE%"=="2" goto LIVE
if "%MODE%"=="3" goto DIAG
if "%MODE%"=="4" goto START
if "%MODE%"=="5" exit /b 0

echo Invalid option.
pause
exit /b 1

:PAPER
set ALPACA_PAPER=true
echo [MODE] Paper trading selected.
goto START

:LIVE
echo.
echo WARNING: LIVE TRADING SELECTED.
echo This can place real orders if your backend is configured for live trading.
echo.
set /p CONFIRM=Type LIVE to continue: 
if /I not "%CONFIRM%"=="LIVE" (
    echo Cancelled.
    pause
    exit /b 0
)
set ALPACA_PAPER=false
echo [MODE] Live trading selected.
goto START

:DIAG
echo.
call health_check.bat
pause
exit /b 0

:START
echo.
echo [1/7] Checking installer state...
if not exist .venv\Scripts\python.exe (
    echo [ERROR] .venv missing. Run INSTALL_FIRST.bat first.
    pause
    exit /b 1
)
if not exist frontend\node_modules (
    echo [ERROR] frontend\node_modules missing. Run INSTALL_FIRST.bat first.
    pause
    exit /b 1
)
if not exist backend\main.py (
    echo [ERROR] backend\main.py missing.
    pause
    exit /b 1
)
echo [OK] Required files found.

echo.
echo [2/7] Stopping old project processes...
call stop_project.bat silent

echo.
echo [3/7] Starting backend with restart monitor...
start "Power Trading Backend Monitor" cmd /k "cd /d %cd% && backend_watchdog.bat"

timeout /t 6 >nul

echo.
echo [4/7] Starting frontend...
start "Power Trading Frontend" cmd /k "cd /d %cd%\frontend && npm run dev 1>> ..\logs\frontend.log 2>>&1"

timeout /t 6 >nul

echo.
echo [5/7] Running health check...
call health_check.bat quick

echo.
echo [6/7] Opening dashboard...
start http://localhost:5173

echo.
echo [7/7] Launch complete.
echo.
echo ==========================================
echo   SYSTEM STARTED
echo ==========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo Logs:     logs\
echo.
pause
