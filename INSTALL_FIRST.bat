@echo off
title Power Trading System Installer
color 0B

cd /d "%~dp0"

echo ==========================================
echo   POWER TRADING SYSTEM - INSTALLER
echo ==========================================
echo.

echo [1/8] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Install Python 3.11+ from https://www.python.org/downloads/
    echo IMPORTANT: Tick "Add Python to PATH" during installation.
    pause
    exit /b 1
)
python --version

echo.
echo [2/8] Checking Node.js...
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Install Node.js LTS from https://nodejs.org/
    pause
    exit /b 1
)
node --version

echo.
echo [3/8] Checking npm...
where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm is missing. Reinstall Node.js LTS.
    pause
    exit /b 1
)
npm --version

echo.
echo [4/8] Checking project folders...
if not exist "backend" (
    echo [ERROR] Missing backend folder.
    pause
    exit /b 1
)

if not exist "frontend" (
    echo [ERROR] Missing frontend folder.
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo [ERROR] Missing frontend\package.json.
    pause
    exit /b 1
)

echo [OK] Project folders found.

echo.
echo [5/8] Creating Python virtual environment...
if not exist ".venv" (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create Python virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [OK] Existing .venv found.
)

echo.
echo [6/8] Installing Python dependencies...
call ".venv\Scripts\activate.bat"

python -m pip install --upgrade pip

if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo [WARNING] requirements.txt not found.
    echo Installing common backend packages...
    pip install fastapi uvicorn python-dotenv requests pandas numpy pydantic yfinance alpaca-py
)

if errorlevel 1 (
    echo [ERROR] Python dependency installation failed.
    pause
    exit /b 1
)

echo.
echo [7/8] Installing frontend dependencies...
cd frontend

npm install

if errorlevel 1 (
    echo [ERROR] Frontend dependency installation failed.
    cd ..
    pause
    exit /b 1
)

cd ..

echo.
echo [8/8] Checking environment file...
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [WARNING] Created .env from .env.example.
        echo Please open .env and add your Alpaca API keys before live trading.
    ) else (
        echo [WARNING] No .env or .env.example found.
        echo You must create .env before connecting to Alpaca.
    )
) else (
    echo [OK] .env found.
)

echo.
echo ==========================================
echo   INSTALLATION COMPLETE
echo ==========================================
echo.
echo You can now double-click:
echo start_project.bat
echo.
pause
