@echo off
REM Simple one-click startup for Local Nexus Controller

echo ============================================================
echo Local Nexus Controller - Quick Start
echo ============================================================
echo.

cd /d "%~dp0"

echo Checking for port conflicts and starting controller...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0run.ps1"

if errorlevel 1 (
    echo.
    echo ============================================================
    echo ERROR: Failed to start
    echo ============================================================
    echo.
    pause
    exit /b 1
)
