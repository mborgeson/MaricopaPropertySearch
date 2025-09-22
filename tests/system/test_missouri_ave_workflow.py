#!/usr/bin/env python3
"""
Missouri Avenue Workflow System Test
Tests the complete end-to-end workflow for Missouri Avenue property search
"""

import sys
import os
import pytest
import asyncio
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.api_client_unified import UnifiedMaricopaAPIClient
from src.unified_data_collector import UnifiedDataCollector
from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.enhanced_config_manager import EnhancedConfigManager


class TestMissouriAveWorkflow:
    """System tests for Missouri Avenue property workflow"""

    def setup_method(self):
        """Setup for each test method"""
        self.config = EnhancedConfigManager()
        self.api_client = UnifiedMaricopaAPIClient(self.config)
        self.data_collector = UnifiedDataCollector(self.api_client, self.config)
        self.db_manager = ThreadSafeDatabaseManager(self.config)

    def teardown_method(self):
        """Cleanup after each test method"""
        if hasattr(self, "db_manager"):
            self.db_manager.close()

    @pytest.mark.missouri_ave
    def test_missouri_avenue_address_search(self):
        """Test searching for Missouri Avenue address - core workflow"""
        # Test data based on validated workflow
        test_address = "10000 W Missouri Ave"
        expected_apn = "10215009"

        # Perform address search
        start_time = time.time()
        results = self.api_client.search_by_address(test_address)
        search_time = time.time() - start_time

        # Validate results
        assert results is not None, "Search should return results"
        assert isinstance(results, list), "Results should be a list"
        assert len(results) > 0, "Should find at least one property"

        # Validate performance (should be under 1 second for basic search)
        assert search_time < 1.0, f"Search took {search_time:.3f}s, should be < 1.0s"

        # Find the target property
        target_property = None
        for prop in results:
            if prop.get("apn") == expected_apn:
                target_property = prop
                break

        assert (
            target_property is not None
        ), f"Should find property with APN {expected_apn}"

        # Validate property data structure
        required_fields = ["apn", "address", "owner_name"]
        for field in required_fields:
            assert field in target_property, f"Property should have '{field}' field"

    @pytest.mark.missouri_ave
    def test_missouri_avenue_apn_search(self):
        """Test searching by APN for Missouri Avenue property"""
        test_apn = "10215009"

        # Perform APN search
        start_time = time.time()
        result = self.api_client.search_by_apn(test_apn)
        search_time = time.time() - start_time

        # Validate results
        assert result is not None, "APN search should return a result"
        assert isinstance(result, dict), "Result should be a dictionary"
        assert (
            result.get("apn") == test_apn
        ), f"Result APN should match search APN {test_apn}"

        # Validate performance (should be very fast for APN search)
        assert (
            search_time < 0.5
        ), f"APN search took {search_time:.3f}s, should be < 0.5s"

        # Validate property details
        assert "address" in result, "Property should have address"
        assert "owner_name" in result, "Property should have owner name"
        assert "Missouri" in result.get(
            "address", ""
        ), "Address should contain 'Missouri'"

    @pytest.mark.missouri_ave
    def test_missouri_avenue_detailed_collection(self):
        """Test detailed data collection for Missouri Avenue property"""
        test_apn = "10215009"

        # Get basic property info first
        basic_result = self.api_client.search_by_apn(test_apn)
        assert basic_result is not None, "Should get basic property info"

        # Perform detailed data collection
        start_time = time.time()
        detailed_result = self.data_collector.collect_detailed_property_data(test_apn)
        collection_time = time.time() - start_time

        # Validate detailed results
        assert detailed_result is not None, "Detailed collection should return results"
        assert isinstance(
            detailed_result, dict
        ), "Detailed result should be a dictionary"

        # Validate performance (detailed collection can take longer)
        assert (
            collection_time < 5.0
        ), f"Detailed collection took {collection_time:.3f}s, should be < 5.0s"

        # Validate enhanced data fields
        enhanced_fields = ["tax_history", "sales_history", "assessment_data"]
        for field in enhanced_fields:
            # These fields should exist, even if empty
            assert (
                field in detailed_result
            ), f"Detailed result should have '{field}' field"

    @pytest.mark.missouri_ave
    def test_missouri_avenue_background_processing(self):
        """Test background data processing for Missouri Avenue property"""
        test_apn = "10215009"

        # Start background collection
        start_time = time.time()
        collection_id = self.data_collector.start_background_collection([test_apn])

        # Wait for initial processing
        time.sleep(1.0)

        # Check progress
        progress = self.data_collector.get_collection_progress(collection_id)
        assert progress is not None, "Should get progress information"
        assert "completed" in progress, "Progress should have completion status"
        assert "total" in progress, "Progress should have total count"

        # Wait for completion (with timeout)
        timeout = 10.0
        while time.time() - start_time < timeout:
            progress = self.data_collector.get_collection_progress(collection_id)
            if progress.get("completed", 0) >= progress.get("total", 1):
                break
            time.sleep(0.5)

        collection_time = time.time() - start_time

        # Validate completion
        final_progress = self.data_collector.get_collection_progress(collection_id)
        assert (
            final_progress.get("completed", 0) > 0
        ), "Should have completed some processing"

        # Get final results
        results = self.data_collector.get_collection_results(collection_id)
        assert results is not None, "Should get collection results"
        assert len(results) > 0, "Should have at least one result"

        # Validate performance
        assert (
            collection_time < 15.0
        ), f"Background collection took {collection_time:.3f}s, should be < 15.0s"

    @pytest.mark.missouri_ave
    def test_missouri_avenue_database_integration(self):
        """Test database operations for Missouri Avenue property"""
        test_apn = "10215009"

        # Get property data
        property_data = self.api_client.search_by_apn(test_apn)
        assert property_data is not None, "Should get property data"

        # Test database storage (in mock mode)
        if self.db_manager.is_mock_mode():
            # In mock mode, test the interface
            success = self.db_manager.store_property_data(test_apn, property_data)
            assert success, "Should successfully store property data in mock mode"

            # Test retrieval
            retrieved_data = self.db_manager.get_property_data(test_apn)
            assert retrieved_data is not None, "Should retrieve stored property data"
            assert retrieved_data.get("apn") == test_apn, "Retrieved APN should match"
        else:
            # In real database mode, test actual operations
            success = self.db_manager.store_property_data(test_apn, property_data)
            assert success, "Should successfully store property data"

            # Test retrieval
            retrieved_data = self.db_manager.get_property_data(test_apn)
            assert retrieved_data is not None, "Should retrieve stored property data"
            assert (
                retrieved_data.get("apn") == test_apn
            ), "Retrieved APN should match stored APN"

    @pytest.mark.missouri_ave
    def test_missouri_avenue_error_handling(self):
        """Test error handling in Missouri Avenue workflow"""
        # Test invalid APN handling
        invalid_apn = "99999999"

        result = self.api_client.search_by_apn(invalid_apn)
        # Should handle gracefully (either return None or empty result)
        assert (
            result is None or result == {}
        ), "Invalid APN should return None or empty result"

        # Test invalid address handling
        invalid_address = "123 Nonexistent Street"

        results = self.api_client.search_by_address(invalid_address)
        # Should handle gracefully (return empty list)
        assert isinstance(results, list), "Invalid address search should return a list"
        assert len(results) == 0, "Invalid address should return empty results"

    @pytest.mark.missouri_ave
    def test_missouri_avenue_performance_baseline(self):
        """Test performance baseline for Missouri Avenue workflow"""
        test_apn = "10215009"

        # Test multiple searches to establish baseline
        search_times = []

        for i in range(3):
            start_time = time.time()
            result = self.api_client.search_by_apn(test_apn)
            search_time = time.time() - start_time
            search_times.append(search_time)

            assert result is not None, f"Search {i+1} should return results"
            time.sleep(0.1)  # Small delay between searches

        # Calculate average search time
        avg_search_time = sum(search_times) / len(search_times)
        max_search_time = max(search_times)

        # Validate performance benchmarks
        assert (
            avg_search_time < 0.5
        ), f"Average search time {avg_search_time:.3f}s should be < 0.5s"
        assert (
            max_search_time < 1.0
        ), f"Max search time {max_search_time:.3f}s should be < 1.0s"

        print(
            f"Performance baseline - Avg: {avg_search_time:.3f}s, Max: {max_search_time:.3f}s"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "missouri_ave"])
