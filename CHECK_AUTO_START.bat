@echo off
REM Quick diagnostic tool to check auto-start configuration

cls
echo ============================================================
echo Local Nexus Controller - Auto-Start Diagnostic
echo ============================================================
echo.

REM Get the directory where this script is located
cd /d "%~dp0"

echo Checking configuration...
echo.

REM Check if .env exists
if not exist ".env" (
    echo [X] ERROR: .env file not found
    echo.
    echo Please copy .env.example to .env and configure it.
    echo.
    goto :end
)

echo [OK] Found .env file
echo.

REM Check for auto-start setting
findstr /C:"LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=true" .env >nul
if %errorlevel% == 0 (
    echo [OK] Auto-start is ENABLED
    echo      Services will start automatically when controller starts
) else (
    echo [!] Auto-start is DISABLED
    echo     To enable, edit .env and set:
    echo     LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=true
)
echo.

echo ============================================================
echo Configuration Summary
echo ============================================================
echo.

REM Show key settings
echo Port:
findstr /C:"LOCAL_NEXUS_PORT" .env | findstr /V "#"
echo.

echo Host:
findstr /C:"LOCAL_NEXUS_HOST" .env | findstr /V "#"
echo.

echo Auto-start:
findstr /C:"LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT" .env | findstr /V "#"
echo.

echo Repositories folder:
findstr /C:"LOCAL_NEXUS_REPOSITORIES_FOLDER" .env | findstr /V "#"
echo.

echo Auto-discovery:
findstr /C:"LOCAL_NEXUS_AUTO_DISCOVERY_ENABLED" .env | findstr /V "#"
echo.

echo ============================================================
echo.

REM Check if database exists
if exist "data\local_nexus.db" (
    echo [OK] Database found at: data\local_nexus.db
    echo.
    echo To see registered services:
    echo   1. Start the controller: start.bat
    echo   2. Open: http://localhost:5010
    echo   3. Click: Services
    echo.
) else (
    echo [!] Database not found yet
    echo     It will be created when you first run the controller
    echo.
)

echo ============================================================
echo Next Steps
echo ============================================================
echo.
echo 1. Start the controller:
echo    - Double-click: start.bat
echo.
echo 2. Check the dashboard:
echo    - Open: http://localhost:5010
echo    - Go to: Services page
echo    - Look for green "Running" status
echo.
echo 3. If services have errors:
echo    - Click service name
echo    - Check "Last Error" field
echo    - Check logs at bottom
echo    - Fix issues
echo.
echo 4. For more help:
echo    - Read: AUTO_START_TROUBLESHOOTING.md
echo    - Or: START_HERE_AFTER_REBOOT.md
echo.

:end
echo ============================================================
echo.
pause
