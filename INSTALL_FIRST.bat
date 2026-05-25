@echo off
title Power Trading System Installer
color 0B
cd /d "%~dp0"
if not exist logs mkdir logs
echo ==========================================
echo   POWER TRADING SYSTEM - INSTALLER
echo ==========================================
echo.

echo [1/9] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Install Python 3.11+ and tick "Add Python to PATH".
    pause
    exit /b 1
)
python --version

echo.
echo [2/9] Checking Node.js...
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Install Node.js LTS.
    pause
    exit /b 1
)
node --version

echo.
echo [3/9] Checking npm...
where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm is missing. Reinstall Node.js LTS.
    pause
    exit /b 1
)
npm --version

echo.
echo [4/9] Checking project structure...
if not exist backend (
    echo [ERROR] Missing backend folder.
    pause
    exit /b 1
)
if not exist frontend (
    echo [ERROR] Missing frontend folder.
    pause
    exit /b 1
)
if not exist frontend\package.json (
    echo [ERROR] Missing frontend\package.json.
    pause
    exit /b 1
)
if not exist backend\main.py (
    echo [ERROR] Missing backend\main.py.
    pause
    exit /b 1
)
echo [OK] Project structure looks good.

echo.
echo [5/9] Creating Python virtual environment...
if not exist .venv (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create .venv.
        pause
        exit /b 1
    )
) else (
    echo [OK] Existing .venv found.
)

echo.
echo [6/9] Installing Python dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo [WARNING] requirements.txt missing. Installing common packages.
    pip install fastapi uvicorn python-dotenv requests pandas numpy pydantic yfinance alpaca-py
)
if errorlevel 1 (
    echo [ERROR] Python dependency install failed.
    pause
    exit /b 1
)

echo.
echo [7/9] Installing frontend dependencies...
cd frontend
npm install
if errorlevel 1 (
    echo [ERROR] npm install failed.
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo [8/9] Creating .env if missing...
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo [WARNING] Created .env from .env.example.
    ) else (
        echo ALPACA_API_KEY=your_alpaca_api_key_here>.env
        echo ALPACA_SECRET_KEY=your_alpaca_secret_key_here>>.env
        echo ALPACA_PAPER=true>>.env
        echo ALPACA_BASE_URL=https://paper-api.alpaca.markets>>.env
        echo BACKEND_HOST=127.0.0.1>>.env
        echo BACKEND_PORT=8000>>.env
        echo FRONTEND_URL=http://localhost:5173>>.env
        echo [WARNING] Created basic .env template.
    )
) else (
    echo [OK] .env found.
)

echo.
echo [9/9] Creating logs folder...
if not exist logs mkdir logs
echo [OK] logs folder ready.

echo.
echo ==========================================
echo   INSTALLATION COMPLETE
echo ==========================================
echo.
echo Next:
echo 1. Open .env and add your Alpaca API keys.
echo 2. Double-click start_project.bat.
echo.
pause
