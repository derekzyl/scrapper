@echo off
echo 🎯 E-commerce Scraper Installation Script
echo ==========================================

REM Check Python version
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Run the installation script
echo 🚀 Running installation...
python install.py

echo.
echo 🎉 Installation script completed!
echo Run 'run.bat' to start the application.
pause 