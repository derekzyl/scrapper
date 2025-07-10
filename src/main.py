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
        
        # Product list container selector
        ttk.Label(url_frame, text="Product List Container:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.container_selector_type = tk.StringVar(value="none")
        none_radio = ttk.Radiobutton(url_frame, text="None", variable=self.container_selector_type, value="none")
        class_radio = ttk.Radiobutton(url_frame, text="Class", variable=self.container_selector_type, value="class")
        id_radio = ttk.Radiobutton(url_frame, text="ID", variable=self.container_selector_type, value="id")
        none_radio.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        class_radio.grid(row=1, column=2, sticky=tk.W, padx=(10, 0))
        id_radio.grid(row=1, column=3, sticky=tk.W, padx=(10, 0))
        self.container_selector_entry = ttk.Entry(url_frame, width=30, font=('Arial', 10))
        self.container_selector_entry.grid(row=1, column=4, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
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
        
        # Parameters
        params_frame = ttk.Frame(options_frame)
        params_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
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
        method = self.method_var.get()
        max_pages = int(self.max_pages_var.get() or 1)
        delay = float(self.delay_var.get() or 1)
        container_selector = self.container_selector_entry.get().strip()
        container_selector_type = self.container_selector_type.get()
        exclude_keywords = [k.strip().lower() for k in self.exclude_keywords_var.get().split(',') if k.strip()]
        infinite_scroll = self.infinite_scroll_var.get()
        threading.Thread(target=self._scrape_thread, args=(url, method, max_pages, delay, container_selector, container_selector_type, exclude_keywords, infinite_scroll), daemon=True).start()

    def _scrape_thread(self, url, method, max_pages, delay, container_selector, container_selector_type, exclude_keywords, infinite_scroll):
        try:
            if method == "requests":
                self._scrape_with_requests(url, max_pages, delay, container_selector, container_selector_type, exclude_keywords)
            elif method == "selenium":
                self._scrape_with_selenium(url, max_pages, delay, container_selector, container_selector_type, exclude_keywords, infinite_scroll)
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

    def _scrape_with_selenium(self, url, max_pages, delay, container_selector, container_selector_type, exclude_keywords, infinite_scroll):
        self.set_status(f"Scraping with Selenium: {url}")
        options = Options()
        options.add_argument('--headless')
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
2. (Optional) Select 'Class' or 'ID' and enter the name of the container that holds the product list.
   - If unsure, leave as 'None'.
3. Choose your scraping method: 'Requests' (faster, for simple sites) or 'Selenium' (for dynamic sites).
4. Set 'Max Pages' and 'Delay' (in seconds) between page loads.
5. (Optional) Add keywords to exclude ads or non-product items.
6. (Optional) Enable 'Infinite Scroll' for sites that load more products as you scroll (Selenium only).
7. Click 'Start Scraping'.
8. After scraping, select which fields to keep and optionally rename them.
9. Preview the data, then export to CSV or Excel.
""", justify=tk.LEFT, font=("Arial", 11), bg="#f6f8fa", wraplength=600)
    label_basic_text.pack(anchor=tk.W, pady=(0,10))
    label_adv = tk.Label(inner_frame, text="ADVANCED USAGE:", font=("Arial", 12, "bold"), fg="#c0392b", bg="#f6f8fa", anchor="w")
    label_adv.pack(anchor=tk.W, pady=(0,2))
    label_adv_text = tk.Label(inner_frame, text="""
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