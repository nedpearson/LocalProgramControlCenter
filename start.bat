@echo off
REM Windows startup script for Local Nexus Controller

echo ============================================================
echo Local Nexus Controller - Windows Startup
echo ============================================================
echo.

REM Get the directory where this script is located
cd /d "%~dp0"

echo Current directory: %CD%
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from python.org
    echo.
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found
    echo Make sure you're running this from the project root directory
    echo.
    pause
    exit /b 1
)

echo Starting Local Nexus Controller...
echo.
echo If this is the first run, dependencies will be installed automatically.
echo This may take 30-60 seconds. Please wait...
echo.

REM Run the application
python -m local_nexus_controller

REM If the script exits, show error message
if errorlevel 1 (
    echo.
    echo ============================================================
    echo ERROR: Application failed to start
    echo ============================================================
    echo.
    echo If you see "ModuleNotFoundError", try installing manually:
    echo   pip install -r requirements.txt
    echo.
    echo Then run this script again.
    echo.
    pause
    exit /b 1
)
