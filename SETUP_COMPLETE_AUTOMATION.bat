@echo off
REM Complete Automation Setup - One Click Solution
REM This configures everything for zero-touch startup

cls
echo ============================================================
echo Local Nexus Controller - Complete Automation Setup
echo ============================================================
echo.
echo This will configure:
echo   1. Controller starts automatically when Windows boots
echo   2. All services start automatically when controller starts
echo   3. Dashboard opens automatically in your browser
echo.
echo Result: Restart Windows = Everything runs automatically!
echo.
echo ============================================================
echo.
echo Press any key to continue or close this window to cancel...
pause > nul

echo.
echo ============================================================
echo Step 1: Verifying Service Auto-Start Configuration
echo ============================================================
echo.

REM Check .env file
if not exist ".env" (
    echo [X] ERROR: .env file not found!
    echo.
    echo Please copy .env.example to .env first:
    echo   copy .env.example .env
    echo.
    goto :error
)

REM Check if service auto-start is enabled
findstr /C:"LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=true" .env >nul
if %errorlevel% == 0 (
    echo [OK] Service auto-start is ENABLED
    echo      Services will start automatically
) else (
    echo [!] Service auto-start is DISABLED
    echo     Enabling it now...

    REM Try to enable it
    powershell -Command "(Get-Content .env) -replace 'LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=false', 'LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=true' | Set-Content .env"

    echo [OK] Service auto-start ENABLED
)

echo.
echo ============================================================
echo Step 2: Setting Up Windows Auto-Start
echo ============================================================
echo.
echo Launching Windows auto-start setup...
echo This requires administrator privileges.
echo.
echo Please click "Yes" when prompted for administrator access.
echo.

REM Launch the Windows auto-start setup
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& {Start-Process PowerShell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File ""%~dp0tools\setup_auto_start.ps1""' -Verb RunAs -Wait}"

echo.
echo ============================================================
echo Step 3: Verification
echo ============================================================
echo.

REM Check if the task was created
schtasks /query /tn "Local Nexus Controller" >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Windows Task Scheduler task created successfully!
    echo.
    goto :success
) else (
    echo [!] Task not found. Setup may have been cancelled.
    echo.
    goto :error
)

:success
echo ============================================================
echo SUCCESS! Complete Automation is Now Configured
echo ============================================================
echo.
echo What happens now:
echo.
echo 1. When you log in to Windows:
echo    - Controller starts automatically
echo    - Runs in background
echo.
echo 2. When controller starts:
echo    - All services with start_command auto-start
echo    - Logs saved to data/logs/
echo    - Dashboard opens in browser
echo.
echo 3. You see:
echo    - Browser opens to http://localhost:5010
echo    - Green "Running" status for all services
echo    - Everything ready to use!
echo.
echo ============================================================
echo Next Steps
echo ============================================================
echo.
echo 1. Test it now (optional):
echo    - Start the controller: start.bat
echo    - Check dashboard: http://localhost:5010
echo    - Verify services are running
echo.
echo 2. Test full automation:
echo    - Log out of Windows (or restart)
echo    - Log back in
echo    - Controller and services start automatically!
echo.
echo 3. View auto-start logs:
echo    - Check: data/logs/
echo    - Each service has its own log file
echo.
echo ============================================================
echo Configuration Files
echo ============================================================
echo.
echo Service auto-start: .env (LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=true)
echo Windows auto-start: Task Scheduler ("Local Nexus Controller")
echo Startup script: tools\start_nexus_on_boot.bat
echo.
echo To disable automation:
echo   - Run: tools\DISABLE_AUTO_START.bat
echo.
echo ============================================================
echo.
pause
exit /b 0

:error
echo ============================================================
echo Setup was not completed
echo ============================================================
echo.
echo Please fix the errors above and try again.
echo.
echo For manual setup:
echo   1. Double-click: tools\ENABLE_AUTO_START.bat
echo   2. Or see: AUTO_START_GUIDE.md
echo.
pause
exit /b 1
