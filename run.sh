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

echo "[INFO] Launching the E-commerce Web Scraper..."
uv run ecommerce-scraper
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to launch the app. Make sure you are in the project directory and dependencies are installed."
    exit 1
fi

