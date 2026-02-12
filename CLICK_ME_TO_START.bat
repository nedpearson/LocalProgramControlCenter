@echo off
cls
echo.
echo ═══════════════════════════════════════════════════════════════
echo         YOU FOUND THE RIGHT FOLDER!
echo ═══════════════════════════════════════════════════════════════
echo.
echo This folder contains 44 files, but you might only see some of them.
echo.
echo Let me show you ALL the .bat files available:
echo.
echo ───────────────────────────────────────────────────────────────
dir /b *.bat
echo ───────────────────────────────────────────────────────────────
echo.
echo.
echo RECOMMENDED: To start the controller now, type: QUICK_START.bat
echo.
echo Press any key to start the controller...
pause > nul
call QUICK_START.bat
