@echo off
REM Easy uninstaller for auto-start feature
REM Double-click this file to disable auto-start on Windows boot

echo ============================================================
echo Local Nexus Controller - Disable Auto-Start
echo ============================================================
echo.
echo This will stop the Local Nexus Controller from
echo automatically starting when you log in.
echo.
echo Press any key to continue or close this window to cancel...
pause > nul

echo.
echo Starting removal...
echo.

REM Run PowerShell script with administrator privileges
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& {Start-Process PowerShell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File ""%~dp0disable_auto_start.ps1""' -Verb RunAs}"

echo.
echo Removal script has been launched.
echo Follow the prompts in the administrator window.
echo.
pause
