@echo off
setlocal EnableDelayedExpansion
title Power Trading System - Professional Launcher
color 0A

REM ==========================================================
REM POWER TRADING SYSTEM - PROFESSIONAL LAUNCHER
REM No virtual environment activation.
REM Uses proven working commands:
REM Backend:  python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
REM Frontend: npm run dev
REM ==========================================================

set "PROJECT_ROOT=C:\Users\dennis\Power_Trading_System"
set "BACKEND_URL=http://127.0.0.1:8000"
set "FRONTEND_URL=http://localhost:5173"
set "LOG_DIR=%PROJECT_ROOT%\logs"
set "LAUNCHER_LOG=%LOG_DIR%\launcher.log"

echo ==========================================
echo   POWER TRADING SYSTEM
echo ==========================================
echo   Professional Launcher
echo ==========================================
echo.

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ========================================== > "%LAUNCHER_LOG%"
echo POWER TRADING SYSTEM LAUNCHER LOG >> "%LAUNCHER_LOG%"
echo Started: %date% %time% >> "%LAUNCHER_LOG%"
echo Project Root: %PROJECT_ROOT% >> "%LAUNCHER_LOG%"
echo ========================================== >> "%LAUNCHER_LOG%"

REM ==========================================================
REM MENU
REM ==========================================================

echo Choose an option:
echo.
echo [1] Start System - Paper Mode
echo [2] Start System - Live Mode
echo [3] Health Check Only
echo [4] Open Dashboard
echo [5] Stop System
echo [6] Exit
echo.

set /p MODE=Select option: 

if "%MODE%"=="1" (
    set "AI_MODE=paper"
    set "ALPACA_PAPER=true"
    goto HEALTH_CHECK
)

if "%MODE%"=="2" (
    echo.
    echo WARNING: LIVE MODE SELECTED.
    echo This may place real trades if your backend is configured for live trading.
    echo.
    set /p CONFIRM=Type LIVE to continue: 
    if /I not "!CONFIRM!"=="LIVE" (
        echo Cancelled.
        pause
        exit /b 0
    )
    set "AI_MODE=live"
    set "ALPACA_PAPER=false"
    goto HEALTH_CHECK
)

if "%MODE%"=="3" goto HEALTH_ONLY
if "%MODE%"=="4" goto OPEN_DASHBOARD
if "%MODE%"=="5" goto STOP_SYSTEM
if "%MODE%"=="6" exit /b 0

echo Invalid option.
pause
exit /b 1

REM ==========================================================
REM HEALTH CHECK
REM ==========================================================

:HEALTH_ONLY
set "CHECK_ONLY=true"
goto HEALTH_CHECK

:HEALTH_CHECK
echo.
echo ==========================================
echo   RUNNING SYSTEM CHECKS
echo ==========================================
echo.

set "FAILED=0"

echo [1/10] Checking project root...
echo [1/10] Checking project root... >> "%LAUNCHER_LOG%"
if exist "%PROJECT_ROOT%" (
    echo [OK] Project root found.
    echo [OK] Project root found. >> "%LAUNCHER_LOG%"
) else (
    echo [ERROR] Project root missing: %PROJECT_ROOT%
    echo [ERROR] Project root missing. >> "%LAUNCHER_LOG%"
    set "FAILED=1"
)

echo.
echo [2/10] Checking backend folder...
echo [2/10] Checking backend folder... >> "%LAUNCHER_LOG%"
if exist "%PROJECT_ROOT%\backend" (
    echo [OK] backend folder found.
    echo [OK] backend folder found. >> "%LAUNCHER_LOG%"
) else (
    echo [ERROR] backend folder missing.
    echo [ERROR] backend folder missing. >> "%LAUNCHER_LOG%"
    set "FAILED=1"
)

echo.
echo [3/10] Checking frontend folder...
echo [3/10] Checking frontend folder... >> "%LAUNCHER_LOG%"
if exist "%PROJECT_ROOT%\frontend" (
    echo [OK] frontend folder found.
    echo [OK] frontend folder found. >> "%LAUNCHER_LOG%"
) else (
    echo [ERROR] frontend folder missing.
    echo [ERROR] frontend folder missing. >> "%LAUNCHER_LOG%"
    set "FAILED=1"
)

echo.
echo [4/10] Checking backend entrypoint...
echo [4/10] Checking backend entrypoint... >> "%LAUNCHER_LOG%"
if exist "%PROJECT_ROOT%\backend\main.py" (
    echo [OK] backend\main.py found.
    echo [OK] backend\main.py found. >> "%LAUNCHER_LOG%"
) else (
    echo [ERROR] backend\main.py missing.
    echo [ERROR] backend\main.py missing. >> "%LAUNCHER_LOG%"
    set "FAILED=1"
)

echo.
echo [5/10] Checking frontend package.json...
echo [5/10] Checking frontend package.json... >> "%LAUNCHER_LOG%"
if exist "%PROJECT_ROOT%\frontend\package.json" (
    echo [OK] frontend\package.json found.
    echo [OK] frontend\package.json found. >> "%LAUNCHER_LOG%"
) else (
    echo [ERROR] frontend\package.json missing.
    echo [ERROR] frontend\package.json missing. >> "%LAUNCHER_LOG%"
    set "FAILED=1"
)

echo.
echo [6/10] Checking Python...
echo [6/10] Checking Python... >> "%LAUNCHER_LOG%"
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    echo [ERROR] Python not found in PATH. >> "%LAUNCHER_LOG%"
    set "FAILED=1"
) else (
    for /f "tokens=*" %%p in ('python --version 2^>^&1') do set "PY_VER=%%p"
    echo [OK] !PY_VER!
    echo [OK] !PY_VER! >> "%LAUNCHER_LOG%"
)

echo.
echo [7/10] Checking Uvicorn...
echo [7/10] Checking Uvicorn... >> "%LAUNCHER_LOG%"
python -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] uvicorn is not installed for this Python.
    echo Run: pip install uvicorn fastapi
    echo [ERROR] uvicorn missing. >> "%LAUNCHER_LOG%"
    set "FAILED=1"
) else (
    echo [OK] uvicorn found.
    echo [OK] uvicorn found. >> "%LAUNCHER_LOG%"
)

echo.
echo [8/10] Checking Node.js...
echo [8/10] Checking Node.js... >> "%LAUNCHER_LOG%"
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found in PATH.
    echo [ERROR] Node.js not found in PATH. >> "%LAUNCHER_LOG%"
    set "FAILED=1"
) else (
    for /f "tokens=*" %%n in ('node --version 2^>^&1') do set "NODE_VER=%%n"
    echo [OK] Node !NODE_VER!
    echo [OK] Node !NODE_VER! >> "%LAUNCHER_LOG%"
)

echo.
echo [9/10] Checking npm...
echo [9/10] Checking npm... >> "%LAUNCHER_LOG%"
where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm not found in PATH.
    echo [ERROR] npm not found in PATH. >> "%LAUNCHER_LOG%"
    set "FAILED=1"
) else (
    echo [OK] npm found.
    echo [OK] npm found. >> "%LAUNCHER_LOG%"
)

echo.
echo [10/10] Checking .env and Alpaca keys...
echo [10/10] Checking .env and Alpaca keys... >> "%LAUNCHER_LOG%"
if exist "%PROJECT_ROOT%\.env" (
    echo [OK] .env found.
    echo [OK] .env found. >> "%LAUNCHER_LOG%"

    findstr /B /C:"ALPACA_API_KEY=" "%PROJECT_ROOT%\.env" >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] ALPACA_API_KEY not found in .env.
        echo [WARNING] ALPACA_API_KEY not found. >> "%LAUNCHER_LOG%"
    ) else (
        echo [OK] ALPACA_API_KEY line found.
        echo [OK] ALPACA_API_KEY line found. >> "%LAUNCHER_LOG%"
    )

    findstr /B /C:"ALPACA_SECRET_KEY=" "%PROJECT_ROOT%\.env" >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] ALPACA_SECRET_KEY not found in .env.
        echo [WARNING] ALPACA_SECRET_KEY not found. >> "%LAUNCHER_LOG%"
    ) else (
        echo [OK] ALPACA_SECRET_KEY line found.
        echo [OK] ALPACA_SECRET_KEY line found. >> "%LAUNCHER_LOG%"
    )
) else (
    echo [WARNING] .env missing.
    echo [WARNING] .env missing. >> "%LAUNCHER_LOG%"
)

echo.
echo ==========================================
echo   CHECK RESULTS
echo ==========================================

if "%FAILED%"=="1" (
    echo.
    echo One or more critical checks failed.
    echo Fix the errors above before starting.
    echo.
    echo Log file:
    echo %LAUNCHER_LOG%
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] All critical checks passed.
echo Log file:
echo %LAUNCHER_LOG%
echo.

if "%CHECK_ONLY%"=="true" (
    pause
    exit /b 0
)

goto START_SYSTEM

REM ==========================================================
REM START SYSTEM
REM ==========================================================

:START_SYSTEM
echo.
echo ==========================================
echo   STARTING POWER TRADING SYSTEM
echo ==========================================
echo.

echo Selected mode:
echo AI_MODE=%AI_MODE%
echo ALPACA_PAPER=%ALPACA_PAPER%
echo.

echo Stopping old backend/frontend windows...
call :STOP_QUIET

echo.
echo Starting backend...
echo Backend command:
echo python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
echo.

start "Power Trading Backend" cmd /k "cd /d "%PROJECT_ROOT%" && set AI_MODE=%AI_MODE% && set ALPACA_PAPER=%ALPACA_PAPER% && echo BACKEND STARTING... && python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"

timeout /t 6 >nul

echo Starting frontend...
echo Frontend command:
echo npm run dev
echo.

start "Power Trading Frontend" cmd /k "cd /d "%PROJECT_ROOT%\frontend" && echo FRONTEND STARTING... && npm run dev"

timeout /t 8 >nul

echo.
echo Checking backend response...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -Uri '%BACKEND_URL%/docs' -UseBasicParsing -TimeoutSec 3 | Out-Null; Write-Host '[OK] Backend appears online.' } catch { Write-Host '[WARNING] Backend not responding yet. Check backend window.' }"

echo.
echo Checking frontend response...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -Uri '%FRONTEND_URL%' -UseBasicParsing -TimeoutSec 3 | Out-Null; Write-Host '[OK] Frontend appears online.' } catch { Write-Host '[WARNING] Frontend not responding yet. Check frontend window.' }"

echo.
echo Opening dashboard...
start %FRONTEND_URL%

echo.
echo ==========================================
echo   SYSTEM STARTED
echo ==========================================
echo.
echo Backend:
echo   %BACKEND_URL%/docs
echo.
echo Frontend:
echo   %FRONTEND_URL%
echo.
echo Keep these windows open:
echo   Power Trading Backend
echo   Power Trading Frontend
echo.
pause
exit /b 0

REM ==========================================================
REM OPEN DASHBOARD
REM ==========================================================

:OPEN_DASHBOARD
start %FRONTEND_URL%
exit /b 0

REM ==========================================================
REM STOP SYSTEM
REM ==========================================================

:STOP_SYSTEM
echo.
echo Stopping Power Trading System...
call :STOP_QUIET
echo System stopped.
pause
exit /b 0

:STOP_QUIET
taskkill /FI "WINDOWTITLE eq Power Trading Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Power Trading Frontend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend*" /T /F >nul 2>&1

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do taskkill /PID %%a /F >nul 2>&1
exit /b 0
