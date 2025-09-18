"""
Enhanced Maricopa County API Client with Playwright Integration
Phase 6 Advanced Features - Extends UnifiedMaricopaAPIClient with browser automation
Provides intelligent fallback from API → Playwright → Web Scraping
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from pathlib import Path

# Import base unified client
from .api_client_unified import (
    UnifiedMaricopaAPIClient,
    PropertyDataCache,
    BatchAPIRequest,
    AdaptiveRateLimiter,
)

# Import Playwright service
from .playwright_service import PlaywrightService, SyncPlaywrightService, ScrapingResult

# Import logging
from .logging_config import get_api_logger

logger = get_api_logger(__name__)


@dataclass
class EnhancedSearchRequest:
    """Enhanced search request with Playwright options"""

    identifier: str
    search_type: str = "apn"  # 'apn', 'address', 'owner'
    use_playwright: bool = True
    capture_screenshots: bool = False
    browser_type: str = "chromium"
    fallback_to_api: bool = True
    fallback_to_scraping: bool = True
    priority: int = 5
    timeout: int = 30


@dataclass
class EnhancedSearchResult:
    """Enhanced search result with multiple data sources"""

    identifier: str
    search_type: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    data_sources: List[str] = field(
        default_factory=list
    )  # ['api', 'playwright', 'scraping']
    screenshots: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class EnhancedMaricopaAPIClient(UnifiedMaricopaAPIClient):
    """
    Enhanced API client with Playwright integration
    Extends UnifiedMaricopaAPIClient with advanced browser automation capabilities
    """

    def __init__(
        self,
        api_token: str = None,
        enable_playwright: bool = True,
        playwright_config: Dict[str, Any] = None,
        screenshot_dir: str = None,
        **kwargs,
    ):

        # Initialize base client
        super().__init__(api_token=api_token, **kwargs)

        # Playwright service configuration
        self.enable_playwright = enable_playwright
        self.playwright_service = None
        self.sync_playwright = None

        if enable_playwright:
            try:
                # Initialize Playwright service
                playwright_config = playwright_config or {}
                self.playwright_service = PlaywrightService(
                    screenshot_dir=screenshot_dir, **playwright_config
                )
                self.sync_playwright = SyncPlaywrightService(
                    screenshot_dir=screenshot_dir, **playwright_config
                )

                logger.info("Enhanced API client initialized with Playwright support")

            except Exception as e:
                logger.warning(f"Playwright initialization failed: {str(e)}")
                self.enable_playwright = False

        # Enhanced statistics
        self.enhanced_stats = {
            "total_enhanced_requests": 0,
            "playwright_requests": 0,
            "api_fallback_requests": 0,
            "scraping_fallback_requests": 0,
            "hybrid_data_sources": 0,
            "screenshot_captures": 0,
        }

    def search_property_enhanced(
        self,
        identifier: str,
        search_type: str = "apn",
        use_playwright: bool = True,
        capture_screenshots: bool = False,
        browser_type: str = "chromium",
        enable_fallback: bool = True,
    ) -> EnhancedSearchResult:
        """
        Enhanced property search with intelligent fallback strategy

        Strategy:
        1. Try Playwright for enhanced data collection (if enabled)
        2. Fallback to API client if Playwright fails
        3. Fallback to traditional web scraping if API fails
        4. Merge data from multiple sources if available

        Args:
            identifier: Property identifier (APN, address, owner name)
            search_type: Type of search ('apn', 'address', 'owner')
            use_playwright: Whether to use Playwright for enhanced collection
            capture_screenshots: Whether to capture property screenshots
            browser_type: Browser to use for Playwright ('chromium', 'firefox', 'webkit')
            enable_fallback: Whether to fallback to other methods if primary fails

        Returns:
            EnhancedSearchResult with data from multiple sources
        """
        start_time = time.time()

        self.enhanced_stats["total_enhanced_requests"] += 1

        result = EnhancedSearchResult(
            identifier=identifier, search_type=search_type, success=False
        )

        data_collected = {}
        sources_used = []
        warnings = []
        screenshots = []

        # Strategy 1: Try Playwright for enhanced data collection
        if use_playwright and self.enable_playwright and self.sync_playwright:
            try:
                logger.info(f"Attempting Playwright search for {identifier}")

                playwright_result = self.sync_playwright.search_property_enhanced(
                    identifier=identifier,
                    search_type=search_type,
                    capture_screenshots=capture_screenshots,
                    browser_type=browser_type,
                )

                if playwright_result.success:
                    data_collected.update(playwright_result.data)
                    sources_used.append("playwright")
                    screenshots.extend(playwright_result.screenshots)

                    result.performance_metrics["playwright"] = (
                        playwright_result.performance_metrics
                    )

                    self.enhanced_stats["playwright_requests"] += 1
                    if playwright_result.screenshots:
                        self.enhanced_stats["screenshot_captures"] += 1

                    logger.info(f"Playwright search successful for {identifier}")

                else:
                    warnings.append(
                        f"Playwright search failed: {playwright_result.error}"
                    )
                    logger.warning(
                        f"Playwright search failed for {identifier}: {playwright_result.error}"
                    )

            except Exception as e:
                warnings.append(f"Playwright error: {str(e)}")
                logger.error(f"Playwright search error for {identifier}: {str(e)}")

        # Strategy 2: Fallback to API client (always try for comparison/backup)
        if enable_fallback or not data_collected:
            try:
                logger.info(f"Attempting API search for {identifier}")

                if search_type == "apn":
                    api_result = self.search_by_apn(identifier)
                elif search_type == "address":
                    api_result = self.search_by_address(identifier)
                elif search_type == "owner":
                    api_result = self.search_by_owner(identifier)
                else:
                    raise ValueError(f"Unknown search type: {search_type}")

                if api_result.get("success", False):
                    # Merge API data with existing data
                    api_data = api_result.get("data", {})

                    # Add API-specific data or fill gaps
                    for key, value in api_data.items():
                        if key not in data_collected or not data_collected[key]:
                            data_collected[key] = value

                    sources_used.append("api")

                    result.performance_metrics["api"] = {
                        "response_time_ms": api_result.get("response_time", 0) * 1000
                    }

                    self.enhanced_stats["api_fallback_requests"] += 1

                    logger.info(f"API search successful for {identifier}")

                else:
                    warnings.append(
                        f"API search failed: {api_result.get('error', 'Unknown error')}"
                    )
                    logger.warning(f"API search failed for {identifier}")

            except Exception as e:
                warnings.append(f"API error: {str(e)}")
                logger.error(f"API search error for {identifier}: {str(e)}")

        # Strategy 3: Fallback to traditional web scraping (if available)
        if enable_fallback and not data_collected and hasattr(self, "web_scraper"):
            try:
                logger.info(f"Attempting web scraping fallback for {identifier}")

                scraper_result = self.web_scraper.scrape_property_data(
                    identifier, search_type
                )

                if scraper_result and scraper_result.get("success", False):
                    scraper_data = scraper_result.get("data", {})

                    for key, value in scraper_data.items():
                        if key not in data_collected or not data_collected[key]:
                            data_collected[key] = value

                    sources_used.append("scraping")
                    self.enhanced_stats["scraping_fallback_requests"] += 1

                    logger.info(f"Web scraping successful for {identifier}")

                else:
                    warnings.append("Web scraping fallback failed")

            except Exception as e:
                warnings.append(f"Web scraping error: {str(e)}")
                logger.error(f"Web scraping error for {identifier}: {str(e)}")

        # Compile final result
        execution_time = time.time() - start_time

        if data_collected:
            result.success = True
            result.data = data_collected
            result.data_sources = sources_used
            result.screenshots = screenshots
            result.execution_time = execution_time
            result.warnings = warnings

            # Track hybrid data collection
            if len(sources_used) > 1:
                self.enhanced_stats["hybrid_data_sources"] += 1

            logger.info(
                f"Enhanced search successful for {identifier} using sources: {sources_used}"
            )

        else:
            result.success = False
            result.error = "All search methods failed"
            result.warnings = warnings
            result.execution_time = execution_time

            logger.error(f"All search methods failed for {identifier}")

        return result

    def batch_search_enhanced(
        self,
        requests: List[EnhancedSearchRequest],
        max_workers: int = 5,
        progress_callback: Optional[callable] = None,
    ) -> List[EnhancedSearchResult]:
        """
        Enhanced batch search with parallel processing and progress tracking

        Args:
            requests: List of enhanced search requests
            max_workers: Maximum number of parallel workers
            progress_callback: Optional callback for progress updates

        Returns:
            List of enhanced search results
        """
        logger.info(f"Starting enhanced batch search for {len(requests)} requests")

        results = []
        completed = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all requests
            future_to_request = {
                executor.submit(
                    self.search_property_enhanced,
                    req.identifier,
                    req.search_type,
                    req.use_playwright,
                    req.capture_screenshots,
                    req.browser_type,
                    req.fallback_to_api or req.fallback_to_scraping,
                ): req
                for req in requests
            }

            # Collect results as they complete
            for future in as_completed(future_to_request):
                request = future_to_request[future]

                try:
                    result = future.result(timeout=request.timeout)
                    results.append(result)

                except Exception as e:
                    # Create error result
                    error_result = EnhancedSearchResult(
                        identifier=request.identifier,
                        search_type=request.search_type,
                        success=False,
                        error=str(e),
                    )
                    results.append(error_result)

                    logger.error(
                        f"Batch search failed for {request.identifier}: {str(e)}"
                    )

                completed += 1

                # Progress callback
                if progress_callback:
                    progress_callback(completed, len(requests))

        logger.info(
            f"Enhanced batch search completed: {completed}/{len(requests)} processed"
        )

        return results

    def search_with_complex_criteria(
        self,
        criteria: Dict[str, Any],
        use_playwright: bool = True,
        browser_type: str = "chromium",
    ) -> EnhancedSearchResult:
        """
        Search using complex criteria via Playwright automation

        Args:
            criteria: Dictionary with search criteria
            use_playwright: Whether to use Playwright for automation
            browser_type: Browser to use

        Returns:
            EnhancedSearchResult with search results
        """
        start_time = time.time()

        if not use_playwright or not self.enable_playwright or not self.sync_playwright:
            return EnhancedSearchResult(
                identifier=str(criteria),
                search_type="complex",
                success=False,
                error="Playwright not available for complex search",
                execution_time=time.time() - start_time,
            )

        try:
            logger.info(f"Performing complex search with criteria: {criteria}")

            playwright_result = self.sync_playwright.automate_complex_search(
                search_criteria=criteria, browser_type=browser_type
            )

            execution_time = time.time() - start_time

            if playwright_result.success:
                return EnhancedSearchResult(
                    identifier=str(criteria),
                    search_type="complex",
                    success=True,
                    data=playwright_result.data,
                    data_sources=["playwright"],
                    performance_metrics={
                        "playwright": playwright_result.performance_metrics
                    },
                    execution_time=execution_time,
                )
            else:
                return EnhancedSearchResult(
                    identifier=str(criteria),
                    search_type="complex",
                    success=False,
                    error=playwright_result.error,
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time

            logger.error(f"Complex search failed: {str(e)}")

            return EnhancedSearchResult(
                identifier=str(criteria),
                search_type="complex",
                success=False,
                error=str(e),
                execution_time=execution_time,
            )

    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics including enhanced features"""
        base_stats = self.get_statistics()

        # Add Playwright stats if available
        playwright_stats = {}
        if self.sync_playwright:
            playwright_stats = self.sync_playwright.get_performance_stats()

        return {
            **base_stats,
            "enhanced_features": self.enhanced_stats,
            "playwright_service": playwright_stats,
            "playwright_enabled": self.enable_playwright,
        }

    def cleanup(self):
        """Clean up resources including Playwright service"""
        # Clean up base client resources
        super().cleanup()

        # Clean up Playwright service
        if self.sync_playwright:
            self.sync_playwright.cleanup()

        if self.playwright_service:
            # This requires async cleanup - schedule for next event loop
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.playwright_service.cleanup())
            except RuntimeError:
                # If no event loop is running, use run_until_complete
                asyncio.run(self.playwright_service.cleanup())

        logger.info("Enhanced API client cleanup completed")


# Convenience functions for common enhanced operations
def enhanced_property_search(
    identifier: str,
    search_type: str = "apn",
    enable_playwright: bool = True,
    capture_screenshots: bool = False,
) -> EnhancedSearchResult:
    """
    Convenience function for enhanced property search

    Args:
        identifier: Property identifier
        search_type: Type of search
        enable_playwright: Whether to use Playwright
        capture_screenshots: Whether to capture screenshots

    Returns:
        Enhanced search result
    """
    client = EnhancedMaricopaAPIClient(enable_playwright=enable_playwright)

    try:
        return client.search_property_enhanced(
            identifier=identifier,
            search_type=search_type,
            use_playwright=enable_playwright,
            capture_screenshots=capture_screenshots,
        )
    finally:
        client.cleanup()


def enhanced_batch_search(
    identifiers: List[str],
    search_type: str = "apn",
    enable_playwright: bool = True,
    max_workers: int = 3,
) -> List[EnhancedSearchResult]:
    """
    Convenience function for enhanced batch search

    Args:
        identifiers: List of property identifiers
        search_type: Type of search
        enable_playwright: Whether to use Playwright
        max_workers: Maximum parallel workers

    Returns:
        List of enhanced search results
    """
    client = EnhancedMaricopaAPIClient(enable_playwright=enable_playwright)

    try:
        requests = [
            EnhancedSearchRequest(
                identifier=identifier,
                search_type=search_type,
                use_playwright=enable_playwright,
            )
            for identifier in identifiers
        ]

        return client.batch_search_enhanced(requests, max_workers=max_workers)

    finally:
        client.cleanup()
