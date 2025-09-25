#!/usr/bin/env python
"""
Parallel Web Scraper Manager
Advanced parallel web scraping with multiple browser instances and intelligent load balancing
"""
import asyncio
import json
import logging
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from threading import Event, Lock, RLock, Semaphore
from typing import Any, Callable, Dict, List, Optional, Set

# Optional selenium imports
try:
    from selenium import webdriver
    from selenium.common.exceptions import (
        NoSuchElementException,
        TimeoutException,
        WebDriverException,
    )
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    SELENIUM_AVAILABLE = True
except ImportError:
    # Mock selenium objects when not available
    webdriver = None
    Service = None
    Options = None
    By = None
    WebDriverWait = None
    EC = None
    TimeoutException = Exception
    NoSuchElementException = Exception
    WebDriverException = Exception
    SELENIUM_AVAILABLE = False

from PyQt5.QtCore import QThread, pyqtSignal

from logging_config import get_logger, get_performance_logger
from recorder_scraper import MaricopaRecorderScraper
from tax_scraper import MaricopaTaxScraper

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)


class ScrapingTask(Enum):
    """Types of scraping tasks"""

    PROPERTY_DETAILS = "property_details"
    TAX_INFORMATION = "tax_information"
    SALES_HISTORY = "sales_history"
    DOCUMENT_RECORDS = "document_records"
    OWNER_PROPERTIES = "owner_properties"


@dataclass
class ScrapingRequest:
    """Individual scraping request"""

    task_type: ScrapingTask
    identifier: str  # APN, owner name, etc.
    priority: int = 5  # 1-10, lower is higher priority
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2
    timeout: float = 30.0
    def __hash__(self):
        return hash((self.task_type, self.identifier))
    def __eq__(self, other):
        if not isinstance(other, ScrapingRequest):
            return False
        return self.task_type == other.task_type and self.identifier == other.identifier


class BrowserPool:
    """Pool of browser instances for parallel scraping"""
    def __init__(
        self,
        chrome_driver_path: str,
        pool_size: int = 4,
        headless: bool = True,
        user_agent_rotation: bool = True,
    ):

        if not SELENIUM_AVAILABLE:
            raise ImportError(
                "Selenium is required for BrowserPool but is not installed. Install with: pip install selenium"
            )

        self.chrome_driver_path = chrome_driver_path
        self.pool_size = pool_size
        self.headless = headless
        self.user_agent_rotation = user_agent_rotation

        self.browser_queue = queue.Queue(maxsize=pool_size)
        self.active_browsers = set()
        self.lock = RLock()
        self.total_browsers = 0

        # User agent rotation for avoiding detection
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        self.current_user_agent_index = 0

        # Initialize pool with some browsers
        self._initialize_pool()

        logger.info(
            f"Browser pool initialized with {pool_size} browsers (headless: {headless})"
        )
    def _initialize_pool(self):
        """Pre-create some browser instances"""
        initial_count = min(2, self.pool_size)  # Start with 2 browsers

        for _ in range(initial_count):
    try:
                browser = self._create_browser()
                self.browser_queue.put(browser, block=False)
                self.total_browsers += 1
                logger.debug("Pre-created browser instance")
    except Exception as e:
                logger.warning(f"Failed to pre-create browser: {e}")
                break
    def _create_browser(self) -> webdriver.Chrome:
        """Create a new Chrome browser instance"""
        options = Options()

        if self.headless:
            options.add_argument("--headless")

        # Performance and stealth options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # User agent rotation
        if self.user_agent_rotation:
            user_agent = self.user_agents[
                self.current_user_agent_index % len(self.user_agents)
            ]
            options.add_argument(f"--user-agent={user_agent}")
            self.current_user_agent_index += 1

        # Additional stealth measures
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2,  # Block images for speed
        }
        options.add_experimental_option("prefs", prefs)

    try:
            service = Service(self.chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=options)

            # Execute stealth scripts
            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            driver.execute_cdp_cmd(
                "Network.setUserAgentOverride",
                {
                    "userAgent": driver.execute_script(
                        "return navigator.userAgent"
                    ).replace("Headless", "")
                },
            )

            return driver

    except Exception as e:
            logger.error(f"Failed to create browser: {e}")
            raise
    def acquire_browser(self, timeout: float = 10.0) -> webdriver.Chrome:
        """Get a browser from the pool"""
        start_time = time.time()

        while time.time() - start_time < timeout:
    try:
                # Try to get existing browser
                browser = self.browser_queue.get(timeout=1.0)

                # Verify browser is still responsive
    try:
                    browser.current_url  # Simple check
                    with self.lock:
                        self.active_browsers.add(browser)
                    return browser
    except Exception as e:
                    logger.warning(f"Browser not responsive, creating new one: {e}")
    try:
                        browser.quit()
    except:
            pass

    except queue.Empty:
                pass

            # Create new browser if pool is empty and we haven't hit limit
            with self.lock:
                if self.total_browsers < self.pool_size:
    try:
                        browser = self._create_browser()
                        self.total_browsers += 1
                        self.active_browsers.add(browser)
                        return browser
    except Exception as e:
                        logger.error(f"Failed to create browser on demand: {e}")
                        continue

            time.sleep(0.5)  # Brief wait before retry

        raise TimeoutError(f"Could not acquire browser within {timeout} seconds")
    def release_browser(self, browser: webdriver.Chrome):
        """Return browser to pool"""
        if not browser:
            return

        with self.lock:
            self.active_browsers.discard(browser)

    try:
                # Basic cleanup
                browser.delete_all_cookies()
                browser.execute_script("window.localStorage.clear();")
                browser.execute_script("window.sessionStorage.clear();")

                # Check if pool has space
                if self.browser_queue.qsize() < self.pool_size:
                    self.browser_queue.put(browser, block=False)
                else:
                    # Pool is full, close this browser
                    browser.quit()
                    self.total_browsers -= 1

    except Exception as e:
                logger.warning(f"Error returning browser to pool: {e}")
    try:
                    browser.quit()
                    self.total_browsers -= 1
    except:
            pass
    def close_all(self):
        """Close all browsers in pool"""
        logger.info("Closing all browsers in pool")

        # Close browsers in queue
        while not self.browser_queue.empty():
    try:
                browser = self.browser_queue.get(timeout=1.0)
                browser.quit()
    except:
            pass

        # Close active browsers
        with self.lock:
            for browser in list(self.active_browsers):
    try:
                    browser.quit()
    except:
            pass
            self.active_browsers.clear()
            self.total_browsers = 0

        logger.info("All browsers closed")
    def get_pool_status(self) -> Dict[str, int]:
        """Get current pool status"""
        with self.lock:
            return {
                "total_browsers": self.total_browsers,
                "available_browsers": self.browser_queue.qsize(),
                "active_browsers": len(self.active_browsers),
                "pool_size": self.pool_size,
            }


class ParallelWebScraperManager:
    """Advanced parallel web scraper with multiple browser instances"""
    def __init__(
        self,
        config_manager,
        max_concurrent_scrapers: int = 4,
        enable_tax_scraping: bool = True,
        enable_recorder_scraping: bool = True,
    ):

        logger.info("Initializing Parallel Web Scraper Manager")

        self.config = config_manager.get_scraping_config()
        self.max_concurrent_scrapers = max_concurrent_scrapers
        self.enable_tax_scraping = enable_tax_scraping
        self.enable_recorder_scraping = enable_recorder_scraping

        # Chrome driver path
        driver_dir = config_manager.get_path("driver")
        chrome_driver_path = str(driver_dir / "chromedriver.exe")

        # Browser pool
        self.browser_pool = BrowserPool(
            chrome_driver_path=chrome_driver_path,
            pool_size=max_concurrent_scrapers + 2,  # Extra browsers for overhead
            headless=self.config.get("headless", True),
            user_agent_rotation=True,
        )

        # Thread pool for scraping operations
        self.executor = ThreadPoolExecutor(
            max_workers=max_concurrent_scrapers, thread_name_prefix="WebScraper"
        )

        # Request management
        self.pending_requests = queue.PriorityQueue()
        self.active_requests = {}
        self.completed_requests = {}
        self.requests_lock = RLock()

        # Rate limiting
        self.scraping_semaphore = Semaphore(max_concurrent_scrapers)
        self.last_request_times = {}  # URL domain -> last request time
        self.domain_delays = {
            "treasurer.maricopa.gov": 2.0,
            "recorder.maricopa.gov": 2.5,
            "mcassessor.maricopa.gov": 1.5,
            "default": 1.0,
        }

        # Performance tracking
        self.total_scraped = 0
        self.total_successful = 0
        self.total_failed = 0
        self.average_scraping_time = 0.0
        self.stats_lock = Lock()

        # Shutdown event
        self.shutdown_event = Event()

        logger.info(
            f"Parallel web scraper initialized - Max concurrent: {max_concurrent_scrapers}"
        )
    def submit_scraping_requests(self, requests: List[ScrapingRequest]) -> List[str]:
        """Submit multiple scraping requests for parallel processing"""
        request_ids = []

        with self.requests_lock:
            for request in requests:
                request_id = (
                    f"{request.task_type.value}_{request.identifier}_{int(time.time())}"
                )

                # Add to pending queue with priority
                priority_tuple = (request.priority, time.time())  # Priority, then FIFO
                self.pending_requests.put((priority_tuple, request_id, request))

                request_ids.append(request_id)

                logger.debug(f"Queued scraping request: {request_id}")

        # Start processing if not already running
        self._process_pending_requests()

        logger.info(f"Submitted {len(requests)} scraping requests")
        return request_ids
    def _process_pending_requests(self):
        """Process pending requests in thread pool"""
        # Submit processing task to executor
        self.executor.submit(self._request_processor_worker)
    def _request_processor_worker(self):
        """Background worker to process scraping requests"""
        while not self.shutdown_event.is_set():
    try:
                # Get next request with timeout
    try:
                    priority_tuple, request_id, request = self.pending_requests.get(
                        timeout=5.0
                    )
    except queue.Empty:
                    continue

                # Execute request with rate limiting
                future = self.executor.submit(
                    self._execute_scraping_request, request_id, request
                )

                with self.requests_lock:
                    self.active_requests[request_id] = (request, future)

                # Don't overwhelm - brief pause
                time.sleep(0.1)

    except Exception as e:
                logger.error(f"Error in request processor: {e}")
                time.sleep(1.0)
    def _execute_scraping_request(self, request_id: str, request: ScrapingRequest):
        """Execute a single scraping request"""
        start_time = time.time()
        request.started_at = datetime.now()

        logger.debug(f"Executing scraping request: {request_id}")

        # Rate limiting
        with self.scraping_semaphore:
            self._apply_rate_limit(request.task_type)

            browser = None
    try:
                # Acquire browser
                browser = self.browser_pool.acquire_browser(timeout=15.0)

                # Execute based on task type
                if request.task_type == ScrapingTask.TAX_INFORMATION:
                    result = self._scrape_tax_information(browser, request.identifier)
                elif request.task_type == ScrapingTask.SALES_HISTORY:
                    result = self._scrape_sales_history(browser, request.identifier)
                elif request.task_type == ScrapingTask.DOCUMENT_RECORDS:
                    result = self._scrape_document_records(browser, request.identifier)
                elif request.task_type == ScrapingTask.PROPERTY_DETAILS:
                    result = self._scrape_property_details(browser, request.identifier)
                elif request.task_type == ScrapingTask.OWNER_PROPERTIES:
                    result = self._scrape_owner_properties(browser, request.identifier)
                else:
                    raise ValueError(f"Unsupported task type: {request.task_type}")

                request.result = result
                request.completed_at = datetime.now()

                # Update statistics
                processing_time = time.time() - start_time
                with self.stats_lock:
                    self.total_scraped += 1
                    self.total_successful += 1
                    total_time = (
                        self.average_scraping_time * (self.total_scraped - 1)
                        + processing_time
                    )
                    self.average_scraping_time = total_time / self.total_scraped

                logger.info(
                    f"Scraping request completed successfully: {request_id} in {processing_time:.2f}s"
                )

    except Exception as e:
                request.error = str(e)
                request.completed_at = datetime.now()

                processing_time = time.time() - start_time
                with self.stats_lock:
                    self.total_scraped += 1
                    self.total_failed += 1

                logger.error(
                    f"Scraping request failed: {request_id} after {processing_time:.2f}s - {e}"
                )

    finally:
                # Release browser back to pool
                if browser:
                    self.browser_pool.release_browser(browser)

                # Move from active to completed
                with self.requests_lock:
                    if request_id in self.active_requests:
                        del self.active_requests[request_id]
                    self.completed_requests[request_id] = request
    def _apply_rate_limit(self, task_type: ScrapingTask):
        """Apply rate limiting based on task type"""
        # Determine target domain
        if task_type == ScrapingTask.TAX_INFORMATION:
            domain = "treasurer.maricopa.gov"
        elif task_type in [ScrapingTask.SALES_HISTORY, ScrapingTask.DOCUMENT_RECORDS]:
            domain = "recorder.maricopa.gov"
        else:
            domain = "default"

        # Check rate limit
        delay = self.domain_delays.get(domain, self.domain_delays["default"])
        last_time = self.last_request_times.get(domain, 0)
        current_time = time.time()

        if current_time - last_time < delay:
            sleep_time = delay - (current_time - last_time)
            logger.debug(f"Rate limiting {domain}: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self.last_request_times[domain] = time.time()
    def _scrape_tax_information(
        self, browser: webdriver.Chrome, apn: str
    ) -> Dict[str, Any]:
        """Scrape tax information using tax scraper"""
        if not self.enable_tax_scraping:
            raise ValueError("Tax scraping is disabled")

    try:
            # Navigate to tax site
            tax_url = f"https://treasurer.maricopa.gov/Parcel/{apn}"
            browser.get(tax_url)

            # Wait for page to load
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Extract tax data using existing tax scraper logic
            tax_scraper = MaricopaTaxScraper()
            result = tax_scraper.extract_tax_data_from_browser(browser, apn)

            return result or {}

    except Exception as e:
            logger.error(f"Tax scraping failed for APN {apn}: {e}")
            raise
    def _scrape_sales_history(
        self, browser: webdriver.Chrome, apn: str
    ) -> Dict[str, Any]:
        """Scrape sales history from recorder's office"""
        if not self.enable_recorder_scraping:
            raise ValueError("Recorder scraping is disabled")

    try:
            # Navigate to recorder site
            recorder_url = f"https://recorder.maricopa.gov/recdocdata/GetDocsByParcel.aspx?parcel={apn}"
            browser.get(recorder_url)

            # Wait for page to load
            WebDriverWait(browser, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Extract sales data using recorder scraper logic
            recorder_scraper = MaricopaRecorderScraper()
            result = recorder_scraper.extract_sales_history_from_browser(browser, apn)

            return result or {}

    except Exception as e:
            logger.error(f"Sales history scraping failed for APN {apn}: {e}")
            raise
    def _scrape_document_records(
        self, browser: webdriver.Chrome, apn: str
    ) -> Dict[str, Any]:
        """Scrape document records from recorder's office"""
        if not self.enable_recorder_scraping:
            raise ValueError("Recorder scraping is disabled")

    try:
            # Navigate to recorder documents page
            docs_url = f"https://recorder.maricopa.gov/recdocdata/GetDocsByParcel.aspx?parcel={apn}&DocTypeCode=All"
            browser.get(docs_url)

            # Wait for page to load
            WebDriverWait(browser, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Extract document records
            recorder_scraper = MaricopaRecorderScraper()
            result = recorder_scraper.extract_document_records_from_browser(
                browser, apn
            )

            return result or {}

    except Exception as e:
            logger.error(f"Document records scraping failed for APN {apn}: {e}")
            raise
    def _scrape_property_details(
        self, browser: webdriver.Chrome, apn: str
    ) -> Dict[str, Any]:
        """Scrape detailed property information"""
    try:
            # Navigate to assessor's property details page
            assessor_url = (
                f"https://mcassessor.maricopa.gov/parcel/parcel.asp?parcel={apn}"
            )
            browser.get(assessor_url)

            # Wait for page to load
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Extract property details
            property_data = {}

            # Try to extract basic information
    try:
                # Look for property address
                address_elements = browser.find_elements(
                    By.XPATH,
                    "//td[contains(text(), 'Property Address')]/following-sibling::td",
                )
                if address_elements:
                    property_data["property_address"] = address_elements[0].text.strip()

                # Look for owner information
                owner_elements = browser.find_elements(
                    By.XPATH, "//td[contains(text(), 'Owner')]/following-sibling::td"
                )
                if owner_elements:
                    property_data["owner_name"] = owner_elements[0].text.strip()

                # Look for legal description
                legal_elements = browser.find_elements(
                    By.XPATH, "//td[contains(text(), 'Legal')]/following-sibling::td"
                )
                if legal_elements:
                    property_data["legal_description"] = legal_elements[0].text.strip()

    except Exception as e:
                logger.warning(f"Error extracting some property details: {e}")

            return property_data

    except Exception as e:
            logger.error(f"Property details scraping failed for APN {apn}: {e}")
            raise
    def _scrape_owner_properties(
        self, browser: webdriver.Chrome, owner_name: str
    ) -> Dict[str, Any]:
        """Scrape all properties owned by a specific owner"""
    try:
            # Navigate to owner search page
            search_url = "https://mcassessor.maricopa.gov/search/searchownerform.asp"
            browser.get(search_url)

            # Wait for page to load
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.NAME, "owner"))
            )

            # Enter owner name and submit
            owner_input = browser.find_element(By.NAME, "owner")
            owner_input.clear()
            owner_input.send_keys(owner_name)

            submit_button = browser.find_element(By.XPATH, "//input[@type='submit']")
            submit_button.click()

            # Wait for results
            WebDriverWait(browser, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )

            # Extract property list
            properties = []
    try:
                # Look for results table
                tables = browser.find_elements(By.TAG_NAME, "table")
                for table in tables:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3:  # Assume APN, address, owner columns
                            property_info = {
                                "apn": cells[0].text.strip(),
                                "property_address": cells[1].text.strip(),
                                "owner_name": owner_name,
                            }
                            properties.append(property_info)
    except Exception as e:
                logger.warning(f"Error extracting owner properties: {e}")

            return {"properties": properties, "owner_name": owner_name}

    except Exception as e:
            logger.error(f"Owner properties scraping failed for {owner_name}: {e}")
            raise
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a scraping request"""
        with self.requests_lock:
            # Check completed requests first
            if request_id in self.completed_requests:
                request = self.completed_requests[request_id]
                return {
                    "request_id": request_id,
                    "status": "completed",
                    "task_type": request.task_type.value,
                    "identifier": request.identifier,
                    "started_at": (
                        request.started_at.isoformat() if request.started_at else None
                    ),
                    "completed_at": (
                        request.completed_at.isoformat()
                        if request.completed_at
                        else None
                    ),
                    "success": request.result is not None,
                    "error": request.error,
                    "retry_count": request.retry_count,
                }

            # Check active requests
            if request_id in self.active_requests:
                request, future = self.active_requests[request_id]
                return {
                    "request_id": request_id,
                    "status": "running",
                    "task_type": request.task_type.value,
                    "identifier": request.identifier,
                    "started_at": (
                        request.started_at.isoformat() if request.started_at else None
                    ),
                    "success": False,
                    "error": None,
                }

            return None
    def get_request_result(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get result from completed scraping request"""
        with self.requests_lock:
            if request_id in self.completed_requests:
                request = self.completed_requests[request_id]
                if request.result is not None:
                    return request.result
            return None
    def batch_scrape_tax_data(self, apns: List[str], priority: int = 5) -> List[str]:
        """Batch scrape tax data for multiple APNs"""
        requests = [
            ScrapingRequest(
                task_type=ScrapingTask.TAX_INFORMATION,
                identifier=apn,
                priority=priority,
            )
            for apn in apns
        ]

        return self.submit_scraping_requests(requests)
    def batch_scrape_sales_data(self, apns: List[str], priority: int = 5) -> List[str]:
        """Batch scrape sales history for multiple APNs"""
        requests = [
            ScrapingRequest(
                task_type=ScrapingTask.SALES_HISTORY, identifier=apn, priority=priority
            )
            for apn in apns
        ]

        return self.submit_scraping_requests(requests)
    def get_scraper_statistics(self) -> Dict[str, Any]:
        """Get comprehensive scraper statistics"""
        with self.stats_lock:
            success_rate = (self.total_successful / max(1, self.total_scraped)) * 100

            browser_stats = self.browser_pool.get_pool_status()

            with self.requests_lock:
                active_count = len(self.active_requests)
                completed_count = len(self.completed_requests)
                pending_count = self.pending_requests.qsize()

        return {
            "total_scraped": self.total_scraped,
            "total_successful": self.total_successful,
            "total_failed": self.total_failed,
            "success_rate_percent": success_rate,
            "average_scraping_time": self.average_scraping_time,
            "active_requests": active_count,
            "completed_requests": completed_count,
            "pending_requests": pending_count,
            "browser_pool": browser_stats,
            "max_concurrent_scrapers": self.max_concurrent_scrapers,
        }
    def shutdown(self):
        """Gracefully shutdown the parallel web scraper"""
        logger.info("Shutting down parallel web scraper...")

        self.shutdown_event.set()

        # Shutdown executor
        self.executor.shutdown(wait=True)

        # Close browser pool
        self.browser_pool.close_all()

        logger.info("Parallel web scraper shutdown completed")


class ParallelWebScrapingWorker(QThread):
    """Qt-based worker for parallel web scraping operations"""

    scraping_started = pyqtSignal(list)  # request_ids
    scraping_progress = pyqtSignal(str, dict)  # request_id, status
    scraping_completed = pyqtSignal(str, dict)  # request_id, result
    scraping_failed = pyqtSignal(str, str)  # request_id, error
    batch_completed = pyqtSignal(list)  # all_results
    def __init__(self, scraper_manager: ParallelWebScraperManager):
        super().__init__()
        self.scraper_manager = scraper_manager
        self.current_request_ids = []
    def start_batch_scraping(self, requests: List[ScrapingRequest]):
        """Start batch scraping in Qt thread"""
        self.requests = requests
        self.start()
    def run(self):
        """Execute batch scraping in background thread"""
    try:
            # Submit requests
            self.current_request_ids = self.scraper_manager.submit_scraping_requests(
                self.requests
            )
            self.scraping_started.emit(self.current_request_ids)

            # Monitor progress
            completed_requests = set()
            all_results = []

            while len(completed_requests) < len(self.current_request_ids):
                for request_id in self.current_request_ids:
                    if request_id in completed_requests:
                        continue

                    status = self.scraper_manager.get_request_status(request_id)
                    if status and status["status"] == "completed":
                        completed_requests.add(request_id)

                        if status["success"]:
                            result = self.scraper_manager.get_request_result(request_id)
                            self.scraping_completed.emit(request_id, result or {})
                            all_results.append(
                                {"request_id": request_id, "result": result}
                            )
                        else:
                            self.scraping_failed.emit(
                                request_id, status.get("error", "Unknown error")
                            )
                            all_results.append(
                                {"request_id": request_id, "error": status.get("error")}
                            )

                    elif status and status["status"] == "running":
                        self.scraping_progress.emit(request_id, status)

                self.msleep(2000)  # Check every 2 seconds

            self.batch_completed.emit(all_results)

    except Exception as e:
            logger.error(f"Parallel web scraping worker error: {e}")
            for request_id in self.current_request_ids:
                self.scraping_failed.emit(request_id, f"Worker error: {str(e)}")
