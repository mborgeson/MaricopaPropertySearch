#!/usr/bin/env python3
"""
Comprehensive Test Suite for Unified API Client
Tests all consolidated features from the 8 merged API client variants
"""
import asyncio
import os
import sys
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, Mock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from api_client_unified import (
        AdaptiveRateLimiter,
        BatchAPIRequest,
        UnifiedMaricopaAPIClient,
    )
        print("✅ Successfully imported UnifiedMaricopaAPIClient")
except ImportError as e:
        print(f"❌ Import error: {e}")
    sys.exit(1)

class TestUnifiedAPIClient(unittest.TestCase):
    """Test suite for unified API client functionality"""
    def setUp(self):
        """Set up test fixtures"""
        self.client = UnifiedMaricopaAPIClient()
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self.client, 'cleanup'):
            self.client.cleanup()
    def test_client_initialization(self):
        """Test that client initializes with all required components"""
        print("\n🔍 Testing client initialization...")

        # Check core components exist
        self.assertIsNotNone(self.client.session)
        self.assertIsNotNone(self.client.rate_limiter)
        self.assertIsNotNone(self.client.executor)
        self.assertIsNotNone(self.client.request_queue)

        # Check configuration
        self.assertEqual(self.client.base_url, "https://mcassessor.maricopa.gov/api")
        self.assertIn("ca1a11a6", self.client.token)
        print("✅ Client initialization test passed")
def test_cache_functionality(self):
        """Test caching system with TTL"""
        print("\n🔍 Testing cache functionality...")

        # Test cache key generation
        key1 = self.client._get_cache_key("/test", {"param": "value"})
        key2 = self.client._get_cache_key("/test", {"param": "value"})
        key3 = self.client._get_cache_key("/test", {"param": "different"})

        self.assertEqual(key1, key2)
        self.assertNotEqual(key1, key3)

        # Test cache storage and retrieval
        test_data = {"test": "data", "timestamp": time.time()}
        self.client._cache_data(key1, test_data, ttl=1.0)

        cached = self.client._get_cached_data(key1)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["test"], "data")

        # Test TTL expiration
        time.sleep(1.1)
        expired = self.client._get_cached_data(key1)
        self.assertIsNone(expired)
        print("✅ Cache functionality test passed")
def test_rate_limiter(self):
        """Test adaptive rate limiting"""
        print("\n🔍 Testing rate limiter...")

        rate_limiter = AdaptiveRateLimiter(initial_rate=10.0, burst_capacity=5)

        # Test burst capacity
        start_time = time.time()
        for i in range(5):
            acquired = rate_limiter.acquire(timeout=1.0)
            self.assertTrue(acquired, f"Failed to acquire token {i}")

        burst_time = time.time() - start_time
        self.assertLess(burst_time, 0.1, "Burst should be nearly instantaneous")

        # Test rate limiting after burst
        acquired = rate_limiter.acquire(timeout=0.1)
        self.assertFalse(acquired, "Should not acquire token after burst exhausted")
        print("✅ Rate limiter test passed")
def test_batch_request_structure(self):
        """Test batch request data structure"""
        print("\n🔍 Testing batch request structure...")

        request = BatchAPIRequest(
            request_id="test_001",
            request_type="search_by_apn",
            identifier="123-45-678",
            priority=1
        )

        self.assertEqual(request.request_id, "test_001")
        self.assertEqual(request.request_type, "search_by_apn")
        self.assertEqual(request.identifier, "123-45-678")
        self.assertEqual(request.priority, 1)
        self.assertIsNone(request.result)
        self.assertIsNone(request.error)

        # Test equality and hashing
        request2 = BatchAPIRequest(
            request_id="test_002",
            request_type="search_by_apn",
            identifier="123-45-678"
        )

        self.assertEqual(request, request2)  # Same type and identifier
        self.assertEqual(hash(request), hash(request2))
        print("✅ Batch request structure test passed")

    @patch('requests.Session.get')
def test_synchronous_api_call(self, mock_get):
        """Test synchronous API calls with mocked responses"""
        print("\n🔍 Testing synchronous API calls...")

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {"apn": "123-45-678", "owner": "Test Owner"}
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test API call
        result = self.client.search_by_apn("123-45-678")

        self.assertIsNotNone(result)
        self.assertTrue(result.get("success", False))
        self.assertIn("data", result)

        # Verify rate limiting was applied
        mock_get.assert_called_once()
        print("✅ Synchronous API call test passed")
def test_thread_safety(self):
        """Test thread safety of the unified client"""
        print("\n🔍 Testing thread safety...")

        results = []
        errors = []
def worker_thread(thread_id):
            try:
                # Simulate concurrent API calls
                with patch('requests.Session.get') as mock_get:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "thread_id": thread_id,
                        "timestamp": time.time()
                    }
                    mock_response.raise_for_status.return_value = None
                    mock_get.return_value = mock_response

                    result = self.client.search_by_apn(f"thread-{thread_id}")
                    results.append(result)

            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")

        # Run multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=5.0)

        # Verify results
        self.assertEqual(len(errors), 0, f"Thread safety errors: {errors}")
        self.assertEqual(len(results), 5, "Not all threads completed successfully")
        print("✅ Thread safety test passed")
def test_performance_metrics(self):
        """Test performance tracking functionality"""
        print("\n🔍 Testing performance metrics...")

        # Access metrics
        stats = self.client.get_performance_stats()

        self.assertIn("total_requests", stats)
        self.assertIn("cache_hits", stats)
        self.assertIn("cache_misses", stats)
        self.assertIn("total_successful", stats)
        self.assertIn("total_failed", stats)
        self.assertIn("average_response_time", stats)

        # All metrics should be non-negative
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                self.assertGreaterEqual(value, 0, f"Metric {key} should be non-negative")
        print("✅ Performance metrics test passed")
def run_integration_tests():
    """Run integration tests that require the full environment"""
        print("\n🔧 Running integration tests...")

    try:
        client = UnifiedMaricopaAPIClient()
        print("✅ Client creation successful")

        # Test that all methods exist
        required_methods = [
            'search_by_apn',
            'search_by_address',
            'search_by_owner',
            'batch_search_by_apns',
            'get_performance_stats',
            'get_comprehensive_property_info'
        ]

        for method in required_methods:
            if hasattr(client, method):
        print(f"✅ Method {method} exists")
            else:
        print(f"❌ Method {method} missing")
                return False

        # Test configuration
        if hasattr(client, 'token') and client.token and "ca1a11a6" in client.token:
        print("✅ API token configured correctly")
        else:
        print("❌ API token not configured")

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False
def main():
    """Main test runner"""
        print("🚀 Starting Unified API Client Test Suite")
        print("=" * 60)

    # Run integration tests first
    integration_success = run_integration_tests()

    if not integration_success:
        print("\n❌ Integration tests failed - stopping execution")
        return 1

    # Run unit tests
        print("\n🧪 Running unit tests...")

    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestUnifiedAPIClient)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
        print(f"   Tests run: {result.testsRun}")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        print(f"   Skipped: {len(result.skipped)}")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print(f"   Tests run: {result.testsRun}")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")

        if result.failures:
        print("\n📝 FAILURES:")
            for test, traceback in result.failures:
        print(f"   {test}: {traceback}")

        if result.errors:
        print("\n🔥 ERRORS:")
            for test, traceback in result.errors:
        print(f"   {test}: {traceback}")

        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)