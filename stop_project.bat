@echo off
title Stop Power Trading System
color 0C

echo ==========================================
echo   POWER TRADING SYSTEM - STOP
echo ==========================================
echo.

echo Closing project terminal windows...

taskkill /FI "WINDOWTITLE eq Power Trading Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Power Trading Frontend*" /T /F >nul 2>&1

echo.
echo Freeing common ports...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /PID %%a /F >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo ==========================================
echo   SYSTEM STOPPED
echo ==========================================
echo.
pause
