@echo off
cls
echo.
echo ═══════════════════════════════════════════════════════════════
echo   Setting Up Auto-Start
echo ═══════════════════════════════════════════════════════════════
echo.
echo This will configure the application to start automatically
echo when you log in to Windows.
echo.
echo IMPORTANT: This requires administrator privileges.
echo.
pause
echo.
echo Running setup script...
powershell -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -ArgumentList '-ExecutionPolicy Bypass -File \"%~dp0tools\setup_auto_start.ps1\"'"
echo.
echo ═══════════════════════════════════════════════════════════════
echo   Setup Complete!
echo ═══════════════════════════════════════════════════════════════
echo.
echo The application will now start automatically when you log in.
echo Check the administrator window for progress.
echo.
pause
