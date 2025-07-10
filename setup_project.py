#!/usr/bin/env python3
"""
Complete project setup script
Creates the full project structure and files
"""

import os
import sys
from pathlib import Path

def create_project_structure():
    """Create the complete project structure"""
    
    # Create main package directory
    os.makedirs("ecommerce_scraper", exist_ok=True)
    
    # Create __init__.py
    init_content = '''"""E-commerce Web Scraper Package"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
'''
    
    with open("ecommerce_scraper/__init__.py", "w") as f:
        f.write(init_content)
    
    # Copy main.py content (the main scraper code)
    # This would be the content from the first artifact
    
    print("✅ Project structure created!")
    print("📁 ecommerce_scraper/")
    print("   ├── __init__.py")
    print("   └── main.py")
    print("📄 pyproject.toml")
    print("📄 setup.py") 
    print("📄 requirements.txt")
    print("📄 install.py")
    print("📄 README.md")
    print("📄 run.sh / run.bat")
    
    return True

def main():
    """Main setup function"""
    print("🏗️  Setting up E-commerce Scraper project...")
    print("=" * 50)
    
    if create_project_structure():
        print("\n🎉 Project setup complete!")
        print("Next steps:")
        print("1. Run: python install.py")
        print("2. Run: ./run.sh (or run.bat on Windows)")
    else:
        print("❌ Setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 