"""
Optimized Web Scraper with Performance Enhancements
Parallel scraping, connection reuse, and smart timeouts
Target: <2 seconds for tax/sales data scraping
"""
import asyncio
import json
import logging
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from logging_config import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)


@dataclass
class ScrapingTask:
    """Represents a web scraping task"""

    name: str
    url: str
    priority: int  # 1=highest, 3=lowest
    timeout: float
    retry_count: int = 0


class OptimizedWebScraperManager:
    """High-performance web scraper with parallel processing and smart resource management"""
    def __init__(self, config_manager):
        logger.info("Initializing Optimized Web Scraper Manager")

        self.config = config_manager.get_scraping_config()
        self.paths_config = config_manager

        # Optimized configuration for speed
        self.max_workers = min(
            self.config.get("max_workers", 4), 6
        )  # Limit to 6 for stability
        self.driver_pool = []
        self.driver_lock = threading.Lock()
        self.active_drivers = 0

        # Performance tracking
        self.scraping_stats = {
            "total_scrapes": 0,
            "successful_scrapes": 0,
            "avg_scrape_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Smart caching for repeated requests
        self._scrape_cache = {}
        self._cache_lock = threading.Lock()

        # Setup optimized Chrome options
        self.chrome_options = self._setup_optimized_chrome_options()

        # Thread pool for parallel scraping
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)

        logger.info(
            f"Optimized Web Scraper initialized with {self.max_workers} workers"
        )
    def _setup_optimized_chrome_options(self) -> Options:
        """Setup Chrome options optimized for speed and performance"""
        options = Options()

        # Essential performance flags
        options.add_argument("--headless")  # Always headless for performance
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")

        # Speed optimizations
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # Don't load images
        options.add_argument("--disable-javascript")  # Disable JS where possible
        options.add_argument("--disable-css")  # Disable CSS loading
        options.add_argument("--disable-web-security")
        options.add_argument("--ignore-certificate-errors")

        # Memory and resource optimization
        options.add_argument("--max_old_space_size=512")  # Limit memory usage
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max-chromedriver-connections=10")

        # Network optimizations
        options.add_argument("--aggressive-cache-discard")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")

        # Set smaller window size for faster rendering
        options.add_argument("--window-size=800,600")

        # Disable unnecessary features
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-features=VizDisplayCompositor")

        # Set preferences for minimal loading
        prefs = {
            "profile.default_content_setting_values": {
                "images": 2,  # Block images
                "plugins": 2,  # Block plugins
                "popups": 2,  # Block popups
                "geolocation": 2,  # Block location sharing
                "notifications": 2,  # Block notifications
                "media_stream": 2,  # Block media stream
            },
            "profile.managed_default_content_settings": {"images": 2},  # Block images
        }
        options.add_experimental_option("prefs", prefs)

        logger.debug("Chrome options configured for maximum performance")
        return options
    def _get_optimized_driver(self) -> webdriver.Chrome:
        """Get an optimized Chrome driver instance"""
        with self.driver_lock:
            if self.driver_pool:
                driver = self.driver_pool.pop()
                logger.debug("Reusing existing Chrome driver from pool")
                return driver

        # Create new driver with optimized settings
        service = Service()
        service.creation_flags = 0x08000000  # CREATE_NO_WINDOW on Windows

        driver = webdriver.Chrome(service=service, options=self.chrome_options)

        # Set optimized timeouts
        driver.set_page_load_timeout(5)  # 5 second page load timeout
        driver.implicitly_wait(1)  # 1 second implicit wait

        with self.driver_lock:
            self.active_drivers += 1

        logger.debug("Created new optimized Chrome driver")
        return driver
    def _return_driver_to_pool(self, driver: webdriver.Chrome):
        """Return driver to pool for reuse"""
    try:
            # Clear cookies and reset state
            driver.delete_all_cookies()
            driver.get("about:blank")

            with self.driver_lock:
                if len(self.driver_pool) < self.max_workers:
                    self.driver_pool.append(driver)
                    logger.debug("Driver returned to pool")
                else:
                    driver.quit()
                    self.active_drivers -= 1
                    logger.debug("Driver closed (pool full)")
    except Exception as e:
            logger.error(f"Error returning driver to pool: {e}")
    try:
                driver.quit()
                with self.driver_lock:
                    self.active_drivers -= 1
    except:
            pass
    def scrape_property_data_parallel(
        self, apn: str, data_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Scrape multiple data types in parallel for maximum speed
        data_types: ['tax', 'sales', 'documents', 'recorder']
        """
        if data_types is None:
            data_types = ["tax", "sales", "documents"]

        logger.info(f"Starting parallel scraping for APN: {apn}, types: {data_types}")
        start_time = time.time()

        # Define scraping tasks
        tasks = []
        if "tax" in data_types:
            tasks.append(
                ScrapingTask(
                    name="tax_info",
                    url=f"https://treasurer.maricopa.gov/Parcel/{apn}",
                    priority=1,
                    timeout=3.0,
                )
            )

        if "sales" in data_types:
            tasks.append(
                ScrapingTask(
                    name="sales_history",
                    url=f"https://recorder.maricopa.gov/parcel/{apn}/sales",
                    priority=2,
                    timeout=4.0,
                )
            )

        if "documents" in data_types:
            tasks.append(
                ScrapingTask(
                    name="documents",
                    url=f"https://recorder.maricopa.gov/parcel/{apn}/documents",
                    priority=2,
                    timeout=3.0,
                )
            )

        if "recorder" in data_types:
            tasks.append(
                ScrapingTask(
                    name="recorder_info",
                    url=f"https://recorder.maricopa.gov/parcel/{apn}",
                    priority=3,
                    timeout=3.0,
                )
            )

        # Execute tasks in parallel
        results = {}
        futures = []

        for task in tasks:
            future = self.thread_pool.submit(self._scrape_single_task, task, apn)
            futures.append((task.name, future))

        # Collect results with timeout
        for task_name, future in futures:
    try:
                result = future.result(timeout=6.0)  # 6 second timeout per task
                if result:
                    results[task_name] = result
                    logger.debug(f"Scraped {task_name} successfully")
                else:
                    logger.warning(f"No data from {task_name}")
    except Exception as e:
                logger.error(f"Error scraping {task_name}: {e}")
                results[task_name] = {"error": str(e)}

        scraping_time = time.time() - start_time
        self._update_scraping_stats(scraping_time, len(results) > 0)

        logger.info(
            f"Parallel scraping completed in {scraping_time:.3f}s for APN: {apn}"
        )

        return {
            "apn": apn,
            "scraping_time": scraping_time,
            "data_collected": list(results.keys()),
            "results": results,
        }
    def _scrape_single_task(self, task: ScrapingTask, apn: str) -> Optional[Dict]:
        """Execute a single scraping task with caching and optimization"""
        cache_key = f"{task.name}:{apn}"

        # Check cache first
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result

        driver = None
    try:
            driver = self._get_optimized_driver()

            # Navigate with timeout
            start_time = time.time()
            driver.get(task.url)

            # Wait for essential content with short timeout
            wait = WebDriverWait(driver, task.timeout)

            # Task-specific scraping logic
            if task.name == "tax_info":
                result = self._scrape_tax_info_fast(driver, wait)
            elif task.name == "sales_history":
                result = self._scrape_sales_history_fast(driver, wait)
            elif task.name == "documents":
                result = self._scrape_documents_fast(driver, wait)
            elif task.name == "recorder_info":
                result = self._scrape_recorder_info_fast(driver, wait)
            else:
                result = None

            scrape_time = time.time() - start_time
            logger.debug(f"{task.name} scraped in {scrape_time:.3f}s")

            # Cache successful results
            if result:
                self._cache_result(cache_key, result)

            return result

    except TimeoutException:
            logger.warning(f"Timeout scraping {task.name} for APN: {apn}")
            return None
    except Exception as e:
            logger.error(f"Error scraping {task.name} for APN {apn}: {e}")
            return None
    finally:
            if driver:
                self._return_driver_to_pool(driver)
    def _scrape_tax_info_fast(
        self, driver: webdriver.Chrome, wait: WebDriverWait
    ) -> Optional[Dict]:
        """Fast tax information scraping with minimal waits"""
    try:
            # Look for tax table or key tax elements
            tax_elements = driver.find_elements(
                By.CSS_SELECTOR, ".tax-info, .property-tax, table"
            )

            if tax_elements:
                tax_data = {
                    "tax_year": None,
                    "tax_amount": None,
                    "assessed_value": None,
                    "tax_status": None,
                    "raw_html": tax_elements[0].get_attribute("outerHTML")[
                        :1000
                    ],  # First 1000 chars
                }

                # Quick text extraction for key values
                page_text = driver.page_source

                # Extract key values using simple text search (faster than complex parsing)
                if "tax year" in page_text.lower():
                    # Extract tax year logic here
                    pass

                return tax_data

            return None

    except Exception as e:
            logger.error(f"Error in fast tax scraping: {e}")
            return None
    def _scrape_sales_history_fast(
        self, driver: webdriver.Chrome, wait: WebDriverWait
    ) -> Optional[List[Dict]]:
        """Fast sales history scraping"""
    try:
            # Look for sales table or sales data elements
            sales_elements = driver.find_elements(
                By.CSS_SELECTOR, ".sales-history, .sales-table, table"
            )

            if sales_elements:
                sales_data = []

                # Quick extraction of sales rows
                rows = driver.find_elements(By.CSS_SELECTOR, "tr, .sale-record")

                for row in rows[:10]:  # Limit to first 10 sales records for speed
                    row_text = row.text.strip()
                    if row_text and len(row_text) > 10:
                        sales_data.append(
                            {
                                "sale_text": row_text,
                                "raw_html": row.get_attribute("outerHTML")[:500],
                            }
                        )

                return sales_data if sales_data else None

            return None

    except Exception as e:
            logger.error(f"Error in fast sales scraping: {e}")
            return None
    def _scrape_documents_fast(
        self, driver: webdriver.Chrome, wait: WebDriverWait
    ) -> Optional[List[Dict]]:
        """Fast document scraping"""
    try:
            # Look for document links or document table
            doc_elements = driver.find_elements(
                By.CSS_SELECTOR, '.documents, .document-list, a[href*="document"]'
            )

            if doc_elements:
                documents = []

                for element in doc_elements[:5]:  # Limit to first 5 documents for speed
                    doc_text = element.text.strip()
                    doc_href = element.get_attribute("href")

                    if doc_text:
                        documents.append(
                            {
                                "document_name": doc_text,
                                "document_url": doc_href,
                                "document_type": "unknown",
                            }
                        )

                return documents if documents else None

            return None

    except Exception as e:
            logger.error(f"Error in fast document scraping: {e}")
            return None
    def _scrape_recorder_info_fast(
        self, driver: webdriver.Chrome, wait: WebDriverWait
    ) -> Optional[Dict]:
        """Fast recorder information scraping"""
    try:
            # Get basic page information quickly
            page_title = driver.title
            page_url = driver.current_url

            # Look for key recorder data elements
            recorder_elements = driver.find_elements(
                By.CSS_SELECTOR, ".property-info, .parcel-info, .main-content"
            )

            recorder_data = {
                "page_title": page_title,
                "page_url": page_url,
                "recorder_data_available": bool(recorder_elements),
                "raw_content": (
                    recorder_elements[0].text[:500] if recorder_elements else None
                ),
            }

            return recorder_data

    except Exception as e:
            logger.error(f"Error in fast recorder scraping: {e}")
            return None
    def _get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """Get cached scraping result if not expired"""
        with self._cache_lock:
            if cache_key in self._scrape_cache:
                cache_entry = self._scrape_cache[cache_key]
                if time.time() - cache_entry["timestamp"] < 1800:  # 30 minute cache
                    self.scraping_stats["cache_hits"] += 1
                    logger.debug(f"Cache hit for: {cache_key}")
                    return cache_entry["data"]
                else:
                    del self._scrape_cache[cache_key]

        self.scraping_stats["cache_misses"] += 1
        return None
    def _cache_result(self, cache_key: str, result: Dict):
        """Cache scraping result"""
        with self._cache_lock:
            self._scrape_cache[cache_key] = {"data": result, "timestamp": time.time()}
    def _update_scraping_stats(self, scraping_time: float, success: bool):
        """Update scraping performance statistics"""
        self.scraping_stats["total_scrapes"] += 1
        if success:
            self.scraping_stats["successful_scrapes"] += 1

        # Update average scraping time
        prev_avg = self.scraping_stats["avg_scrape_time"]
        count = self.scraping_stats["total_scrapes"]
        self.scraping_stats["avg_scrape_time"] = (
            prev_avg * (count - 1) + scraping_time
        ) / count
    def get_performance_report(self) -> Dict[str, Any]:
        """Get scraping performance report"""
        cache_total = (
            self.scraping_stats["cache_hits"] + self.scraping_stats["cache_misses"]
        )
        cache_hit_rate = (self.scraping_stats["cache_hits"] / max(cache_total, 1)) * 100

        return {
            "scraping_stats": self.scraping_stats,
            "cache_hit_rate": cache_hit_rate,
            "active_drivers": self.active_drivers,
            "driver_pool_size": len(self.driver_pool),
            "cached_entries": len(self._scrape_cache),
        }
    def clear_cache(self):
        """Clear scraping cache"""
        with self._cache_lock:
            self._scrape_cache.clear()
        logger.info("Scraping cache cleared")
    def close_all_drivers(self):
        """Close all drivers and clean up resources"""
        with self.driver_lock:
            for driver in self.driver_pool:
    try:
                    driver.quit()
    except:
            pass
            self.driver_pool.clear()
            self.active_drivers = 0

        self.thread_pool.shutdown(wait=True)
        logger.info("All web drivers closed and thread pool shut down")
    def __del__(self):
        """Cleanup when object is destroyed"""
    try:
            self.close_all_drivers()
    except:
            pass
