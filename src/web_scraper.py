"""
Web Scraper Manager
Handles web scraping of Maricopa County property information
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor
import threading

# Import centralized logging
from logging_config import get_logger, get_performance_logger, log_exception, log_debug_variables

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)

class WebScraperManager:
    def __init__(self, config_manager):
        logger.info("Initializing Web Scraper Manager")
        
        self.config = config_manager.get_scraping_config()
        self.paths_config = config_manager
        self.drivers = []
        self.driver_lock = threading.Lock()
        
        logger.debug(f"Scraping Configuration - Browser: {self.config['browser']}, "
                    f"Headless: {self.config['headless']}, "
                    f"Timeout: {self.config['timeout']}s, "
                    f"Max Workers: {self.config['max_workers']}")
        
        # Setup Chrome options
        self.chrome_options = Options()
        if self.config['headless']:
            self.chrome_options.add_argument('--headless')
            logger.debug("Chrome configured for headless mode")
        
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Chrome driver path
        driver_dir = self.paths_config.get_path('driver')
        self.chrome_driver_path = driver_dir / "chromedriver.exe"
        
        logger.debug(f"Chrome driver path: {self.chrome_driver_path}")
        logger.info("Web scraper manager initialized successfully")
    
    def _create_driver(self) -> webdriver.Chrome:
        """Create a new Chrome driver instance"""
        try:
            service = Service(str(self.chrome_driver_path))
            driver = webdriver.Chrome(service=service, options=self.chrome_options)
            
            # Execute script to hide automation
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
        except Exception as e:
            logger.error(f"Failed to create Chrome driver: {e}")
            raise
    
    def _get_driver(self) -> webdriver.Chrome:
        """Get a driver from the pool or create a new one"""
        with self.driver_lock:
            if self.drivers:
                return self.drivers.pop()
            else:
                return self._create_driver()
    
    def _return_driver(self, driver: webdriver.Chrome):
        """Return a driver to the pool"""
        with self.driver_lock:
            if len(self.drivers) < self.config['max_workers']:
                self.drivers.append(driver)
            else:
                driver.quit()
    
    @perf_logger.log_performance('scrape_property_by_apn')
    def scrape_property_by_apn(self, apn: str) -> Optional[Dict]:
        """Scrape property information by APN from Maricopa County website"""
        logger.info(f"Starting web scraping for APN: {apn}")
        
        driver = None
        try:
            driver = self._get_driver()
            logger.debug(f"Obtained browser driver for APN: {apn}")
            
            # Navigate to the actual Maricopa County assessor website
            search_url = f"https://mcassessor.maricopa.gov/parcel/{self._format_apn(apn)}"
            logger.info(f"Navigating to: {search_url}")
            driver.get(search_url)
            
            # Wait for page to load
            wait = WebDriverWait(driver, self.config['timeout'])
            
            # Check if we got a valid property page or error
            try:
                # Wait for either property data or error message
                wait.until(
                    lambda d: d.find_elements(By.CLASS_NAME, "property-data") or 
                             d.find_elements(By.CLASS_NAME, "error-message") or
                             "No parcel found" in d.page_source.lower()
                )
                
                # Check if property was found
                if "No parcel found" in driver.page_source.lower() or driver.find_elements(By.CLASS_NAME, "error-message"):
                    logger.warning(f"Property not found for APN: {apn}")
                    return None
                    
            except TimeoutException:
                # Try alternative selector patterns
                pass
            
            # Extract property information using real selectors
            property_data = self._extract_real_property_details(driver, apn)
            
            if property_data:
                logger.info(f"Successfully scraped property {apn}")
                return property_data
            else:
                logger.warning(f"No property data found for {apn}")
                return None
            
        except TimeoutException:
            logger.error(f"Timeout while scraping property {apn}")
            if self.config.get('screenshot_on_error', False):
                self._take_screenshot(driver, f"timeout_error_{apn}")
            return None
            
        except Exception as e:
            logger.error(f"Error scraping property {apn}: {e}")
            if self.config.get('screenshot_on_error', False):
                self._take_screenshot(driver, f"scrape_error_{apn}")
            return None
            
        finally:
            if driver:
                self._return_driver(driver)
    
    def _extract_real_property_details(self, driver: webdriver.Chrome, apn: str) -> Dict:
        """Extract property details from the page"""
        property_data = {
            'apn': apn,
            'scraped_at': time.time()
        }
        
        try:
            # Extract basic property information
            property_data['owner_name'] = self._safe_get_text(
                driver, By.CLASS_NAME, "owner-name"
            )
            
            property_data['property_address'] = self._safe_get_text(
                driver, By.CLASS_NAME, "property-address"
            )
            
            property_data['mailing_address'] = self._safe_get_text(
                driver, By.CLASS_NAME, "mailing-address"
            )
            
            property_data['legal_description'] = self._safe_get_text(
                driver, By.CLASS_NAME, "legal-description"
            )
            
            # Extract property characteristics
            property_data['land_use_code'] = self._safe_get_text(
                driver, By.CLASS_NAME, "land-use"
            )
            
            year_built_text = self._safe_get_text(driver, By.CLASS_NAME, "year-built")
            property_data['year_built'] = self._parse_int(year_built_text)
            
            sqft_text = self._safe_get_text(driver, By.CLASS_NAME, "living-area")
            property_data['living_area_sqft'] = self._parse_int(sqft_text)
            
            lot_size_text = self._safe_get_text(driver, By.CLASS_NAME, "lot-size")
            property_data['lot_size_sqft'] = self._parse_int(lot_size_text)
            
            bedrooms_text = self._safe_get_text(driver, By.CLASS_NAME, "bedrooms")
            property_data['bedrooms'] = self._parse_int(bedrooms_text)
            
            bathrooms_text = self._safe_get_text(driver, By.CLASS_NAME, "bathrooms")
            property_data['bathrooms'] = self._parse_float(bathrooms_text)
            
            # Check for pool
            pool_element = driver.find_elements(By.CLASS_NAME, "pool-indicator")
            property_data['pool'] = len(pool_element) > 0
            
            garage_text = self._safe_get_text(driver, By.CLASS_NAME, "garage-spaces")
            property_data['garage_spaces'] = self._parse_int(garage_text)
            
            # Extract tax information if available
            try:
                tax_table = driver.find_element(By.CLASS_NAME, "tax-history-table")
                property_data['tax_history'] = self._extract_tax_table(tax_table)
            except NoSuchElementException:
                property_data['tax_history'] = []
            
            # Extract sales information if available
            try:
                sales_table = driver.find_element(By.CLASS_NAME, "sales-history-table")
                property_data['sales_history'] = self._extract_sales_table(sales_table)
            except NoSuchElementException:
                property_data['sales_history'] = []
            
            return property_data
            
        except Exception as e:
            logger.error(f"Error extracting property details for {apn}: {e}")
            return property_data
    
    def _safe_get_text(self, driver: webdriver.Chrome, by: By, selector: str) -> Optional[str]:
        """Safely get text from an element"""
        try:
            element = driver.find_element(by, selector)
            return element.text.strip()
        except NoSuchElementException:
            return None
    
    def _parse_int(self, text: str) -> Optional[int]:
        """Parse integer from text"""
        if not text:
            return None
        try:
            # Remove non-numeric characters except digits
            numeric_text = ''.join(c for c in text if c.isdigit())
            return int(numeric_text) if numeric_text else None
        except ValueError:
            return None
    
    def _parse_float(self, text: str) -> Optional[float]:
        """Parse float from text"""
        if not text:
            return None
        try:
            # Remove non-numeric characters except digits and decimal point
            numeric_text = ''.join(c for c in text if c.isdigit() or c == '.')
            return float(numeric_text) if numeric_text else None
        except ValueError:
            return None
    
    def _extract_tax_table(self, table_element) -> List[Dict]:
        """Extract tax history from table"""
        tax_history = []
        try:
            rows = table_element.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
            
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 4:
                    tax_record = {
                        'tax_year': self._parse_int(cells[0].text),
                        'assessed_value': self._parse_float(cells[1].text),
                        'tax_amount': self._parse_float(cells[2].text),
                        'payment_status': cells[3].text.strip()
                    }
                    tax_history.append(tax_record)
        except Exception as e:
            logger.error(f"Error extracting tax table: {e}")
        
        return tax_history
    
    def _extract_sales_table(self, table_element) -> List[Dict]:
        """Extract sales history from table"""
        sales_history = []
        try:
            rows = table_element.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
            
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 4:
                    sales_record = {
                        'sale_date': cells[0].text.strip(),
                        'sale_price': self._parse_float(cells[1].text),
                        'seller_name': cells[2].text.strip(),
                        'buyer_name': cells[3].text.strip()
                    }
                    sales_history.append(sales_record)
        except Exception as e:
            logger.error(f"Error extracting sales table: {e}")
        
        return sales_history
    
    def _take_screenshot(self, driver: webdriver.Chrome, filename: str):
        """Take screenshot for debugging"""
        try:
            screenshot_dir = self.paths_config.get_path('log') / "screenshots"
            screenshot_dir.mkdir(exist_ok=True)
            
            screenshot_path = screenshot_dir / f"{filename}_{int(time.time())}.png"
            driver.save_screenshot(str(screenshot_path))
            logger.info(f"Screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
    
    def bulk_scrape_properties(self, apns: List[str], max_workers: int = None) -> Dict[str, Dict]:
        """Scrape multiple properties in parallel"""
        if not max_workers:
            max_workers = min(self.config['max_workers'], len(apns))
        
        logger.info(f"Starting bulk scrape of {len(apns)} properties with {max_workers} workers")
        
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all scraping tasks
            future_to_apn = {
                executor.submit(self.scrape_property_by_apn, apn): apn 
                for apn in apns
            }
            
            # Collect results
            for future in future_to_apn:
                apn = future_to_apn[future]
                try:
                    result = future.result()
                    if result:
                        results[apn] = result
                except Exception as e:
                    logger.error(f"Error in bulk scrape for {apn}: {e}")
        
        logger.info(f"Bulk scrape completed: {len(results)}/{len(apns)} properties scraped successfully")
        return results
    
    def search_by_owner_name(self, owner_name: str, limit: int = 50) -> List[Dict]:
        """Search properties by owner name using web scraping on the real website"""
        driver = None
        try:
            driver = self._get_driver()
            
            # Use the actual search endpoint with proper URL encoding
            search_url = f"https://mcassessor.maricopa.gov/search/property/?q={self._url_encode(owner_name)}"
            logger.info(f"Searching for owner: {owner_name} at {search_url}")
            driver.get(search_url)
            
            wait = WebDriverWait(driver, self.config['timeout'])
            
            # Wait for results to load
            try:
                wait.until(
                    lambda d: d.find_elements(By.CLASS_NAME, "search-results") or
                             d.find_elements(By.CLASS_NAME, "property-result") or
                             "No results found" in d.page_source.lower()
                )
            except TimeoutException:
                logger.error(f"Timeout waiting for search results for owner: {owner_name}")
                return []
            
            # Check if no results
            if "No results found" in driver.page_source.lower():
                logger.info(f"No properties found for owner: {owner_name}")
                return []
            
            # Extract search results from real page structure
            results = self._extract_real_search_results(driver, owner_name, limit)
            
            logger.info(f"Found {len(results)} properties for owner: {owner_name}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching by owner name '{owner_name}': {e}")
            return []
            
        finally:
            if driver:
                self._return_driver(driver)
    
    def _extract_real_search_results(self, driver: webdriver.Chrome, search_term: str, limit: int) -> List[Dict]:
        """Extract search results from results page"""
        results = []
        try:
            result_rows = driver.find_elements(By.CLASS_NAME, "result-row")[:limit]
            
            for row in result_rows:
                try:
                    result = {
                        'apn': self._safe_get_text(row, By.CLASS_NAME, "apn"),
                        'owner_name': self._safe_get_text(row, By.CLASS_NAME, "owner"),
                        'property_address': self._safe_get_text(row, By.CLASS_NAME, "address"),
                        'assessed_value': self._safe_get_text(row, By.CLASS_NAME, "value")
                    }
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Error extracting search result row: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error extracting search results: {e}")
        
        return results
    
    def _format_apn(self, apn: str) -> str:
        """Format APN for URL usage"""
        # Remove spaces, dashes, dots for URL
        return apn.replace(' ', '').replace('-', '').replace('.', '')
    
    def _url_encode(self, text: str) -> str:
        """URL encode search text"""
        import urllib.parse
        return urllib.parse.quote_plus(text)
    
    def _extract_from_tables(self, driver: webdriver.Chrome, property_data: Dict):
        """Extract property data from tables on the page"""
        try:
            # Look for data tables
            tables = driver.find_elements(By.TAG_NAME, 'table')
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, 'tr')
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    if len(cells) >= 2:
                        label = cells[0].text.strip().lower()
                        value = cells[1].text.strip()
                        
                        if 'owner' in label and value:
                            property_data['owner_name'] = value
                        elif 'address' in label and value:
                            property_data['property_address'] = value
                        elif 'legal' in label and value:
                            property_data['legal_description'] = value
                        elif 'year' in label and 'built' in label:
                            property_data['year_built'] = self._parse_int(value)
                        elif 'value' in label or 'assessed' in label:
                            property_data['latest_assessed_value'] = self._parse_float(value)
        except Exception as e:
            logger.debug(f"Error extracting from tables: {e}")
    
    def _extract_structured_data(self, driver: webdriver.Chrome, property_data: Dict):
        """Extract structured data (JSON-LD, microdata, etc.)"""
        try:
            # Look for JSON-LD structured data
            scripts = driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
            for script in scripts:
                try:
                    data = json.loads(script.get_attribute('innerHTML'))
                    if isinstance(data, dict):
                        if 'name' in data:
                            property_data['owner_name'] = data['name']
                        if 'address' in data:
                            property_data['property_address'] = str(data['address'])
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            logger.debug(f"Error extracting structured data: {e}")
    
    def _extract_from_page_text(self, driver: webdriver.Chrome, property_data: Dict):
        """Extract data from page text using patterns"""
        try:
            page_text = driver.page_source
            
            # Use regex patterns to find data
            import re
            
            # APN pattern
            apn_match = re.search(r'APN[:\s]*([\d-\.\s]+)', page_text, re.IGNORECASE)
            if apn_match:
                property_data['apn'] = apn_match.group(1).strip()
            
            # Address pattern
            address_match = re.search(r'Address[:\s]*([^\n\r<]+)', page_text, re.IGNORECASE)
            if address_match:
                property_data['property_address'] = address_match.group(1).strip()
            
            # Owner pattern
            owner_match = re.search(r'Owner[:\s]*([^\n\r<]+)', page_text, re.IGNORECASE)
            if owner_match:
                property_data['owner_name'] = owner_match.group(1).strip()
                
        except Exception as e:
            logger.debug(f"Error extracting from page text: {e}")
    
    def _extract_result_from_element(self, element, search_term: str) -> Dict:
        """Extract result data from a search result element"""
        result = {}
        
        try:
            # Try to find APN in the element
            apn_selectors = ['[class*="apn"]', '[class*="parcel"]', 'a[href*="parcel/"]']
            for selector in apn_selectors:
                apn_elem = element.find_elements(By.CSS_SELECTOR, selector)
                if apn_elem:
                    apn_text = apn_elem[0].text.strip()
                    if apn_text:
                        result['apn'] = apn_text
                        break
                    # Try getting APN from href
                    href = apn_elem[0].get_attribute('href')
                    if href and '/parcel/' in href:
                        result['apn'] = href.split('/parcel/')[-1].split('/')[0]
                        break
            
            # Get all text content and try to extract information
            element_text = element.text.strip()
            lines = [line.strip() for line in element_text.split('\n') if line.strip()]
            
            # Assign data based on content
            for line in lines:
                if not result.get('owner_name') and any(char.isalpha() for char in line):
                    # Likely owner name if it contains letters
                    result['owner_name'] = line
                elif not result.get('property_address') and (any(num.isdigit() for num in line.split()) or 'AZ' in line.upper()):
                    # Likely address if contains numbers or AZ
                    result['property_address'] = line
                elif '$' in line:
                    # Likely assessed value
                    result['assessed_value'] = line
            
            # Fallback: use search term as owner if we didn't find one
            if not result.get('owner_name'):
                result['owner_name'] = search_term
                
            # Ensure we have an APN
            if not result.get('apn'):
                # Try to extract from any links
                links = element.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href = link.get_attribute('href')
                    if href and '/parcel/' in href:
                        result['apn'] = href.split('/parcel/')[-1].split('/')[0]
                        break
            
        except Exception as e:
            logger.debug(f"Error extracting from result element: {e}")
        
        return result
    
    def _try_pagination(self, driver: webdriver.Chrome, current_results: List[Dict], needed: int):
        """Try to get more results from pagination"""
        try:
            # Look for next page buttons
            next_buttons = driver.find_elements(By.CSS_SELECTOR, '.next, .page-next, [class*="next"]')
            for button in next_buttons:
                if button.is_enabled():
                    button.click()
                    time.sleep(2)  # Wait for page load
                    
                    # Extract results from new page
                    new_results = self._extract_real_search_results(driver, "", needed)
                    current_results.extend(new_results[:needed])
                    break
        except Exception as e:
            logger.debug(f"Error with pagination: {e}")
    
    def close(self):
        """Close all driver instances"""
        with self.driver_lock:
            for driver in self.drivers:
                try:
                    driver.quit()
                except Exception as e:
                    logger.warning(f"Error closing driver: {e}")
            self.drivers.clear()
        
        logger.info("Web scraper manager closed")


class MockWebScraperManager(WebScraperManager):
    """Mock web scraper for testing without Chrome dependencies"""
    
    def __init__(self, config_manager):
        self.config = config_manager.get_scraping_config()
        logger.info("Using Mock Web Scraper - no actual web scraping will be performed")
    
    def scrape_property_by_apn(self, apn: str) -> Optional[Dict]:
        """Mock scraping by APN"""
        import random
        time.sleep(random.uniform(0.5, 2.0))  # Simulate scraping time
        
        logger.info(f"Mock: Scraping property {apn}")
        
        return {
            'apn': apn,
            'owner_name': f'Mock Owner {apn[-4:]}',
            'property_address': f'{random.randint(100, 9999)} Mock Street, Phoenix, AZ',
            'mailing_address': f'PO Box {random.randint(1000, 9999)}, Phoenix, AZ',
            'legal_description': f'Mock legal description for {apn}',
            'land_use_code': random.choice(['R1', 'R2', 'C1']),
            'year_built': random.randint(1950, 2023),
            'living_area_sqft': random.randint(800, 5000),
            'lot_size_sqft': random.randint(5000, 20000),
            'bedrooms': random.randint(2, 6),
            'bathrooms': random.randint(1, 4),
            'pool': random.choice([True, False]),
            'garage_spaces': random.randint(0, 3),
            'scraped_at': time.time(),
            'tax_history': [],
            'sales_history': []
        }
    
    def search_by_owner_name(self, owner_name: str, limit: int = 50) -> List[Dict]:
        """Mock search by owner name"""
        import random
        
        logger.info(f"Mock: Searching properties by owner: {owner_name}")
        
        num_results = random.randint(0, min(5, limit))
        return [
            {
                'apn': f"12345{i:03d}",
                'owner_name': owner_name,
                'property_address': f'{random.randint(100, 9999)} Mock Street, Phoenix, AZ',
                'assessed_value': f"${random.randint(100000, 800000):,}"
            }
            for i in range(num_results)
        ]
    
    def bulk_scrape_properties(self, apns: List[str], max_workers: int = None) -> Dict[str, Dict]:
        """Mock bulk scraping"""
        logger.info(f"Mock: Bulk scraping {len(apns)} properties")
        
        results = {}
        for apn in apns:
            results[apn] = self.scrape_property_by_apn(apn)
        
        return results
    
    def close(self):
        """Mock close method"""
        logger.info("Mock web scraper closed")