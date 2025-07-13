import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv
import json
import re
import time
import random
from urllib.parse import urljoin, urlparse
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import warnings
import sys
import os

warnings.filterwarnings('ignore')

class EcommerceScraper:
    def __init__(self, root):
        self.root = root
        self.root.title("E-commerce Web Scraper v1.0.0")
        self.root.geometry("900x700")
        
        # Set icon if available
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Data storage
        self.products = []
        self.categories = []
        self.is_scraping = False
        self.driver = None
        
        # Setup GUI
        self.setup_gui()
        
    def setup_gui(self):
        # Create main style
        style = ttk.Style()
        style.theme_use('clam')

        # --- Scrollable Canvas Setup ---
        outer_frame = ttk.Frame(self.root)
        outer_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        canvas = tk.Canvas(outer_frame, borderwidth=0, highlightthickness=0)
        v_scroll = ttk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
        h_scroll = ttk.Scrollbar(outer_frame, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        outer_frame.rowconfigure(0, weight=1)
        outer_frame.columnconfigure(0, weight=1)

        # Frame inside canvas for all content
        main_frame = ttk.Frame(canvas, padding="15")
        self.main_frame = main_frame  # Save reference if needed
        main_frame_id = canvas.create_window((0, 0), window=main_frame, anchor="nw")

        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        main_frame.bind("<Configure>", _on_frame_configure)

        def _on_canvas_configure(event):
            # Make the inner frame width/height match the canvas if smaller
            canvas.itemconfig(main_frame_id, width=event.width)
        canvas.bind("<Configure>", _on_canvas_configure)

        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        def _on_shift_mousewheel(event):
            canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<Shift-MouseWheel>", _on_shift_mousewheel)

        # --- All UI below goes inside main_frame ---
        # Title
        title_label = ttk.Label(main_frame, text=" Web Scraper ", 
                               font=('Arial', 18, 'bold'), foreground='#2c3e50')
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))
        
        # URL input section
        url_frame = ttk.LabelFrame(main_frame, text="Website Configuration", padding="10")
        url_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(url_frame, text="Website URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(url_frame, width=70, font=('Arial', 10))
        self.url_entry.grid(row=0, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.url_entry.insert(0, "https://example-store.com")
        
        # API Endpoint input (new)
        ttk.Label(url_frame, text="API Endpoint (Optional):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.api_endpoint_entry = ttk.Entry(url_frame, width=70, font=('Arial', 10))
        self.api_endpoint_entry.grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.api_endpoint_entry.insert(0, "")
        
        # Product list container selector
        ttk.Label(url_frame, text="Product List Container:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.container_selector_type = tk.StringVar(value="none")
        none_radio = ttk.Radiobutton(url_frame, text="None", variable=self.container_selector_type, value="none")
        class_radio = ttk.Radiobutton(url_frame, text="Class", variable=self.container_selector_type, value="class")
        id_radio = ttk.Radiobutton(url_frame, text="ID", variable=self.container_selector_type, value="id")
        none_radio.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        class_radio.grid(row=2, column=2, sticky=tk.W, padx=(10, 0))
        id_radio.grid(row=2, column=3, sticky=tk.W, padx=(10, 0))
        self.container_selector_entry = ttk.Entry(url_frame, width=30, font=('Arial', 10))
        self.container_selector_entry.grid(row=2, column=4, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.container_selector_entry.insert(0, "product-list")
        
        # Scraping options
        options_frame = ttk.LabelFrame(main_frame, text="Scraping Options", padding="10")
        options_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Method selection
        ttk.Label(options_frame, text="Scraping Method:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.method_var = tk.StringVar(value="requests")
        method_frame = ttk.Frame(options_frame)
        method_frame.grid(row=0, column=1, columnspan=3, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(method_frame, text="Requests + BeautifulSoup (Fast)", 
                       variable=self.method_var, value="requests").pack(side=tk.LEFT)
        ttk.Radiobutton(method_frame, text="Selenium (Dynamic sites)", 
                       variable=self.method_var, value="selenium").pack(side=tk.LEFT, padx=(20, 0))
        ttk.Radiobutton(method_frame, text="API Detection (Auto)", 
                       variable=self.method_var, value="api").pack(side=tk.LEFT, padx=(20, 0))
        
        # Headless Selenium option
        self.headless_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Use Headless Selenium (Avoid bot detection)", 
                       variable=self.headless_var).grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=5)
        
        # Anti-detection options
        anti_detection_frame = ttk.Frame(options_frame)
        anti_detection_frame.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=5)
        
        self.rotate_ua_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(anti_detection_frame, text="Rotate User Agents", 
                       variable=self.rotate_ua_var).pack(side=tk.LEFT, padx=(0, 10))
        
        self.use_proxy_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(anti_detection_frame, text="Use Proxy (if available)", 
                       variable=self.use_proxy_var).pack(side=tk.LEFT, padx=(0, 10))
        
        self.delay_requests_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(anti_detection_frame, text="Add Random Delays", 
                       variable=self.delay_requests_var).pack(side=tk.LEFT)
        
        # API Analysis button
        api_analysis_frame = ttk.Frame(options_frame)
        api_analysis_frame.grid(row=3, column=0, columnspan=4, sticky=tk.W, pady=5)
        ttk.Button(api_analysis_frame, text="Analyze API Structure", 
                  command=self.analyze_api_structure).pack(side=tk.LEFT, padx=(0, 10))
        self.api_analysis_status = ttk.Label(api_analysis_frame, text="", foreground='#27ae60')
        self.api_analysis_status.pack(side=tk.LEFT)
        
        # Parameters
        params_frame = ttk.Frame(options_frame)
        params_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(params_frame, text="Max Pages:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.max_pages_var = tk.StringVar(value="5")
        ttk.Entry(params_frame, textvariable=self.max_pages_var, width=8).grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(params_frame, text="Delay (sec):").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.delay_var = tk.StringVar(value="1")
        ttk.Entry(params_frame, textvariable=self.delay_var, width=8).grid(row=0, column=3, padx=(0, 20))

        # Exclusion keywords for sanitization
        ttk.Label(params_frame, text="Exclude Keywords (comma separated):").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.exclude_keywords_var = tk.StringVar(value="ad,sponsored,promo,banner")
        ttk.Entry(params_frame, textvariable=self.exclude_keywords_var, width=30).grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=(0, 20))

        # Infinite scroll option
        self.infinite_scroll_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(params_frame, text="Enable Infinite Scroll (Selenium only)", variable=self.infinite_scroll_var).grid(row=1, column=3, sticky=tk.W)
        
        # What to scrape
        ttk.Label(params_frame, text="Scrape:").grid_forget()
        self.scrape_products_var = tk.BooleanVar(value=True)
        self.scrape_categories_var = tk.BooleanVar(value=False)
        # Remove checkboxes for products and categories
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=4, pady=15)
        
        self.start_btn = ttk.Button(button_frame, text="Start Scraping", command=self.start_scraping, style='Accent.TButton')
        self.start_btn.grid(row=0, column=0, padx=10)
        self.stop_btn = ttk.Button(button_frame, text="Stop Scraping", command=self.stop_scraping, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=10)
        self.export_csv_btn = ttk.Button(button_frame, text="Export CSV", command=self.export_csv)
        self.export_csv_btn.grid(row=0, column=2, padx=10)
        self.export_excel_btn = ttk.Button(button_frame, text="Export Excel", command=self.export_excel)
        self.export_excel_btn.grid(row=0, column=3, padx=10)
        self.clear_btn = ttk.Button(button_frame, text="Clear Data", command=self.clear_data)
        self.clear_btn.grid(row=0, column=4, padx=10)

        # Header selection (for sanitization)
        self.header_frame = ttk.LabelFrame(main_frame, text="Select Fields to Keep", padding="10")
        self.header_frame.grid(row=6, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        self.header_vars = {}
        self.header_checkbuttons = {}
        self.header_rename_vars = {}
        self.header_frame.grid_remove()  # Hide initially

        # Data preview grid
        self.preview_frame = ttk.LabelFrame(main_frame, text="Data Preview (Random 20 Products)", padding="10")
        self.preview_frame.grid(row=7, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        self.preview_tree = None
        self.preview_frame.grid_remove()  # Hide initially
        
        # Feedback/status area
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=6, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        self.status_var = tk.StringVar(value="Ready.")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, font=('Arial', 10), foreground='#2980b9')
        self.status_label.pack(anchor=tk.W, fill=tk.X)

    def set_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()
        
    def analyze_api_structure(self):
        """Analyze API endpoint structure and create key-value mappings"""
        api_endpoint = self.api_endpoint_entry.get().strip()
        if not api_endpoint:
            messagebox.showwarning("Warning", "Please enter an API endpoint first.")
            return
            
        self.api_analysis_status.config(text="Analyzing...")
        self.root.update_idletasks()
        
        # Run analysis in a separate thread
        threading.Thread(target=self._analyze_api_structure_thread, args=(api_endpoint,), daemon=True).start()
        
    def _analyze_api_structure_thread(self, api_endpoint):
        """Thread function to analyze API structure"""
        try:
            self.set_status(f"Analyzing API structure: {api_endpoint}")
            
            # Use headless Selenium to get the API response
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            
            try:
                # Navigate to the main site first to get proper headers
                base_url = self.url_entry.get().strip()
                if base_url:
                    driver.get(base_url)
                    time.sleep(3)
                
                # Make the API request
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': base_url if base_url else api_endpoint,
                }
                
                response = requests.get(api_endpoint, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    try:
                        api_data = response.json()
                        analysis_result = self._analyze_json_structure(api_data)
                        
                        # Show analysis results in a popup
                        self.root.after(0, lambda: self._show_api_analysis_results(analysis_result))
                        
                    except json.JSONDecodeError:
                        self.root.after(0, lambda: messagebox.showerror("Error", "API response is not valid JSON"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"API request failed with status {response.status_code}"))
                    
            finally:
                driver.quit()
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Analysis failed: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.api_analysis_status.config(text=""))
            
    def _analyze_json_structure(self, data, path="", max_depth=3):
        """Recursively analyze JSON structure to find product data patterns"""
        analysis = {
            'structure': {},
            'product_arrays': [],
            'field_mappings': {},
            'sample_data': {}
        }
        
        def analyze_recursive(obj, current_path, depth=0):
            if depth > max_depth:
                return
                
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{current_path}.{key}" if current_path else key
                    
                    # Check if this looks like a product array
                    if isinstance(value, list) and len(value) > 0:
                        if isinstance(value[0], dict):
                            # Analyze first item to see if it's a product
                            first_item = value[0]
                            product_indicators = ['name', 'title', 'price', 'id', 'productId', 'sku', 'url', 'image']
                            score = sum(1 for indicator in product_indicators if indicator.lower() in str(first_item).lower())
                            
                            if score >= 2:  # Likely a product array
                                analysis['product_arrays'].append({
                                    'path': new_path,
                                    'count': len(value),
                                    'sample_item': first_item,
                                    'score': score
                                })
                                
                                # Analyze fields in the first product
                                if len(value) > 0:
                                    analysis['sample_data'][new_path] = value[0]
                                    analysis['field_mappings'][new_path] = self._suggest_field_mappings(value[0])
                    
                    analyze_recursive(value, new_path, depth + 1)
                    
            elif isinstance(obj, list) and len(obj) > 0:
                analyze_recursive(obj[0], current_path, depth + 1)
                
        analyze_recursive(data, path)
        return analysis
        
    def _suggest_field_mappings(self, product_item):
        """Suggest field mappings for a product item"""
        mappings = {}
        
        # Common field patterns
        field_patterns = {
            'url': ['url', 'link', 'href', 'product_url', 'productUrl', 'permalink'],
            'title': ['title', 'name', 'product_name', 'product_title', 'displayName', 'label'],
            'price': ['price', 'cost', 'amount', 'current_price', 'sale_price', 'currentPrice', 'value'],
            'model_number': ['model', 'model_number', 'sku', 'product_id', 'mpn', 'productId', 'code'],
            'upc': ['upc', 'barcode', 'ean', 'gtin', 'isbn'],
            'imageUrl': ['image', 'image_url', 'imageUrl', 'thumbnail', 'photo', 'heroImage', 'img']
        }
        
        for our_field, patterns in field_patterns.items():
            for pattern in patterns:
                # Check exact matches first
                if pattern in product_item:
                    mappings[our_field] = pattern
                    break
                # Check case-insensitive matches
                elif any(key.lower() == pattern.lower() for key in product_item.keys()):
                    matching_key = next(key for key in product_item.keys() if key.lower() == pattern.lower())
                    mappings[our_field] = matching_key
                    break
                    
        return mappings
        
    def _show_api_analysis_results(self, analysis):
        """Show API analysis results in a popup window"""
        popup = tk.Toplevel(self.root)
        popup.title("API Structure Analysis Results")
        popup.geometry("800x600")
        popup.transient(self.root)
        popup.grab_set()
        
        # Create scrollable frame
        canvas = tk.Canvas(popup)
        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Title
        title_label = ttk.Label(scrollable_frame, text="API Structure Analysis", font=('Arial', 14, 'bold'))
        title_label.pack(pady=10)
        
        if analysis['product_arrays']:
            # Found product arrays
            ttk.Label(scrollable_frame, text="Found Product Arrays:", font=('Arial', 12, 'bold')).pack(pady=(10, 5), anchor=tk.W)
            
            for i, product_array in enumerate(analysis['product_arrays']):
                array_frame = ttk.LabelFrame(scrollable_frame, text=f"Array {i+1}: {product_array['path']}")
                array_frame.pack(fill=tk.X, padx=10, pady=5)
                
                ttk.Label(array_frame, text=f"Products found: {product_array['count']}").pack(anchor=tk.W, padx=5, pady=2)
                ttk.Label(array_frame, text=f"Confidence score: {product_array['score']}/8").pack(anchor=tk.W, padx=5, pady=2)
                
                # Show field mappings
                if product_array['path'] in analysis['field_mappings']:
                    mappings = analysis['field_mappings'][product_array['path']]
                    if mappings:
                        ttk.Label(array_frame, text="Suggested field mappings:").pack(anchor=tk.W, padx=5, pady=(10, 5))
                        for our_field, api_field in mappings.items():
                            ttk.Label(array_frame, text=f"  {our_field} → {api_field}").pack(anchor=tk.W, padx=20, pady=1)
                
                # Show sample data
                if product_array['path'] in analysis['sample_data']:
                    sample = analysis['sample_data'][product_array['path']]
                    ttk.Label(array_frame, text="Sample product data:").pack(anchor=tk.W, padx=5, pady=(10, 5))
                    
                    # Create a text widget for the sample data
                    sample_text = tk.Text(array_frame, height=8, width=60)
                    sample_text.pack(padx=5, pady=5, fill=tk.X)
                    sample_text.insert(tk.END, json.dumps(sample, indent=2))
                    sample_text.config(state=tk.DISABLED)
                    
            # Add button to use this analysis
            ttk.Button(scrollable_frame, text="Use This API Structure", 
                      command=lambda: self._use_api_analysis(analysis)).pack(pady=10)
        else:
            ttk.Label(scrollable_frame, text="No product arrays found in the API response.", 
                     font=('Arial', 10)).pack(pady=20)
            
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def _use_api_analysis(self, analysis):
        """Use the analyzed API structure for scraping"""
        if analysis['product_arrays']:
            # Store the analysis results for use during scraping
            self.api_analysis = analysis
            messagebox.showinfo("Success", "API analysis stored. You can now start scraping with the 'API Detection' method.")
        else:
            messagebox.showwarning("Warning", "No product arrays found in the analysis.")
            
    def _get_random_user_agent(self):
        """Get a random user agent to avoid detection"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        ]
        return random.choice(user_agents)
        
    def _get_enhanced_headers(self, base_url, api_endpoint):
        """Get enhanced headers to bypass 403 errors"""
        headers = {
            'User-Agent': self._get_random_user_agent() if self.rotate_ua_var.get() else 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*, text/html, application/xhtml+xml, application/xml;q=0.9, image/webp, image/apng, */*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8,fr;q=0.7,de;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # Add referer and origin if we have a base URL
        if base_url:
            parsed_base = urlparse(base_url)
            headers['Referer'] = base_url
            headers['Origin'] = f"{parsed_base.scheme}://{parsed_base.netloc}"
            
        # Add specific headers for common e-commerce sites
        if 'nike' in api_endpoint.lower():
            headers.update({
                'x-nike-visitor-id': 'visid_' + ''.join(random.choices('0123456789abcdef', k=32)),
                'x-requested-with': 'XMLHttpRequest'
            })
        elif 'amazon' in api_endpoint.lower():
            headers.update({
                'x-amz-cf-id': ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz', k=64)),
                'x-amz-cf-pop': 'IAD89-P1'
            })
        elif 'walmart' in api_endpoint.lower():
            headers.update({
                'wm_sec': '1',
                'wm_qos': '3'
            })
            
        return headers
        
    def _make_anti_detection_request(self, url, base_url, max_retries=3):
        """Make an API request with anti-detection measures"""
        session = requests.Session()
        
        # Add random delay if enabled
        if self.delay_requests_var.get():
            time.sleep(random.uniform(1, 3))
            
        for attempt in range(max_retries):
            try:
                headers = self._get_enhanced_headers(base_url, url)
                
                # Try different request methods
                if attempt == 0:
                    response = session.get(url, headers=headers, timeout=15)
                elif attempt == 1:
                    # Try with different accept header
                    headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
                    response = session.get(url, headers=headers, timeout=15)
                else:
                    # Try POST request for some APIs
                    response = session.post(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    self.set_status(f"403 error on attempt {attempt + 1}, trying different approach...")
                    # Wait longer before retry
                    time.sleep(random.uniform(2, 5))
                else:
                    self.set_status(f"HTTP {response.status_code} on attempt {attempt + 1}")
                    
            except Exception as e:
                self.set_status(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(1, 3))
                    
        return None
        
    def _try_selenium_api_request(self, api_endpoint, base_url):
        """Try to get API response using Selenium to bypass 403"""
        try:
            options = Options()
            if self.headless_var.get():
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            
            try:
                # Execute script to remove webdriver property
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                # Navigate to base URL first to set cookies
                if base_url:
                    driver.get(base_url)
                    time.sleep(3)
                
                # Now try to get the API response
                driver.get(api_endpoint)
                time.sleep(5)
                
                # Try to get the response from network logs
                logs = driver.get_log('performance')
                for entry in logs:
                    try:
                        message = json.loads(entry['message'])
                        if 'message' in message and message['message']['method'] == 'Network.responseReceived':
                            request_url = message['message']['params']['response']['url']
                            if api_endpoint in request_url:
                                # Try to get response body
                                response_body = driver.execute_script("""
                                    return window.performance.getEntries().find(entry => 
                                        entry.name.includes(arguments[0])
                                    );
                                """, api_endpoint)
                                if response_body:
                                    return response_body
                    except:
                        continue
                        
            finally:
                driver.quit()
                
        except Exception as e:
            self.set_status(f"Selenium API request failed: {e}")
            
        return None

    def update_header_selection(self):
        # Called after scraping to update header checkboxes
        # Remove previous canvas if exists
        if hasattr(self, 'header_canvas') and self.header_canvas:
            self.header_canvas.destroy()
        if hasattr(self, 'header_h_scroll') and self.header_h_scroll:
            self.header_h_scroll.destroy()
        # Clear previous vars
        self.header_vars.clear()
        self.header_checkbuttons.clear()
        self.header_rename_vars = {}
        if not self.products:
            self.header_frame.grid_remove()
            return
        all_keys = set()
        for p in self.products:
            all_keys.update(p.keys())
        all_keys = sorted(all_keys)
        # Create a canvas for horizontal scrolling
        self.header_canvas = tk.Canvas(self.header_frame, width=900, height=60, highlightthickness=0)
        self.header_canvas.grid(row=0, column=0, sticky="nsew")
        self.header_h_scroll = ttk.Scrollbar(self.header_frame, orient="horizontal", command=self.header_canvas.xview)
        self.header_h_scroll.grid(row=1, column=0, sticky="ew")
        self.header_canvas.configure(xscrollcommand=self.header_h_scroll.set)
        # Frame inside canvas
        header_inner_frame = ttk.Frame(self.header_canvas)
        for i, key in enumerate(all_keys):
            var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(header_inner_frame, text=key, variable=var, command=self.update_preview_grid)
            cb.grid(row=0, column=2*i, sticky=tk.W, padx=5, pady=2)
            rename_var = tk.StringVar(value=key)
            rename_entry = ttk.Entry(header_inner_frame, textvariable=rename_var, width=12)
            rename_entry.grid(row=0, column=2*i+1, sticky=tk.W, padx=(0, 10), pady=2)
            self.header_rename_vars[key] = rename_var
            self.header_vars[key] = var
            self.header_checkbuttons[key] = cb
        header_inner_frame.update_idletasks()
        self.header_canvas.create_window((0, 0), window=header_inner_frame, anchor="nw")
        header_inner_frame.update_idletasks()
        self.header_canvas.config(scrollregion=self.header_canvas.bbox("all"))
        self.header_frame.grid()
        # Bind resizing
        def _on_header_frame_configure(event):
            self.header_canvas.config(scrollregion=self.header_canvas.bbox("all"))
        header_inner_frame.bind("<Configure>", _on_header_frame_configure)

    def get_selected_headers(self):
        return [k for k, v in self.header_vars.items() if v.get()]

    def get_renamed_headers(self):
        # Returns a dict: original_key -> renamed_key (for selected only)
        return {k: self.header_rename_vars[k].get() for k in self.get_selected_headers()}

    def update_preview_grid(self):
        # Show a table of 20 random products with only selected headers
        import random
        # Remove previous preview canvas if exists
        if hasattr(self, 'preview_canvas') and self.preview_canvas:
            self.preview_canvas.destroy()
        if hasattr(self, 'preview_h_scroll') and self.preview_h_scroll:
            self.preview_h_scroll.destroy()
        if hasattr(self, 'preview_tree') and self.preview_tree:
            self.preview_tree.destroy()
        if not self.products:
            self.preview_frame.grid_remove()
            return
        headers = self.get_selected_headers()
        if not headers:
            self.preview_frame.grid_remove()
            return
        renamed = self.get_renamed_headers()
        # Create a canvas for horizontal scrolling
        self.preview_canvas = tk.Canvas(self.preview_frame, width=900, height=350, highlightthickness=0)
        self.preview_canvas.grid(row=0, column=0, sticky="nsew")
        self.preview_h_scroll = ttk.Scrollbar(self.preview_frame, orient="horizontal", command=self.preview_canvas.xview)
        self.preview_h_scroll.grid(row=1, column=0, sticky="ew")
        self.preview_canvas.configure(xscrollcommand=self.preview_h_scroll.set)
        # Frame inside canvas
        preview_inner_frame = ttk.Frame(self.preview_canvas)
        self.preview_tree = ttk.Treeview(preview_inner_frame, columns=list(renamed.values()), show='headings', height=16)
        for orig, new in renamed.items():
            self.preview_tree.heading(new, text=new)
            self.preview_tree.column(new, width=120, anchor=tk.W)
        sample = random.sample(self.products, min(20, len(self.products)))
        for p in sample:
            row = [p.get(orig, '') for orig in renamed.keys()]
            self.preview_tree.insert('', tk.END, values=row)
        self.preview_tree.pack(fill=tk.BOTH, expand=True)
        preview_inner_frame.update_idletasks()
        self.preview_canvas.create_window((0, 0), window=preview_inner_frame, anchor="nw")
        preview_inner_frame.update_idletasks()
        self.preview_canvas.config(scrollregion=self.preview_canvas.bbox("all"))
        self.preview_frame.grid()
        # Bind resizing
        def _on_preview_frame_configure(event):
            self.preview_canvas.config(scrollregion=self.preview_canvas.bbox("all"))
        preview_inner_frame.bind("<Configure>", _on_preview_frame_configure)

    def start_scraping(self):
        self.set_status("Starting scraping...")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.products = []
        self.is_scraping = True
        url = self.url_entry.get().strip()
        api_endpoint = self.api_endpoint_entry.get().strip()
        method = self.method_var.get()
        max_pages = int(self.max_pages_var.get() or 1)
        delay = float(self.delay_var.get() or 1)
        container_selector = self.container_selector_entry.get().strip()
        container_selector_type = self.container_selector_type.get()
        exclude_keywords = [k.strip().lower() for k in self.exclude_keywords_var.get().split(',') if k.strip()]
        infinite_scroll = self.infinite_scroll_var.get()
        headless = self.headless_var.get()
        rotate_ua = self.rotate_ua_var.get()
        use_proxy = self.use_proxy_var.get()
        delay_requests = self.delay_requests_var.get()
        threading.Thread(target=self._scrape_thread, args=(url, api_endpoint, method, max_pages, delay, container_selector, container_selector_type, exclude_keywords, infinite_scroll, headless, rotate_ua, use_proxy, delay_requests), daemon=True).start()

    def _scrape_thread(self, url, api_endpoint, method, max_pages, delay, container_selector, container_selector_type, exclude_keywords, infinite_scroll, headless, rotate_ua, use_proxy, delay_requests):
        try:
            if method == "requests":
                self._scrape_with_requests(url, max_pages, delay, container_selector, container_selector_type, exclude_keywords)
            elif method == "selenium":
                self._scrape_with_selenium(url, max_pages, delay, container_selector, container_selector_type, exclude_keywords, infinite_scroll, headless)
            elif method == "api":
                self._scrape_with_api_detection(url, api_endpoint, max_pages, delay, exclude_keywords, headless)
            else:
                self.set_status(f"Unknown scraping method: {method}")
        except Exception as e:
            self.set_status(f"Error: {e}")
        finally:
            self.is_scraping = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.update_header_selection()
            self.update_preview_grid()

    def _detect_api_endpoints(self, driver, url):
        """Detect potential API endpoints for products"""
        api_endpoints = []
        try:
            # Get performance logs
            logs = driver.get_log('performance')
            for entry in logs:
                try:
                    message = json.loads(entry['message'])
                    if 'message' in message and message['message']['method'] == 'Network.responseReceived':
                        request_url = message['message']['params']['response']['url']
                        # Look for common API patterns
                        api_patterns = [
                            '/api/', '/graphql', '/products', '/catalog', '/search',
                            'products.json', 'catalog.json', 'search.json',
                            'product-proxy', 'nikecloud.com/products', 'adtech-prod'
                        ]
                        if any(pattern in request_url.lower() for pattern in api_patterns):
                            api_endpoints.append({
                                'url': request_url,
                                'method': 'GET',
                                'type': 'api'
                            })
                except:
                    continue
        except Exception as e:
            self.set_status(f"API detection error: {e}")
        return api_endpoints

    def _extract_from_api_response(self, response_data):
        """Extract product data from API response"""
        products = []
        try:
            if isinstance(response_data, dict):
                # Common API response structures
                data_keys = ['products', 'items', 'results', 'data', 'catalog', 'objects']
                for key in data_keys:
                    if key in response_data:
                        items = response_data[key]
                        if isinstance(items, list):
                            for item in items:
                                product = self._map_api_product(item)
                                if product:
                                    products.append(product)
                        break
                # If no standard key found, try to find arrays in the response
                if not products:
                    for key, value in response_data.items():
                        if isinstance(value, list) and len(value) > 0:
                            # Check if first item looks like a product
                            if isinstance(value[0], dict) and any(field in value[0] for field in ['name', 'title', 'price', 'id', 'productId']):
                                for item in value:
                                    product = self._map_api_product(item)
                                    if product:
                                        products.append(product)
                                break
        except Exception as e:
            self.set_status(f"API response parsing error: {e}")
        return products

    def _map_api_product(self, api_item):
        """Map API product fields to our standard format"""
        product = {}
        try:
            # Common field mappings
            field_mappings = {
                'url': ['url', 'link', 'href', 'product_url', 'productUrl'],
                'title': ['title', 'name', 'product_name', 'product_title', 'displayName'],
                'price': ['price', 'cost', 'amount', 'current_price', 'sale_price', 'currentPrice'],
                'model_number': ['model', 'model_number', 'sku', 'product_id', 'mpn', 'productId'],
                'upc': ['upc', 'barcode', 'ean', 'gtin'],
                'imageUrl': ['image', 'image_url', 'imageUrl', 'thumbnail', 'photo', 'heroImage']
            }
            
            for our_field, api_fields in field_mappings.items():
                for api_field in api_fields:
                    if api_field in api_item:
                        product[our_field] = str(api_item[api_field])
                        break
                if our_field not in product:
                    product[our_field] = ''
            
            # Add any other fields found
            for key, value in api_item.items():
                if key not in [field for fields in field_mappings.values() for field in fields]:
                    product[key] = str(value)
                    
        except Exception as e:
            self.set_status(f"Product mapping error: {e}")
        return product

    def _scrape_with_api_detection(self, url, api_endpoint, max_pages, delay, exclude_keywords, headless):
        """Scrape using detected API endpoints or direct API endpoint"""
        products = []
        
        # If direct API endpoint is provided, use it
        if api_endpoint:
            self.set_status(f"Using direct API endpoint: {api_endpoint}")
            try:
                # Use analyzed API structure if available
                if hasattr(self, 'api_analysis') and self.api_analysis:
                    products = self._extract_from_analyzed_api(api_endpoint, url)
                else:
                    # Use standard API extraction
                    products = self._extract_from_direct_api(api_endpoint, url)
                    
                if products:
                    self.set_status(f"Extracted {len(products)} products from direct API")
                else:
                    self.set_status("Direct API returned no products, trying auto-detection...")
                    
            except Exception as e:
                self.set_status(f"Direct API failed: {e}, trying auto-detection...")
        
        # If no direct API or direct API failed, try auto-detection
        if not products:
            self.set_status(f"Auto-detecting API endpoints: {url}")
            options = Options()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            
            try:
                # Load the page to capture network requests
                driver.get(url)
                time.sleep(5)  # Wait longer for page to load and API calls
                
                # Detect API endpoints
                api_endpoints = self._detect_api_endpoints(driver, url)
                
                if api_endpoints:
                    self.set_status(f"Found {len(api_endpoints)} potential API endpoints")
                    for endpoint in api_endpoints:
                        try:
                            self.set_status(f"Trying API endpoint: {endpoint['url']}")
                            # Add headers to mimic browser request
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                                'Accept': 'application/json, text/plain, */*',
                                'Accept-Language': 'en-US,en;q=0.9',
                                'Referer': url,
                            }
                            response = requests.get(endpoint['url'], headers=headers, timeout=15)
                            if response.status_code == 200:
                                try:
                                    api_data = response.json()
                                    api_products = self._extract_from_api_response(api_data)
                                    if api_products:
                                        products.extend(api_products)
                                        self.set_status(f"Extracted {len(api_products)} products from API")
                                        break  # Use first successful API
                                    else:
                                        self.set_status("API returned no products, trying next endpoint...")
                                except json.JSONDecodeError:
                                    self.set_status("API response is not JSON, trying next endpoint...")
                                    continue
                            else:
                                self.set_status(f"API request failed with status {response.status_code}")
                        except Exception as e:
                            self.set_status(f"API request failed: {e}")
                            continue
                
                # Fallback to Selenium HTML scraping if no API found or API failed
                if not products:
                    self.set_status("No API found or API failed, falling back to HTML scraping with Selenium")
                    try:
                        # Scroll to load more products
                        for i in range(3):
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(2)
                        
                        # Find product elements using Selenium
                        product_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid*="product"], [class*="product"], [class*="card"], article, .product-card, .product-item')
                        
                        if not product_elements:
                            # Try more generic selectors
                            product_elements = driver.find_elements(By.CSS_SELECTOR, 'div[class*="product"], li[class*="product"], div[class*="card"], div[class*="item"]')
                        
                        self.set_status(f"Found {len(product_elements)} product elements")
                        
                        for element in product_elements:
                            try:
                                # Extract data from Selenium element
                                product_data = self._extract_from_selenium_element(element, url)
                                if product_data:
                                    products.append(product_data)
                            except Exception as e:
                                self.set_status(f"Error extracting from element: {e}")
                                continue
                                
                    except Exception as e:
                        self.set_status(f"Selenium fallback error: {e}")
                            
            finally:
                driver.quit()
        
        # Sanitize products
        products = self._sanitize_products(products, exclude_keywords)
        self.products = products
        self.set_status(f"API scraping finished. Total products: {len(products)}")
        
    def _extract_from_direct_api(self, api_endpoint, base_url):
        """Extract products from a direct API endpoint with anti-detection and pagination"""
        products = []
        max_pages = int(self.max_pages_var.get() or 1)
        
        # Detect if this is a Criteo advertising API
        if self._detect_bestbuy_criteo_api(api_endpoint):
            self.set_status("⚠️ Using Criteo advertising API - limited to 12 products per page")
        
        try:
            # Try to get the first page to understand pagination
            response = self._make_anti_detection_request(api_endpoint, base_url)
            
            if response and response.status_code == 200:
                api_data = response.json()
                
                # Check if this is a single page or has pagination
                pagination_info = self._detect_pagination(api_data, api_endpoint)
                
                if pagination_info:
                    # Handle paginated API
                    products = self._extract_paginated_api(api_endpoint, base_url, pagination_info, max_pages)
                else:
                    # Single page API - but try pagination anyway if max_pages > 1
                    first_page_products = self._extract_from_api_response(api_data)
                    products.extend(first_page_products)
                    
                    if max_pages > 1 and len(first_page_products) >= 12:  # Lowered threshold for advertising APIs
                        self.set_status("No pagination detected but trying page-based pagination anyway...")
                        # Try simple page-based pagination
                        simple_pagination = {'page_key': 'page'}
                        additional_products = self._extract_paginated_api(api_endpoint, base_url, simple_pagination, max_pages - 1)
                        products.extend(additional_products)
                    else:
                        self.set_status(f"Single page API. Found {len(first_page_products)} products.")
            else:
                # If anti-detection failed, try Selenium approach
                self.set_status("Anti-detection request failed, trying Selenium approach...")
                selenium_response = self._try_selenium_api_request(api_endpoint, base_url)
                
                if selenium_response:
                    try:
                        api_data = json.loads(selenium_response)
                        pagination_info = self._detect_pagination(api_data, api_endpoint)
                        
                        if pagination_info:
                            products = self._extract_paginated_api_selenium(api_endpoint, base_url, pagination_info, max_pages)
                        else:
                            # Try simple pagination with Selenium too
                            first_page_products = self._extract_from_api_response(api_data)
                            products.extend(first_page_products)
                            
                            if max_pages > 1 and len(first_page_products) >= 12:  # Lowered threshold
                                self.set_status("No pagination detected but trying page-based pagination with Selenium...")
                                simple_pagination = {'page_key': 'page'}
                                additional_products = self._extract_paginated_api_selenium(api_endpoint, base_url, simple_pagination, max_pages - 1)
                                products.extend(additional_products)
                    except:
                        self.set_status("Selenium response is not valid JSON")
                else:
                    self.set_status("All API request methods failed")
                    
        except Exception as e:
            self.set_status(f"Direct API extraction error: {e}")
            
        return products
        
    def _detect_pagination(self, api_data, api_endpoint):
        """Detect pagination patterns in API response"""
        pagination_info = {}
        
        # Special handling for Best Buy and Criteo APIs
        if 'bestbuy' in api_endpoint.lower() or 'criteo' in api_endpoint.lower():
            self.set_status("Detected Best Buy/Criteo API - applying special pagination rules")
            
            # Check if this is a Criteo advertising API (limited to 12 products)
            if 'criteo' in api_endpoint.lower() and 'retailmedia' in api_endpoint.lower():
                pagination_info.update({
                    'page_key': 'page-number',
                    'limit_key': 'block',
                    'is_criteo_api': True,
                    'max_products_per_page': 12
                })
                return pagination_info
                
            # Check for Best Buy's actual product API patterns
            if 'bestbuy' in api_endpoint.lower():
                pagination_info.update({
                    'page_key': 'page',
                    'limit_key': 'pageSize',
                    'is_bestbuy_api': True
                })
                
        # Check URL for existing pagination parameters
        if '?' in api_endpoint:
            url_params = api_endpoint.split('?')[1]
            if 'page=' in url_params or 'page-number=' in url_params:
                pagination_info['page_key'] = 'page' if 'page=' in url_params else 'page-number'
            elif 'offset=' in url_params:
                pagination_info['offset_key'] = 'offset'
            elif 'cursor=' in url_params:
                pagination_info['cursor_key'] = 'cursor'
            elif 'anchor=' in url_params:
                pagination_info['anchor_key'] = 'anchor'
        
        # Check response data for pagination indicators
        if isinstance(api_data, dict):
            # Look for common pagination fields in the response
            pagination_fields = {
                'page': ['page', 'currentPage', 'pageNumber'],
                'total': ['total', 'totalCount', 'totalItems', 'count'],
                'limit': ['limit', 'pageSize', 'size', 'per_page'],
                'has_next': ['hasNext', 'hasMore', 'nextPage', 'has_next_page'],
                'next_cursor': ['nextCursor', 'next_cursor', 'cursor'],
                'next_page': ['nextPage', 'next_page']
            }
            
            for pagination_type, field_names in pagination_fields.items():
                for field_name in field_names:
                    if field_name in api_data:
                        pagination_info[f'{pagination_type}_key'] = field_name
                        break
                        
            # Check for array-based pagination (common in e-commerce APIs)
            if 'products' in api_data and isinstance(api_data['products'], list):
                products_count = len(api_data['products'])
                # If we have a reasonable number of products, assume pagination is possible
                if products_count >= 12:  # Lowered threshold for advertising APIs
                    if 'page_key' not in pagination_info and 'offset_key' not in pagination_info:
                        pagination_info['page_key'] = 'page'  # Default to page-based
                        
            # Check for other common product array keys
            product_array_keys = ['items', 'results', 'data', 'catalog', 'objects']
            for key in product_array_keys:
                if key in api_data and isinstance(api_data[key], list):
                    products_count = len(api_data[key])
                    if products_count >= 12:  # Lowered threshold
                        if 'page_key' not in pagination_info and 'offset_key' not in pagination_info:
                            pagination_info['page_key'] = 'page'  # Default to page-based
                        break
                        
        # If we found any pagination indicators, return the info
        if pagination_info:
            self.set_status(f"Detected pagination: {pagination_info}")
            return pagination_info
            
        return None
        
    def _extract_paginated_api(self, api_endpoint, base_url, pagination_info, max_pages):
        """Extract products from a paginated API"""
        products = []
        page = 1
        offset = 0
        cursor = None
        anchor = None
        
        self.set_status(f"Starting paginated API extraction. Max pages: {max_pages}")
        self.set_status(f"Pagination info: {pagination_info}")
        
        while page <= max_pages and self.is_scraping:
            try:
                # Build paginated URL
                paginated_url = self._build_paginated_url(api_endpoint, page, offset, cursor, anchor, pagination_info)
                
                self.set_status(f"Fetching page {page} from API: {paginated_url}")
                
                # Make request with anti-detection
                response = self._make_anti_detection_request(paginated_url, base_url)
                
                if response and response.status_code == 200:
                    api_data = response.json()
                    page_products = self._extract_from_api_response(api_data)
                    
                    if page_products:
                        products.extend(page_products)
                        self.set_status(f"Page {page}: Found {len(page_products)} products. Total: {len(products)}")
                        
                        # Check if there are more pages
                        has_more = self._has_more_pages(api_data, pagination_info)
                        self.set_status(f"Page {page}: Has more pages: {has_more}")
                        
                        if not has_more:
                            self.set_status(f"Page {page}: No more pages available, stopping pagination")
                            break
                            
                        # Update pagination parameters for next page
                        page, offset, cursor, anchor = self._get_next_page_params(api_data, pagination_info, page, offset, cursor, anchor)
                        self.set_status(f"Next page params: page={page}, offset={offset}, cursor={cursor}, anchor={anchor}")
                    else:
                        self.set_status(f"Page {page}: No products found, stopping pagination")
                        break
                else:
                    self.set_status(f"Page {page}: Request failed with status {response.status_code if response else 'No response'}, stopping pagination")
                    break
                    
                # Add delay between pages
                if self.delay_requests_var.get():
                    time.sleep(random.uniform(1, 3))
                    
            except Exception as e:
                self.set_status(f"Error on page {page}: {e}")
                break
                
        self.set_status(f"Pagination completed. Total products extracted: {len(products)}")
        return products
        
    def _build_paginated_url(self, api_endpoint, page, offset, cursor, anchor, pagination_info):
        """Build URL with pagination parameters"""
        # Parse the base URL and existing parameters
        if '?' in api_endpoint:
            base_url, existing_params = api_endpoint.split('?', 1)
        else:
            base_url = api_endpoint
            existing_params = ""
            
        # Parse existing parameters
        params = {}
        if existing_params:
            for param in existing_params.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
                    
        # Special handling for Criteo API
        if pagination_info.get('is_criteo_api'):
            # Keep all existing Criteo parameters but update page-number
            if page > 1:
                params['page-number'] = str(page)
            # Update block parameter for different product sets
            if 'block' in params:
                try:
                    current_block = int(params['block'])
                    params['block'] = str(current_block + (page - 1) * 12)  # Increment block for each page
                except ValueError:
                    params['block'] = str((page - 1) * 12)
            return f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
            
        # Special handling for Best Buy API
        if pagination_info.get('is_bestbuy_api'):
            # Remove existing pagination parameters
            pagination_keys = ['page', 'pageSize', 'offset', 'cursor', 'anchor']
            for key in pagination_keys:
                if key in params:
                    del params[key]
                    
            # Add Best Buy specific pagination
            if page > 1:
                params['page'] = str(page)
            if 'pageSize' not in params:
                params['pageSize'] = '50'  # Best Buy typically uses 50 products per page
                
        else:
            # Standard pagination handling
            # Remove existing pagination parameters
            pagination_keys = ['page', 'page-number', 'offset', 'cursor', 'anchor', 'limit', 'size', 'per_page']
            for key in pagination_keys:
                if key in params:
                    del params[key]
                    
            # Add new pagination parameters based on detected type
            if pagination_info.get('page_key') and page > 1:
                params[pagination_info['page_key']] = str(page)
            elif pagination_info.get('offset_key') and offset > 0:
                params[pagination_info['offset_key']] = str(offset)
            elif pagination_info.get('cursor_key') and cursor:
                params[pagination_info['cursor_key']] = str(cursor)
            elif pagination_info.get('anchor_key') and anchor:
                params[pagination_info['anchor_key']] = str(anchor)
            elif page > 1:
                # Default to page-based if no specific type detected
                params['page'] = str(page)
                
            # Add limit if not present
            if 'limit' not in params and 'size' not in params and 'per_page' not in params:
                params['limit'] = '50'  # Default page size
                
        # Build the final URL
        if params:
            param_strings = [f"{key}={value}" for key, value in params.items()]
            return f"{base_url}?{'&'.join(param_strings)}"
        else:
            return base_url
            
    def _has_more_pages(self, api_data, pagination_info):
        """Check if there are more pages available"""
        if isinstance(api_data, dict):
            # Special handling for Criteo API
            if pagination_info.get('is_criteo_api'):
                # Criteo API typically returns 12 products per page
                # If we get exactly 12 products, there might be more pages
                products = self._extract_from_api_response(api_data)
                if len(products) == 12:
                    return True
                return False
                
            # Special handling for Best Buy API
            if pagination_info.get('is_bestbuy_api'):
                # Check for Best Buy specific pagination indicators
                if 'totalCount' in api_data and 'currentPage' in api_data:
                    try:
                        total = int(api_data['totalCount'])
                        current_page = int(api_data['currentPage'])
                        page_size = int(api_data.get('pageSize', 50))
                        if current_page * page_size < total:
                            return True
                    except (ValueError, TypeError):
                        pass
                        
            # Check various pagination indicators
            if pagination_info.get('has_next_key') and pagination_info['has_next_key'] in api_data:
                return bool(api_data[pagination_info['has_next_key']])
            elif pagination_info.get('has_more_key') and pagination_info['has_more_key'] in api_data:
                return bool(api_data[pagination_info['has_more_key']])
            elif pagination_info.get('next_cursor_key') and pagination_info['next_cursor_key'] in api_data:
                return bool(api_data[pagination_info['next_cursor_key']])
            elif pagination_info.get('next_page_key') and pagination_info['next_page_key'] in api_data:
                return bool(api_data[pagination_info['next_page_key']])
                
            # Check if we have products and they seem to be a full page
            products = self._extract_from_api_response(api_data)
            if len(products) >= 12:  # Lowered threshold for advertising APIs
                return True
                
            # Check for total count vs current count
            if pagination_info.get('total_key') and pagination_info['total_key'] in api_data:
                total = api_data[pagination_info['total_key']]
                current_count = len(products)
                if isinstance(total, (int, str)) and current_count > 0:
                    try:
                        total = int(total)
                        if current_count < total:
                            return True
                    except ValueError:
                        pass
                        
        return False
        
    def _get_next_page_params(self, api_data, pagination_info, current_page, current_offset, current_cursor, current_anchor):
        """Get parameters for the next page"""
        next_page = current_page + 1
        next_offset = current_offset + 50  # Default page size
        next_cursor = None
        next_anchor = None
        
        if isinstance(api_data, dict):
            # Get next cursor if available
            if pagination_info.get('next_cursor_key') and pagination_info['next_cursor_key'] in api_data:
                next_cursor = api_data[pagination_info['next_cursor_key']]
                
            # Get next page number if available
            if pagination_info.get('next_page_key') and pagination_info['next_page_key'] in api_data:
                next_page = api_data[pagination_info['next_page_key']]
                
            # Calculate offset based on limit
            if pagination_info.get('limit_key') and pagination_info['limit_key'] in api_data:
                try:
                    limit = int(api_data[pagination_info['limit_key']])
                    next_offset = current_offset + limit
                except (ValueError, TypeError):
                    next_offset = current_offset + 50
            elif 'limit' in api_data:
                try:
                    limit = int(api_data['limit'])
                    next_offset = current_offset + limit
                except (ValueError, TypeError):
                    next_offset = current_offset + 50
                    
            # Handle Nike-style anchor pagination
            if pagination_info.get('anchor_key') and pagination_info['anchor_key'] in api_data:
                try:
                    current_anchor_val = int(api_data[pagination_info['anchor_key']])
                    next_anchor = current_anchor_val + 50  # Default increment
                except (ValueError, TypeError):
                    next_anchor = current_anchor + 50 if current_anchor else 50
                    
        return next_page, next_offset, next_cursor, next_anchor
        
    def _extract_paginated_api_selenium(self, api_endpoint, base_url, pagination_info, max_pages):
        """Extract products from paginated API using Selenium"""
        products = []
        page = 1
        offset = 0
        cursor = None
        anchor = None
        
        while page <= max_pages and self.is_scraping:
            try:
                # Build paginated URL
                paginated_url = self._build_paginated_url(api_endpoint, page, offset, cursor, anchor, pagination_info)
                
                self.set_status(f"Fetching page {page} from API using Selenium...")
                
                # Use Selenium to get the response
                selenium_response = self._try_selenium_api_request(paginated_url, base_url)
                
                if selenium_response:
                    try:
                        api_data = json.loads(selenium_response)
                        page_products = self._extract_from_api_response(api_data)
                        
                        if page_products:
                            products.extend(page_products)
                            self.set_status(f"Page {page}: Found {len(page_products)} products. Total: {len(products)}")
                            
                            # Check if there are more pages
                            if not self._has_more_pages(api_data, pagination_info):
                                break
                                
                            # Update pagination parameters for next page
                            page, offset, cursor, anchor = self._get_next_page_params(api_data, pagination_info, page, offset, cursor, anchor)
                        else:
                            self.set_status(f"Page {page}: No products found, stopping pagination")
                            break
                    except:
                        self.set_status(f"Page {page}: Invalid JSON response")
                        break
                else:
                    self.set_status(f"Page {page}: Selenium request failed, stopping pagination")
                    break
                    
                # Add delay between pages
                if self.delay_requests_var.get():
                    time.sleep(random.uniform(2, 4))  # Longer delay for Selenium
                    
            except Exception as e:
                self.set_status(f"Error on page {page}: {e}")
                break
                
        return products

    def _extract_from_analyzed_api(self, api_endpoint, base_url):
        """Extract products using the analyzed API structure with anti-detection and pagination"""
        products = []
        max_pages = int(self.max_pages_var.get() or 1)
        
        try:
            # Try anti-detection request first
            response = self._make_anti_detection_request(api_endpoint, base_url)
            
            if response and response.status_code == 200:
                api_data = response.json()
                
                # Check for pagination
                pagination_info = self._detect_pagination(api_data, api_endpoint)
                
                if pagination_info:
                    # Handle paginated API with analyzed structure
                    products = self._extract_paginated_analyzed_api(api_endpoint, base_url, pagination_info, max_pages)
                else:
                    # Single page API with analyzed structure
                    products = self._extract_analyzed_single_page(api_data)
            else:
                # If anti-detection failed, try Selenium approach
                self.set_status("Anti-detection request failed, trying Selenium approach...")
                selenium_response = self._try_selenium_api_request(api_endpoint, base_url)
                
                if selenium_response:
                    try:
                        api_data = json.loads(selenium_response)
                        pagination_info = self._detect_pagination(api_data, api_endpoint)
                        
                        if pagination_info:
                            products = self._extract_paginated_analyzed_api_selenium(api_endpoint, base_url, pagination_info, max_pages)
                        else:
                            products = self._extract_analyzed_single_page(api_data)
                    except:
                        self.set_status("Selenium response is not valid JSON")
                else:
                    self.set_status("All API request methods failed")
                    
        except Exception as e:
            self.set_status(f"Analyzed API extraction error: {e}")
            
        return products
        
    def _extract_analyzed_single_page(self, api_data):
        """Extract products from a single page using analyzed structure"""
        products = []
        
        # Use the analyzed structure to extract products
        for product_array in self.api_analysis['product_arrays']:
            # Navigate to the product array using the path
            path_parts = product_array['path'].split('.')
            current_data = api_data
            
            for part in path_parts:
                if isinstance(current_data, dict) and part in current_data:
                    current_data = current_data[part]
                else:
                    break
            
            if isinstance(current_data, list):
                mappings = self.api_analysis['field_mappings'].get(product_array['path'], {})
                
                for item in current_data:
                    product = self._map_api_product_with_mappings(item, mappings)
                    if product:
                        products.append(product)
                        
        return products
        
    def _extract_paginated_analyzed_api(self, api_endpoint, base_url, pagination_info, max_pages):
        """Extract products from paginated API using analyzed structure"""
        products = []
        page = 1
        offset = 0
        cursor = None
        anchor = None
        
        while page <= max_pages and self.is_scraping:
            try:
                # Build paginated URL
                paginated_url = self._build_paginated_url(api_endpoint, page, offset, cursor, anchor, pagination_info)
                
                self.set_status(f"Fetching page {page} from analyzed API...")
                
                # Make request with anti-detection
                response = self._make_anti_detection_request(paginated_url, base_url)
                
                if response and response.status_code == 200:
                    api_data = response.json()
                    page_products = self._extract_analyzed_single_page(api_data)
                    
                    if page_products:
                        products.extend(page_products)
                        self.set_status(f"Page {page}: Found {len(page_products)} products. Total: {len(products)}")
                        
                        # Check if there are more pages
                        if not self._has_more_pages(api_data, pagination_info):
                            break
                            
                        # Update pagination parameters for next page
                        page, offset, cursor, anchor = self._get_next_page_params(api_data, pagination_info, page, offset, cursor, anchor)
                    else:
                        self.set_status(f"Page {page}: No products found, stopping pagination")
                        break
                else:
                    self.set_status(f"Page {page}: Request failed, stopping pagination")
                    break
                    
                # Add delay between pages
                if self.delay_requests_var.get():
                    time.sleep(random.uniform(1, 3))
                    
            except Exception as e:
                self.set_status(f"Error on page {page}: {e}")
                break
                
        return products
        
    def _extract_paginated_analyzed_api_selenium(self, api_endpoint, base_url, pagination_info, max_pages):
        """Extract products from paginated API using analyzed structure and Selenium"""
        products = []
        page = 1
        offset = 0
        cursor = None
        anchor = None
        
        while page <= max_pages and self.is_scraping:
            try:
                # Build paginated URL
                paginated_url = self._build_paginated_url(api_endpoint, page, offset, cursor, anchor, pagination_info)
                
                self.set_status(f"Fetching page {page} from analyzed API using Selenium...")
                
                # Use Selenium to get the response
                selenium_response = self._try_selenium_api_request(paginated_url, base_url)
                
                if selenium_response:
                    try:
                        api_data = json.loads(selenium_response)
                        page_products = self._extract_analyzed_single_page(api_data)
                        
                        if page_products:
                            products.extend(page_products)
                            self.set_status(f"Page {page}: Found {len(page_products)} products. Total: {len(products)}")
                            
                            # Check if there are more pages
                            if not self._has_more_pages(api_data, pagination_info):
                                break
                                
                            # Update pagination parameters for next page
                            page, offset, cursor, anchor = self._get_next_page_params(api_data, pagination_info, page, offset, cursor, anchor)
                        else:
                            self.set_status(f"Page {page}: No products found, stopping pagination")
                            break
                    except:
                        self.set_status(f"Page {page}: Invalid JSON response")
                        break
                else:
                    self.set_status(f"Page {page}: Selenium request failed, stopping pagination")
                    break
                    
                # Add delay between pages
                if self.delay_requests_var.get():
                    time.sleep(random.uniform(2, 4))  # Longer delay for Selenium
                    
            except Exception as e:
                self.set_status(f"Error on page {page}: {e}")
                break
                
        return products

    def _map_api_product_with_mappings(self, api_item, mappings):
        """Map API product fields using the analyzed mappings"""
        product = {}
        try:
            # Use the analyzed mappings
            for our_field, api_field in mappings.items():
                if api_field in api_item:
                    product[our_field] = str(api_item[api_field])
                else:
                    product[our_field] = ''
            
            # Add any other fields found
            for key, value in api_item.items():
                if key not in mappings.values():
                    product[key] = str(value)
                    
        except Exception as e:
            self.set_status(f"Product mapping error: {e}")
        return product

    def _extract_from_selenium_element(self, element, base_url):
        """Extract product data from a Selenium WebElement"""
        try:
            product = {}
            
            # Extract URL
            try:
                link = element.find_element(By.CSS_SELECTOR, 'a[href]')
                href = link.get_attribute('href')
                if href:
                    product['url'] = href
                else:
                    product['url'] = ''
            except:
                product['url'] = ''
            
            # Extract title
            try:
                title_selectors = ['[data-testid*="title"]', 'h3', 'h4', '.product-title', '.product-name', '[class*="title"]']
                for selector in title_selectors:
                    try:
                        title_elem = element.find_element(By.CSS_SELECTOR, selector)
                        title = title_elem.text.strip()
                        if title:
                            product['title'] = title
                            break
                    except:
                        continue
                if 'title' not in product:
                    product['title'] = ''
            except:
                product['title'] = ''
            
            # Extract price
            try:
                price_selectors = ['[data-testid*="price"]', '.price', '[class*="price"]', 'span[class*="price"]']
                for selector in price_selectors:
                    try:
                        price_elem = element.find_element(By.CSS_SELECTOR, selector)
                        price = price_elem.text.strip()
                        if price and any(char in price for char in '$€£¥₦₹₽₩'):
                            product['price'] = price
                            break
                    except:
                        continue
                if 'price' not in product:
                    product['price'] = ''
            except:
                product['price'] = ''
            
            # Extract image
            try:
                img = element.find_element(By.CSS_SELECTOR, 'img[src]')
                src = img.get_attribute('src')
                if src:
                    product['imageUrl'] = src
                else:
                    product['imageUrl'] = ''
            except:
                product['imageUrl'] = ''
            
            # Set default values for missing fields
            product['model_number'] = ''
            product['upc'] = ''
            
            # Only return if we have at least a title or URL
            if product.get('title') or product.get('url'):
                return product
            else:
                return None
                
        except Exception as e:
            self.set_status(f"Error extracting from Selenium element: {e}")
            return None

    def _extract_product_fields(self, element, base_url):
        # Extract prioritized fields: url, title, price, model_number, upc, imageUrl
        data = {}
        # --- URL ---
        a = element.find('a', href=True)
        if a:
            data['url'] = urljoin(base_url, a['href'])
        else:
            data['url'] = ''
        # --- Title ---
        title = None
        # Try common title fields
        for tag in ['h1', 'h2', 'h3', 'span', 'div', 'a']:
            t = element.find(tag, attrs={"class": re.compile(r'(title|name|product)', re.I)})
            if t and t.get_text(strip=True):
                title = t.get_text(strip=True)
                break
        if not title:
            t = element.find(['h1', 'h2', 'h3', 'span', 'div', 'a'], string=True)
            if t:
                title = t.get_text(strip=True)
        data['title'] = title or ''
        # --- Price ---
        price = None
        price_tag = element.find(attrs={"class": re.compile(r'(price|amount|cost)', re.I)})
        if price_tag:
            price = price_tag.get_text(strip=True)
        else:
            # Try to find text with currency symbol
            price_text = element.find(string=re.compile(r'\$|€|£|₦|₹|¥|₽|₩|USD|EUR|GBP|NGN|INR|JPY|RUB|KRW'))
            if price_text:
                price = price_text.strip()
        data['price'] = price or ''
        # --- Model Number ---
        model = None
        # Look for common model number fields
        for key in ['model', 'model_number', 'mpn', 'part_number']:
            tag = element.find(attrs={"class": re.compile(key, re.I)})
            if tag and tag.get_text(strip=True):
                model = tag.get_text(strip=True)
                break
        if not model:
            # Look for text like 'Model: ...'
            model_text = element.find(string=re.compile(r'Model\s*[:#-]?\s*([\w-]+)', re.I))
            if model_text:
                m = re.search(r'Model\s*[:#-]?\s*([\w-]+)', model_text, re.I)
                if m:
                    model = m.group(1)
        data['model_number'] = model or ''
        # --- UPC ---
        upc = None
        for key in ['upc', 'barcode', 'ean']:
            tag = element.find(attrs={"class": re.compile(key, re.I)})
            if tag and tag.get_text(strip=True):
                upc = tag.get_text(strip=True)
                break
        if not upc:
            upc_text = element.find(string=re.compile(r'UPC\s*[:#-]?\s*([\w-]+)', re.I))
            if upc_text:
                m = re.search(r'UPC\s*[:#-]?\s*([\w-]+)', upc_text, re.I)
                if m:
                    upc = m.group(1)
        data['upc'] = upc or ''
        # --- imageUrl ---
        img = element.find('img', src=True)
        if img:
            data['imageUrl'] = urljoin(base_url, img['src'])
        else:
            data['imageUrl'] = ''
        # --- Add all other text fields (for header selection) ---
        for tag in element.find_all(['span', 'div', 'p']):
            text = tag.get_text(strip=True)
            if text and text not in data.values():
                key = tag.get('class', [tag.name])[0]
                if key not in data:
                    data[key] = text
        # --- Add all attributes (for header selection) ---
        for tag in element.find_all(True):
            for attr, val in tag.attrs.items():
                if isinstance(val, list):
                    val = ' '.join(val)
                key = f"{tag.name}_{attr}"
                if key not in data:
                    data[key] = val
        # Ensure all prioritized fields are present
        for k in ['url', 'title', 'price', 'model_number', 'upc', 'imageUrl']:
            if k not in data:
                data[k] = ''
        return data

    def _extract_category_fields(self, element, base_url):
        data = {}
        a = element.find('a', href=True)
        if a:
            data['name'] = a.get_text(strip=True)
            data['url'] = urljoin(base_url, a['href'])
        else:
            data['name'] = element.get_text(strip=True)
        return data

    def _sanitize_products(self, products, exclude_keywords):
        sanitized = []
        for p in products:
            # Remove if missing all of price, model_number, upc
            if not (p.get('price') or p.get('model_number') or p.get('upc')):
                continue
            # Remove if title or imageUrl contains ad/sponsored keywords
            title = (p.get('title') or '').lower()
            img = (p.get('imageUrl') or '').lower()
            if any(kw in title or kw in img for kw in exclude_keywords):
                continue
            sanitized.append(p)
        return sanitized

    def _scrape_with_requests(self, url, max_pages, delay, container_selector, container_selector_type, exclude_keywords):
        self.set_status(f"Scraping with Requests: {url}")
        session = requests.Session()
        products = []
        for page in range(1, max_pages+1):
            if not self.is_scraping:
                self.set_status("Scraping stopped by user.")
                return
            page_url = url
            if page > 1:
                page_url = f"{url}?page={page}"
            
            # Rotate User Agent
            session.headers['User-Agent'] = self._get_random_user_agent()
            
            # Add random delays
            time.sleep(random.uniform(0.5, 1.5)) # Random delay between 0.5 and 1.5 seconds
            
            try:
                resp = session.get(page_url, timeout=15)
                soup = BeautifulSoup(resp.text, "lxml")
                # Use user-supplied selector for product blocks
                product_blocks = []
                if container_selector_type != "none" and container_selector:
                    try:
                        if container_selector_type == "class":
                            container = soup.find(class_=container_selector)
                        elif container_selector_type == "id":
                            container = soup.find(id=container_selector)
                        else:
                            container = None
                        if container:
                            product_blocks = container.find_all(['div', 'li', 'article'], recursive=True)
                    except Exception as e:
                        self.set_status(f"Selector error: {e}")
                if not product_blocks:
                    # fallback: all div/li/article with a link and image
                    product_blocks = soup.find_all(lambda tag: tag.name in ['div', 'li', 'article'] and tag.find('a', href=True) and (tag.find('img') or tag.find(attrs={"class": lambda v: v and 'product' in v})))
                found = 0
                for block in product_blocks:
                    pdata = self._extract_product_fields(block, url)
                    if pdata:
                        products.append(pdata)
                        found += 1
                self.set_status(f"Page {page}: Found {found} products.")
                time.sleep(delay)
            except requests.exceptions.RequestException as e:
                self.set_status(f"Request failed for page {page}: {e}")
                continue
        # Sanitize products
        products = self._sanitize_products(products, exclude_keywords)
        self.products = products
        self.set_status(f"Scraping finished. Total products: {len(products)}")

    def _scrape_with_selenium(self, url, max_pages, delay, container_selector, container_selector_type, exclude_keywords, infinite_scroll, headless):
        self.set_status(f"Scraping with Selenium: {url}")
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        products = []
        try:
            if infinite_scroll:
                driver.get(url)
                last_height = driver.execute_script("return document.body.scrollHeight")
                scroll_count = 0
                while self.is_scraping and scroll_count < max_pages:
                    soup = BeautifulSoup(driver.page_source, "lxml")
                    product_blocks = []
                    if container_selector_type != "none" and container_selector:
                        try:
                            if container_selector_type == "class":
                                container = soup.find(class_=container_selector)
                            elif container_selector_type == "id":
                                container = soup.find(id=container_selector)
                            else:
                                container = None
                            if container:
                                product_blocks = container.find_all(['div', 'li', 'article'], recursive=True)
                        except Exception as e:
                            self.set_status(f"Selector error: {e}")
                    if not product_blocks:
                        product_blocks = soup.find_all(lambda tag: tag.name in ['div', 'li', 'article'] and tag.find('a', href=True) and (tag.find('img') or tag.find(attrs={"class": lambda v: v and 'product' in v})))
                    found = 0
                    for block in product_blocks:
                        pdata = self._extract_product_fields(block, url)
                        if pdata:
                            products.append(pdata)
                            found += 1
                    self.set_status(f"Scroll {scroll_count+1}: Found {found} products.")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(delay)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                    scroll_count += 1
            else:
                for page in range(1, max_pages+1):
                    if not self.is_scraping:
                        self.set_status("Scraping stopped by user.")
                        return
                    page_url = url
                    if page > 1:
                        page_url = f"{url}?page={page}"
                    driver.get(page_url)
                    soup = BeautifulSoup(driver.page_source, "lxml")
                    # Use user-supplied selector for product blocks
                    product_blocks = []
                    if container_selector_type != "none" and container_selector:
                        try:
                            if container_selector_type == "class":
                                container = soup.find(class_=container_selector)
                            elif container_selector_type == "id":
                                container = soup.find(id=container_selector)
                            else:
                                container = None
                            if container:
                                product_blocks = container.find_all(['div', 'li', 'article'], recursive=True)
                        except Exception as e:
                            self.set_status(f"Selector error: {e}")
                    if not product_blocks:
                        # fallback: all div/li/article with a link and image
                        product_blocks = soup.find_all(lambda tag: tag.name in ['div', 'li', 'article'] and tag.find('a', href=True) and (tag.find('img') or tag.find(attrs={"class": lambda v: v and 'product' in v})))
                    found = 0
                    for block in product_blocks:
                        pdata = self._extract_product_fields(block, url)
                        if pdata:
                            products.append(pdata)
                            found += 1
                    self.set_status(f"Page {page}: Found {found} products.")
                    time.sleep(delay)
        finally:
            driver.quit()
        # Sanitize products
        products = self._sanitize_products(products, exclude_keywords)
        self.products = products
        self.set_status(f"Scraping finished. Total products: {len(products)}")

    def stop_scraping(self):
        self.is_scraping = False
        self.set_status("Scraping stopped by user.")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def export_csv(self):
        if not self.products:
            self.set_status("No products to export.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save CSV"
        )
        if not file_path:
            self.set_status("Export cancelled.")
            return
        try:
            # Use only selected and renamed keys
            renamed = self.get_renamed_headers()
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(renamed.values()))
                writer.writeheader()
                for p in self.products:
                    row = {renamed[k]: p.get(k, '') for k in renamed.keys()}
                    writer.writerow(row)
            self.set_status(f"CSV file exported: {file_path}")
        except Exception as e:
            self.set_status(f"Error exporting CSV: {e}")

    def export_categories_csv(self):
        pass  # removed

    def export_excel(self):
        if not self.products:
            self.set_status("No products to export.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Save Excel"
        )
        if not file_path:
            self.set_status("Export cancelled.")
            return
        try:
            import pandas as pd
            renamed = self.get_renamed_headers()
            df = pd.DataFrame([{renamed[k]: p.get(k, '') for k in renamed.keys()} for p in self.products])
            df.to_excel(file_path, index=False)
            self.set_status(f"Excel file exported: {file_path}")
        except Exception as e:
            self.set_status(f"Error exporting Excel: {e}")

    def clear_data(self):
        # ... clear logic ...
        self.set_status("Data cleared.")

    def on_product_select(self, event):
        selected = self.product_table.selection()
        if not selected:
            return
        try:
            idx = int(selected[0])
            if 0 <= idx < len(self.products):
                product = self.products[idx]
                self.detail_text.config(state=tk.NORMAL)
                self.detail_text.delete('1.0', tk.END)
                for k, v in product.items():
                    self.detail_text.insert(tk.END, f"{k}: {v}\n")
                self.detail_text.config(state=tk.DISABLED)
        except Exception as e:
            self.set_status(f"Error displaying product: {e}")

    def _show_bestbuy_api_help(self):
        """Show help for finding the correct Best Buy API endpoint"""
        help_text = """
BEST BUY API HELP:

The URL you provided is a Criteo advertising API that only returns 12 sponsored products.
To get the full Best Buy product catalog, you need to find the actual Best Buy API.

HOW TO FIND THE REAL BEST BUY API:

1. Open Best Buy website: https://www.bestbuy.ca
2. Navigate to the category you want to scrape
3. Open Developer Tools (F12)
4. Go to Network tab
5. Filter by "Fetch/XHR" or "API"
6. Look for requests containing:
   - "api.bestbuy.ca"
   - "search" or "products"
   - "category" or "catalog"

COMMON BEST BUY API PATTERNS:
- https://api.bestbuy.ca/v2/products?categoryPath.id=20001&page=1&pageSize=50
- https://api.bestbuy.ca/v2/products?search=computer&page=1&pageSize=50
- https://api.bestbuy.ca/v2/products?categoryPath.id=20001&sortBy=relevance&page=1

CRITEO API LIMITATIONS:
- Only returns 12 sponsored/advertising products
- Not the full product catalog
- Designed for advertising display, not scraping
- Limited pagination support

Try finding the actual Best Buy API endpoint for better results!
        """
        
        popup = tk.Toplevel(self.root)
        popup.title("Best Buy API Help")
        popup.geometry("600x500")
        popup.transient(self.root)
        popup.grab_set()
        
        text_widget = tk.Text(popup, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
        ttk.Button(popup, text="Close", command=popup.destroy).pack(pady=10)
        
    def _detect_bestbuy_criteo_api(self, api_endpoint):
        """Detect if the API is a Criteo advertising API and show help"""
        if 'criteo' in api_endpoint.lower() and 'retailmedia' in api_endpoint.lower():
            self.set_status("⚠️ Detected Criteo advertising API - limited to 12 products")
            self.root.after(2000, self._show_bestbuy_api_help)  # Show help after 2 seconds
            return True
        return False

def show_documentation_popup(root, on_close):
    doc_win = tk.Toplevel(root)
    doc_win.title("How to Use: E-commerce Web Scraper")
    doc_win.geometry("650x520")
    doc_win.grab_set()
    doc_win.resizable(False, False)
    # Set soft background color
    doc_win.configure(bg="#f6f8fa")
    # Header bar
    header_frame = tk.Frame(doc_win, bg="#2980b9", height=54)
    header_frame.pack(fill=tk.X, side=tk.TOP)
    header_label = tk.Label(header_frame, text="E-commerce Web Scraper", font=("Arial", 16, "bold"), fg="white", bg="#2980b9", pady=10)
    header_label.pack(side=tk.LEFT, padx=20)
    # --- Vertical scrollable area ---
    canvas = tk.Canvas(doc_win, width=620, height=400, highlightthickness=0, bg="#f6f8fa", bd=0)
    v_scroll = ttk.Scrollbar(doc_win, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=v_scroll.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20,0), pady=(10,0))
    v_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=(10,0))
    inner_frame = tk.Frame(canvas, bg="#f6f8fa")
    # Section titles with color
    label_basic = tk.Label(inner_frame, text="BASIC USAGE:", font=("Arial", 12, "bold"), fg="#2980b9", bg="#f6f8fa", anchor="w")
    label_basic.pack(anchor=tk.W, pady=(0,2))
    label_basic_text = tk.Label(inner_frame, text="""
1. Enter the website URL you want to scrape.
2. (Optional) Enter a direct API endpoint if you know the site's product API.
3. (Optional) Select 'Class' or 'ID' and enter the name of the container that holds the product list.
   - If unsure, leave as 'None'.
4. Choose your scraping method:
   - 'Requests' (faster, for simple sites)
   - 'Selenium' (for dynamic sites)
   - 'API Detection' (automatically finds and uses API endpoints)
5. Configure anti-detection options:
   - Enable 'Headless Selenium' to avoid bot detection (recommended)
   - Enable 'Rotate User Agents' to use different browser signatures
   - Enable 'Add Random Delays' to mimic human behavior
6. (Optional) Click 'Analyze API Structure' to understand complex APIs before scraping.
7. Set 'Max Pages' and 'Delay' (in seconds) between page loads.
8. (Optional) Add keywords to exclude ads or non-product items.
9. (Optional) Enable 'Infinite Scroll' for sites that load more products as you scroll (Selenium only).
10. Click 'Start Scraping'.
11. After scraping, select which fields to keep and optionally rename them.
12. Preview the data, then export to CSV or Excel.
""", justify=tk.LEFT, font=("Arial", 11), bg="#f6f8fa", wraplength=600)
    label_basic_text.pack(anchor=tk.W, pady=(0,10))
    label_adv = tk.Label(inner_frame, text="ADVANCED USAGE:", font=("Arial", 12, "bold"), fg="#c0392b", bg="#f6f8fa", anchor="tk.W")
    label_adv.pack(anchor=tk.W, pady=(0,2))
    label_adv_text = tk.Label(inner_frame, text="""
API ENDPOINT FEATURE:
- If you know the site's product API endpoint, enter it directly for faster scraping.
- Use 'Analyze API Structure' to automatically detect product arrays and field mappings.
- The analyzer will show you the JSON structure and suggest field mappings.
- This is especially useful for sites with complex API responses.
- **PAGINATION SUPPORT**: The scraper automatically detects and handles pagination in APIs.
  - Supports page-based, offset-based, and cursor-based pagination.
  - Respects the 'Max Pages' setting to control how many pages to fetch.
  - Shows progress for each page being fetched.
  - Special handling for Best Buy, Criteo, and other e-commerce APIs.

ANTI-DETECTION FEATURES:
- **Rotate User Agents**: Uses different browser user agents to avoid detection.
- **Add Random Delays**: Adds random delays between requests to mimic human behavior.
- **Enhanced Headers**: Uses complete browser headers including site-specific ones.
- **Multiple Fallback Methods**: Tries different approaches if one fails (GET, POST, Selenium).
- **403 Error Bypass**: Automatically tries multiple strategies to bypass 403 errors.

HEADLESS SELENIUM:
- Enable this option to run Selenium in headless mode (no browser window).
- Helps avoid bot detection and uses less system resources.
- Recommended for production scraping.

BEST BUY & CRITEO API HANDLING:
- **Automatic Detection**: Recognizes Best Buy and Criteo advertising APIs.
- **Criteo API Warning**: Shows warnings when using limited advertising APIs (12 products max).
- **Help System**: Provides guidance for finding the real Best Buy product API.
- **Special Pagination**: Handles Criteo's unique pagination parameters (page-number, block).
- **Real API Support**: Optimized for actual Best Buy product APIs with proper pagination.

CONTAINER SELECTION:
- To get the product list container's class or id:
   1. Open the website in your browser.
   2. Right-click on the product list and select 'Inspect' or 'Inspect Element'.
   3. Look for a <div>, <ul>, or <section> that contains all the product items.
   4. Find its class (class="...") or id (id="...").
   5. Enter just the class or id name (no dot or #) in the app and select the correct toggle.
- Avoid using containers with names like 'ad', 'advert', 'promo', 'banner', or those that only contain unrelated content.
- If you see too many unrelated items, try specifying the product list container.
- You can scroll the interface horizontally if fields overflow.

TROUBLESHOOTING:
- **403 Errors**: Enable anti-detection features and try different methods.
- **Limited Products**: Check if you're using an advertising API instead of a product API.
- **Pagination Issues**: Use 'Analyze API Structure' to understand the API format.
- **Slow Scraping**: Reduce 'Max Pages' or increase 'Delay' between requests.
- **No Products Found**: Try different scraping methods or check the website structure.

If you need help, contact your project provider.
""", justify=tk.LEFT, font=("Arial", 11), bg="#f6f8fa", wraplength=600)
    label_adv_text.pack(anchor=tk.W, pady=(0,10))
    # Add the checkbox and button inside the scrollable area
    dont_show_var = tk.BooleanVar(value=False)
    chk = ttk.Checkbutton(inner_frame, text="Don't show this again", variable=dont_show_var)
    chk.pack(pady=(10, 10), anchor=tk.W)
    style = ttk.Style()
    style.configure("Accent.TButton", foreground="white", background="#27ae60", font=("Arial", 11, "bold"), padding=6)
    def close_popup():
        if dont_show_var.get():
            onboard_file = os.path.join(os.path.expanduser("~"), ".ecommerce_scraper_onboarded")
            try:
                with open(onboard_file, "w") as f:
                    f.write("1\n")
            except Exception:
                pass
        doc_win.destroy()
        on_close()
    btn = ttk.Button(inner_frame, text="Close and Start App", style="Accent.TButton", command=close_popup)
    btn.pack(pady=10, anchor=tk.W)
    inner_frame.update_idletasks()
    canvas.create_window((0, 0), window=inner_frame, anchor="nw")
    inner_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))
    def _on_frame_configure(event):
        canvas.config(scrollregion=canvas.bbox("all"))
    inner_frame.bind("<Configure>", _on_frame_configure)
    # --- End vertical scrollable area ---
    doc_win.protocol("WM_DELETE_WINDOW", close_popup)

def main():
    root = tk.Tk()
    root.withdraw()  # Hide main window until doc is closed
    def start_app():
        root.deiconify()
        app = EcommerceScraper(root)
    # Check if onboarding file exists
    onboard_file = os.path.join(os.path.expanduser("~"), ".ecommerce_scraper_onboarded")
    if os.path.exists(onboard_file):
        start_app()
    else:
        show_documentation_popup(root, start_app)
    root.mainloop()

if __name__ == "__main__":
    main() 