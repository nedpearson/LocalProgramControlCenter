@echo off
cls
echo.
echo ═══════════════════════════════════════════════════════════════
echo   Starting Local Nexus Controller
echo ═══════════════════════════════════════════════════════════════
echo.
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo.
echo Starting application on http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo ═══════════════════════════════════════════════════════════════
echo.
python -m local_nexus_controller
