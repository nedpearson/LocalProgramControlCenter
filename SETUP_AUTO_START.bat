@echo off
REM One-click setup for auto-start on Windows boot

echo ============================================================
echo Local Nexus Controller - Auto-Start Setup
echo ============================================================
echo.
echo This will configure Windows to automatically start the
echo controller when you log in.
echo.
echo IMPORTANT: This requires administrator privileges.
echo.
pause

REM Run the PowerShell setup script as administrator
powershell -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -ArgumentList '-ExecutionPolicy Bypass -File \"%~dp0tools\setup_auto_start.ps1\"'"

echo.
echo Setup initiated. Check the administrator window for progress.
echo.
pause
