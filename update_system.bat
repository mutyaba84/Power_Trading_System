@echo off
title Power Trading System Updater
color 0D
cd /d "%~dp0"

echo ==========================================
echo   POWER TRADING SYSTEM - UPDATE
echo ==========================================
echo.

echo [1/5] Checking Git...
where git >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Git not installed or not in PATH. Skipping git pull.
) else (
    if exist .git (
        echo Pulling latest project updates...
        git pull
    ) else (
        echo [WARNING] This folder is not a Git repository. Skipping git pull.
    )
)

echo.
echo [2/5] Updating Python dependencies...
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    if exist requirements.txt pip install -r requirements.txt
) else (
    echo [WARNING] .venv missing. Run INSTALL_FIRST.bat.
)

echo.
echo [3/5] Updating frontend dependencies...
if exist frontend\package.json (
    cd frontend
    npm install
    cd ..
) else (
    echo [WARNING] frontend\package.json missing.
)

echo.
echo [4/5] Running health check...
call health_check.bat quick

echo.
echo [5/5] Update complete.
echo.
pause
