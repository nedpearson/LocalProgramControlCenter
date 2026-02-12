@echo off
cls
echo.
echo ═══════════════════════════════════════════════════════════════
echo   ALL FILES IN THIS PROJECT FOLDER
echo ═══════════════════════════════════════════════════════════════
echo.
echo BATCH FILES (.bat):
echo ───────────────────────────────────────────────────────────────
dir /b *.bat
echo.
echo.
echo DOCUMENTATION (.md and .txt):
echo ───────────────────────────────────────────────────────────────
dir /b *.md *.txt
echo.
echo.
echo ═══════════════════════════════════════════════════════════════
echo CURRENT FOLDER LOCATION:
echo ───────────────────────────────────────────────────────────────
cd
echo.
echo ═══════════════════════════════════════────────────────────════
echo.
echo Press any key to open this folder in File Explorer...
pause > nul
explorer .
