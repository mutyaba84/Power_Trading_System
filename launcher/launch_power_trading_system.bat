@echo off
setlocal enabledelayedexpansion

REM ======================================================
REM 🚀 POWER TRADING SYSTEM - ULTIMATE LAUNCHER
REM ======================================================

set "EXTERNAL_MEMORY=D:\AI_Trading_Storage"
set "LOGDIR=%EXTERNAL_MEMORY%\logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

for /f "tokens=2 delims==." %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set "timestamp=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%-%datetime:~12,2%"
set "LOGFILE=%LOGDIR%\session_%timestamp%.log"

echo ============================================= >> "%LOGFILE%"
echo   POWER TRADING SYSTEM - LAUNCHER             >> "%LOGFILE%"
echo   Session started: %date% %time%              >> "%LOGFILE%"
echo ============================================= >> "%LOGFILE%"

REM ======================================================
REM Parse mode arguments
REM ======================================================
set "MODE=paper"
if "%~1"=="--live" set "MODE=live"
if "%~1"=="--diagnose" set "MODE=diagnose"

REM ======================================================
REM 1️⃣ Internet Check
REM ======================================================
echo 🌐 Checking internet...
ping -n 1 8.8.8.8 >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ No internet connection. >> "%LOGFILE%"
    echo ❌ Internet not available.
    if "%MODE%"=="diagnose" goto finish
    pause
    exit /b
)
echo ✅ Internet OK. >> "%LOGFILE%"

REM ======================================================
REM 2️⃣ Docker Check
REM ======================================================
echo 🐳 Checking Docker...
docker info >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo 🐳 Docker not running. >> "%LOGFILE%"
    if "%MODE%"=="diagnose" goto checks_continue
    echo Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    :waitloop
    timeout /t 5 >nul
    docker info >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 goto waitloop
)
:checks_continue
echo ✅ Docker running. >> "%LOGFILE%"

REM ======================================================
REM 3️⃣ GPU Check
REM ======================================================
echo 🎮 Checking GPU...
nvidia-smi >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ GPU not found. >> "%LOGFILE%"
) else (
    echo ✅ GPU detected. >> "%LOGFILE%"
)

REM ======================================================
REM 4️⃣ External Storage Check
REM ======================================================
echo 💾 Checking external storage...
if exist "%EXTERNAL_MEMORY%" (
    echo ✅ External storage found. >> "%LOGFILE%"
) else (
    echo ⚠️ No external storage. Creating local folder. >> "%LOGFILE%"
    mkdir "%EXTERNAL_MEMORY%"
)

REM ======================================================
REM DIAGNOSTIC MODE EXIT
REM ======================================================
if "%MODE%"=="diagnose" (
    :finish
    echo ============================================= >> "%LOGFILE%"
    echo   🔍 DIAGNOSTIC MODE COMPLETED                >> "%LOGFILE%"
    echo   Log saved to: %LOGFILE%                     >> "%LOGFILE%"
    echo ============================================= >> "%LOGFILE%"
    echo ✅ Diagnostic complete. Report saved to: %LOGFILE%
    pause
    exit /b
)

REM ======================================================
REM NORMAL RUN MODE
REM ======================================================
echo 🚀 Starting Power Trading System in %MODE% mode...

if "%MODE%"=="live" (
    python ai_core\system_runner.py --live >> "%LOGFILE%" 2>&1
) else (
    python ai_core\system_runner.py >> "%LOGFILE%" 2>&1
)

echo ============================================= >> "%LOGFILE%"
echo   ✅ SESSION ENDED CLEANLY - %date% %time%     >> "%LOGFILE%"
echo ============================================= >> "%LOGFILE%"
pause
