# E-commerce Web Scraper

A comprehensive Python application with GUI for scraping e-commerce websites to extract product information and categories. Built with modern tools and best practices.

## 🚀 Features

- **User-friendly GUI** - Built with tkinter for easy interaction
- **Flexible scraping methods** - Choose between Requests+BeautifulSoup or Selenium
- **Smart data extraction** - Automatically detects products and categories
- **Export capabilities** - Save data to CSV or Excel formats
- **Pagination support** - Automatically scrapes multiple pages
- **Real-time progress** - Live updates during scraping
- **Modern packaging** - Uses `uv` for fast dependency management

## 📦 Quick Installation & Setup

### Option 1: Automated Installation (Recommended)

```bash
# Download and run the installation script
python install.py
```

This will:
- Check Python version compatibility
- Install `uv` package manager if not present
- Create virtual environment
- Install all dependencies
- Create launcher scripts

### Option 2: Manual Installation with uv

```bash
# Install uv first (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Unix/Linux/macOS
# or
pip install uv  # Alternative method

# Clone/download the project files
# Then run:
uv sync
```

### Option 3: Traditional pip installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 🏃‍♂️ Running the Application

After installation, you can run the scraper in several ways:

```bash
# Method 1: Using uv (recommended)
uv run python -m main

# Method 2: Using launcher scripts
./run.sh        # Linux/macOS
run.bat         # Windows

# Method 3: Direct execution
uv run ecommerce-scraper

# Method 4: Traditional python
python -m main
```

## 🛠️ Usage Guide

1. **Enter Website URL** - Input the e-commerce site you want to scrape
2. **Choose Scraping Method**:
   - **Requests + BeautifulSoup**: Fast, works with static content
   - **Selenium**: Slower but works with dynamic/JavaScript sites
3. **Configure Settings**:
   - Max pages to scrape
   - Delay between requests (be respectful!)
   - Choose what to scrape (products, categories, or both)
4. **Start Scraping** - Click "Start Scraping" and monitor progress
5. **Export Data** - Use CSV or Excel export options

## 📊 Data Extracted

### Products
- Product name
- Price
- Product URL
- Category
- Image URL (when available)

### Categories
- Category name
- Category URL
- Product count

## 🔧 Dependencies

- **requests** - HTTP requests
- **beautifulsoup4** - HTML parsing
- **pandas** - Data manipulation
- **openpyxl** - Excel file support
- **selenium** - Web browser automation
- **webdriver-manager** - Automatic Chrome driver management
- **lxml** - Fast XML/HTML parsing

## 📁 Project Structure

```
ecommerce-scraper/
├── ecommerce_scraper/
│   ├── __init__.py
│   └── main.py          # Main application
├── pyproject.toml       # uv/pip configuration
├── setup.py            # Traditional setup
├── install.py          # Automated installer
├── README.md           # This file
├── run.sh              # Unix launcher
└── run.bat             # Windows launcher
```

## ⚡ Why uv?

This project uses `uv` as the package manager because it's:
- **Fast** - 10-100x faster than pip
- **Reliable** - Consistent dependency resolution
- **Modern** - Built with Rust, designed for Python
- **Compatible** - Works with existing pip/setuptools projects

## 🤖 Selenium Setup

For dynamic websites, the scraper uses Selenium with Chrome:
- Chrome browser is required
- ChromeDriver is automatically downloaded via webdriver-manager
- Runs in headless mode by default

## 📈 Performance Tips

1. **Use Requests method** for static sites (much faster)
2. **Adjust delays** to be respectful to websites
3. **Limit pages** to avoid overwhelming servers
4. **Check robots.txt** before scraping

## 🔒 Ethical Scraping

- Always check website's `robots.txt`
- Respect rate limits and terms of service
- Use appropriate delays between requests
- Consider reaching out to website owners for permission

## 🐛 Troubleshooting

### Common Issues:

1. **Chrome/ChromeDriver errors**:
   ```bash
   # Update Chrome and clear cache
   uv run python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"
   ```

2. **Permission errors**:
   ```bash
   # On Unix systems
   chmod +x run.sh
   ```

3. **Package conflicts**:
   ```bash
   # Clean and reinstall
   uv clean
   uv sync
   ```

## 📝 License

This project is provided for educational purposes. Always respect website terms of service and robots.txt files.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the scraper.

---

**Happy Scraping! 🗷**
