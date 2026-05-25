@echo off
title Power Trading Health Check
color 0B
cd /d "%~dp0"
if not exist logs mkdir logs

echo ==========================================
echo   POWER TRADING SYSTEM - HEALTH CHECK
echo ==========================================
echo.

echo [1/5] Checking Python environment...
if exist .venv\Scripts\python.exe (
    echo [OK] Python virtual environment found.
) else (
    echo [ERROR] .venv missing.
)

echo.
echo [2/5] Checking frontend dependencies...
if exist frontend\node_modules (
    echo [OK] Frontend dependencies found.
) else (
    echo [ERROR] frontend\node_modules missing.
)

echo.
echo [3/5] Checking .env...
if exist .env (
    echo [OK] .env found.
) else (
    echo [WARNING] .env missing.
)

echo.
echo [4/5] Checking backend port 8000...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -Uri 'http://localhost:8000' -UseBasicParsing -TimeoutSec 3 | Out-Null; Write-Host '[OK] Backend responded.' } catch { Write-Host '[WARNING] Backend not responding on http://localhost:8000' }"

echo.
echo [5/5] Checking frontend port 5173...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -Uri 'http://localhost:5173' -UseBasicParsing -TimeoutSec 3 | Out-Null; Write-Host '[OK] Frontend responded.' } catch { Write-Host '[WARNING] Frontend not responding on http://localhost:5173' }"

echo.
echo Health check complete.
echo.
if "%1"=="quick" exit /b 0
pause
