#!/bin/sh

# Check if uv is installed
if command -v uv >/dev/null 2>&1; then
    echo "[INFO] uv is already installed."
else
    echo "[INFO] uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    if command -v uv >/dev/null 2>&1; then
        echo "[INFO] uv installed successfully."
    else
        echo "[ERROR] Failed to install uv. Please install it manually from https://astral.sh/uv/"
        exit 1
    fi
fi

# Check if this is a git repository and pull latest changes
if [ -d ".git" ]; then
    echo "[INFO] Git repository detected. Pulling latest changes..."
    git pull origin master 2>/dev/null || git pull origin main 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "[INFO] Successfully pulled latest changes from repository."
    else
        echo "[WARNING] Failed to pull latest changes. Continuing with current version..."
    fi
else
    echo "[INFO] Not a git repository. Skipping git pull."
fi

echo "[INFO] Launching the E-commerce Web Scraper..."
uv run ecommerce-scraper
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to launch the app. Make sure you are in the project directory and dependencies are installed."
    exit 1
fi

