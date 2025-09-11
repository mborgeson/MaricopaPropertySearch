#!/usr/bin/env python3
"""
Maricopa County Assessor Property Search Tool - Ultimate Edition
Features: Web Scraping, CSV Import, API Integration, Batch Processing
Works with real data from multiple sources
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime
import threading
from functools import lru_cache
from dataclasses import dataclass, asdict, field
import re
from urllib.parse import urlencode, quote, unquote
import webbrowser
import csv
import os
from pathlib import Path
import queue
import time
import sys
import traceback

# Selenium Imports for Browser Automation
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Optional: For web scraping (install with: pip install beautifulsoup4 lxml)
try:
    from bs4 import BeautifulSoup
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False
    print("Note: Install beautifulsoup4 for web scraping: pip install beautifulsoup4 lxml")

# ============================================================================
# Configuration
# ============================================================================

class APIConfig:
    """Configuration for Maricopa County Assessor's Office"""
    BASE_URL = "https://mcassessor.maricopa.gov/#/"
    SEARCH_URL = "https://mcassessor.maricopa.gov/#/search" # The new search URL
    PARCEL_URL = "https://mcassessor.maricopa.gov/#/parcel/{apn}" # The new parcel URL format

# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ValuationRecord:
    tax_year: int = 0
    full_cash_value: Optional[float] = None
    limited_value: Optional[float] = None
    assessed_lpv: Optional[float] = None


@dataclass
class PropertyInfo:
    """Property information model"""
    apn: str
    owner_name: str = ""
    mailing_address: str = ""
    property_address: str = ""
    legal_description: str = ""
    lot_size: str = ""
    building_size: str = ""
    year_built: str = ""
    bedrooms: str = ""
    bathrooms: str = ""
    property_class: str = ""
    land_use: str = ""
    market_value: str = ""
    assessed_value: str = ""
    last_sale_date: Optional[datetime] = None
    last_sale_price: Optional[float] = None
    valuation_history: List[ValuationRecord] = field(default_factory=list)
    
    def to_display_dict(self) -> Dict[str, str]:
        return {
            "APN": self.apn, "Owner": self.owner_name, "Property Address": self.property_address,
            "Mailing Address": self.mailing_address, "Legal Description": self.legal_description,
            "Lot Size": self.lot_size, "Building Size": self.building_size, "Year Built": self.year_built,
            "Bedrooms": self.bedrooms, "Bathrooms": self.bathrooms, "Property Class": self.property_class,
            "Land Use": self.land_use, "Market Value": self.market_value, "Assessed Value": self.assessed_value
        }
    
    def to_csv_row(self) -> List[str]:
        return [
            self.apn, self.owner_name, self.property_address, self.mailing_address, self.legal_description,
            self.lot_size, self.building_size, self.year_built, self.bedrooms, self.bathrooms,
            self.property_class, self.land_use, self.market_value, self.assessed_value
        ]

@dataclass
class TaxInfo:
    """Tax information model"""
    apn: str = ""; tax_year: str = ""; assessed_value: float = 0; limited_value: float = 0; total_taxes: float = 0; tax_status: str = ""
    def to_csv_row(self) -> List[str]:
        return [self.apn, self.tax_year, str(self.assessed_value), str(self.limited_value), str(self.total_taxes), self.tax_status]

@dataclass
class SaleInfo:
    """Sale history model"""
    apn: str = ""; sale_date: str = ""; sale_price: float = 0; deed_type: str = ""; seller: str = ""; buyer: str = ""
    def to_csv_row(self) -> List[str]:
        return [self.apn, self.sale_date, str(self.sale_price), self.deed_type, self.seller, self.buyer]

# ============================================================================
# CSV Import Module
# ============================================================================

class CSVImporter:
    @staticmethod
    def import_property_csv(filepath: str) -> List[PropertyInfo]:
        # ... (This class remains unchanged)
        properties = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    prop = PropertyInfo(
                        apn=row.get('APN', '') or row.get('Parcel', '') or row.get('parcel_id', ''),
                        owner_name=row.get('Owner', '') or row.get('owner_name', ''),
                        property_address=row.get('Property Address', '') or row.get('situs_address', ''),
                        mailing_address=row.get('Mailing Address', '') or row.get('mail_address', ''),
                        legal_description=row.get('Legal', '') or row.get('legal_desc', ''),
                        lot_size=row.get('Lot Size', '') or row.get('lot_sqft', ''),
                        building_size=row.get('Building Size', '') or row.get('building_sqft', ''),
                        year_built=row.get('Year Built', '') or row.get('year_built', ''),
                        bedrooms=row.get('Bedrooms', '') or row.get('bedrooms', ''),
                        bathrooms=row.get('Bathrooms', '') or row.get('bathrooms', ''),
                        property_class=row.get('Class', '') or row.get('property_class', ''),
                        land_use=row.get('Land Use', '') or row.get('land_use', ''),
                        market_value=row.get('Market Value', '') or row.get('market_value', ''),
                        assessed_value=row.get('Assessed Value', '') or row.get('assessed_value', '')
                    )
                    if prop.apn: properties.append(prop)
        except Exception as e:
            print(f"CSV import error: {e}")
        return properties

# ============================================================================
# Selenium-Based Browser Automation API
# ============================================================================

class MaricopaAssessorAPI:
    """API client that uses Selenium to control a browser and scrape data."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.driver = self._initialize_driver()
        self.csv_importer = CSVImporter()
        self.csv_cache: Dict[str, PropertyInfo] = {}

    def _initialize_driver(self):
        """Sets up the Selenium WebDriver."""
        print("Initializing headless Chrome browser...")
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--log-level=3") # Suppress console logs from browser
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("Browser initialized successfully.")
            return driver
        except Exception as e:
            print(f"FATAL: Could not initialize Selenium WebDriver: {e}")
            print("Please ensure Google Chrome is installed on your system.")
            messagebox.showerror("Browser Error", "Could not start Chrome. Please ensure it is installed.")
            return None

    def search_by_address(self, address: str) -> List[PropertyInfo]:
        """Searches for a property by address using direct URL navigation."""
        if not self.driver: return []
        
        # NEW LOGIC: Construct the URL and go there directly
        cleaned_address = address.lower().replace(", phoenix", "").strip()
        search_url = f"https://mcassessor.maricopa.gov/mcs/?q={quote(cleaned_address)}"
        print(f"Navigating directly to search results for: {address}")
        self.driver.get(search_url)
        
        try:
            # Wait for the page to load. We'll wait for the body tag as a basic check.
            wait = WebDriverWait(self.driver, self.timeout)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            print("Results page loaded. Parsing results...")
            
            # Give a brief moment for JS to render all results
            time.sleep(2)

            # The parsing method will be updated next, for now it will just save the html
            return self._parse_search_results(self.driver.page_source)

        except TimeoutException:
            print("Search results page timed out.")
            return []
        except Exception as e:
            print(f"An error occurred during address search: {e}")
            traceback.print_exc()
            return []

    def search_by_apn(self, apn: str, use_scraping: bool = True) -> Optional[PropertyInfo]:
        """Searches for a single property by APN."""
        if not self.driver: return None
        
        if apn in self.csv_cache:
            print(f"Found APN {apn} in CSV cache.")
            return self.csv_cache[apn]

        # NEW URL LOGIC
        print(f"Navigating to new parcel page for APN: {apn}")
        parcel_url = f"https://mcassessor.maricopa.gov/mcs/?q={apn}&mod=pd"
        self.driver.get(parcel_url)

        try:
            wait = WebDriverWait(self.driver, self.timeout)
            print("Waiting for parcel data to load...")
            # Generic wait to avoid timeout and allow parsing function to execute
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            print("Parcel page loaded.")
            time.sleep(1)

            # This parser will be in debug mode to save the HTML
            return self._parse_parcel_page(self.driver.page_source, apn)

        except TimeoutException:
            print("Parcel page timed out or did not load correctly.")
            return None
        except Exception as e:
            print(f"An error occurred during APN search: {e}")
            traceback.print_exc()
            return None

    def _parse_search_results(self, html: str) -> List[PropertyInfo]:
        """Parses the HTML of a search results page."""
        print("Parsing new search results page format...")
        soup = BeautifulSoup(html, 'html.parser')
        properties = []
        
        # Find the table body containing the real property results
        results_table_body = soup.find('tbody', id='rpdata')
        
        if not results_table_body:
            print("Could not find the results table body ('#rpdata').")
            return []

        # Find all table rows within that body
        for row in results_table_body.find_all('tr'):
            # Check if this row is a "no records found" message
            if 'no parcel records found' in row.text.lower():
                print("Found 'No parcel records found' message.")
                continue

            cells = row.find_all('td')
            if len(cells) >= 3:  # We need at least APN, Owner, and Address
                try:
                    apn_text = cells[0].text.strip()
                    # Clean up the APN, remove the rental tag if present and format it
                    apn = apn_text.replace('\xa0', ' ').split(' ')[0]

                    owner = cells[1].text.strip()
                    address = cells[2].text.strip()
                    
                    if apn:
                        print(f"Parsed APN: {apn}, Owner: {owner}")
                        properties.append(PropertyInfo(apn=apn, owner_name=owner, property_address=address))
                except IndexError:
                    print("A row had fewer than 3 cells, skipping.")
                    continue # Skip malformed rows
                except Exception as e:
                    print(f"Error parsing a result row: {e}")
                    continue # Ignore items that can't be parsed
        
        if not properties:
            print("Could not parse any individual items from the results page.")

        return properties

    

    def get_full_tax_info(self, apn: str) -> List[TaxInfo]:
        """Navigates to Treasurer's site, submits form, and saves results HTML for debugging."""
        print(f"Navigating to Treasurer's site to submit form for APN: {apn}")
        treasurer_url = "https://treasurer.maricopa.gov/parcel/default.aspx" # Base URL for the form
        self.driver.get(treasurer_url)

        try:
            wait = WebDriverWait(self.driver, self.timeout)

            # Split APN into parts (e.g., 112-05-091B -> 112, 05, 091, B)
            apn_parts = re.match(r'(\d{3})-(\d{2})-(\d{3})([A-Z]?)', apn)
            if not apn_parts:
                print(f"Invalid APN format for Treasurer's site: {apn}")
                return []

            book_num = apn_parts.group(1)
            map_num = apn_parts.group(2)
            item_num = apn_parts.group(3)
            split_char = apn_parts.group(4) if apn_parts.group(4) else ""

            # Find input fields
            txt_book = wait.until(EC.presence_of_element_located((By.ID, "txtParcelNumBook")))
            txt_map = wait.until(EC.presence_of_element_located((By.ID, "txtParcelNumMap")))
            txt_item = wait.until(EC.presence_of_element_located((By.ID, "txtParcelNumItem")))
            txt_split = wait.until(EC.presence_of_element_located((By.ID, "txtParcelNumSplit")))
            btn_submit = wait.until(EC.element_to_be_clickable((By.ID, "btnSubmit")))

            # Fill fields
            txt_book.send_keys(book_num)
            txt_map.send_keys(map_num)
            txt_item.send_keys(item_num)
            if split_char:
                txt_split.send_keys(split_char)

            # Execute __doPostBack to submit the form
            print("Executing __doPostBack to submit form...")
            self.driver.execute_script(f"__doPostBack('ctl00$cphMainContent$btnSubmit', '')")

            # Wait for the URL to change to reflect the parcel number
            wait.until(EC.url_contains(apn))
            print("Treasurer's results page loaded. Saving HTML for analysis.")
            
            debug_path = Path.home() / "maricopa_treasurer_results_page.html"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"SUCCESS: Saved Treasurer's results page HTML to: {debug_path}")
            print("ACTION REQUIRED: Please run `read_file` on that new file so I can write the full tax parser.")
            
            return []

        except TimeoutException:
            print("Treasurer's page elements not found or results page timed out.")
            return []
        except Exception as e:
            print(f"An error occurred during Treasurer's site form submission: {e}")
            traceback.print_exc()
            return []

    def _parse_parcel_page(self, html: str, apn: str) -> Optional[PropertyInfo]:
        """Parses the HTML of a single parcel's detail page."""
        print(f"Parsing new parcel page format for {apn}")
        soup = BeautifulSoup(html, 'html.parser')
        prop = PropertyInfo(apn=apn)

        def get_info_by_header(header_text: str) -> str:
            try:
                header_div = soup.find('div', class_='td-header', text=header_text)
                if header_div and header_div.find_next_sibling('div', class_='td-body'):
                    return header_div.find_next_sibling('div', class_='td-body').text.strip()
            except Exception:
                return ""
            return ""

        try:
            owner_section = soup.find('div', id='owner')
            if owner_section:
                owner_name_tag = owner_section.find('div', class_='banner-text')
                if owner_name_tag:
                    prop.owner_name = owner_name_tag.text.strip()
                prop.mailing_address = get_info_by_header("Mailing Address")
                sale_date_str = get_info_by_header("Sale Date")
                sale_price_str = get_info_by_header("Sale Price")
                try:
                    prop.last_sale_date = datetime.strptime(sale_date_str, '%m/%d/%Y')
                except (ValueError, TypeError):
                    prop.last_sale_date = None
                try:
                    prop.last_sale_price = float(re.sub(r'[$,]', '', sale_price_str))
                except (ValueError, TypeError):
                    prop.last_sale_price = None

            prop_info_ribbon = soup.find('h4', text='Property Information')
            if prop_info_ribbon:
                parent_div = prop_info_ribbon.find_parent('div', class_='parcel-section')
                if parent_div:
                    address_tag = parent_div.find('div', class_='banner-text')
                    if address_tag:
                        prop.property_address = address_tag.text.strip()
                    prop.legal_description = get_info_by_header("Description")
                    prop.lot_size = get_info_by_header("Lot Size")

            valuation_section = soup.find('div', id='valuation')
            if valuation_section:
                fcv = valuation_section.find('div', id='Valuations_0_FullCashValue')
                lpv = valuation_section.find('div', id='Valuations_0_LimitedPropertyValue')
                if fcv:
                    prop.market_value = fcv.text.strip()
                if lpv:
                    prop.assessed_value = lpv.text.strip()
            
            add_info_section = soup.find('div', id='addinfo')
            if add_info_section:
                year_built_div = add_info_section.find('div', id='ResidentialPropertyData_ConstructionYear')
                building_size_div = add_info_section.find('div', id='ResidentialPropertyData_LivableSpace')
                if year_built_div:
                    prop.year_built = year_built_div.text.strip()
                if building_size_div:
                    prop.building_size = building_size_div.text.strip()

            if not prop.owner_name:
                glance_div = soup.find('div', id='property-glance')
                if glance_div and 'The current owner is' in glance_div.text:
                    owner_search = re.search(r'The current owner is (.*?)\.', glance_div.text)
                    if owner_search:
                        prop.owner_name = owner_search.group(1).strip()

            prop.valuation_history = []
            if valuation_section:
                def to_float(currency_str: str) -> Optional[float]:
                    try:
                        return float(re.sub(r'[$,]', '', currency_str))
                    except (ValueError, TypeError):
                        return None
                for i in range(5):
                    try:
                        year_str = valuation_section.find('div', id=f'Valuations_{i}_TaxYear').text.strip()
                        fcv_str = valuation_section.find('div', id=f'Valuations_{i}_FullCashValue').text.strip()
                        lpv_str = valuation_section.find('div', id=f'Valuations_{i}_LimitedPropertyValue').text.strip()
                        assessed_str = valuation_section.find('div', id=f'Valuations_{i}_AssessedLPV').text.strip()
                        record = ValuationRecord(
                            tax_year=int(year_str),
                            full_cash_value=to_float(fcv_str),
                            limited_value=to_float(lpv_str),
                            assessed_lpv=to_float(assessed_str)
                        )
                        prop.valuation_history.append(record)
                    except (AttributeError, ValueError):
                        break

            print("Finished parsing parcel page.")
            if not prop.owner_name and not prop.property_address:
                 print("Could not parse critical info (owner/address), returning None.")
                 return None
            return prop
        except Exception as e:
            print(f"A critical error occurred during parcel page parsing: {e}")
            traceback.print_exc()
            return None

    def get_tax_info(self, prop_info: PropertyInfo) -> List[TaxInfo]:
        """Constructs a list of TaxInfo objects from the parsed valuation history."""
        tax_history = []
        if prop_info and prop_info.valuation_history:
            for val_record in prop_info.valuation_history:
                tax_info = TaxInfo(
                    apn=prop_info.apn,
                    tax_year=str(val_record.tax_year),
                    assessed_value=val_record.full_cash_value or 0.0,
                    limited_value=val_record.limited_value or 0.0,
                    total_taxes=0.0, 
                    tax_status="N/A"
                )
                tax_history.append(tax_info)
        return tax_history

    def get_sales_history(self, prop_info: PropertyInfo) -> List[SaleInfo]:
        """Constructs a SaleInfo object from the already-parsed PropertyInfo."""
        if prop_info and prop_info.last_sale_date and prop_info.last_sale_price is not None:
            sale = SaleInfo(
                apn=prop_info.apn,
                sale_date=prop_info.last_sale_date.strftime('%Y-%m-%d'),
                sale_price=prop_info.last_sale_price,
                deed_type="N/A"
            )
            return [sale]
        return []

    def import_csv_data(self, filepath: str) -> int:
        return self.csv_importer.import_property_csv(filepath)

    def quit(self):
        """Closes the browser instance."""
        if self.driver:
            print("Closing browser...")
            self.driver.quit()

# ============================================================================
# Enhanced GUI Application
# ============================================================================

class PropertySearchApp:
    """Enhanced GUI application with multiple data source support"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Maricopa County Property Search Tool - Ultimate Edition")
        self.root.geometry("1200x800")
        
        self.api = MaricopaAssessorAPI()
        
        self.current_property: Optional[PropertyInfo] = None
        self.current_apn: Optional[str] = None
        self.current_tax_info: List[TaxInfo] = []
        self.current_sales_info: List[SaleInfo] = []
        
        self._setup_styles()
        self._create_widgets()
        self._bind_events()
        self._check_dependencies()
        
        # Ensure browser is closed when window is closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Handle window closing event."""
        print("Closing application and browser...")
        if self.api:
            self.api.quit()
        self.root.destroy()

    class TextRedirector:
        def __init__(self, widget, tag="stdout"): self.widget = widget; self.tag = tag
        def write(self, str_data):
            self.widget.config(state=tk.NORMAL)
            self.widget.insert(tk.END, str_data, (self.tag,))
            self.widget.see(tk.END)
            self.widget.config(state=tk.DISABLED)
        def flush(self): pass

    def _check_dependencies(self):
        if not SCRAPING_AVAILABLE:
            self._set_status("Note: Install beautifulsoup4 for web scraping: pip install beautifulsoup4 lxml")
        else:
            self._set_status("Ready - Selenium browser automation enabled")
    
    # ... (The rest of the GUI class remains largely the same)
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Search.TButton', padding=10)
        style.configure('Export.TButton', padding=5)
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        title_label = ttk.Label(main_frame, text="Maricopa County Property Search - Ultimate Edition", style='Title.TLabel')
        title_label.grid(row=0, column=0, pady=(0, 10))
        self._create_search_frame(main_frame)
        self._create_results_notebook(main_frame)
        self._create_status_bar(main_frame)
        self._create_toolbar(main_frame)
    
    def _create_search_frame(self, parent):
        search_frame = ttk.LabelFrame(parent, text="Search Options", padding="10")
        search_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        ttk.Label(search_frame, text="Search by:").grid(row=0, column=0, sticky=tk.W)
        self.search_type = tk.StringVar(value="address")
        search_type_frame = ttk.Frame(search_frame)
        search_type_frame.grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(search_type_frame, text="APN", variable=self.search_type, value="apn").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(search_type_frame, text="Address", variable=self.search_type, value="address").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(search_type_frame, text="Batch File", variable=self.search_type, value="batch").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(search_type_frame, text="Import CSV", variable=self.search_type, value="import").pack(side=tk.LEFT, padx=5)
        ttk.Label(search_frame, text="Enter:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.search_entry = ttk.Entry(search_frame, width=60)
        self.search_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(5, 0))
        self.search_entry.insert(0, "301 W Jefferson St, Phoenix")
        buttons_frame = ttk.Frame(search_frame)
        buttons_frame.grid(row=1, column=2, padx=(5, 0), pady=(5, 0))
        self.search_button = ttk.Button(buttons_frame, text="Search", command=self._perform_search)
        self.search_button.pack(side=tk.LEFT)
        self.browse_button = ttk.Button(buttons_frame, text="Browse...", command=self._browse_file)
        self.browse_button.pack(side=tk.LEFT, padx=(5, 0))
        options_frame = ttk.LabelFrame(search_frame, text="Data Sources", padding="5")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        self.use_csv = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Use Imported CSV Data", variable=self.use_csv).pack(side=tk.LEFT, padx=5)
    
    def _create_results_notebook(self, parent):
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.property_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.property_frame, text="Property Info")
        self._create_property_tab()
        self.tax_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tax_frame, text="Tax Information")
        self._create_tax_tab()
        self.sales_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sales_frame, text="Sales History")
        self._create_sales_tab()
        self.docs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.docs_frame, text="Documents")
        self._create_docs_tab()
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="Log")
        self._create_log_tab()

    def _create_log_tab(self):
        log_container = ttk.Frame(self.log_frame, padding=10)
        log_container.pack(fill=tk.BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(log_container, wrap=tk.WORD, font=('Courier New', 9), state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        sys.stdout = self.TextRedirector(self.log_text, "stdout")
        sys.stderr = self.TextRedirector(self.log_text, "stderr")
        print("--- Application Log Initialized ---")

    def _create_property_tab(self):
        self.property_text = scrolledtext.ScrolledText(self.property_frame, wrap=tk.WORD, width=80, height=25, font=('Courier', 10))
        self.property_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_tax_tab(self):
        columns = ('Year', 'Assessed', 'Limited', 'Taxes', 'Status')
        self.tax_tree = ttk.Treeview(self.tax_frame, columns=columns, show='headings', height=15)
        for col in columns: self.tax_tree.heading(col, text=col); self.tax_tree.column(col, width=150)
        tax_scroll = ttk.Scrollbar(self.tax_frame, orient=tk.VERTICAL, command=self.tax_tree.yview)
        self.tax_tree.configure(yscrollcommand=tax_scroll.set)
        self.tax_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        tax_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
    
    def _create_sales_tab(self):
        columns = ('Date', 'Price', 'Type', 'Seller', 'Buyer')
        self.sales_tree = ttk.Treeview(self.sales_frame, columns=columns, show='headings', height=15)
        for col in columns: self.sales_tree.heading(col, text=col); self.sales_tree.column(col, width=150)
        sales_scroll = ttk.Scrollbar(self.sales_frame, orient=tk.VERTICAL, command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=sales_scroll.set)
        self.sales_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        sales_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
    
    def _create_docs_tab(self):
        docs_container = ttk.Frame(self.docs_frame); docs_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        ttk.Label(docs_container, text="Official County Links:", font=('Arial', 11, 'bold')).pack(pady=10)
        buttons_frame = ttk.Frame(docs_container); buttons_frame.pack(pady=20)
        self.assessor_link_btn = ttk.Button(buttons_frame, text="View on Assessor Website", command=self._open_assessor_link, state=tk.DISABLED)
        self.assessor_link_btn.pack(pady=5)
        self.recorder_link_btn = ttk.Button(buttons_frame, text="Search Recorder Documents", command=self._open_recorder_link, state=tk.DISABLED)
        self.recorder_link_btn.pack(pady=5)
        self.tax_bill_btn = ttk.Button(buttons_frame, text="View Tax Bills", command=self._open_tax_bills, state=tk.DISABLED)
        self.tax_bill_btn.pack(pady=5)
    
    def _create_toolbar(self, parent):
        toolbar = ttk.LabelFrame(parent, text="Actions", padding="5")
        toolbar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        ttk.Button(toolbar, text="Import CSV Data", command=self._import_csv_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Export Current", command=self._export_current).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Batch Process APNs", command=self._batch_process).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Clear Cache", command=self._clear_cache).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Open Export Folder", command=self._open_export_folder).pack(side=tk.LEFT, padx=5)
        self.data_status = ttk.Label(toolbar, text="CSV Cache: 0 properties")
        self.data_status.pack(side=tk.RIGHT, padx=10)
    
    def _create_status_bar(self, parent):
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT)
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=100)
    
    def _bind_events(self):
        self.search_entry.bind('<Return>', lambda e: self._perform_search())
    
    def _browse_file(self):
        filename = filedialog.askopenfilename(title="Select CSV file", filetypes=[("CSV files", "*.csv"), ("All files", "*.* ")], initialdir=os.path.expanduser("~\Documents"))
        if filename:
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, filename)
            if self.search_type.get() == "apn": self.search_type.set("import")
    
    def _perform_search(self):
        search_value = self.search_entry.get().strip()
        if not search_value: messagebox.showwarning("Input Required", "Please enter search criteria."); return
        search_type = self.search_type.get()
        self.notebook.select(self.log_frame)
        self.log_text.config(state=tk.NORMAL); self.log_text.delete(1.0, tk.END); self.log_text.config(state=tk.DISABLED)
        print(f"--- Starting new search ---"); print(f"Type: {search_type}, Value: {search_value}")
        if search_type == "import": self._import_csv_data()
        else:
            self._set_status("Searching..."); self.search_button.config(state=tk.DISABLED)
            self.progress.pack(side=tk.RIGHT, padx=5); self.progress.start()
            thread = threading.Thread(target=self._search_thread, args=(search_value, search_type), daemon=True)
            thread.start()
    
    def _search_thread(self, search_value: str, search_type: str):
        try:
            if search_type == "apn":
                property_info = self.api.search_by_apn(search_value)
                if property_info:
                    self.current_property = property_info
                    self.current_apn = property_info.apn
                    self.root.after(0, self._display_property_info, property_info)
                    self.root.after(0, self._load_additional_data, property_info.apn)
                else:
                    self.root.after(0, self._show_no_results)
            elif search_type == "address":
                properties = self.api.search_by_address(search_value)
                if properties and properties[0].apn:
                    print(f"Address search found {len(properties)} result(s). Fetching full details for first APN: {properties[0].apn}")
                    # Now, get the full details for the first result
                    detailed_property_info = self.api.search_by_apn(properties[0].apn)
                    if detailed_property_info:
                        self.current_property = detailed_property_info
                        self.current_apn = detailed_property_info.apn
                        self.root.after(0, self._display_property_info, detailed_property_info)
                        self.root.after(0, self._load_additional_data, detailed_property_info.apn)
                    else:
                        # If detail fetch fails, show partial info from the list
                        print("Could not fetch full details, displaying partial info from search list.")
                        self.current_property = properties[0]
                        self.current_apn = properties[0].apn
                        self.root.after(0, self._display_property_info, properties[0])
                        self.root.after(0, self._load_additional_data, properties[0].apn)
                else:
                    self.root.after(0, self._show_no_results)
        except Exception as e:
            print(f"An unexpected error occurred in the search thread: {e}"); traceback.print_exc()
            self.root.after(0, self._show_error, str(e))
        finally:
            self.root.after(0, self._search_complete)
    
    def _import_csv_data(self):
        filepath = self.search_entry.get().strip()
        if not filepath: filepath = filedialog.askopenfilename(title="Select Property CSV file", filetypes=[("CSV files", "*.csv"), ("All files", "*.* ")])
        if filepath and os.path.exists(filepath):
            try:
                count = self.api.import_csv_data(filepath)
                self.data_status.config(text=f"CSV Cache: {len(self.api.csv_cache)} properties")
                messagebox.showinfo("Import Success", f"Imported {count} properties into cache.")
                self.use_csv.set(True)
            except Exception as e: messagebox.showerror("Import Error", f"Error importing CSV:\n{str(e)}")
    
    def _load_additional_data(self, apn: str):
        def load():
            try:
                print(f"Loading tax info for {apn}..."); tax_info = self.api.get_full_tax_info(apn) # Call the new method
                self.current_tax_info = tax_info; self.root.after(0, self._display_tax_info, tax_info); print("Tax info loaded.")
                print(f"Loading sales history for {apn}..."); sales_info = self.api.get_sales_history(self.current_property)
                self.current_sales_info = sales_info; self.root.after(0, self._display_sales_info, sales_info); print("Sales history loaded.")
                self.root.after(0, self._enable_document_buttons)
            except Exception as e: print(f"Error loading additional data: {e}")
        thread = threading.Thread(target=load, daemon=True); thread.start()
    
    def _display_property_info(self, property_info: PropertyInfo):
        self.property_text.delete(1.0, tk.END)
        display_data = property_info.to_display_dict()
        for key, value in display_data.items():
            if value: self.property_text.insert(tk.END, f"{key:.<30} {value}\n")
        self.notebook.select(self.property_frame)
        self._set_status(f"Property found: {property_info.apn}")
        print(f"Successfully displayed property: {property_info.apn}")
    
    def _display_tax_info(self, tax_list: List[TaxInfo]):
        for item in self.tax_tree.get_children(): self.tax_tree.delete(item)
        for tax in tax_list:
            values = (tax.tax_year, f"${tax.assessed_value:,.0f}", f"${tax.limited_value:,.0f}", f"${tax.total_taxes:,.2f}", tax.tax_status)
            self.tax_tree.insert('', tk.END, values=values)
    
    def _display_sales_info(self, sales_list: List[SaleInfo]):
        for item in self.sales_tree.get_children(): self.sales_tree.delete(item)
        for sale in sales_list:
            values = (sale.sale_date, f"${sale.sale_price:,.0f}", sale.deed_type, sale.seller[:30], sale.buyer[:30])
            self.sales_tree.insert('', tk.END, values=values)
    
    def _enable_document_buttons(self):
        self.assessor_link_btn.config(state=tk.NORMAL)
        self.recorder_link_btn.config(state=tk.NORMAL)
        self.tax_bill_btn.config(state=tk.NORMAL)
    
    def _open_assessor_link(self):
        if self.current_apn: webbrowser.open(APIConfig.PARCEL_URL.format(apn=self.current_apn))
    
    def _open_recorder_link(self):
        if self.current_apn: webbrowser.open(f"https://recorder.maricopa.gov/recdocdata/GetRecDataDetail.aspx?rec={self.current_apn}")
    
    def _open_tax_bills(self):
        if self.current_apn: webbrowser.open(f"https://treasurer.maricopa.gov/parcelinfo/?q={self.current_apn}")
    
    def _export_current(self):
        if not self.current_property: messagebox.showwarning("No Data", "No property data to export."); return
        try:
            export_folder = Path.home() / "MaricopaPropertyExports"; export_folder.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S"); folder = export_folder / timestamp; folder.mkdir(exist_ok=True)
            prop_file = folder / f"property_{self.current_apn}.csv"
            with open(prop_file, 'w', newline='') as f:
                writer = csv.writer(f); writer.writerow(["Field", "Value"])
                for key, value in self.current_property.to_display_dict().items(): writer.writerow([key, value])
            messagebox.showinfo("Export Complete", f"Data exported to:\n{folder}")
        except Exception as e: messagebox.showerror("Export Error", f"Error exporting data:\n{str(e)}")
    
    def _clear_cache(self):
        self.api.csv_cache.clear(); self.data_status.config(text="CSV Cache: 0 properties")
        messagebox.showinfo("Cache Cleared", "CSV cache has been cleared.")
    
    def _open_export_folder(self):
        folder = Path.home() / "MaricopaPropertyExports"; folder.mkdir(exist_ok=True); os.startfile(folder)
    
    def _show_no_results(self):
        print("Search completed, but no results were found.")
        self.property_text.delete(1.0, tk.END)
        self.property_text.insert(tk.END, "No results found.\n\nCheck the 'Log' tab for detailed error messages.\n")
        self.notebook.select(self.property_frame)
    
    def _show_error(self, error_msg: str):
        messagebox.showerror("Error", f"An error occurred:\n{error_msg}")
    
    def _search_complete(self):
        self.search_button.config(state=tk.NORMAL); self.progress.stop(); self.progress.pack_forget()
        self._set_status("Search complete."); print("--- Search finished ---")
    
    def _set_status(self, message: str):
        self.status_var.set(message)
    
    def _batch_process(self):
        filename = filedialog.askopenfilename(title="Select file with APNs (one per line)", filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.* ")])
        if not filename: return
        try:
            with open(filename, 'r') as f: apns = [line.strip() for line in f if line.strip()]
            if not apns: messagebox.showwarning("No APNs", "No APNs found in file"); return
            results = []
            self._set_status(f"Processing {len(apns)} APNs..."); self.progress.pack(side=tk.RIGHT, padx=5); self.progress.start()
            for i, apn in enumerate(apns[:100]):
                self._set_status(f"Processing {i+1}/{len(apns)}: {apn}"); self.root.update()
                prop = self.api.search_by_apn(apn)
                if prop: results.append(prop)
            self.progress.stop(); self.progress.pack_forget()
            if results:
                export_folder = Path.home() / "MaricopaPropertyExports"; export_folder.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = export_folder / f"batch_results_{timestamp}.csv"
                with open(output_file, 'w', newline='') as f:
                    writer = csv.writer(f); writer.writerow(["APN", "Owner", "Property Address", "Assessed Value"])
                    for prop in results: writer.writerow([prop.apn, prop.owner_name, prop.property_address, prop.assessed_value])
                messagebox.showinfo("Batch Complete", f"Processed {len(results)} properties\nSaved to: {output_file}")
        except Exception as e:
            messagebox.showerror("Batch Error", f"Error processing batch: {str(e)}")
            self.progress.stop(); self.progress.pack_forget()

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main application entry point"""
    root = tk.Tk()
    app = PropertySearchApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
