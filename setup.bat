@echo off
ECHO EduPath AI Platform - Quick Setup for Windows
ECHO ========================================

REM Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Python is not installed or not in PATH
    ECHO Please install Python 3.8+ from https://python.org
    PAUSE
    EXIT /B 1
)

ECHO Python found successfully

REM Create virtual environment
IF NOT EXISTS "edupath_env" (
    ECHO Creating virtual environment...
    python -m venv edupath_env
    IF %ERRORLEVEL% NEQ 0 (
        ECHO ERROR: Failed to create virtual environment
        PAUSE
        EXIT /B 1
    )
) ELSE (
    ECHO Virtual environment already exists
)

REM Activate virtual environment and install dependencies
ECHO Installing dependencies...
edupath_env\Scripts\pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Failed to install dependencies
    PAUSE
    EXIT /B 1
)

REM Create .env file if it doesn't exist
IF NOT EXISTS ".env" (
    IF EXIST ".env.example" (
        ECHO Creating .env file from template...
        COPY .env.example .env
        ECHO.
        ECHO IMPORTANT: Please edit .env file with your:
        ECHO - MySQL database credentials
        ECHO - Groq API key
        ECHO - Secret key
        ECHO.
        ECHO Then run this script again or start the application manually.
    ) ELSE (
        ECHO ERROR: .env.example file not found
    )
)

ECHO.
ECHO Setup completed successfully!
ECHO.
ECHO Next steps:
ECHO 1. Edit .env file with your credentials
ECHO 2. Make sure MySQL is running
ECHO 3. Run: edupath_env\Scripts\python app.py
ECHO 4. Open browser to: http://127.0.0.1:5000
ECHO.
PAUSE
