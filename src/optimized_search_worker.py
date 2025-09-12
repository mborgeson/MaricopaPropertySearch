"""
Optimized Search Worker
Enhanced background search worker with better thread management, caching, and error handling
"""

import time
import logging
from typing import Dict, List, Optional, Any
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
from dataclasses import asdict
import traceback

from src.search_cache import SearchCache, SearchHistory
from src.search_validator import SearchValidator, SearchType, ValidationResult, SearchFilters
from optimized_database_manager import OptimizedDatabaseManager

logger = logging.getLogger(__name__)

class OptimizedSearchWorker(QThread):
    """Enhanced background worker for property searches with caching and validation"""
    
    # Signals
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    results_ready = pyqtSignal(list, int)  # results, total_count
    error_occurred = pyqtSignal(str)
    validation_failed = pyqtSignal(str, list)  # error_message, suggestions
    search_completed = pyqtSignal(str, str, int, float)  # type, term, count, duration
    
    def __init__(self, search_term: str, search_type: SearchType, 
                 db_manager: OptimizedDatabaseManager, api_client, scraper,
                 filters: SearchFilters = None, use_cache: bool = True, fresh_data_only: bool = False):
        super().__init__()
        
        self.search_term = search_term
        self.search_type = search_type
        self.db_manager = db_manager
        self.api_client = api_client
        self.scraper = scraper
        self.filters = filters or SearchFilters()
        self.use_cache = use_cache and not fresh_data_only  # Disable cache if fresh data only
        self.fresh_data_only = fresh_data_only
        
        # Thread safety
        self._mutex = QMutex()
        self._is_cancelled = False
        
        # Components
        self.validator = SearchValidator()
        self.cache = SearchCache()
        self.history = SearchHistory()
        
        # Search configuration
        self.search_timeout = 30.0  # Maximum search time
        self.cache_ttl = 3600  # 1 hour cache TTL
        self.max_results = 1000
        
        logger.debug(f"Search worker initialized: {search_type.value} = '{search_term}'")
    
    def run(self):
        """Execute optimized search in background thread"""
        search_start_time = time.time()
        
        try:
            # Validate input first
            self.status_updated.emit("Validating search input...")
            validation = self._validate_input()
            
            if not validation.is_valid:
                self._handle_validation_failure(validation)
                return
            
            # Use sanitized input
            sanitized_term = validation.sanitized_input
            search_type = validation.search_type or self.search_type
            
            self.progress_updated.emit(10)
            
            # Skip cache check if fresh data only mode is enabled
            cached_results = None
            if self.use_cache and not self.fresh_data_only:
                self.status_updated.emit("Checking cache...")
                cached_results = self._check_cache(sanitized_term, search_type)
                
                if cached_results is not None:
                    self.progress_updated.emit(100)
                    self.status_updated.emit(f"Found {len(cached_results)} properties (cached)")
                    
                    # Apply client-side filtering if needed
                    filtered_results = self._apply_client_filters(cached_results)
                    
                    search_duration = time.time() - search_start_time
                    self.results_ready.emit(filtered_results, len(filtered_results))
                    self.search_completed.emit(search_type.value, sanitized_term, len(filtered_results), search_duration)
                    
                    # Still log to history
                    self.history.add_search(search_type.value, sanitized_term, len(filtered_results))
                    return
            elif self.fresh_data_only:
                self.status_updated.emit("Fresh data only mode - skipping cache...")
                logger.info(f"Fresh data only mode enabled for {search_type.value} search: {sanitized_term}")
            
            self.progress_updated.emit(20)
            
            # Perform live external search first if fresh data only, otherwise use database
            if self.fresh_data_only:
                self.status_updated.emit("Collecting fresh data from live sources...")
                db_results = self._search_external_sources_fresh(sanitized_term, search_type)
                total_count = len(db_results)
            else:
                # Perform database search
                db_results, total_count = self._search_database(sanitized_term, search_type)
            
            if self._is_cancelled:
                return
            
            self.progress_updated.emit(60)
            
            # If no database results and it's not an APN search, try external sources (unless fresh data only mode)
            if not db_results and search_type != SearchType.APN and not self.fresh_data_only:
                external_results = self._search_external_sources(sanitized_term, search_type)
                db_results.extend(external_results)
                total_count = len(db_results)
            elif not db_results and self.fresh_data_only:
                # In fresh data only mode, if first attempt failed, show clear message
                logger.warning(f"Fresh data collection returned no results for {search_type.value}: {sanitized_term}")
                self.status_updated.emit("No fresh data found from live sources")
            
            if self._is_cancelled:
                return
            
            self.progress_updated.emit(90)
            
            # Cache results for future use (only if not in fresh data only mode)
            if self.use_cache and db_results and not self.fresh_data_only:
                self._cache_results(sanitized_term, search_type, db_results)
            elif self.fresh_data_only and db_results:
                logger.info(f"Fresh data only mode - not caching {len(db_results)} results")
            
            # Log search
            self._log_search(search_type, sanitized_term, total_count)
            
            self.progress_updated.emit(100)
            search_duration = time.time() - search_start_time
            
            data_source_msg = " (fresh data)" if self.fresh_data_only else ""
            self.status_updated.emit(f"Found {total_count} properties in {search_duration:.2f}s{data_source_msg}")
            self.results_ready.emit(db_results, total_count)
            self.search_completed.emit(search_type.value, sanitized_term, total_count, search_duration)
            
            logger.info(f"Search completed: {search_type.value} '{sanitized_term}' -> {total_count} results in {search_duration:.2f}s")
            
        except Exception as e:
            search_duration = time.time() - search_start_time
            error_msg = f"Search failed: {str(e)}"
            
            logger.error(f"Search error after {search_duration:.2f}s: {e}")
            logger.debug(traceback.format_exc())
            
            self.error_occurred.emit(error_msg)
        
        finally:
            self.progress_updated.emit(0)  # Reset progress
    
    def cancel_search(self):
        """Cancel the current search operation"""
        with QMutexLocker(self._mutex):
            self._is_cancelled = True
            logger.info("Search cancellation requested")
    
    def _validate_input(self) -> ValidationResult:
        """Validate and sanitize search input"""
        return self.validator.validate_search_input(self.search_term, self.search_type)
    
    def _handle_validation_failure(self, validation: ValidationResult):
        """Handle validation failures with helpful suggestions"""
        error_message = "; ".join(validation.errors)
        
        # Get suggestions for correction
        suggestions = self.validator.get_search_suggestions(self.search_term)
        
        # Auto-detect search type if possible
        detected_type = self.validator.auto_detect_search_type(self.search_term)
        if detected_type and detected_type != self.search_type:
            error_message += f" (Did you mean to search by {detected_type.value}?)"
        
        self.validation_failed.emit(error_message, suggestions.get(self.search_type.value, []))
        logger.warning(f"Validation failed: {error_message}")
    
    def _check_cache(self, search_term: str, search_type: SearchType) -> Optional[List[Dict]]:
        """Check cache for existing results"""
        try:
            filters_dict = asdict(self.filters) if self.filters else None
            return self.cache.get(search_type.value, search_term, filters_dict)
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
            return None
    
    def _search_database(self, search_term: str, search_type: SearchType) -> tuple[List[Dict], int]:
        """Search database with advanced filtering"""
        self.status_updated.emit("Searching database...")
        
        try:
            results, total_count = self.db_manager.advanced_property_search(
                search_term=search_term,
                search_type=search_type,
                filters=self.filters,
                limit=self.max_results
            )
            
            logger.debug(f"Database search returned {len(results)}/{total_count} results")
            return results, total_count
            
        except Exception as e:
            logger.error(f"Database search failed: {e}")
            return [], 0
    
    def _search_external_sources(self, search_term: str, search_type: SearchType) -> List[Dict]:
        """Search external API and web sources"""
        external_results = []
        
        try:
            if self._is_cancelled:
                return []
            
            # API search
            self.status_updated.emit("Searching API...")
            if search_type == SearchType.OWNER:
                api_results = self.api_client.search_by_owner(search_term, limit=50)
            elif search_type == SearchType.ADDRESS:
                api_results = self.api_client.search_by_address(search_term, limit=50)
            else:
                api_results = []
            
            # Store new properties in database
            for prop in api_results:
                self.db_manager.insert_property(prop)
            
            external_results.extend(api_results)
            
            if self._is_cancelled:
                return external_results
            
            # Web scraping fallback (only if still no results)
            if not external_results and search_type in [SearchType.OWNER, SearchType.APN]:
                self.status_updated.emit("Web scraping...")
                self.progress_updated.emit(75)
                
                if search_type == SearchType.OWNER:
                    scrape_results = self.scraper.search_by_owner_name(search_term)
                else:  # APN
                    scrape_result = self.scraper.scrape_property_by_apn(search_term)
                    scrape_results = [scrape_result] if scrape_result else []
                
                external_results.extend(scrape_results)
            
        except Exception as e:
            logger.error(f"External search failed: {e}")
        
        logger.debug(f"External sources returned {len(external_results)} results")
        return external_results
    
    def _search_external_sources_fresh(self, search_term: str, search_type: SearchType) -> List[Dict]:
        """Search external sources with fresh data priority (no database fallback)"""
        fresh_results = []
        
        try:
            if self._is_cancelled:
                return []
            
            # Force fresh API search first
            self.status_updated.emit("Fetching fresh data from API...")
            self.progress_updated.emit(40)
            
            if search_type == SearchType.OWNER:
                api_results = self.api_client.search_by_owner(search_term, limit=100)
            elif search_type == SearchType.ADDRESS:
                api_results = self.api_client.search_by_address(search_term, limit=100)
            elif search_type == SearchType.APN:
                # For APN, get comprehensive fresh data
                api_result = self.api_client.get_comprehensive_property_info(search_term)
                api_results = [api_result] if api_result else []
            else:
                api_results = []
            
            fresh_results.extend(api_results)
            logger.info(f"Fresh API search returned {len(api_results)} results")
            
            if self._is_cancelled:
                return fresh_results
            
            # If no API results, try web scraping for additional fresh data
            if not fresh_results and search_type in [SearchType.OWNER, SearchType.APN]:
                self.status_updated.emit("Collecting fresh data via web scraping...")
                self.progress_updated.emit(70)
                
                if search_type == SearchType.OWNER:
                    scrape_results = self.scraper.search_by_owner_name(search_term)
                else:  # APN
                    scrape_result = self.scraper.scrape_property_by_apn(search_term)
                    scrape_results = [scrape_result] if scrape_result else []
                
                fresh_results.extend(scrape_results)
                logger.info(f"Fresh web scraping returned {len(scrape_results)} results")
            
            # Save fresh data to database for future reference
            if fresh_results:
                self.status_updated.emit("Saving fresh data to database...")
                for prop in fresh_results:
                    try:
                        self.db_manager.insert_property(prop)
                    except Exception as e:
                        logger.warning(f"Failed to save fresh property data: {e}")
                
                logger.info(f"Saved {len(fresh_results)} fresh properties to database")
            
        except Exception as e:
            logger.error(f"Fresh external search failed: {e}")
            # In fresh data only mode, we don't fall back to cached data
        
        logger.info(f"Fresh data collection returned {len(fresh_results)} total results")
        return fresh_results
    
    def _apply_client_filters(self, results: List[Dict]) -> List[Dict]:
        """Apply additional client-side filtering to cached results"""
        if not self.filters or not results:
            return results
        
        filtered = []
        
        for result in results:
            # Apply year built filter
            if self.filters.year_built_min and result.get('year_built'):
                if result['year_built'] < self.filters.year_built_min:
                    continue
                    
            if self.filters.year_built_max and result.get('year_built'):
                if result['year_built'] > self.filters.year_built_max:
                    continue
            
            # Apply living area filter
            if self.filters.living_area_min and result.get('living_area_sqft'):
                if result['living_area_sqft'] < self.filters.living_area_min:
                    continue
                    
            if self.filters.living_area_max and result.get('living_area_sqft'):
                if result['living_area_sqft'] > self.filters.living_area_max:
                    continue
            
            # Pool filter
            if self.filters.has_pool is not None:
                if result.get('pool', False) != self.filters.has_pool:
                    continue
            
            # Land use codes filter
            if self.filters.land_use_codes:
                if result.get('land_use_code') not in self.filters.land_use_codes:
                    continue
            
            filtered.append(result)
        
        return filtered
    
    def _cache_results(self, search_term: str, search_type: SearchType, results: List[Dict]):
        """Cache search results for future use"""
        try:
            filters_dict = asdict(self.filters) if self.filters else None
            self.cache.put(
                search_type=search_type.value,
                search_term=search_term,
                results=results,
                filters=filters_dict,
                ttl=self.cache_ttl
            )
            logger.debug(f"Cached {len(results)} results for {search_type.value}: '{search_term}'")
        except Exception as e:
            logger.warning(f"Failed to cache results: {e}")
    
    def _log_search(self, search_type: SearchType, search_term: str, results_count: int):
        """Log search for analytics and history"""
        try:
            # Database logging
            self.db_manager.log_search(search_type.value, search_term, results_count)
            
            # In-memory history
            self.history.add_search(search_type.value, search_term, results_count)
            
        except Exception as e:
            logger.warning(f"Failed to log search: {e}")
    
    def get_search_suggestions(self, partial_term: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on history and database"""
        suggestions = []
        
        try:
            # Get from history
            history_suggestions = self.history.get_suggestions(
                partial_term, self.search_type.value, limit // 2
            )
            suggestions.extend(history_suggestions)
            
            # Get from database
            db_suggestions = self.db_manager.get_property_suggestions(
                partial_term, self.search_type, limit - len(suggestions)
            )
            suggestions.extend(db_suggestions)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_suggestions = []
            for item in suggestions:
                if item.lower() not in seen:
                    seen.add(item.lower())
                    unique_suggestions.append(item)
            
            return unique_suggestions[:limit]
            
        except Exception as e:
            logger.warning(f"Failed to get suggestions: {e}")
            return []
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache.get_stats()
    
    def clear_cache(self):
        """Clear search cache"""
        try:
            self.cache.invalidate()
            logger.info("Search cache cleared")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")


class SearchWorkerPool:
    """Pool manager for search workers to handle concurrent searches"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.active_workers = []
        self._mutex = QMutex()
    
    def submit_search(self, search_term: str, search_type: SearchType,
                     db_manager: OptimizedDatabaseManager, api_client, scraper,
                     filters: SearchFilters = None, use_cache: bool = True, fresh_data_only: bool = False) -> OptimizedSearchWorker:
        """Submit a new search request"""
        
        with QMutexLocker(self._mutex):
            # Cancel and clean up finished workers
            self._cleanup_workers()
            
            # Check if we're at capacity
            if len(self.active_workers) >= self.max_workers:
                # Cancel oldest worker
                oldest_worker = self.active_workers[0]
                oldest_worker.cancel_search()
                oldest_worker.wait(1000)  # Wait up to 1 second
                self.active_workers.remove(oldest_worker)
            
            # Create new worker
            worker = OptimizedSearchWorker(
                search_term=search_term,
                search_type=search_type,
                db_manager=db_manager,
                api_client=api_client,
                scraper=scraper,
                filters=filters,
                use_cache=use_cache,
                fresh_data_only=fresh_data_only
            )
            
            # Connect cleanup signal
            worker.finished.connect(lambda: self._worker_finished(worker))
            
            self.active_workers.append(worker)
            return worker
    
    def _cleanup_workers(self):
        """Remove finished workers from active list"""
        self.active_workers = [w for w in self.active_workers if w.isRunning()]
    
    def _worker_finished(self, worker: OptimizedSearchWorker):
        """Handle worker completion"""
        with QMutexLocker(self._mutex):
            if worker in self.active_workers:
                self.active_workers.remove(worker)
    
    def cancel_all(self):
        """Cancel all active searches"""
        with QMutexLocker(self._mutex):
            for worker in self.active_workers:
                worker.cancel_search()
            
            # Wait for all to finish
            for worker in self.active_workers:
                worker.wait(2000)  # 2 second timeout
            
            self.active_workers.clear()
    
    def get_active_count(self) -> int:
        """Get number of active workers"""
        with QMutexLocker(self._mutex):
            self._cleanup_workers()
            return len(self.active_workers)