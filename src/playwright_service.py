"""
Playwright Service for Enhanced Browser Automation
Phase 6 Advanced Features - Cross-browser automation with intelligent fallback
Integrates with existing UnifiedMaricopaAPIClient for enhanced data collection
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock, Event
from pathlib import Path
import tempfile
import os
from urllib.parse import urljoin, urlparse

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    from playwright.sync_api import sync_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    # Fallback to None types for type hints
    Browser = BrowserContext = Page = None

from .logging_config import get_api_logger

logger = get_api_logger(__name__)


@dataclass
class BrowserConfig:
    """Configuration for browser instances"""

    browser_type: str = "chromium"  # chromium, firefox, webkit
    headless: bool = True
    viewport: Dict[str, int] = field(
        default_factory=lambda: {"width": 1920, "height": 1080}
    )
    timeout: int = 30000  # 30 seconds
    slow_mo: int = 0  # Delay between actions in ms
    user_agent: Optional[str] = None
    proxy: Optional[Dict[str, str]] = None


@dataclass
class ScrapingResult:
    """Result from browser automation operation"""

    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    screenshots: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: float = 0.0
    browser_used: str = ""


class BrowserPool:
    """Manages a pool of browser instances for efficient resource usage"""

    def __init__(
        self, max_browsers: int = 3, browser_configs: List[BrowserConfig] = None
    ):
        self.max_browsers = max_browsers
        self.browser_configs = browser_configs or [BrowserConfig()]
        self.active_browsers: Dict[str, Browser] = {}
        self.browser_contexts: Dict[str, List[BrowserContext]] = {}
        self.lock = Lock()

        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available - browser automation disabled")

    async def get_browser(self, browser_type: str = "chromium") -> Optional[Browser]:
        """Get or create a browser instance"""
        if not PLAYWRIGHT_AVAILABLE:
            return None

        async with self.lock:
            if browser_type not in self.active_browsers:
                if len(self.active_browsers) >= self.max_browsers:
                    # Close oldest browser
                    oldest_key = next(iter(self.active_browsers))
                    await self.close_browser(oldest_key)

                config = next(
                    (c for c in self.browser_configs if c.browser_type == browser_type),
                    BrowserConfig(browser_type=browser_type),
                )

                playwright = await async_playwright().start()
                browser_launcher = getattr(playwright, browser_type)

                browser = await browser_launcher.launch(
                    headless=config.headless, slow_mo=config.slow_mo, proxy=config.proxy
                )

                self.active_browsers[browser_type] = browser
                self.browser_contexts[browser_type] = []

                logger.info(f"Created new {browser_type} browser instance")

            return self.active_browsers[browser_type]

    async def get_context(
        self, browser_type: str = "chromium"
    ) -> Optional[BrowserContext]:
        """Get or create a browser context"""
        browser = await self.get_browser(browser_type)
        if not browser:
            return None

        config = next(
            (c for c in self.browser_configs if c.browser_type == browser_type),
            BrowserConfig(browser_type=browser_type),
        )

        context = await browser.new_context(
            viewport=config.viewport, user_agent=config.user_agent
        )

        # Set default timeout
        context.set_default_timeout(config.timeout)

        self.browser_contexts[browser_type].append(context)
        return context

    async def close_browser(self, browser_type: str):
        """Close a specific browser and its contexts"""
        if browser_type in self.active_browsers:
            # Close all contexts first
            if browser_type in self.browser_contexts:
                for context in self.browser_contexts[browser_type]:
                    await context.close()
                del self.browser_contexts[browser_type]

            # Close browser
            await self.active_browsers[browser_type].close()
            del self.active_browsers[browser_type]

            logger.info(f"Closed {browser_type} browser instance")

    async def close_all(self):
        """Close all browsers and contexts"""
        for browser_type in list(self.active_browsers.keys()):
            await self.close_browser(browser_type)


class PlaywrightService:
    """
    Advanced browser automation service for property data collection
    Provides enhanced web scraping capabilities beyond traditional methods
    """

    def __init__(
        self,
        browser_configs: List[BrowserConfig] = None,
        screenshot_dir: str = None,
        max_browsers: int = 3,
    ):

        self.browser_pool = BrowserPool(max_browsers, browser_configs)
        self.screenshot_dir = (
            Path(screenshot_dir)
            if screenshot_dir
            else Path(tempfile.gettempdir()) / "maricopa_screenshots"
        )
        self.screenshot_dir.mkdir(exist_ok=True)

        # Performance tracking
        self.performance_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
        }

        logger.info(
            f"Playwright service initialized - Available: {PLAYWRIGHT_AVAILABLE}"
        )
        logger.info(f"Screenshot directory: {self.screenshot_dir}")

    async def search_property_enhanced(
        self,
        identifier: str,
        search_type: str = "apn",
        capture_screenshots: bool = True,
        browser_type: str = "chromium",
    ) -> ScrapingResult:
        """
        Enhanced property search using browser automation

        Args:
            identifier: Property identifier (APN, address, etc.)
            search_type: Type of search ('apn', 'address', 'owner')
            capture_screenshots: Whether to capture screenshots
            browser_type: Browser to use ('chromium', 'firefox', 'webkit')

        Returns:
            ScrapingResult with enhanced property data
        """
        start_time = time.time()

        if not PLAYWRIGHT_AVAILABLE:
            return ScrapingResult(
                success=False,
                error="Playwright not available",
                execution_time=time.time() - start_time,
            )

        try:
            context = await self.browser_pool.get_context(browser_type)
            if not context:
                return ScrapingResult(
                    success=False,
                    error=f"Could not create {browser_type} browser context",
                    execution_time=time.time() - start_time,
                )

            page = await context.new_page()

            # Navigate to property search page
            search_url = self._build_search_url(identifier, search_type)
            await page.goto(search_url, wait_until="networkidle")

            # Wait for dynamic content to load
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)  # Additional wait for JavaScript

            # Extract property data
            property_data = await self._extract_property_data(page, search_type)

            # Capture screenshots if requested
            screenshots = []
            if capture_screenshots:
                screenshots = await self._capture_property_screenshots(page, identifier)

            # Get performance metrics
            performance_metrics = await self._get_performance_metrics(page)

            await page.close()

            execution_time = time.time() - start_time

            # Update stats
            self.performance_stats["total_requests"] += 1
            self.performance_stats["successful_requests"] += 1

            return ScrapingResult(
                success=True,
                data=property_data,
                screenshots=screenshots,
                performance_metrics=performance_metrics,
                execution_time=execution_time,
                browser_used=browser_type,
            )

        except Exception as e:
            execution_time = time.time() - start_time

            # Update stats
            self.performance_stats["total_requests"] += 1
            self.performance_stats["failed_requests"] += 1

            logger.error(f"Playwright search failed for {identifier}: {str(e)}")

            return ScrapingResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                browser_used=browser_type,
            )

    def _build_search_url(self, identifier: str, search_type: str) -> str:
        """Build appropriate search URL based on search type"""
        base_url = "https://mcassessor.maricopa.gov"

        if search_type == "apn":
            return f"{base_url}/parcel/{identifier}"
        elif search_type == "address":
            # Build address search URL
            return f"{base_url}/search?address={identifier.replace(' ', '+')}"
        elif search_type == "owner":
            return f"{base_url}/search?owner={identifier.replace(' ', '+')}"
        else:
            return f"{base_url}/search?q={identifier.replace(' ', '+')}"

    async def _extract_property_data(
        self, page: Page, search_type: str
    ) -> Dict[str, Any]:
        """Extract property data from the page"""
        data = {}

        try:
            # Wait for property information to load
            await page.wait_for_selector(
                ".property-info, .parcel-info, .assessment-info", timeout=10000
            )

            # Extract basic property information
            data["apn"] = await self._safe_text_content(
                page, '[data-field="apn"], .apn-value, #parcel-number'
            )
            data["address"] = await self._safe_text_content(
                page, '[data-field="address"], .property-address, .parcel-address'
            )
            data["owner"] = await self._safe_text_content(
                page, '[data-field="owner"], .owner-name, .property-owner'
            )

            # Extract assessment information
            data["assessed_value"] = await self._safe_text_content(
                page, '[data-field="assessed-value"], .assessed-value'
            )
            data["market_value"] = await self._safe_text_content(
                page, '[data-field="market-value"], .market-value'
            )
            data["property_type"] = await self._safe_text_content(
                page, '[data-field="property-type"], .property-type'
            )

            # Extract property characteristics
            data["year_built"] = await self._safe_text_content(
                page, '[data-field="year-built"], .year-built'
            )
            data["square_feet"] = await self._safe_text_content(
                page, '[data-field="square-feet"], .square-feet'
            )
            data["lot_size"] = await self._safe_text_content(
                page, '[data-field="lot-size"], .lot-size'
            )

            # Extract dynamic content that might not be available via API
            data["legal_description"] = await self._safe_text_content(
                page, ".legal-description, .legal-desc"
            )
            data["zoning"] = await self._safe_text_content(
                page, ".zoning-info, .zoning"
            )
            data["subdivision"] = await self._safe_text_content(
                page, ".subdivision-info, .subdivision"
            )

            # Extract tax information if available
            tax_elements = await page.query_selector_all(".tax-info tr, .tax-record")
            if tax_elements:
                data["tax_records"] = []
                for element in tax_elements[:5]:  # Limit to recent records
                    tax_text = await element.text_content()
                    if tax_text and tax_text.strip():
                        data["tax_records"].append(tax_text.strip())

            logger.info(f"Extracted {len(data)} fields from property page")

        except Exception as e:
            logger.warning(f"Error extracting property data: {str(e)}")
            data["extraction_error"] = str(e)

        return data

    async def _safe_text_content(self, page: Page, selector: str) -> Optional[str]:
        """Safely extract text content from an element"""
        try:
            element = await page.query_selector(selector)
            if element:
                text = await element.text_content()
                return text.strip() if text else None
        except Exception:
            pass
        return None

    async def _capture_property_screenshots(
        self, page: Page, identifier: str
    ) -> List[str]:
        """Capture screenshots of property information"""
        screenshots = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            # Full page screenshot
            full_screenshot_path = (
                self.screenshot_dir / f"{identifier}_{timestamp}_full.png"
            )
            await page.screenshot(path=str(full_screenshot_path), full_page=True)
            screenshots.append(str(full_screenshot_path))

            # Property details section
            details_element = await page.query_selector(
                ".property-details, .parcel-details, .assessment-details"
            )
            if details_element:
                details_screenshot_path = (
                    self.screenshot_dir / f"{identifier}_{timestamp}_details.png"
                )
                await details_element.screenshot(path=str(details_screenshot_path))
                screenshots.append(str(details_screenshot_path))

            # Map section if available
            map_element = await page.query_selector(
                ".map-container, .property-map, #map"
            )
            if map_element:
                map_screenshot_path = (
                    self.screenshot_dir / f"{identifier}_{timestamp}_map.png"
                )
                await map_element.screenshot(path=str(map_screenshot_path))
                screenshots.append(str(map_screenshot_path))

            logger.info(f"Captured {len(screenshots)} screenshots for {identifier}")

        except Exception as e:
            logger.warning(f"Error capturing screenshots: {str(e)}")

        return screenshots

    async def _get_performance_metrics(self, page: Page) -> Dict[str, float]:
        """Get page performance metrics"""
        try:
            # Get performance timing data
            timing_data = await page.evaluate(
                """
                () => {
                    const timing = performance.timing;
                    return {
                        load_time: timing.loadEventEnd - timing.navigationStart,
                        dom_ready: timing.domContentLoadedEventEnd - timing.navigationStart,
                        first_byte: timing.responseStart - timing.navigationStart,
                        connect_time: timing.connectEnd - timing.connectStart
                    };
                }
            """
            )

            return {
                "load_time_ms": timing_data.get("load_time", 0),
                "dom_ready_ms": timing_data.get("dom_ready", 0),
                "first_byte_ms": timing_data.get("first_byte", 0),
                "connect_time_ms": timing_data.get("connect_time", 0),
            }

        except Exception as e:
            logger.warning(f"Error getting performance metrics: {str(e)}")
            return {}

    async def automate_complex_search(
        self, search_criteria: Dict[str, Any], browser_type: str = "chromium"
    ) -> ScrapingResult:
        """
        Automate complex search forms with multiple criteria

        Args:
            search_criteria: Dictionary with search parameters
            browser_type: Browser to use

        Returns:
            ScrapingResult with search results
        """
        start_time = time.time()

        if not PLAYWRIGHT_AVAILABLE:
            return ScrapingResult(
                success=False,
                error="Playwright not available",
                execution_time=time.time() - start_time,
            )

        try:
            context = await self.browser_pool.get_context(browser_type)
            if not context:
                return ScrapingResult(
                    success=False,
                    error=f"Could not create {browser_type} browser context",
                )

            page = await context.new_page()

            # Navigate to advanced search page
            advanced_search_url = "https://mcassessor.maricopa.gov/advanced-search"
            await page.goto(advanced_search_url, wait_until="networkidle")

            # Fill out search form
            await self._fill_search_form(page, search_criteria)

            # Submit search
            await page.click(
                'input[type="submit"], button[type="submit"], .search-button'
            )
            await page.wait_for_load_state("networkidle")

            # Extract results
            results = await self._extract_search_results(page)

            await page.close()

            execution_time = time.time() - start_time

            return ScrapingResult(
                success=True,
                data={"search_results": results, "criteria": search_criteria},
                execution_time=execution_time,
                browser_used=browser_type,
            )

        except Exception as e:
            execution_time = time.time() - start_time

            logger.error(f"Complex search automation failed: {str(e)}")

            return ScrapingResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                browser_used=browser_type,
            )

    async def _fill_search_form(self, page: Page, criteria: Dict[str, Any]):
        """Fill out complex search form fields"""

        # Owner name
        if "owner_name" in criteria:
            await page.fill('input[name="owner"], #owner-name', criteria["owner_name"])

        # Address
        if "address" in criteria:
            await page.fill(
                'input[name="address"], #property-address', criteria["address"]
            )

        # Date ranges
        if "sale_date_from" in criteria:
            await page.fill(
                'input[name="sale_date_from"], #sale-date-from',
                criteria["sale_date_from"],
            )

        if "sale_date_to" in criteria:
            await page.fill(
                'input[name="sale_date_to"], #sale-date-to', criteria["sale_date_to"]
            )

        # Value ranges
        if "assessed_value_min" in criteria:
            await page.fill(
                'input[name="assessed_min"], #assessed-value-min',
                str(criteria["assessed_value_min"]),
            )

        if "assessed_value_max" in criteria:
            await page.fill(
                'input[name="assessed_max"], #assessed-value-max',
                str(criteria["assessed_value_max"]),
            )

        # Property characteristics
        if "property_type" in criteria:
            await page.select_option(
                'select[name="property_type"], #property-type',
                criteria["property_type"],
            )

        if "year_built_min" in criteria:
            await page.fill(
                'input[name="year_built_min"], #year-built-min',
                str(criteria["year_built_min"]),
            )

    async def _extract_search_results(self, page: Page) -> List[Dict[str, Any]]:
        """Extract search results from results page"""
        results = []

        try:
            # Wait for results to load
            await page.wait_for_selector(
                ".search-results, .results-table, .property-results", timeout=10000
            )

            # Extract result rows
            result_elements = await page.query_selector_all(
                ".result-row, tr.property-row, .property-result"
            )

            for element in result_elements:
                result_data = {}

                # Extract common fields
                apn_element = await element.query_selector('.apn, [data-field="apn"]')
                if apn_element:
                    result_data["apn"] = await apn_element.text_content()

                address_element = await element.query_selector(
                    '.address, [data-field="address"]'
                )
                if address_element:
                    result_data["address"] = await address_element.text_content()

                owner_element = await element.query_selector(
                    '.owner, [data-field="owner"]'
                )
                if owner_element:
                    result_data["owner"] = await owner_element.text_content()

                value_element = await element.query_selector(
                    '.value, [data-field="assessed-value"]'
                )
                if value_element:
                    result_data["assessed_value"] = await value_element.text_content()

                if result_data:  # Only add if we extracted some data
                    results.append(result_data)

            logger.info(f"Extracted {len(results)} search results")

        except Exception as e:
            logger.warning(f"Error extracting search results: {str(e)}")

        return results

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get service performance statistics"""
        total_requests = self.performance_stats["total_requests"]

        if total_requests > 0:
            success_rate = (
                self.performance_stats["successful_requests"] / total_requests
            )
            failure_rate = self.performance_stats["failed_requests"] / total_requests
        else:
            success_rate = failure_rate = 0.0

        return {
            **self.performance_stats,
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "playwright_available": PLAYWRIGHT_AVAILABLE,
        }

    async def cleanup(self):
        """Clean up resources"""
        await self.browser_pool.close_all()
        logger.info("Playwright service cleaned up")


# Sync wrapper for easier integration with existing sync code
class SyncPlaywrightService:
    """Synchronous wrapper for PlaywrightService"""

    def __init__(self, *args, **kwargs):
        self.async_service = PlaywrightService(*args, **kwargs)
        self._loop = None

    def _get_event_loop(self):
        """Get or create event loop for sync operations"""
        if self._loop is None:
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    def search_property_enhanced(self, *args, **kwargs) -> ScrapingResult:
        """Sync wrapper for enhanced property search"""
        loop = self._get_event_loop()
        return loop.run_until_complete(
            self.async_service.search_property_enhanced(*args, **kwargs)
        )

    def automate_complex_search(self, *args, **kwargs) -> ScrapingResult:
        """Sync wrapper for complex search automation"""
        loop = self._get_event_loop()
        return loop.run_until_complete(
            self.async_service.automate_complex_search(*args, **kwargs)
        )

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.async_service.get_performance_stats()

    def cleanup(self):
        """Clean up resources"""
        loop = self._get_event_loop()
        loop.run_until_complete(self.async_service.cleanup())
