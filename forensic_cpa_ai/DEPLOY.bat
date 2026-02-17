@echo off
REM Deployment script for Forensic CPA AI
REM This script copies the project files to the target directory

echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║     Forensic CPA AI - Deployment Script                          ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

REM Set the target directory
set TARGET_DIR=C:\Users\nedpe\Desktop\Repositories\Forensic_CPA_AI

echo Target directory: %TARGET_DIR%
echo.

REM Check if target directory exists
if not exist "%TARGET_DIR%" (
    echo Creating target directory...
    mkdir "%TARGET_DIR%"
)

echo Copying project files...

REM Copy all project files
copy /Y main.py "%TARGET_DIR%\"
copy /Y requirements.txt "%TARGET_DIR%\"
copy /Y README.md "%TARGET_DIR%\"
copy /Y SETUP_INSTRUCTIONS.md "%TARGET_DIR%\"
copy /Y .env.example "%TARGET_DIR%\"
copy /Y .gitignore "%TARGET_DIR%\"
copy /Y local-nexus.bundle.json "%TARGET_DIR%\"

echo.
echo ═══════════════════════════════════════════════════════════════════
echo Files copied successfully!
echo.
echo Next steps:
echo   1. Navigate to: %TARGET_DIR%
echo   2. Run: python -m venv .venv
echo   3. Run: .venv\Scripts\activate
echo   4. Run: pip install -r requirements.txt
echo   5. Run: python main.py
echo.
echo Or simply run QUICK_START.bat in the target directory
echo ═══════════════════════════════════════════════════════════════════
echo.

pause
