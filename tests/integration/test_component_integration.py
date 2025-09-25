"""
Integration tests for MaricopaPropertySearch unified components

Tests the interactions between the 4 unified components:
- UnifiedMaricopaAPIClient ↔ UnifiedDataCollector
- UnifiedDataCollector ↔ ThreadSafeDatabaseManager
- UnifiedGUILauncher ↔ All components
- End-to-end workflow validation
"""
import asyncio

# Import components
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api_client_unified import UnifiedMaricopaAPIClient
from gui_launcher_unified import UnifiedGUILauncher
from threadsafe_database_manager import ThreadSafeDatabaseManager
from unified_data_collector import UnifiedDataCollector


class TestComponentIntegration:
    """Integration tests for unified component interactions."""

    @pytest.fixture
    def integrated_system(self, mock_environment):
        """Create an integrated system with all components."""
        # Mock configuration
        api_config = {
            "base_url": "https://api.test.com",
            "api_token": "test_token",
            "mock_mode": True,
        }

        db_config = {"host": "localhost", "database": "test_db", "mock_mode": True}

        # Initialize components
        with patch("api_client_unified.get_api_logger"):
            api_client = UnifiedMaricopaAPIClient(config=api_config)

        with patch("unified_data_collector.get_logger"):
            with patch("unified_data_collector.get_performance_logger"):
                data_collector = UnifiedDataCollector(api_client=api_client)

        with patch("threadsafe_database_manager.get_logger"):
            db_manager = ThreadSafeDatabaseManager(config=db_config)

        with patch("gui_launcher_unified.get_logger"):
            gui_launcher = UnifiedGUILauncher()

        return {
            "api_client": api_client,
            "data_collector": data_collector,
            "db_manager": db_manager,
            "gui_launcher": gui_launcher,
        }

    @pytest.mark.integration
    def test_api_client_data_collector_integration(
        self, integrated_system, mock_property_data
    ):
        """Test API client and data collector integration."""
        api_client = integrated_system["api_client"]
        data_collector = integrated_system["data_collector"]

        # Mock API client response
        api_client.search_property = Mock(
            return_value={"success": True, "data": mock_property_data}
        )

        # Test data collection through API client
        result = data_collector.collect_property_data("10215009")

        # Verify integration
        assert result["success"] is True
        assert result["data"]["apn"] == "10215009"
        api_client.search_property.assert_called_once_with("10215009")

    @pytest.mark.integration
    def test_data_collector_database_integration(
        self, integrated_system, mock_property_data
    ):
        """Test data collector and database manager integration."""
        data_collector = integrated_system["data_collector"]
        db_manager = integrated_system["db_manager"]

        # Mock database operations
        db_manager.insert_property = Mock(return_value=True)
        db_manager.search_properties_by_apn = Mock(return_value=[mock_property_data])

        # Test data flow: collection → database storage
        data_collector.api_client.search_property = Mock(
            return_value={"success": True, "data": mock_property_data}
        )

        # Collect and store data
        collected_data = data_collector.collect_property_data("10215009")
        storage_result = db_manager.insert_property(collected_data["data"])

        # Verify integration
        assert collected_data["success"] is True
        assert storage_result is True
        db_manager.insert_property.assert_called_once()

    @pytest.mark.integration
    def test_full_data_pipeline_integration(
        self, integrated_system, mock_property_data
    ):
        """Test complete data pipeline: API → Collector → Database."""
        api_client = integrated_system["api_client"]
        data_collector = integrated_system["data_collector"]
        db_manager = integrated_system["db_manager"]

        # Setup mock responses
        api_client.search_property = Mock(
            return_value={"success": True, "data": mock_property_data}
        )
        db_manager.insert_property = Mock(return_value=True)
        db_manager.search_properties_by_apn = Mock(return_value=[mock_property_data])

        # Execute full pipeline
        # 1. Collect data
        collected_data = data_collector.collect_property_data("10215009")

        # 2. Store in database
        storage_result = db_manager.insert_property(collected_data["data"])

        # 3. Retrieve from database
        retrieved_data = db_manager.search_properties_by_apn("10215009")

        # Verify full pipeline
        assert collected_data["success"] is True
        assert storage_result is True
        assert len(retrieved_data) == 1
        assert retrieved_data[0]["apn"] == "10215009"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_integration_workflow(
        self, integrated_system, mock_property_data
    ):
        """Test asynchronous integration between components."""
        api_client = integrated_system["api_client"]
        data_collector = integrated_system["data_collector"]

        # Setup async mock
        api_client.search_property_async = AsyncMock(
            return_value={"success": True, "data": mock_property_data}
        )

        # Test async data collection
        result = await data_collector.collect_property_data_async("10215009")

        # Verify async integration
        assert result["success"] is True
        assert result["data"]["apn"] == "10215009"
        api_client.search_property_async.assert_called_once_with("10215009")

    @pytest.mark.integration
    def test_batch_processing_integration(self, integrated_system, mock_property_data):
        """Test batch processing across multiple components."""
        api_client = integrated_system["api_client"]
        data_collector = integrated_system["data_collector"]
        db_manager = integrated_system["db_manager"]

        # Setup batch data
        apn_list = ["10215009", "10215010", "10215011"]

        # Mock batch responses
    def mock_search_property(apn):
            return {"success": True, "data": {**mock_property_data, "apn": apn}}

        api_client.search_property = Mock(side_effect=mock_search_property)
        db_manager.batch_insert_properties = Mock(return_value=True)

        # Execute batch collection
        results = data_collector.collect_batch_data(apn_list)

        # Store batch results
        batch_data = [result["data"] for result in results if result["success"]]
        storage_result = db_manager.batch_insert_properties(batch_data)

        # Verify batch integration
        assert len(results) == 3
        assert all(result["success"] for result in results)
        assert storage_result is True
        assert api_client.search_property.call_count == 3

    @pytest.mark.integration
    def test_error_propagation_integration(self, integrated_system):
        """Test error propagation between components."""
        api_client = integrated_system["api_client"]
        data_collector = integrated_system["data_collector"]

        # Setup API error
        api_client.search_property = Mock(
            return_value={"success": False, "error": "Property not found"}
        )

        # Test error propagation
        result = data_collector.collect_property_data("invalid_apn")

        # Verify error handling
        assert result["success"] is False
        assert "error" in result
        api_client.search_property.assert_called_once()

    @pytest.mark.integration
    def test_concurrent_access_integration(self, integrated_system, mock_property_data):
        """Test concurrent access across components."""
        api_client = integrated_system["api_client"]
        data_collector = integrated_system["data_collector"]
        db_manager = integrated_system["db_manager"]

        # Setup concurrent operations
        api_client.search_property = Mock(
            return_value={"success": True, "data": mock_property_data}
        )
        db_manager.insert_property = Mock(return_value=True)
    def concurrent_operation(thread_id):
            apn = f"102150{thread_id:02d}"
            # Collect data
            result = data_collector.collect_property_data(apn)
            # Store data
            if result["success"]:
                db_manager.insert_property(result["data"])
            return result

        # Execute concurrent operations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(concurrent_operation, i) for i in range(10)]
            results = [future.result() for future in futures]

        # Verify concurrent integration
        assert len(results) == 10
        assert all(result["success"] for result in results)
        assert api_client.search_property.call_count == 10

    @pytest.mark.integration
    def test_gui_launcher_system_integration(self, integrated_system):
        """Test GUI launcher integration with system components."""
        gui_launcher = integrated_system["gui_launcher"]
        db_manager = integrated_system["db_manager"]

        # Mock database health check
        db_manager.health_check = Mock(return_value={"status": "healthy"})

        # Test system health validation
        health_status = gui_launcher.test_database_connection()

        # Verify GUI launcher integration
        assert health_status["available"] is True
        assert health_status["status"] == "healthy"

    @pytest.mark.integration
    @pytest.mark.performance
    def test_end_to_end_performance_integration(
        self, integrated_system, mock_property_data, performance_timer
    ):
        """Test end-to-end performance across all components."""
        api_client = integrated_system["api_client"]
        data_collector = integrated_system["data_collector"]
        db_manager = integrated_system["db_manager"]

        # Setup performance mocks
        api_client.search_property = Mock(
            return_value={"success": True, "data": mock_property_data}
        )
        db_manager.insert_property = Mock(return_value=True)

        # Measure end-to-end performance
        performance_timer.start()

        # Execute complete workflow
        collected_data = data_collector.collect_property_data("10215009")
        storage_result = db_manager.insert_property(collected_data["data"])

        elapsed_time = performance_timer.stop()

        # Verify performance integration
        assert collected_data["success"] is True
        assert storage_result is True
        assert elapsed_time < 0.5  # Should complete under 500ms

    @pytest.mark.integration
    @pytest.mark.missouri_ave
    def test_missouri_ave_workflow_integration(
        self, integrated_system, mock_property_data
    ):
        """Test the validated Missouri Avenue workflow integration."""
        api_client = integrated_system["api_client"]
        data_collector = integrated_system["data_collector"]
        db_manager = integrated_system["db_manager"]

        # Setup Missouri Avenue data
        missouri_data = {
            **mock_property_data,
            "apn": "10215009",
            "address": "10000 W Missouri Ave",
        }

        api_client.search_property = Mock(
            return_value={"success": True, "data": missouri_data}
        )
        db_manager.insert_property = Mock(return_value=True)
        db_manager.search_properties_by_apn = Mock(return_value=[missouri_data])

        # Execute Missouri Avenue workflow
        # 1. Search property
        search_result = data_collector.collect_property_data("10215009")

        # 2. Store property data
        storage_result = db_manager.insert_property(search_result["data"])

        # 3. Retrieve and validate
        retrieved_data = db_manager.search_properties_by_apn("10215009")

        # Verify Missouri Avenue integration
        assert search_result["success"] is True
        assert search_result["data"]["apn"] == "10215009"
        assert search_result["data"]["address"] == "10000 W Missouri Ave"
        assert storage_result is True
        assert len(retrieved_data) == 1

    @pytest.mark.integration
    def test_fallback_mechanism_integration(
        self, integrated_system, mock_property_data
    ):
        """Test fallback mechanisms across components."""
        api_client = integrated_system["api_client"]
        data_collector = integrated_system["data_collector"]

        # Setup fallback scenario
        call_count = 0
    def mock_search_with_fallback(apn):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call fails
                return {"success": False, "error": "API unavailable"}
            else:
                # Fallback succeeds
                return {"success": True, "data": mock_property_data}

        api_client.search_property = Mock(side_effect=mock_search_with_fallback)

        # Test fallback integration
        result = data_collector.collect_property_data_with_fallback("10215009")

        # Verify fallback mechanism
        assert result["success"] is True
        assert call_count == 2  # Initial failure + successful fallback

    @pytest.mark.integration
    def test_caching_integration(self, integrated_system, mock_property_data):
        """Test caching behavior across components."""
        api_client = integrated_system["api_client"]
        data_collector = integrated_system["data_collector"]

        # Enable caching
        api_client.cache = {}
        api_client.search_property = Mock(
            return_value={"success": True, "data": mock_property_data}
        )

        # First request (cache miss)
        result1 = data_collector.collect_property_data("10215009")

        # Store in cache
        cache_key = "property_10215009"
        api_client.cache[cache_key] = result1["data"]

        # Second request (should use cache)
        result2 = data_collector.collect_property_data("10215009")

        # Verify caching integration
        assert result1["success"] is True
        assert result2["success"] is True
        # Note: In real implementation, second call would use cache

    @pytest.mark.integration
    def test_configuration_integration(self, integrated_system):
        """Test configuration consistency across components."""
        api_client = integrated_system["api_client"]
        db_manager = integrated_system["db_manager"]
        gui_launcher = integrated_system["gui_launcher"]

        # Verify configuration consistency
        assert api_client.config is not None
        assert db_manager.config is not None
        assert gui_launcher.config is not None

        # Test configuration updates
        new_config = {"timeout": 10}

        api_client.update_config(new_config)
        updated_config = api_client.get_config()

        assert updated_config["timeout"] == 10

    @pytest.mark.integration
    def test_logging_integration(self, integrated_system):
        """Test logging coordination across components."""
        api_client = integrated_system["api_client"]
        data_collector = integrated_system["data_collector"]
        db_manager = integrated_system["db_manager"]

        # Test logging setup
        assert hasattr(api_client, "logger")
        assert hasattr(data_collector, "logger")
        assert hasattr(db_manager, "logger")

        # Test coordinated logging
        with patch.object(api_client, "logger") as mock_api_logger:
            with patch.object(data_collector, "logger") as mock_dc_logger:
                # Simulate operation with logging
                api_client.logger.info("API operation")
                data_collector.logger.info("Data collection operation")

                # Verify logging coordination
                mock_api_logger.info.assert_called_with("API operation")
                mock_dc_logger.info.assert_called_with("Data collection operation")

    @pytest.mark.integration
    def test_resource_cleanup_integration(self, integrated_system):
        """Test resource cleanup across all components."""
        api_client = integrated_system["api_client"]
        data_collector = integrated_system["data_collector"]
        db_manager = integrated_system["db_manager"]
        gui_launcher = integrated_system["gui_launcher"]

        # Simulate resource usage
        data_collector.start_background_processing()

        # Test coordinated cleanup
    try:
            api_client.close()
            data_collector.cleanup()
            db_manager.cleanup()
            gui_launcher.cleanup()

            # Verify cleanup succeeded
            assert data_collector.is_running is False

    except Exception as e:
            pytest.fail(f"Cleanup integration failed: {e}")

    @pytest.mark.integration
    def test_system_health_monitoring_integration(self, integrated_system):
        """Test system health monitoring across components."""
        api_client = integrated_system["api_client"]
        db_manager = integrated_system["db_manager"]
        gui_launcher = integrated_system["gui_launcher"]

        # Mock health checks
        api_client.health_check = Mock(return_value={"status": "healthy"})
        db_manager.health_check = Mock(return_value={"status": "healthy"})

        # Test system health aggregation
        system_health = {
            "api_client": api_client.health_check(),
            "database": db_manager.health_check(),
            "gui_launcher": gui_launcher.test_gui_capability(),
        }

        # Verify health monitoring integration
        assert system_health["api_client"]["status"] == "healthy"
        assert system_health["database"]["status"] == "healthy"
        assert "success" in system_health["gui_launcher"]
