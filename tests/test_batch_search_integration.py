#!/usr/bin/env python
"""
Batch Search Integration Tests
Tests the complete batch search processing system integration
"""
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from src.batch_processing_manager import BatchProcessingManager
from src.batch_search_engine import BatchPriority, BatchSearchEngine, SearchMode
from src.batch_search_integration import (
    BatchSearchIntegrationManager,
    BatchSearchJobType,
    BatchSearchResult,
    BatchSearchSummary,
)


class TestBatchSearchIntegration(unittest.TestCase):
    """Test suite for batch search integration"""
    def setUp(self):
        """Set up test fixtures"""
        # Create mock components
        self.mock_api_client = Mock()
        self.mock_db_manager = Mock()
        self.mock_web_scraper = Mock()
        self.mock_background_manager = Mock()

        # Configure mock responses
        self.mock_api_client.search_by_apn.return_value = {
            "apn": "123-45-678",
            "owner": "Test Owner",
        }
        self.mock_db_manager.get_connection.return_value = Mock()

        # Create integration manager
        self.integration_manager = BatchSearchIntegrationManager(
            api_client=self.mock_api_client,
            db_manager=self.mock_db_manager,
            web_scraper_manager=self.mock_web_scraper,
            background_manager=self.mock_background_manager,
        )
    def test_integration_manager_initialization(self):
        """Test that integration manager initializes correctly"""
        self.assertIsNotNone(self.integration_manager)
        self.assertIsNotNone(self.integration_manager.batch_search_engine)
        self.assertIsNotNone(self.integration_manager.batch_processing_manager)
        self.assertEqual(len(self.integration_manager.active_jobs), 0)
        self.assertEqual(len(self.integration_manager.completed_jobs), 0)
    def test_batch_search_job_creation(self):
        """Test creating a batch search job"""
        identifiers = ["123-45-678", "234-56-789", "345-67-890"]

        # Mock the batch search engine to return a job ID
        with patch.object(
            self.integration_manager.batch_search_engine, "submit_batch_search"
        ) as mock_submit:
            mock_submit.return_value = "test_job_123"

            job_id = self.integration_manager.execute_batch_search(
                identifiers=identifiers,
                search_type="apn",
                job_type=BatchSearchJobType.BASIC_SEARCH,
                max_concurrent=3,
            )

            self.assertIsNotNone(job_id)
            self.assertIn(job_id, self.integration_manager.active_jobs)

            # Verify job info
            job_info = self.integration_manager.active_jobs[job_id]
            self.assertEqual(job_info["identifiers"], identifiers)
            self.assertEqual(job_info["search_type"], "apn")
            self.assertEqual(job_info["job_type"], BatchSearchJobType.BASIC_SEARCH)
    def test_job_status_retrieval(self):
        """Test retrieving job status"""
        # Create a test job
        job_id = "test_job_456"
        job_info = {
            "job_id": job_id,
            "job_type": BatchSearchJobType.BASIC_SEARCH,
            "identifiers": ["123-45-678"],
            "search_type": "apn",
            "max_concurrent": 3,
            "start_time": time.time(),
            "status": "running",
            "progress": 50.0,
        }

        self.integration_manager.active_jobs[job_id] = job_info

        # Test status retrieval
        status = self.integration_manager.get_job_status(job_id)

        self.assertIsNotNone(status)
        self.assertEqual(status["job_id"], job_id)
        self.assertEqual(status["status"], "running")
        self.assertEqual(status["progress"], 50.0)
        self.assertEqual(status["job_type"], BatchSearchJobType.BASIC_SEARCH.value)
    def test_batch_search_result_processing(self):
        """Test processing batch search results"""
        # Create sample raw results
        raw_results = [
            {
                "identifier": "123-45-678",
                "success": True,
                "result": {"apn": "123-45-678", "owner": "John Smith"},
                "error": None,
            },
            {
                "identifier": "234-56-789",
                "success": False,
                "result": None,
                "error": "Property not found",
            },
        ]

        # Process results
        processed_results = self.integration_manager._process_engine_results(
            raw_results, "apn"
        )

        self.assertEqual(len(processed_results), 2)

        # Check successful result
        success_result = processed_results[0]
        self.assertTrue(success_result.success)
        self.assertEqual(success_result.identifier, "123-45-678")
        self.assertIsNotNone(success_result.result_data)

        # Check failed result
        failed_result = processed_results[1]
        self.assertFalse(failed_result.success)
        self.assertEqual(failed_result.identifier, "234-56-789")
        self.assertEqual(failed_result.error_message, "Property not found")
    def test_export_functionality(self):
        """Test CSV export functionality"""
        # Create a completed job with results
        job_id = "test_job_export"

        results = [
            BatchSearchResult(
                identifier="123-45-678",
                search_type="apn",
                success=True,
                result_data={"apn": "123-45-678", "owner": "John Smith"},
                processing_time=1.5,
                api_calls_used=1,
                data_sources_used=["api"],
            ),
            BatchSearchResult(
                identifier="234-56-789",
                search_type="apn",
                success=False,
                error_message="Property not found",
                processing_time=0.8,
                api_calls_used=1,
                data_sources_used=["api"],
            ),
        ]

        summary = BatchSearchSummary(
            job_id=job_id,
            job_type=BatchSearchJobType.BASIC_SEARCH,
            total_items=2,
            successful_items=1,
            failed_items=1,
            total_processing_time=2.3,
            average_time_per_item=1.15,
            api_calls_total=2,
            results=results,
        )

        self.integration_manager.completed_jobs[job_id] = summary

        # Test export to temporary file
import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as temp_file:
            temp_path = temp_file.name

    try:
            success = self.integration_manager.export_results_to_csv(job_id, temp_path)
            self.assertTrue(success)

            # Verify file exists and has content
            self.assertTrue(os.path.exists(temp_path))
            with open(temp_path, "r") as f:
                content = f.read()
                self.assertIn("123-45-678", content)
                self.assertIn("234-56-789", content)
                self.assertIn("SUMMARY", content)

    finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    def test_job_cancellation(self):
        """Test job cancellation functionality"""
        job_id = "test_job_cancel"

        # Create active job
        job_info = {"job_id": job_id, "status": "running"}
        self.integration_manager.active_jobs[job_id] = job_info

        # Mock the underlying engine cancel method
        with patch.object(
            self.integration_manager.batch_search_engine, "cancel_job"
        ) as mock_cancel:
            mock_cancel.return_value = True

            success = self.integration_manager.cancel_job(job_id)

            self.assertTrue(success)
            mock_cancel.assert_called_once_with(
                None
            )  # engine_job_id would be None in test
    def test_statistics_collection(self):
        """Test statistics collection and reporting"""
        # Add some test data to statistics
        self.integration_manager.total_jobs_processed = 5
        self.integration_manager.total_items_processed = 25
        self.integration_manager.average_throughput = 2.5

        # Add mock component statistics
        mock_engine_stats = {
            "total_requests_processed": 25,
            "success_rate_percent": 92.0,
            "connection_pool_size": 15,
        }

        with patch.object(
            self.integration_manager.batch_search_engine, "get_engine_statistics"
        ) as mock_engine:
            with patch.object(
                self.integration_manager.batch_processing_manager,
                "get_manager_statistics",
            ) as mock_manager:
                mock_engine.return_value = mock_engine_stats
                mock_manager.return_value = {"total_jobs_processed": 3}

                stats = self.integration_manager.get_integration_statistics()

                self.assertEqual(stats["total_jobs_processed"], 5)
                self.assertEqual(stats["total_items_processed"], 25)
                self.assertEqual(stats["average_throughput_items_per_second"], 2.5)
                self.assertIn("batch_search_engine", stats)
                self.assertIn("batch_processing_manager", stats)
    def test_different_job_types(self):
        """Test handling of different job types"""
        test_cases = [
            {
                "job_type": BatchSearchJobType.BASIC_SEARCH,
                "expected_engine_used": True,
                "expected_manager_used": False,
            },
            {
                "job_type": BatchSearchJobType.COMPREHENSIVE_SEARCH,
                "expected_engine_used": False,
                "expected_manager_used": True,
            },
            {
                "job_type": BatchSearchJobType.VALIDATION_SEARCH,
                "expected_engine_used": False,
                "expected_manager_used": True,
            },
        ]

        for case in test_cases:
            with self.subTest(job_type=case["job_type"]):
                identifiers = ["123-45-678"]

                # Mock the appropriate methods
                with patch.object(
                    self.integration_manager.batch_search_engine, "submit_batch_search"
                ) as mock_engine:
                    with patch.object(
                        self.integration_manager.batch_processing_manager,
                        "submit_batch_job",
                    ) as mock_manager:
                        mock_engine.return_value = "engine_job_123"
                        mock_manager.return_value = "manager_job_123"

                        job_id = self.integration_manager.execute_batch_search(
                            identifiers=identifiers,
                            search_type="apn",
                            job_type=case["job_type"],
                        )

                        self.assertIsNotNone(job_id)

                        # Verify correct component was used
                        if case["expected_engine_used"]:
                            mock_engine.assert_called_once()
                        else:
                            mock_engine.assert_not_called()

                        if case["expected_manager_used"]:
                            mock_manager.assert_called_once()
                        else:
                            mock_manager.assert_not_called()
    def test_background_collection_integration(self):
        """Test integration with background data collection"""
        # Create successful search results
        results = [
            BatchSearchResult(
                identifier="123-45-678",
                search_type="apn",
                success=True,
                result_data={"apn": "123-45-678", "owner": "John Smith"},
            ),
            BatchSearchResult(
                identifier="234-56-789",
                search_type="apn",
                success=True,
                result_data=[
                    {"apn": "234-56-789", "owner": "Jane Doe"},
                    {"apn": "234-56-790", "owner": "Bob Smith"},
                ],
            ),
        ]

        # Test background collection trigger
        with patch.object(
            self.integration_manager.background_manager, "enhance_search_results"
        ) as mock_enhance:
            self.integration_manager._trigger_background_collection(results)

            # Should have been called with APNs from successful results
            mock_enhance.assert_called_once()
            call_args = mock_enhance.call_args[0][0]  # First argument

            # Should contain APNs from both successful results
            apns = [item["apn"] for item in call_args]
            self.assertIn("123-45-678", apns)
            self.assertIn("234-56-789", apns)
            self.assertIn("234-56-790", apns)
    def tearDown(self):
        """Clean up after tests"""
        # Shutdown the integration manager
    try:
            self.integration_manager.shutdown()
    except:
            pass


class TestBatchSearchResultHandling(unittest.TestCase):
    """Test batch search result data structures"""
    def test_batch_search_result_creation(self):
        """Test creating BatchSearchResult objects"""
        result = BatchSearchResult(
            identifier="123-45-678",
            search_type="apn",
            success=True,
            result_data={"apn": "123-45-678", "owner": "Test Owner"},
            processing_time=1.5,
            api_calls_used=1,
            data_sources_used=["api", "cache"],
        )

        self.assertEqual(result.identifier, "123-45-678")
        self.assertEqual(result.search_type, "apn")
        self.assertTrue(result.success)
        self.assertIsNotNone(result.result_data)
        self.assertEqual(result.processing_time, 1.5)
        self.assertEqual(result.api_calls_used, 1)
        self.assertEqual(len(result.data_sources_used), 2)
    def test_batch_search_summary_creation(self):
        """Test creating BatchSearchSummary objects"""
        results = [
            BatchSearchResult("123-45-678", "apn", True),
            BatchSearchResult("234-56-789", "apn", False, error_message="Not found"),
        ]

        summary = BatchSearchSummary(
            job_id="test_job",
            job_type=BatchSearchJobType.BASIC_SEARCH,
            total_items=2,
            successful_items=1,
            failed_items=1,
            total_processing_time=5.0,
            average_time_per_item=2.5,
            api_calls_total=2,
            results=results,
        )

        self.assertEqual(summary.job_id, "test_job")
        self.assertEqual(summary.total_items, 2)
        self.assertEqual(summary.successful_items, 1)
        self.assertEqual(summary.failed_items, 1)
        self.assertEqual(len(summary.results), 2)
        self.assertEqual(summary.average_time_per_item, 2.5)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
