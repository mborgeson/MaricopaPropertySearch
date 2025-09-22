"""
Unit tests for UnifiedDataCollector

Tests the consolidated data collector that combines 4 previous implementations
with features including background processing, priority queues, and real-time progress.
"""

import pytest
import asyncio
import time
import threading
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from queue import Queue, Empty, PriorityQueue

# Import the component under test
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from unified_data_collector import (
    UnifiedDataCollector,
    JobPriority,
    DataCollectionJob,
    CollectionStrategy,
    ProgressTracker,
    BackgroundProcessor,
)


class TestUnifiedDataCollector:
    """Test suite for UnifiedDataCollector component."""

    @pytest.fixture
    def mock_api_client(self):
        """Mock API client for data collector testing."""
        api_client = Mock()
        api_client.search_property.return_value = {
            "success": True,
            "data": {"apn": "10215009", "address": "10000 W Missouri Ave"},
        }
        api_client.search_property_async = AsyncMock(
            return_value={
                "success": True,
                "data": {"apn": "10215009", "address": "10000 W Missouri Ave"},
            }
        )
        return api_client

    @pytest.fixture
    def data_collector(self, mock_api_client):
        """Create a UnifiedDataCollector instance for testing."""
        with patch("unified_data_collector.get_logger"):
            with patch("unified_data_collector.get_performance_logger"):
                collector = UnifiedDataCollector(api_client=mock_api_client)
                # Mock background thread to avoid actual threading in tests
                collector.background_thread = Mock()
                return collector

    @pytest.mark.unit
    def test_collector_initialization(self, mock_api_client):
        """Test proper initialization of the data collector."""
        with patch("unified_data_collector.get_logger"):
            with patch("unified_data_collector.get_performance_logger"):
                collector = UnifiedDataCollector(api_client=mock_api_client)

                assert collector.api_client == mock_api_client
                assert isinstance(collector.job_queue, PriorityQueue)
                assert collector.is_running is False
                assert collector.progress_tracker is not None

    @pytest.mark.unit
    def test_job_priority_enum(self):
        """Test JobPriority enum functionality."""
        assert JobPriority.CRITICAL.value == 0
        assert JobPriority.HIGH.value == 1
        assert JobPriority.NORMAL.value == 2
        assert JobPriority.LOW.value == 3

        # Test priority ordering
        assert JobPriority.CRITICAL < JobPriority.HIGH
        assert JobPriority.HIGH < JobPriority.NORMAL
        assert JobPriority.NORMAL < JobPriority.LOW

    @pytest.mark.unit
    def test_data_collection_job_creation(self):
        """Test creation of data collection jobs."""
        job = DataCollectionJob(
            job_id="test_job_001",
            apn="10215009",
            priority=JobPriority.HIGH,
            collection_type="property_search",
            params={"include_tax_history": True},
        )

        assert job.job_id == "test_job_001"
        assert job.apn == "10215009"
        assert job.priority == JobPriority.HIGH
        assert job.collection_type == "property_search"
        assert job.params["include_tax_history"] is True
        assert job.created_at is not None
        assert job.status == "pending"

    @pytest.mark.unit
    def test_progress_tracker_functionality(self, data_collector):
        """Test progress tracking functionality."""
        tracker = data_collector.progress_tracker

        # Test initial state
        assert tracker.total_jobs == 0
        assert tracker.completed_jobs == 0
        assert tracker.progress_percentage == 0.0

        # Test job tracking
        tracker.add_job("job_001")
        tracker.add_job("job_002")
        assert tracker.total_jobs == 2

        # Test completion tracking
        tracker.complete_job("job_001")
        assert tracker.completed_jobs == 1
        assert tracker.progress_percentage == 50.0

        tracker.complete_job("job_002")
        assert tracker.completed_jobs == 2
        assert tracker.progress_percentage == 100.0

    @pytest.mark.unit
    def test_single_property_collection(self, data_collector, mock_property_data):
        """Test collection of single property data."""
        # Setup mock return data
        data_collector.api_client.search_property.return_value = {
            "success": True,
            "data": mock_property_data,
        }

        # Execute collection
        result = data_collector.collect_property_data("10215009")

        # Verify results
        assert result["success"] is True
        assert result["data"]["apn"] == "10215009"
        data_collector.api_client.search_property.assert_called_once_with("10215009")

    @pytest.mark.unit
    def test_single_property_collection_error(self, data_collector):
        """Test error handling in single property collection."""
        # Setup mock error
        data_collector.api_client.search_property.return_value = {
            "success": False,
            "error": "Property not found",
        }

        # Execute collection
        result = data_collector.collect_property_data("invalid_apn")

        # Verify error handling
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.unit
    def test_batch_property_collection(self, data_collector, mock_property_data):
        """Test batch collection of multiple properties."""
        apn_list = ["10215009", "10215010", "10215011"]

        # Setup mock return data for batch
        def mock_search_property(apn):
            return {"success": True, "data": {**mock_property_data, "apn": apn}}

        data_collector.api_client.search_property.side_effect = mock_search_property

        # Execute batch collection
        results = data_collector.collect_batch_data(apn_list)

        # Verify results
        assert len(results) == 3
        assert all(result["success"] for result in results)
        assert data_collector.api_client.search_property.call_count == 3

    @pytest.mark.unit
    def test_batch_collection_with_errors(self, data_collector, mock_property_data):
        """Test batch collection with mixed success/error results."""
        apn_list = ["10215009", "invalid_apn", "10215011"]

        # Setup mock with mixed results
        def mock_search_property(apn):
            if apn == "invalid_apn":
                return {"success": False, "error": "Property not found"}
            return {"success": True, "data": {**mock_property_data, "apn": apn}}

        data_collector.api_client.search_property.side_effect = mock_search_property

        # Execute batch collection
        results = data_collector.collect_batch_data(apn_list)

        # Verify mixed results
        assert len(results) == 3
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert results[2]["success"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_async_property_collection(self, data_collector, mock_property_data):
        """Test asynchronous property data collection."""
        # Setup mock async return data
        data_collector.api_client.search_property_async.return_value = {
            "success": True,
            "data": mock_property_data,
        }

        # Execute async collection
        result = await data_collector.collect_property_data_async("10215009")

        # Verify results
        assert result["success"] is True
        assert result["data"]["apn"] == "10215009"
        data_collector.api_client.search_property_async.assert_called_once_with(
            "10215009"
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_async_batch_collection(self, data_collector, mock_property_data):
        """Test asynchronous batch collection."""
        apn_list = ["10215009", "10215010", "10215011"]

        # Setup mock async return data
        async def mock_async_search(apn):
            return {"success": True, "data": {**mock_property_data, "apn": apn}}

        data_collector.api_client.search_property_async.side_effect = mock_async_search

        # Execute async batch collection
        results = await data_collector.collect_batch_data_async(apn_list)

        # Verify results
        assert len(results) == 3
        assert all(result["success"] for result in results)
        assert data_collector.api_client.search_property_async.call_count == 3

    @pytest.mark.unit
    def test_job_queue_management(self, data_collector):
        """Test job queue functionality."""
        # Test adding jobs with different priorities
        job_high = DataCollectionJob(
            job_id="high_priority", apn="10215009", priority=JobPriority.HIGH
        )
        job_low = DataCollectionJob(
            job_id="low_priority", apn="10215010", priority=JobPriority.LOW
        )

        data_collector.add_job(job_high)
        data_collector.add_job(job_low)

        # Test queue ordering (high priority should come first)
        first_job = data_collector.get_next_job()
        assert first_job.job_id == "high_priority"

        second_job = data_collector.get_next_job()
        assert second_job.job_id == "low_priority"

    @pytest.mark.unit
    def test_background_processing_start_stop(self, data_collector):
        """Test starting and stopping background processing."""
        # Test start
        data_collector.start_background_processing()
        assert data_collector.is_running is True

        # Test stop
        data_collector.stop_background_processing()
        assert data_collector.is_running is False

    @pytest.mark.unit
    def test_progress_callback_functionality(self, data_collector):
        """Test progress callback mechanism."""
        progress_updates = []

        def mock_progress_callback(progress_data):
            progress_updates.append(progress_data)

        data_collector.set_progress_callback(mock_progress_callback)

        # Simulate progress updates
        data_collector.update_progress("job_001", 50, "Processing...")
        data_collector.update_progress("job_001", 100, "Complete")

        # Verify callbacks were called
        assert len(progress_updates) == 2
        assert progress_updates[0]["progress"] == 50
        assert progress_updates[1]["progress"] == 100

    @pytest.mark.unit
    def test_cancellation_functionality(self, data_collector):
        """Test job cancellation functionality."""
        # Add a job
        job = DataCollectionJob(
            job_id="cancellable_job", apn="10215009", priority=JobPriority.NORMAL
        )
        data_collector.add_job(job)

        # Test cancellation
        result = data_collector.cancel_job("cancellable_job")
        assert result is True

        # Test cancelling non-existent job
        result = data_collector.cancel_job("non_existent_job")
        assert result is False

    @pytest.mark.unit
    def test_collection_strategy_selection(self, data_collector):
        """Test collection strategy selection based on job parameters."""
        # Test strategy for single property
        strategy = data_collector.select_collection_strategy(
            job_count=1, priority=JobPriority.HIGH, include_background_data=False
        )
        assert strategy == CollectionStrategy.SINGLE_THREADED

        # Test strategy for batch processing
        strategy = data_collector.select_collection_strategy(
            job_count=10, priority=JobPriority.NORMAL, include_background_data=True
        )
        assert strategy == CollectionStrategy.PARALLEL_BATCH

    @pytest.mark.unit
    @pytest.mark.performance
    def test_performance_metrics(
        self, data_collector, performance_timer, mock_property_data
    ):
        """Test performance tracking and metrics."""
        # Setup mock for performance testing
        data_collector.api_client.search_property.return_value = {
            "success": True,
            "data": mock_property_data,
        }

        # Measure collection performance
        performance_timer.start()
        result = data_collector.collect_property_data("10215009")
        elapsed_time = performance_timer.stop()

        # Verify performance meets baseline
        assert result["success"] is True
        assert elapsed_time < 0.1  # Should complete under 100ms

    @pytest.mark.unit
    def test_memory_management(self, data_collector):
        """Test memory management and cleanup."""
        # Add multiple jobs to test memory usage
        for i in range(100):
            job = DataCollectionJob(
                job_id=f"job_{i:03d}",
                apn=f"1021500{i:02d}",
                priority=JobPriority.NORMAL,
            )
            data_collector.add_job(job)

        # Test queue size
        assert data_collector.job_queue.qsize() == 100

        # Test cleanup
        data_collector.clear_completed_jobs()
        data_collector.clear_queue()
        assert data_collector.job_queue.qsize() == 0

    @pytest.mark.unit
    def test_error_recovery_mechanisms(self, data_collector):
        """Test error recovery and resilience."""
        # Setup API client to fail initially, then succeed
        call_count = 0

        def mock_search_with_recovery(apn):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Temporary failure")
            return {"success": True, "data": {"apn": apn, "address": "Recovery Test"}}

        data_collector.api_client.search_property.side_effect = (
            mock_search_with_recovery
        )

        # Test recovery mechanism
        result = data_collector.collect_property_data_with_retry(
            "10215009", max_retries=3
        )

        # Verify recovery succeeded
        assert result["success"] is True
        assert call_count == 3  # Failed twice, succeeded on third try

    @pytest.mark.unit
    def test_missouri_ave_workflow_validation(self, data_collector, mock_property_data):
        """Test the validated Missouri Avenue workflow."""
        missouri_data = {
            **mock_property_data,
            "apn": "10215009",
            "address": "10000 W Missouri Ave",
        }

        data_collector.api_client.search_property.return_value = {
            "success": True,
            "data": missouri_data,
        }

        # Execute Missouri Avenue collection
        result = data_collector.collect_property_data("10215009")

        # Verify Missouri Avenue specific validation
        assert result["success"] is True
        assert result["data"]["apn"] == "10215009"
        assert result["data"]["address"] == "10000 W Missouri Ave"

    @pytest.mark.unit
    def test_thread_safety(self, data_collector):
        """Test thread safety of the data collector."""
        results = []
        errors = []

        def worker_thread(thread_id):
            try:
                for i in range(10):
                    job = DataCollectionJob(
                        job_id=f"thread_{thread_id}_job_{i}",
                        apn=f"102150{thread_id}{i:02d}",
                        priority=JobPriority.NORMAL,
                    )
                    data_collector.add_job(job)
                    results.append(f"thread_{thread_id}_completed")
            except Exception as e:
                errors.append(str(e))

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify thread safety
        assert len(errors) == 0  # No thread safety errors
        assert len(results) == 5  # All threads completed
        assert data_collector.job_queue.qsize() == 50  # All jobs added

    @pytest.mark.unit
    def test_cleanup_and_resource_management(self, data_collector):
        """Test proper cleanup and resource management."""
        # Start background processing
        data_collector.start_background_processing()

        # Add some jobs
        for i in range(5):
            job = DataCollectionJob(
                job_id=f"cleanup_job_{i}",
                apn=f"1021500{i}",
                priority=JobPriority.NORMAL,
            )
            data_collector.add_job(job)

        # Test cleanup
        data_collector.cleanup()

        # Verify cleanup
        assert data_collector.is_running is False
        assert data_collector.job_queue.qsize() == 0
