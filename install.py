#!/usr/bin/env python3
"""
Installation script for E-commerce Scraper
This script will set up the environment using uv and install all dependencies
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and handle errors"""
    print(f"📋 {description}")
    print(f"🔧 Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"❌ Error details: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_uv():
    """Install uv package manager"""
    print("🚀 Installing uv package manager...")
    
    system = platform.system().lower()
    
    if system == "windows":
        # Windows installation
        cmd = ["powershell", "-Command", 
               "irm https://astral.sh/uv/install.ps1 | iex"]
    else:
        # Unix-like systems (Linux, macOS)
        cmd = ["curl", "-LsSf", "https://astral.sh/uv/install.sh", "|", "sh"]
        
    print("💾 Installing uv...")
    try:
        if system == "windows":
            subprocess.run(cmd, check=True, shell=True)
        else:
            subprocess.run("curl -LsSf https://astral.sh/uv/install.sh | sh", 
                         check=True, shell=True)
        print("✅ uv installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install uv: {e}")
        print("🔄 Trying alternative installation method...")
        
        # Try pip installation as fallback
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "uv"], 
                         check=True)
            print("✅ uv installed via pip")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install uv via pip")
            return False

def check_uv_installation():
    """Check if uv is installed"""
    print("🔍 Checking for uv installation...")
    try:
        result = subprocess.run(["uv", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Found uv: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ uv not found")
        return False

def setup_project():
    """Set up the project with uv"""
    print("🏗️  Setting up project...")
    
    # Initialize uv project
    if not run_command(["uv", "init", "--no-readme"], "Initializing uv project"):
        print("ℹ️  Project might already be initialized")
    
    # Install dependencies
    if not run_command(["uv", "add", 
                       "requests>=2.31.0",
                       "beautifulsoup4>=4.12.2", 
                       "pandas>=2.0.0",
                       "openpyxl>=3.1.0",
                       "selenium>=4.15.0",
                       "webdriver-manager>=4.0.0",
                       "lxml>=4.9.0"], 
                      "Installing dependencies"):
        return False
    
    print("✅ Project setup complete!")
    return True

def create_launcher_scripts():
    """Create convenient launcher scripts"""
    print("📝 Creating launcher scripts...")
    
    # Create run script for Unix-like systems
    run_script = """#!/bin/bash
echo "🚀 Starting E-commerce Scraper..."
uv run python -m main
"""
    
    # Create run script for Windows
    run_bat = """@echo off
echo 🚀 Starting E-commerce Scraper...
uv run python -m main
pause
"""
    
    try:
        with open("run.sh", "w") as f:
            f.write(run_script)
        os.chmod("run.sh", 0o755)
        
        with open("run.bat", "w") as f:
            f.write(run_bat)
            
        print("✅ Launcher scripts created (run.sh, run.bat)")
        return True
    except Exception as e:
        print(f"❌ Failed to create launcher scripts: {e}")
        return False

def main():
    """Main installation process"""
    print("🎯 E-commerce Scraper Installation Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check if uv is installed
    if not check_uv_installation():
        print("💾 uv not found, installing...")
        if not install_uv():
            print("❌ Failed to install uv. Please install manually:")
            print("   Windows: https://docs.astral.sh/uv/getting-started/installation/")
            print("   Unix: curl -LsSf https://astral.sh/uv/install.sh | sh")
            sys.exit(1)
    
    # Setup project
    if not setup_project():
        print("❌ Failed to set up project")
        sys.exit(1)
    
    # Create launcher scripts
    create_launcher_scripts()
    
    print("\n🎉 Installation Complete!")
    print("=" * 50)
    print("🚀 To run the scraper:")
    print("   Option 1: uv run python -m main")
    print("   Option 2: ./run.sh (Linux/Mac) or run.bat (Windows)")
    print("   Option 3: uv run ecommerce-scraper")
    print("\n📚 Project structure:")
    print("   📁 ecommerce_scraper/")
    print("   📄 pyproject.toml")
    print("   📄 install.py")
    print("   📄 run.sh / run.bat")
    print("\n🔧 To add more dependencies: uv add <package-name>")
    print("🗑️  To remove the environment: uv clean")

if __name__ == "__main__":
    main() 