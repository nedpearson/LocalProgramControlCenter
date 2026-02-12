@echo off
REM Easy installer for auto-start feature
REM Double-click this file to enable auto-start on Windows boot

echo ============================================================
echo Local Nexus Controller - Enable Auto-Start
echo ============================================================
echo.
echo This will configure Windows to automatically start the
echo Local Nexus Controller when you log in.
echo.
echo Press any key to continue or close this window to cancel...
pause > nul

echo.
echo Starting setup...
echo.

REM Run PowerShell script with administrator privileges
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& {Start-Process PowerShell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File ""%~dp0setup_auto_start.ps1""' -Verb RunAs}"

echo.
echo Setup script has been launched.
echo Follow the prompts in the administrator window.
echo.
pause
