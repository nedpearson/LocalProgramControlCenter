@echo off
cls
echo.
echo ═══════════════════════════════════════════════════════════════
echo     LOCAL NEXUS CONTROLLER - MAIN MENU
echo ═══════════════════════════════════════════════════════════════
echo.
echo  What would you like to do?
echo.
echo  [1] Start Controller Now (Manual)
echo      - Starts the controller right now
echo      - Use this to test everything works
echo.
echo  [2] Setup Auto-Start (Requires Admin)
echo      - Configure Windows to start controller on boot
echo      - One-time setup
echo.
echo  [3] View All Files in This Folder
echo      - Shows all .bat and documentation files
echo.
echo  [4] Exit
echo.
echo ═══════════════════════════════════════════════════════════════
echo.
set /p choice=Enter your choice (1-4):

if "%choice%"=="1" (
    echo.
    echo Starting controller...
    call QUICK_START.bat
    goto end
)

if "%choice%"=="2" (
    echo.
    echo Opening auto-start setup...
    echo.
    echo IMPORTANT: You need to run this as Administrator!
    echo Right-click on "SIMPLE_AUTO_START_SETUP.bat" and select "Run as administrator"
    echo.
    pause
    explorer .
    goto end
)

if "%choice%"=="3" (
    call LIST_ALL_FILES.bat
    goto end
)

if "%choice%"=="4" (
    exit
)

echo.
echo Invalid choice. Please try again.
echo.
pause
goto :start

:end
