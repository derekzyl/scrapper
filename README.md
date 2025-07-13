# E-commerce Web Scraper v1.0.0

A powerful, feature-rich web scraper for e-commerce websites with advanced API support, anti-detection features, and intelligent pagination handling.

## 🚀 Features

### Core Scraping Methods
- **Requests + BeautifulSoup**: Fast scraping for simple websites
- **Selenium**: Dynamic content scraping with browser automation
- **API Detection**: Automatic detection and use of product APIs
- **Direct API Support**: Use known API endpoints for maximum efficiency

### Advanced API Features
- **API Structure Analysis**: Automatically analyze JSON structure and suggest field mappings
- **Intelligent Pagination**: Supports page-based, offset-based, and cursor-based pagination
- **Multi-page Extraction**: Fetch hundreds of products across multiple pages
- **Special API Handling**: Optimized for Best Buy, Nike, Amazon, and other major retailers

### Anti-Detection System
- **Headless Selenium**: Run without browser window to avoid detection
- **User Agent Rotation**: Use different browser signatures for each request
- **Random Delays**: Add realistic delays between requests
- **Enhanced Headers**: Complete browser headers with site-specific optimizations
- **Multiple Fallback Methods**: GET, POST, and Selenium approaches
- **403 Error Bypass**: Automatic strategies to overcome access restrictions

### Data Processing
- **Smart Field Mapping**: Automatic mapping of API fields to standard format
- **Data Sanitization**: Remove ads and non-product items
- **Flexible Export**: CSV and Excel export with custom field selection
- **Data Preview**: Real-time preview of scraped data
- **Field Renaming**: Customize column names in exports

### User Interface
- **Scrollable Interface**: Horizontal and vertical scrolling for all screen sizes
- **Real-time Status**: Live updates on scraping progress
- **Interactive Documentation**: Built-in help system with examples
- **Onboarding**: First-time user guidance with "Don't show again" option

## 📋 Requirements

- Python 3.7+
- Chrome browser (for Selenium)
- Internet connection

## 🛠️ Installation

### Option 1: Using uv (Recommended)
```bash
# Run the installer script
./run.sh  # Linux/Mac
run.bat   # Windows
```

### Option 2: Manual Installation
```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -r requirements.txt

# Run the scraper
uv run python src/main.py
```

## 🎯 Quick Start

1. **Launch the Application**
   ```bash
   ./run.sh  # or run.bat on Windows
   ```

2. **Basic Scraping**
   - Enter website URL
   - Choose scraping method
   - Set Max Pages and Delay
   - Click "Start Scraping"

3. **API Scraping (Advanced)**
   - Enter API endpoint
   - Click "Analyze API Structure" to understand the data
   - Use "API Detection" method
   - Enable anti-detection features

## 🔧 Configuration

### Anti-Detection Settings
- **Headless Selenium**: Run without browser window
- **Rotate User Agents**: Use different browser signatures
- **Add Random Delays**: Mimic human behavior
- **Use Proxy**: Add proxy support (if available)

### Scraping Parameters
- **Max Pages**: Number of pages to scrape (1-100)
- **Delay**: Seconds between requests (0.5-10)
- **Exclude Keywords**: Filter out ads (ad, sponsored, promo)
- **Infinite Scroll**: For dynamic loading sites

### Container Selection
- **None**: Automatic product detection
- **Class**: Specify CSS class name
- **ID**: Specify CSS ID name

## 📊 API Support

### Supported API Types
- **REST APIs**: Standard JSON APIs
- **GraphQL**: Modern API queries
- **Advertising APIs**: Criteo, Google Ads, etc.
- **E-commerce APIs**: Best Buy, Nike, Amazon, etc.

### Pagination Patterns
- **Page-based**: `?page=1&limit=50`
- **Offset-based**: `?offset=0&limit=50`
- **Cursor-based**: `?cursor=abc123`
- **Custom patterns**: Site-specific pagination

### Special API Handling
- **Best Buy**: Optimized for `api.bestbuy.ca` endpoints
- **Criteo**: Handles advertising APIs with 12-product limits
- **Nike**: Special handling for Nike Cloud APIs
- **Amazon**: Enhanced headers and parameters

## 🎨 User Interface

### Main Features
- **Responsive Design**: Works on all screen sizes
- **Scrollable Sections**: Horizontal and vertical scrolling
- **Color-coded Status**: Visual feedback for different states
- **Interactive Elements**: Buttons, checkboxes, and input fields

### Data Management
- **Field Selection**: Choose which columns to export
- **Field Renaming**: Customize column names
- **Data Preview**: View scraped data before export
- **Export Options**: CSV and Excel formats

## 🔍 Troubleshooting

### Common Issues

**403 Errors**
- Enable anti-detection features
- Try different scraping methods
- Use proxy or VPN
- Check if site blocks automated access

**Limited Products (12 products)**
- You might be using an advertising API
- Look for the actual product API
- Use "Analyze API Structure" to understand the data
- Check the help popup for guidance

**Slow Scraping**
- Reduce Max Pages
- Increase Delay between requests
- Use Requests method instead of Selenium
- Enable Headless mode

**No Products Found**
- Check website structure
- Try different container selectors
- Use API Detection method
- Verify the URL is correct

### Debug Information
- **Status Messages**: Real-time progress updates
- **Error Logging**: Detailed error information
- **API Analysis**: JSON structure breakdown
- **Pagination Info**: Page-by-page progress

## 📈 Performance Tips

### For Large Sites
- Start with small Max Pages (1-5)
- Use API endpoints when available
- Enable anti-detection features
- Use appropriate delays

### For Fast Scraping
- Use Requests method for simple sites
- Disable unnecessary anti-detection
- Use direct API endpoints
- Minimize delays

### For Reliable Scraping
- Enable all anti-detection features
- Use longer delays
- Try multiple scraping methods
- Monitor status messages

## 🔒 Privacy & Ethics

### Best Practices
- Respect robots.txt files
- Use reasonable delays
- Don't overload servers
- Follow website terms of service

### Anti-Detection
- Rotate user agents
- Add random delays
- Use headless browsers
- Mimic human behavior

## 📝 Examples

### Basic Website Scraping
```
Website URL: https://example-store.com
Method: Requests
Max Pages: 5
Delay: 1 second
```

### API Scraping
```
Website URL: https://www.bestbuy.ca
API Endpoint: https://api.bestbuy.ca/v2/products?categoryPath.id=20001
Method: API Detection
Max Pages: 10
```

### Anti-Detection Scraping
```
Website URL: https://www.nike.com
Method: Selenium
Headless: Enabled
Rotate User Agents: Enabled
Random Delays: Enabled
```

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the built-in documentation
3. Contact your project provider
4. Check the status messages for guidance

## 📄 License

This project is provided as-is for educational and research purposes. Please respect website terms of service and robots.txt files when scraping.

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Compatibility**: Python 3.7+, Chrome browser
