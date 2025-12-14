@echo off
setlocal enabledelayedexpansion

REM ======================================================
REM 🚀 POWER TRADING SYSTEM - HYBRID LAUNCHER (SAFE VERSION)
REM ======================================================

REM ------------------------------------------------------
REM 🧭 Determine external memory path
REM ------------------------------------------------------
if exist "D:\" (
    set "EXTERNAL_MEMORY=D:\AI_Trading_Storage"
) else (
    set "EXTERNAL_MEMORY=%~dp0external_memory"
)

REM ------------------------------------------------------
REM 🗂️ Ensure storage and logs exist
REM ------------------------------------------------------
if not exist "%EXTERNAL_MEMORY%" mkdir "%EXTERNAL_MEMORY%"
set "LOGDIR=%EXTERNAL_MEMORY%\logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

REM ------------------------------------------------------
REM 🕒 Timestamp
REM ------------------------------------------------------
for /f "tokens=2 delims==." %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set "timestamp=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%-%datetime:~12,2%"
set "LOGFILE=%LOGDIR%\session_%timestamp%.log"

echo ============================================= >> "%LOGFILE%"
echo   POWER TRADING SYSTEM - LAUNCHER             >> "%LOGFILE%"
echo   Session started: %date% %time%              >> "%LOGFILE%"
echo ============================================= >> "%LOGFILE%"

REM ------------------------------------------------------
REM 🧠 Parse mode arguments
REM ------------------------------------------------------
set "MODE=paper"
if /I "%~1"=="--live" set "MODE=live"
if /I "%~1"=="--diagnose" set "MODE=diagnose"

echo 🔧 Launching in %MODE% mode...
echo Mode: %MODE% >> "%LOGFILE%"

REM ------------------------------------------------------
REM 🌐 Internet Check
REM ------------------------------------------------------
echo 🌐 Checking internet...
ping -n 1 8.8.8.8 >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ No internet connection. >> "%LOGFILE%"
    echo ❌ Internet not available.
    pause
    exit /b
)
echo ✅ Internet OK. >> "%LOGFILE%"

REM ------------------------------------------------------
REM 🐳 Docker Check & Start
REM ------------------------------------------------------
echo 🐳 Checking Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo 🐳 Docker not running. >> "%LOGFILE%"
    echo Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    :wait_docker
    timeout /t 5 >nul
    docker info >nul 2>&1
    if %errorlevel% neq 0 goto wait_docker
)
echo ✅ Docker running. >> "%LOGFILE%"

REM ------------------------------------------------------
REM 🎮 GPU Check (informational only)
REM ------------------------------------------------------
where nvidia-smi >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ GPU not detected (CPU mode). >> "%LOGFILE%"
) else (
    echo ✅ GPU detected. >> "%LOGFILE%"
)

REM ------------------------------------------------------
REM 💾 Storage Confirmation
REM ------------------------------------------------------
echo 💾 Using storage path: %EXTERNAL_MEMORY%
echo 💾 Storage path: %EXTERNAL_MEMORY% >> "%LOGFILE%"

REM ------------------------------------------------------
REM 🧬 Export runtime mode for Docker
REM ------------------------------------------------------
set "AI_MODE=%MODE%"
echo AI_MODE=%AI_MODE% >> "%LOGFILE%"

REM ------------------------------------------------------
REM 🚀 Launch Docker Compose
REM ------------------------------------------------------
echo 🚀 Launching containers...
docker compose up --build -d >> "%LOGFILE%" 2>&1
timeout /t 10 >nul

REM ------------------------------------------------------
REM ✅ Verify backend container
REM ------------------------------------------------------
docker ps | find /I "ai_trading_backend" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Backend container failed. Attempting recovery... >> "%LOGFILE%"
    docker compose down >> "%LOGFILE%" 2>&1
    timeout /t 5 >nul
    docker compose up --build -d >> "%LOGFILE%" 2>&1
    timeout /t 10 >nul

    docker ps | find /I "ai_trading_backend" >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Recovery failed. Manual intervention required. >> "%LOGFILE%"
        echo ❌ Unable to launch backend.
        pause
        exit /b
    )
)
echo ✅ Containers running. >> "%LOGFILE%"

REM ------------------------------------------------------
REM 🔍 Diagnostic Mode (NO LIVE LOOP)
REM ------------------------------------------------------
if /I "%MODE%"=="diagnose" (
    echo 🔍 Diagnostic mode enabled. >> "%LOGFILE%"
    start "" python backend\stress_test\diagnostic_runner.py
    pause
    exit /b
)

REM ------------------------------------------------------
REM 🌐 Launch Frontend Dashboard
REM ------------------------------------------------------
start "" "http://localhost:3000"
echo 🌐 Frontend launched at http://localhost:3000 >> "%LOGFILE%"

REM ------------------------------------------------------
REM ❤️ Continuous Health Monitor (SAFE)
REM ------------------------------------------------------
:monitor_loop
timeout /t 30 >nul

docker ps | find /I "ai_trading_backend" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Backend container stopped. Restarting... >> "%LOGFILE%"
    docker compose restart ai_trading_backend >> "%LOGFILE%" 2>&1
    timeout /t 10 >nul
)

REM Optional heartbeat check (non-fatal)
if not exist "%EXTERNAL_MEMORY%\ai_state\decision_kernel_state.json" (
    echo ⚠️ AI heartbeat missing. >> "%LOGFILE%"
)

goto monitor_loop

REM ------------------------------------------------------
REM 🔚 Cleanup
REM ------------------------------------------------------
docker compose down >> "%LOGFILE%" 2>&1
echo ============================================= >> "%LOGFILE%"
echo   ✅ SESSION ENDED CLEANLY                     >> "%LOGFILE%"
echo ============================================= >> "%LOGFILE%"
pause
exit /b
