@echo off
REM This script shows you the project location

cls
echo ============================================================
echo Local Nexus Controller - Project Location
echo ============================================================
echo.
echo Your project is located at:
echo.
echo   %~dp0
echo.
echo ============================================================
echo.
echo To start the controller, you can:
echo.
echo 1. Double-click: start.bat
echo    (in this same folder)
echo.
echo 2. Open PowerShell/Command Prompt here and run:
echo    start.bat
echo.
echo 3. Enable auto-start by double-clicking:
echo    tools\ENABLE_AUTO_START.bat
echo.
echo ============================================================
echo.
echo Copy this path for use in commands:
echo.
echo %~dp0
echo.
pause
