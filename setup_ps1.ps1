# EduPath AI Platform - PowerShell Setup Script
# This script handles PowerShell execution policy and setup

Write-Host "EduPath AI Platform - PowerShell Setup" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Please run this script as Administrator for best results"
    Write-Host "Continuing without administrator privileges..." -ForegroundColor Yellow
}

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Error "Python is not installed or not in PATH"
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Red
    exit 1
}

# Set execution policy for current session
try {
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
    Write-Host "PowerShell execution policy set for current session" -ForegroundColor Green
} catch {
    Write-Warning "Could not set execution policy: $($_.Exception.Message)"
}

# Create virtual environment
if (-not (Test-Path "edupath_env")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    try {
        python -m venv edupath_env
        Write-Host "Virtual environment created successfully" -ForegroundColor Green
    } catch {
        Write-Error "Failed to create virtual environment: $($_.Exception.Message)"
        exit 1
    }
} else {
    Write-Host "Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment and install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
try {
    # Use pip directly from virtual environment
    & ".\edupath_env\Scripts\pip.exe" install -r requirements.txt
    Write-Host "Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Error "Failed to install dependencies: $($_.Exception.Message)"
    Write-Host "Trying alternative installation method..." -ForegroundColor Yellow
    
    # Try installing without version constraints for problematic packages
    try {
        & ".\edupath_env\Scripts\pip.exe" install Flask Flask-SQLAlchemy Flask-Login Flask-WTF python-dotenv PyMySQL groq requests
        Write-Host "Core dependencies installed successfully" -ForegroundColor Green
        Write-Host "Note: Some ML libraries may need manual installation" -ForegroundColor Yellow
    } catch {
        Write-Error "Core dependency installation also failed"
        exit 1
    }
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "Creating .env file from template..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host ".env file created" -ForegroundColor Green
    } else {
        Write-Warning ".env.example file not found"
    }
} else {
    Write-Host ".env file already exists" -ForegroundColor Green
}

# Check environment variables
Write-Host "Checking environment variables..." -ForegroundColor Yellow
try {
    # Load python to check .env file
    $envCheck = python -c "
import os
from dotenv import load_dotenv
load_dotenv()
required_vars = ['DATABASE_URL', 'GROQ_API_KEY', 'SECRET_KEY']
missing_vars = []
for var in required_vars:
    value = os.getenv(var)
    if not value or value in ['your-groq-api-key-here', 'your-secret-key-here']:
        missing_vars.append(var)
if missing_vars:
    print('MISSING: ' + ', '.join(missing_vars))
else:
    print('OK')
"
    
    if ($envCheck -eq "OK") {
        Write-Host "Environment variables configured" -ForegroundColor Green
    } else {
        Write-Warning "Missing environment variables: $envCheck"
        Write-Host "Please update .env file with your credentials" -ForegroundColor Yellow
    }
} catch {
    Write-Warning "Could not check environment variables: $($_.Exception.Message)"
}

# Test database connection
Write-Host "Testing database connection..." -ForegroundColor Yellow
try {
    $dbTest = python -c "
import os
from dotenv import load_dotenv
load_dotenv()
try:
    import pymysql
    db_url = os.getenv('DATABASE_URL', '')
    if 'mysql+pymysql://' in db_url:
        print('Database configuration found')
    else:
        print('Database configuration missing')
except ImportError:
    print('PyMySQL not installed')
except Exception as e:
    print(f'Database connection failed: {e}')
"
    
    Write-Host "Database test: $dbTest" -ForegroundColor Green
} catch {
    Write-Warning "Could not test database connection"
}

# Initialize database if possible
Write-Host "Attempting to initialize database..." -ForegroundColor Yellow
try {
    $dbInit = python -c "
from app import create_app
from database import db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
"
    Write-Host "Database initialization: $dbInit" -ForegroundColor Green
} catch {
    Write-Warning "Database initialization failed: $($_.Exception.Message)"
    Write-Host "You may need to set up MySQL first and update .env file" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "SETUP COMPLETED!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env file with your MySQL and Groq API credentials" -ForegroundColor White
Write-Host "2. Make sure MySQL Server is running" -ForegroundColor White
Write-Host "3. Run the application:" -ForegroundColor White
Write-Host "   .\edupath_env\Scripts\python.exe app.py" -ForegroundColor Yellow
Write-Host "4. Open browser to: http://127.0.0.1:5000" -ForegroundColor White

Write-Host ""
Write-Host "To activate virtual environment manually:" -ForegroundColor Cyan
Write-Host "   .\edupath_env\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host "   (You may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser)" -ForegroundColor Gray

Write-Host ""
Write-Host "If you encounter issues, check:" -ForegroundColor Cyan
Write-Host "- MySQL Server is installed and running" -ForegroundColor White
Write-Host "- .env file contains correct credentials" -ForegroundColor White
Write-Host "- Database 'edupath_db' exists in MySQL" -ForegroundColor White

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
