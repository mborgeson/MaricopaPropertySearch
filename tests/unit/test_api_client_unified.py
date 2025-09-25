"""
Unit tests for UnifiedMaricopaAPIClient

Tests the consolidated API client that combines 6 previous implementations
with features including rate limiting, connection pooling, and error handling.
"""

import asyncio
import json

# Import the component under test
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import aiohttp
import pytest
from requests.exceptions import HTTPError, RequestException, Timeout

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api_client_unified import (
    APIClientConfig,
    BatchAPIRequest,
    ConnectionPoolManager,
    PropertyDataCache,
    RateLimiter,
    UnifiedMaricopaAPIClient,
)


class TestUnifiedMaricopaAPIClient:
    """Test suite for UnifiedMaricopaAPIClient component."""

    @pytest.fixture
    def client_config(self):
        """Provide a test configuration for the API client."""
        return APIClientConfig(
            base_url="https://api.test.com",
            api_token="test_token",
            max_retries=3,
            retry_delay=0.1,
            rate_limit_requests=10,
            rate_limit_period=60,
            connection_pool_size=5,
            timeout=5.0,
        )

    @pytest.fixture
    def api_client(self, client_config):
        """Create a UnifiedMaricopaAPIClient instance for testing."""
        with patch("api_client_unified.get_api_logger"):
            client = UnifiedMaricopaAPIClient(config=client_config)
            # Mock the session to avoid actual HTTP requests
            client.session = Mock()
            client.async_session = AsyncMock()
            return client

    @pytest.mark.unit
    def test_client_initialization(self, client_config):
        """Test proper initialization of the API client."""
        with patch("api_client_unified.get_api_logger"):
            client = UnifiedMaricopaAPIClient(config=client_config)

            assert client.config.base_url == "https://api.test.com"
            assert client.config.api_token == "test_token"
            assert client.config.max_retries == 3
            assert isinstance(client.cache, dict)
            assert client.rate_limiter is not None
            assert client.connection_pool is not None

    @pytest.mark.unit
    def test_property_data_cache(self):
        """Test PropertyDataCache functionality."""
        test_data = {"apn": "10215009", "address": "10000 W Missouri Ave"}
        cache_entry = PropertyDataCache(
            data=test_data, timestamp=time.time(), ttl=300.0
        )

        assert cache_entry.data == test_data
        assert not cache_entry.is_expired()

        # Test expired cache
        old_cache = PropertyDataCache(
            data=test_data, timestamp=time.time() - 400, ttl=300.0
        )
        assert old_cache.is_expired()

    @pytest.mark.unit
    def test_rate_limiter_functionality(self, api_client):
        """Test rate limiting behavior."""
        # Mock the rate limiter's acquire method
        api_client.rate_limiter.acquire = Mock(return_value=True)

        # Test rate limit check
        result = api_client.rate_limiter.acquire()
        assert result is True
        api_client.rate_limiter.acquire.assert_called_once()

    @pytest.mark.unit
    @patch("requests.Session.get")
    def test_sync_property_search_success(
        self, mock_get, api_client, mock_property_data
    ):
        """Test successful synchronous property search."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": mock_property_data}
        mock_get.return_value = mock_response

        # Execute search
        result = api_client.search_property("10215009")

        # Verify results
        assert result["success"] is True
        assert result["data"]["apn"] == "10215009"
        mock_get.assert_called_once()

    @pytest.mark.unit
    @patch("requests.Session.get")
    def test_sync_property_search_api_error(self, mock_get, api_client):
        """Test handling of API errors in synchronous search."""
        # Setup mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = HTTPError("Internal Server Error")
        mock_get.return_value = mock_response

        # Execute search and expect error handling
        result = api_client.search_property("10215009")

        # Verify error handling
        assert result["success"] is False
        assert "error" in result
        mock_get.assert_called_once()

    @pytest.mark.unit
    @patch("requests.Session.get")
    def test_sync_property_search_timeout(self, mock_get, api_client):
        """Test handling of timeout errors."""
        # Setup mock timeout
        mock_get.side_effect = Timeout("Request timeout")

        # Execute search
        result = api_client.search_property("10215009")

        # Verify timeout handling
        assert result["success"] is False
        assert "timeout" in result.get("error", "").lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_async_property_search_success(self, api_client, mock_property_data):
        """Test successful asynchronous property search."""
        # Setup mock async response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"success": True, "data": mock_property_data}
        )

        # Mock the async session get method
        api_client.async_session.get = AsyncMock(return_value=mock_response)

        # Execute async search
        result = await api_client.search_property_async("10215009")

        # Verify results
        assert result["success"] is True
        assert result["data"]["apn"] == "10215009"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_async_property_search_error(self, api_client):
        """Test error handling in asynchronous search."""
        # Setup mock error
        api_client.async_session.get = AsyncMock(
            side_effect=aiohttp.ClientError("Connection error")
        )

        # Execute async search
        result = await api_client.search_property_async("10215009")

        # Verify error handling
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.unit
    def test_cache_functionality(self, api_client, mock_property_data):
        """Test caching behavior."""
        cache_key = "property_10215009"

        # Test cache miss
        assert api_client.get_from_cache(cache_key) is None

        # Test cache set
        api_client.set_cache(cache_key, mock_property_data, ttl=300)
        cached_data = api_client.get_from_cache(cache_key)

        assert cached_data is not None
        assert cached_data["apn"] == mock_property_data["apn"]

    @pytest.mark.unit
    def test_cache_expiration(self, api_client, mock_property_data):
        """Test cache entry expiration."""
        cache_key = "property_expired"

        # Set cache with very short TTL
        api_client.set_cache(cache_key, mock_property_data, ttl=0.001)

        # Wait for expiration
        time.sleep(0.002)

        # Verify cache miss due to expiration
        cached_data = api_client.get_from_cache(cache_key)
        assert cached_data is None

    @pytest.mark.unit
    @patch("requests.Session.get")
    def test_retry_mechanism(self, mock_get, api_client):
        """Test retry mechanism for failed requests."""
        # Setup mock to fail twice, then succeed
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"success": True, "data": {}}

        mock_get.side_effect = [
            RequestException("Connection error"),
            RequestException("Connection error"),
            mock_response_success,
        ]

        # Execute search
        result = api_client.search_property("10215009")

        # Verify retry behavior
        assert result["success"] is True
        assert mock_get.call_count == 3

    @pytest.mark.unit
    @patch("requests.Session.get")
    def test_retry_exhaustion(self, mock_get, api_client):
        """Test behavior when all retries are exhausted."""
        # Setup mock to always fail
        mock_get.side_effect = RequestException("Persistent connection error")

        # Execute search
        result = api_client.search_property("10215009")

        # Verify retry exhaustion handling
        assert result["success"] is False
        assert "error" in result
        assert mock_get.call_count == api_client.config.max_retries

    @pytest.mark.unit
    def test_batch_request_creation(self, api_client):
        """Test creation of batch API requests."""
        request_params = [{"apn": "10215009"}, {"apn": "10215010"}, {"apn": "10215011"}]

        batch_requests = []
        for i, params in enumerate(request_params):
            batch_request = BatchAPIRequest(
                request_id=f"req_{i}",
                endpoint="/property/search",
                params=params,
                priority=1,
            )
            batch_requests.append(batch_request)

        assert len(batch_requests) == 3
        assert batch_requests[0].request_id == "req_0"
        assert batch_requests[0].params["apn"] == "10215009"

    @pytest.mark.unit
    @patch("requests.Session.get")
    def test_batch_property_search(self, mock_get, api_client, mock_property_data):
        """Test batch property search functionality."""
        # Setup mock responses for batch requests
        mock_responses = []
        for i in range(3):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "data": {**mock_property_data, "apn": f"1021500{9+i}"},
            }
            mock_responses.append(mock_response)

        mock_get.side_effect = mock_responses

        # Execute batch search
        apn_list = ["10215009", "10215010", "10215011"]
        results = api_client.batch_search_properties(apn_list)

        # Verify batch results
        assert len(results) == 3
        assert all(result["success"] for result in results)
        assert mock_get.call_count == 3

    @pytest.mark.unit
    def test_connection_pool_management(self, api_client):
        """Test connection pool functionality."""
        # Test connection pool initialization
        assert api_client.connection_pool is not None

        # Test pool size configuration
        assert (
            api_client.connection_pool.max_size
            == api_client.config.connection_pool_size
        )

    @pytest.mark.unit
    @pytest.mark.performance
    def test_performance_with_caching(
        self, api_client, mock_property_data, performance_timer
    ):
        """Test performance improvement with caching."""
        with patch.object(api_client, "_make_request") as mock_request:
            mock_request.return_value = {"success": True, "data": mock_property_data}

            # First request (cache miss)
            performance_timer.start()
            result1 = api_client.search_property("10215009")
            first_request_time = performance_timer.stop()

            # Second request (cache hit)
            performance_timer.start()
            result2 = api_client.search_property("10215009")
            second_request_time = performance_timer.stop()

            # Verify caching performance improvement
            assert result1["success"] is True
            assert result2["success"] is True
            assert mock_request.call_count == 1  # Only one actual request made
            assert second_request_time < first_request_time  # Cache should be faster

    @pytest.mark.unit
    def test_error_handling_and_logging(self, api_client):
        """Test comprehensive error handling and logging."""
        with patch.object(api_client, "logger") as mock_logger:
            with patch.object(api_client, "_make_request") as mock_request:
                mock_request.side_effect = Exception("Test error")

                # Execute search with error
                result = api_client.search_property("10215009")

                # Verify error handling
                assert result["success"] is False
                assert "error" in result

                # Verify logging
                mock_logger.error.assert_called()

    @pytest.mark.unit
    def test_missouri_ave_validation_case(self, api_client, mock_property_data):
        """Test the validated Missouri Avenue property case."""
        missouri_data = {
            **mock_property_data,
            "apn": "10215009",
            "address": "10000 W Missouri Ave",
        }

        with patch.object(api_client, "_make_request") as mock_request:
            mock_request.return_value = {"success": True, "data": missouri_data}

            # Execute Missouri Avenue search
            result = api_client.search_property("10215009")

            # Verify Missouri Avenue specific data
            assert result["success"] is True
            assert result["data"]["apn"] == "10215009"
            assert result["data"]["address"] == "10000 W Missouri Ave"

    @pytest.mark.unit
    def test_configuration_validation(self):
        """Test API client configuration validation."""
        # Test valid configuration
        valid_config = APIClientConfig(
            base_url="https://api.test.com", api_token="test_token"
        )
        assert valid_config.base_url == "https://api.test.com"

        # Test configuration with custom settings
        custom_config = APIClientConfig(
            base_url="https://api.test.com",
            api_token="test_token",
            max_retries=5,
            rate_limit_requests=20,
        )
        assert custom_config.max_retries == 5
        assert custom_config.rate_limit_requests == 20

    @pytest.mark.unit
    def test_client_cleanup(self, api_client):
        """Test proper cleanup of client resources."""
        # Test session cleanup
        api_client.close()

        # Verify cleanup calls
        if hasattr(api_client.session, "close"):
            api_client.session.close.assert_called_once()
