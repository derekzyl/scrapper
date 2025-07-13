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

REM Check if this is a git repository and pull latest changes
if exist ".git" (
    echo [INFO] Git repository detected. Pulling latest changes...
    git pull origin master >nul 2>nul
    if %ERRORLEVEL%==0 (
        echo [INFO] Successfully pulled latest changes from repository.
    ) else (
        git pull origin main >nul 2>nul
        if %ERRORLEVEL%==0 (
            echo [INFO] Successfully pulled latest changes from repository.
        ) else (
            echo [WARNING] Failed to pull latest changes. Continuing with current version...
        )
    )
) else (
    echo [INFO] Not a git repository. Skipping git pull.
)

echo [INFO] Launching the E-commerce Web Scraper...
uv run ecommerce-scraper
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to launch the app. Make sure you are in the project directory and dependencies are installed.
    pause
    exit /b 1
)
pause
