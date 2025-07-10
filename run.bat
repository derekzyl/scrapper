@echo off
setlocal

REM Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL%==0 (
    echo [INFO] uv is already installed.
) else (
    echo [INFO] uv not found. Installing uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    where uv >nul 2>nul
    if %ERRORLEVEL%==0 (
        echo [INFO] uv installed successfully.
    ) else (
        echo [ERROR] Failed to install uv. Please install it manually from https://astral.sh/uv/
        pause
        exit /b 1
    )
)

echo [INFO] Launching the E-commerce Web Scraper...
uv run ecommerce-scraper
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to launch the app. Make sure you are in the project directory and dependencies are installed.
    pause
    exit /b 1
)
pause
