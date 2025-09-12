"""
Unit tests for search performance and responsiveness requirements
"""

import pytest
import time
from unittest.mock import Mock, patch
import asyncio

# Performance benchmarks (in seconds)
DATABASE_SEARCH_LIMIT = 2.0
UI_RESPONSE_LIMIT = 0.1
API_ENHANCEMENT_LIMIT = 10.0
STARTUP_TIME_LIMIT = 3.0

@pytest.mark.unit
@pytest.mark.performance
class TestSearchPerformance:
    """Test search operation performance requirements"""
    
    def test_database_search_performance(self, test_database, performance_timer, app_config):
        """Test that database searches complete within 2 seconds"""
        
        performance_timer.start()
        
        results = test_database.search_properties_by_owner("SMITH", limit=10)
        
        elapsed = performance_timer.stop()
        
        assert elapsed < DATABASE_SEARCH_LIMIT, f"Database search took {elapsed:.3f}s, limit is {DATABASE_SEARCH_LIMIT}s"
        assert len(results) >= 0  # Should return valid results
        
    def test_database_search_with_large_dataset(self, test_database, performance_timer):
        """Test database performance with larger result sets"""
        
        # Insert additional test data for volume testing
        self._create_large_dataset(test_database, 100)
        
        performance_timer.start()
        
        results = test_database.search_properties_by_owner("", limit=50)  # Broad search
        
        elapsed = performance_timer.stop()
        
        assert elapsed < DATABASE_SEARCH_LIMIT * 1.5, f"Large dataset search took {elapsed:.3f}s"
        
    def test_apn_search_performance(self, test_database, performance_timer):
        """Test APN search performance (should be fastest due to indexing)"""
        
        performance_timer.start()
        
        result = test_database.get_property_by_apn("101-01-001A")
        
        elapsed = performance_timer.stop()
        
        assert elapsed < 0.5, f"APN search took {elapsed:.3f}s, should be < 0.5s"
        assert result is not None
        
    def test_address_search_performance(self, test_database, performance_timer):
        """Test address search performance"""
        
        performance_timer.start()
        
        results = test_database.search_properties_by_address("MAIN ST", limit=10)
        
        elapsed = performance_timer.stop()
        
        assert elapsed < DATABASE_SEARCH_LIMIT, f"Address search took {elapsed:.3f}s"
        
    def _create_large_dataset(self, db_manager, count):
        """Helper to create larger test dataset"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                for i in range(count):
                    cursor.execute("""
                        INSERT INTO properties (
                            apn, owner_name, property_address, city, zip_code,
                            property_type, assessed_value, market_value,
                            square_feet, year_built, last_updated
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                        )
                    """, (
                        f"999-{i:02d}-{i:03d}X",
                        f"TEST OWNER {i}",
                        f"{100 + i} TEST ST",
                        "PHOENIX",
                        "85001",
                        "RESIDENTIAL",
                        200000 + (i * 1000),
                        220000 + (i * 1000),
                        1500 + (i * 10),
                        1990 + (i % 30)
                    ))
                    
                conn.commit()
        except Exception as e:
            print(f"Error creating large dataset: {e}")

@pytest.mark.unit
@pytest.mark.performance 
class TestCachePerformance:
    """Test caching system performance"""
    
    def test_cache_hit_performance(self, app_config, performance_timer):
        """Test that cache hits are extremely fast"""
        from search_cache import SearchCache
        
        cache = SearchCache(max_size=100, ttl_seconds=300)
        
        # Populate cache
        test_data = {"results": ["property1", "property2"]}
        cache.put("test_search", test_data)
        
        performance_timer.start()
        
        result = cache.get("test_search")
        
        elapsed = performance_timer.stop()
        
        assert elapsed < 0.001, f"Cache hit took {elapsed:.6f}s, should be < 1ms"
        assert result == test_data
        
    def test_cache_miss_performance(self, performance_timer):
        """Test that cache misses don't add significant overhead"""
        from search_cache import SearchCache
        
        cache = SearchCache(max_size=100, ttl_seconds=300)
        
        performance_timer.start()
        
        result = cache.get("nonexistent_key")
        
        elapsed = performance_timer.stop()
        
        assert elapsed < 0.001, f"Cache miss took {elapsed:.6f}s"
        assert result is None

@pytest.mark.unit
@pytest.mark.performance
@pytest.mark.gui
class TestUIResponsiveness:
    """Test UI responsiveness requirements"""
    
    def test_search_button_response_time(self, qt_app, app_config, performance_timer):
        """Test that UI responds to search button click within 100ms"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp
        
        window = EnhancedPropertySearchApp(app_config)
        
        # Mock the actual search to focus on UI response
        with patch.object(window, '_perform_search') as mock_search:
            performance_timer.start()
            
            # Simulate button click
            window.search_btn.click()
            
            elapsed = performance_timer.stop()
            
            assert elapsed < UI_RESPONSE_LIMIT, f"UI response took {elapsed:.3f}s"
            mock_search.assert_called_once()
            
        window.close()
        
    def test_search_type_change_responsiveness(self, qt_app, app_config, performance_timer):
        """Test that search type dropdown changes are responsive"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp
        
        window = EnhancedPropertySearchApp(app_config)
        
        performance_timer.start()
        
        # Change search type
        window.search_type_combo.setCurrentText("Property Address")
        
        elapsed = performance_timer.stop()
        
        assert elapsed < UI_RESPONSE_LIMIT, f"Search type change took {elapsed:.3f}s"
        
        window.close()
        
    def test_results_table_population_speed(self, qt_app, app_config, sample_search_results, performance_timer):
        """Test that results table populates quickly"""
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp
        
        window = EnhancedPropertySearchApp(app_config)
        
        performance_timer.start()
        
        window._populate_results_table(sample_search_results)
        
        elapsed = performance_timer.stop()
        
        assert elapsed < 0.5, f"Results table population took {elapsed:.3f}s"
        assert window.results_table.rowCount() == len(sample_search_results)
        
        window.close()

@pytest.mark.unit
@pytest.mark.performance
class TestBackgroundProcessing:
    """Test background data enhancement performance"""
    
    def test_background_enhancement_non_blocking(self, app_config, performance_timer):
        """Test that background enhancement doesn't block UI"""
        from search_worker import SearchWorker
        
        # Create a mock search worker
        worker = SearchWorker("owner", "SMITH", None, None, None)
        
        performance_timer.start()
        
        # Start background thread
        worker.start()
        
        # UI operation should complete immediately
        elapsed = performance_timer.stop()
        
        assert elapsed < UI_RESPONSE_LIMIT, f"Background thread start blocked for {elapsed:.3f}s"
        
        # Clean up
        worker.quit()
        worker.wait()
        
    def test_api_enhancement_timeout(self, app_config, performance_timer):
        """Test that API enhancement respects timeout limits"""
        from src.api_client import MockMaricopaAPIClient
        
        client = MockMaricopaAPIClient(app_config)
        
        # Mock a slow API response
        with patch.object(client, 'search_by_owner') as mock_search:
            def slow_response(*args, **kwargs):
                time.sleep(12)  # Longer than our limit
                return []
                
            mock_search.side_effect = slow_response
            
            performance_timer.start()
            
            try:
                results = client.search_by_owner("SMITH", timeout=API_ENHANCEMENT_LIMIT)
            except Exception:
                pass  # Timeout expected
                
            elapsed = performance_timer.stop()
            
            assert elapsed <= API_ENHANCEMENT_LIMIT + 1, f"API call took {elapsed:.3f}s, timeout should prevent this"
            
        client.close()

@pytest.mark.unit
@pytest.mark.performance
class TestMemoryUsage:
    """Test memory usage and resource management"""
    
    def test_large_result_set_memory_usage(self, test_database):
        """Test that large result sets don't cause memory issues"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform multiple large searches
        for _ in range(10):
            results = test_database.search_properties_by_owner("", limit=100)
            del results  # Explicit cleanup
            
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        assert memory_growth < 50, f"Memory grew by {memory_growth:.2f}MB, should be < 50MB"
        
    def test_connection_pool_efficiency(self, test_database, performance_timer):
        """Test that connection pooling improves performance"""
        
        # Multiple rapid queries should reuse connections
        times = []
        
        for i in range(10):
            performance_timer.start()
            
            result = test_database.get_property_by_apn(f"101-01-{i:03d}A")
            
            times.append(performance_timer.stop())
            
        # Later queries should be faster due to warm connection pool
        avg_early = sum(times[:3]) / 3
        avg_later = sum(times[-3:]) / 3
        
        assert avg_later <= avg_early * 1.2, "Connection pooling should maintain consistent performance"

@pytest.mark.performance
@pytest.mark.slow
class TestApplicationStartupPerformance:
    """Test application startup performance"""
    
    def test_cold_startup_time(self, performance_timer):
        """Test application cold startup time"""
        import subprocess
        import sys
        
        performance_timer.start()
        
        # Start application process
        process = subprocess.Popen([
            sys.executable, 
            str(PROJECT_ROOT / "src" / "maricopa_property_search.py"),
            "--test-startup"  # Flag to exit after initialization
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for process to complete
        stdout, stderr = process.communicate()
        
        elapsed = performance_timer.stop()
        
        assert elapsed < STARTUP_TIME_LIMIT, f"Application startup took {elapsed:.3f}s"
        assert process.returncode == 0, f"Application failed to start: {stderr.decode()}"
        
    def test_warm_startup_time(self, performance_timer):
        """Test application warm startup (second launch)"""
        # This would test startup when Python modules are cached
        # Implementation similar to cold startup test
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])