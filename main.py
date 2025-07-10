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
        
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="E-commerce Web Scraper", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # URL input section
        url_frame = ttk.LabelFrame(main_frame, text="Website Configuration", padding="10")
        url_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(url_frame, text="Website URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(url_frame, width=70, font=('Arial', 10))
        self.url_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        self.url_entry.insert(0, "https://example-store.com")
        
        # Scraping options
        options_frame = ttk.LabelFrame(main_frame, text="Scraping Options", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Method selection
        ttk.Label(options_frame, text="Scraping Method:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.method_var = tk.StringVar(value="requests")
        method_frame = ttk.Frame(options_frame)
        method_frame.grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(method_frame, text="Requests + BeautifulSoup (Fast)", 
                       variable=self.method_var, value="requests").pack(side=tk.LEFT)
        ttk.Radiobutton(method_frame, text="Selenium (Dynamic sites)", 
                       variable=self.method_var, value="selenium").pack(side=tk.LEFT, padx=(20, 0))
        
        # Parameters
        params_frame = ttk.Frame(options_frame)
        params_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(params_frame, text="Max Pages:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.max_pages_var = tk.StringVar(value="5")
        ttk.Entry(params_frame, textvariable=self.max_pages_var, width=8).grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(params_frame, text="Delay (sec):").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.delay_var = tk.StringVar(value="1")
        ttk.Entry(params_frame, textvariable=self.delay_var, width=8).grid(row=0, column=3, padx=(0, 20))
        
        # What to scrape
        ttk.Label(params_frame, text="Scrape:").grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        self.scrape_products_var = tk.BooleanVar(value=True)
        self.scrape_categories_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(params_frame, text="Products", variable=self.scrape_products_var).grid(row=0, column=5, padx=(0, 10))
        ttk.Checkbutton(params_frame, text="Categories", variable=self.scrape_categories_var).grid(row=0, column=6)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=15)
        # ... existing code ... 
        