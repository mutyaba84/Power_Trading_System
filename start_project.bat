@echo off
title Power Trading System Launcher
color 0A

cd /d "%~dp0"

echo ==========================================
echo   POWER TRADING SYSTEM - START
echo ==========================================
echo.

echo [1/6] Checking Python virtual environment...
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment not found.
    echo Run INSTALL_FIRST.bat before starting the system.
    pause
    exit /b 1
)

echo [OK] Virtual environment found.

echo.
echo [2/6] Checking frontend dependencies...
if not exist "frontend\node_modules" (
    echo [ERROR] frontend\node_modules not found.
    echo Run INSTALL_FIRST.bat before starting the system.
    pause
    exit /b 1
)

echo [OK] Frontend dependencies found.

echo.
echo [3/6] Checking backend entry file...
if not exist "backend\main.py" (
    echo [ERROR] backend\main.py not found.
    pause
    exit /b 1
)

echo [OK] Backend entry found.

echo.
echo [4/6] Starting backend...
start "Power Trading Backend" cmd /k "cd /d %cd%\backend && ..\.venv\Scripts\activate.bat && python main.py"

timeout /t 5 >nul

echo.
echo [5/6] Starting frontend...
start "Power Trading Frontend" cmd /k "cd /d %cd%\frontend && npm run dev"

timeout /t 5 >nul

echo.
echo [6/6] Opening dashboard...
start http://localhost:5173

echo.
echo ==========================================
echo   SYSTEM STARTED
echo ==========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Keep the backend and frontend windows open.
echo Use stop_project.bat to stop common project processes.
echo.
pause
