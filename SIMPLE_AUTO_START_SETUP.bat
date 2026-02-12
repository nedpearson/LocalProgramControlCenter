@echo off
REM Simple Auto-Start Setup - No Complex Dependencies

cls
echo ============================================================
echo Local Nexus Controller - Simple Auto-Start Setup
echo ============================================================
echo.
echo This will configure Windows to automatically start the
echo controller when you log in.
echo.
echo REQUIRES: Administrator privileges
echo.
pause

cd /d "%~dp0"

REM Create the startup script content
set SCRIPT_PATH=%~dp0tools\auto_start_controller.ps1

echo.
echo Creating Task Scheduler entry...
echo.

REM Create the scheduled task
schtasks /Create /TN "Local Nexus Controller" /TR "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File \"%SCRIPT_PATH%\"" /SC ONLOGON /RL HIGHEST /F

if errorlevel 1 (
    echo.
    echo ============================================================
    echo ERROR: Failed to create scheduled task
    echo ============================================================
    echo.
    echo Make sure you run this as Administrator.
    echo Right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo SUCCESS! Auto-start configured
echo ============================================================
echo.
echo The controller will now start automatically when you log in.
echo.
echo To test it:
echo   1. Log out and log back in
echo   2. OR run: QUICK_START.bat
echo.
echo To disable:
echo   schtasks /Delete /TN "Local Nexus Controller" /F
echo.
pause
