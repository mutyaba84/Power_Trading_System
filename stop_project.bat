@echo off
title Stop Power Trading System
color 0C

if not "%1"=="silent" (
    echo ==========================================
    echo   POWER TRADING SYSTEM - STOP
    echo ==========================================
    echo.
)

taskkill /FI "WINDOWTITLE eq Power Trading Backend Monitor*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Power Trading Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Power Trading Frontend*" /T /F >nul 2>&1

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /PID %%a /F >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do (
    taskkill /PID %%a /F >nul 2>&1
)

if not "%1"=="silent" (
    echo System stopped.
    echo.
    pause
)
