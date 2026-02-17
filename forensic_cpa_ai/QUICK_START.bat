@echo off
REM Quick Start script for Forensic CPA AI
REM Run this from the project directory

echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║     Forensic CPA AI - Quick Start                                ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from:
    echo   - Microsoft Store: Search for "Python 3.12"
    echo   - Official site: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Python found!
python --version
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created!
    echo.
)

REM Activate virtual environment and install dependencies
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed!
    echo.
)

REM Create .env if it doesn't exist
if not exist ".env" (
    echo Creating .env file from .env.example...
    copy .env.example .env
)

REM Create uploads directory
if not exist "uploads" (
    mkdir uploads
)

echo.
echo ═══════════════════════════════════════════════════════════════════
echo Starting Forensic CPA AI...
echo ═══════════════════════════════════════════════════════════════════
echo.

REM Start the application
python main.py
