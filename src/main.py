import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv
import json
import re
import time
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
        
        # API Analysis button
        api_analysis_frame = ttk.Frame(options_frame)
        api_analysis_frame.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=5)
        ttk.Button(api_analysis_frame, text="Analyze API Structure", 
                  command=self.analyze_api_structure).pack(side=tk.LEFT, padx=(0, 10))
        self.api_analysis_status = ttk.Label(api_analysis_frame, text="", foreground='#27ae60')
        self.api_analysis_status.pack(side=tk.LEFT)
        
        # Parameters
        params_frame = ttk.Frame(options_frame)
        params_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
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
        button_frame.grid(row=3, column=0, columnspan=4, pady=15)
        
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
        self.header_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        self.header_vars = {}
        self.header_checkbuttons = {}
        self.header_rename_vars = {}
        self.header_frame.grid_remove()  # Hide initially

        # Data preview grid
        self.preview_frame = ttk.LabelFrame(main_frame, text="Data Preview (Random 20 Products)", padding="10")
        self.preview_frame.grid(row=5, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        self.preview_tree = None
        self.preview_frame.grid_remove()  # Hide initially
        
        # Feedback/status area
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
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
        threading.Thread(target=self._scrape_thread, args=(url, api_endpoint, method, max_pages, delay, container_selector, container_selector_type, exclude_keywords, infinite_scroll, headless), daemon=True).start()

    def _scrape_thread(self, url, api_endpoint, method, max_pages, delay, container_selector, container_selector_type, exclude_keywords, infinite_scroll, headless):
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
        """Extract products from a direct API endpoint"""
        products = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': base_url if base_url else api_endpoint,
            }
            
            response = requests.get(api_endpoint, headers=headers, timeout=15)
            if response.status_code == 200:
                api_data = response.json()
                products = self._extract_from_api_response(api_data)
            else:
                self.set_status(f"Direct API request failed with status {response.status_code}")
                
        except Exception as e:
            self.set_status(f"Direct API extraction error: {e}")
            
        return products
        
    def _extract_from_analyzed_api(self, api_endpoint, base_url):
        """Extract products using the analyzed API structure"""
        products = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': base_url if base_url else api_endpoint,
            }
            
            response = requests.get(api_endpoint, headers=headers, timeout=15)
            if response.status_code == 200:
                api_data = response.json()
                
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
                                
            else:
                self.set_status(f"Analyzed API request failed with status {response.status_code}")
                
        except Exception as e:
            self.set_status(f"Analyzed API extraction error: {e}")
            
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
5. Enable 'Headless Selenium' to avoid bot detection (recommended).
6. Set 'Max Pages' and 'Delay' (in seconds) between page loads.
7. (Optional) Add keywords to exclude ads or non-product items.
8. (Optional) Enable 'Infinite Scroll' for sites that load more products as you scroll (Selenium only).
9. Click 'Start Scraping'.
10. After scraping, select which fields to keep and optionally rename them.
11. Preview the data, then export to CSV or Excel.
""", justify=tk.LEFT, font=("Arial", 11), bg="#f6f8fa", wraplength=600)
    label_basic_text.pack(anchor=tk.W, pady=(0,10))
    label_adv = tk.Label(inner_frame, text="ADVANCED USAGE:", font=("Arial", 12, "bold"), fg="#c0392b", bg="#f6f8fa", anchor="w")
    label_adv.pack(anchor=tk.W, pady=(0,2))
    label_adv_text = tk.Label(inner_frame, text="""
API ENDPOINT FEATURE:
- If you know the site's product API endpoint, enter it directly for faster scraping.
- Use 'Analyze API Structure' to automatically detect product arrays and field mappings.
- The analyzer will show you the JSON structure and suggest field mappings.
- This is especially useful for sites with complex API responses.

HEADLESS SELENIUM:
- Enable this option to run Selenium in headless mode (no browser window).
- Helps avoid bot detection and uses less system resources.
- Recommended for production scraping.

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
- If you need help, contact your project provider.
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