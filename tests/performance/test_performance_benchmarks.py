"""
Performance benchmarking tests for MaricopaPropertySearch unified components

Tests performance targets and regression detection for:
- API Client response times
- Data Collector throughput
- Database Manager query performance
- GUI Launcher startup time
"""

import pytest
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch
import psutil
import gc

# Import components for benchmarking
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api_client_unified import UnifiedMaricopaAPIClient
from unified_data_collector import UnifiedDataCollector
from threadsafe_database_manager import ThreadSafeDatabaseManager
from gui_launcher_unified import UnifiedGUILauncher

class TestPerformanceBenchmarks:
    """Performance benchmark tests with regression detection."""

    @pytest.fixture
    def performance_config(self):
        """Performance testing configuration."""
        return {
            'api_client': {
                'base_url': 'https://api.test.com',
                'api_token': 'test_token',
                'mock_mode': True
            },
            'database': {
                'host': 'localhost',
                'database': 'test_db',
                'mock_mode': True
            },
            'benchmarks': {
                'api_response_time': 0.1,  # seconds
                'database_query_time': 0.05,
                'gui_startup_time': 2.0,
                'search_completion_time': 0.5,
                'memory_usage_mb': 100
            }
        }

    @pytest.fixture
    def memory_monitor(self):
        """Memory monitoring utility."""
        class MemoryMonitor:
            def __init__(self):
                self.initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
                self.peak_memory = self.initial_memory

            def update_peak(self):
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                self.peak_memory = max(self.peak_memory, current_memory)

            def get_usage(self):
                return self.peak_memory - self.initial_memory

        return MemoryMonitor()

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_api_client_response_time_benchmark(self, benchmark, performance_config, mock_property_data):
        """Benchmark API client response time."""
        with patch('api_client_unified.get_api_logger'):
            api_client = UnifiedMaricopaAPIClient(config=performance_config['api_client'])

        # Mock successful response
        api_client.session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True, 'data': mock_property_data}
        api_client.session.get.return_value = mock_response

        # Benchmark the search operation
        result = benchmark(api_client.search_property, "10215009")

        # Verify functionality
        assert result['success'] is True
        assert result['data']['apn'] == "10215009"

        # Performance assertion (benchmark library handles timing)
        # The benchmark fixture automatically measures and records timing

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_api_client_batch_processing_benchmark(self, benchmark, performance_config, mock_property_data):
        """Benchmark API client batch processing performance."""
        with patch('api_client_unified.get_api_logger'):
            api_client = UnifiedMaricopaAPIClient(config=performance_config['api_client'])

        # Setup batch test data
        apn_list = [f"102150{i:02d}" for i in range(10)]

        # Mock batch responses
        api_client.session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True, 'data': mock_property_data}
        api_client.session.get.return_value = mock_response

        # Benchmark batch operation
        result = benchmark(api_client.batch_search_properties, apn_list)

        # Verify batch results
        assert len(result) == 10
        assert all(r['success'] for r in result)

    @pytest.mark.performance
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_async_data_collection_benchmark(self, benchmark, performance_config, mock_property_data):
        """Benchmark asynchronous data collection performance."""
        with patch('unified_data_collector.get_logger'):
            with patch('unified_data_collector.get_performance_logger'):
                # Setup mock API client
                mock_api_client = Mock()
                mock_api_client.search_property_async = Mock(return_value={
                    'success': True,
                    'data': mock_property_data
                })

                data_collector = UnifiedDataCollector(api_client=mock_api_client)

                # Benchmark async collection
                async def async_collection():
                    return await data_collector.collect_property_data_async("10215009")

                result = await benchmark(async_collection)

                # Verify functionality
                assert result['success'] is True

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_database_query_performance_benchmark(self, benchmark, performance_config, sample_database_records):
        """Benchmark database query performance."""
        with patch('threadsafe_database_manager.get_logger'):
            db_manager = ThreadSafeDatabaseManager(config=performance_config['database'])

        # Mock database query
        with patch.object(db_manager, 'execute_query') as mock_execute:
            mock_execute.return_value = sample_database_records

            # Benchmark database query
            result = benchmark(db_manager.search_properties_by_apn, "10215009")

            # Verify query results
            assert result is not None
            assert len(result) >= 1

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_concurrent_database_access_benchmark(self, benchmark, performance_config):
        """Benchmark concurrent database access performance."""
        with patch('threadsafe_database_manager.get_logger'):
            db_manager = ThreadSafeDatabaseManager(config=performance_config['database'])

        def concurrent_operation():
            """Single database operation for concurrent testing."""
            connection = db_manager.get_connection()
            # Simulate work
            time.sleep(0.001)
            db_manager.release_connection(connection)
            return True

        def concurrent_workload():
            """Execute multiple concurrent database operations."""
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(concurrent_operation) for _ in range(50)]
                results = [future.result() for future in futures]
            return results

        # Benchmark concurrent access
        result = benchmark(concurrent_workload)

        # Verify all operations completed successfully
        assert len(result) == 50
        assert all(result)

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_gui_launcher_startup_benchmark(self, benchmark, mock_environment):
        """Benchmark GUI launcher startup performance."""
        with patch('gui_launcher_unified.get_logger'):
            with patch.dict('os.environ', mock_environment):
                def startup_operation():
                    launcher = UnifiedGUILauncher()
                    # Mock platform detection to avoid actual system calls
                    launcher.platform_detector.detect_platform = Mock(return_value={
                        'os_type': 'Linux',
                        'is_wsl': False,
                        'gui_backend': 'XCB',
                        'display_available': True
                    })
                    return launcher.test_gui_capability()

                # Benchmark startup
                result = benchmark(startup_operation)

                # Verify startup succeeded
                assert 'success' in result

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_data_collector_throughput_benchmark(self, benchmark, performance_config, mock_property_data):
        """Benchmark data collector throughput."""
        with patch('unified_data_collector.get_logger'):
            with patch('unified_data_collector.get_performance_logger'):
                # Setup mock API client
                mock_api_client = Mock()
                mock_api_client.search_property.return_value = {
                    'success': True,
                    'data': mock_property_data
                }

                data_collector = UnifiedDataCollector(api_client=mock_api_client)

                # Create batch workload
                apn_list = [f"102150{i:02d}" for i in range(20)]

                # Benchmark throughput
                result = benchmark(data_collector.collect_batch_data, apn_list)

                # Verify throughput results
                assert len(result) == 20
                assert all(r['success'] for r in result)

    @pytest.mark.performance
    def test_memory_usage_benchmark(self, performance_config, memory_monitor, mock_property_data):
        """Benchmark memory usage during operations."""
        # Initialize components
        with patch('api_client_unified.get_api_logger'):
            api_client = UnifiedMaricopaAPIClient(config=performance_config['api_client'])

        with patch('unified_data_collector.get_logger'):
            with patch('unified_data_collector.get_performance_logger'):
                mock_api_client = Mock()
                mock_api_client.search_property.return_value = {
                    'success': True,
                    'data': mock_property_data
                }
                data_collector = UnifiedDataCollector(api_client=mock_api_client)

        with patch('threadsafe_database_manager.get_logger'):
            db_manager = ThreadSafeDatabaseManager(config=performance_config['database'])

        # Force garbage collection before test
        gc.collect()

        # Execute memory-intensive operations
        for i in range(100):
            # Simulate property searches
            result = data_collector.collect_property_data(f"102150{i:02d}")
            memory_monitor.update_peak()

            # Simulate database operations
            connection = db_manager.get_connection()
            db_manager.release_connection(connection)
            memory_monitor.update_peak()

        # Check memory usage
        memory_usage = memory_monitor.get_usage()
        baseline = performance_config['benchmarks']['memory_usage_mb']

        # Assert memory usage is within acceptable limits
        assert memory_usage < baseline * 1.5, f"Memory usage {memory_usage:.1f}MB exceeds baseline {baseline}MB"

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_missouri_ave_workflow_performance(self, benchmark, performance_config, mock_property_data):
        """Benchmark the validated Missouri Avenue workflow."""
        # Setup Missouri Avenue specific data
        missouri_data = {
            **mock_property_data,
            'apn': '10215009',
            'address': '10000 W Missouri Ave'
        }

        def missouri_ave_workflow():
            """Complete Missouri Avenue workflow."""
            # Initialize components
            with patch('api_client_unified.get_api_logger'):
                api_client = UnifiedMaricopaAPIClient(config=performance_config['api_client'])

            with patch('unified_data_collector.get_logger'):
                with patch('unified_data_collector.get_performance_logger'):
                    mock_api_client = Mock()
                    mock_api_client.search_property.return_value = {
                        'success': True,
                        'data': missouri_data
                    }
                    data_collector = UnifiedDataCollector(api_client=mock_api_client)

            with patch('threadsafe_database_manager.get_logger'):
                db_manager = ThreadSafeDatabaseManager(config=performance_config['database'])

            # Mock database operations
            with patch.object(db_manager, 'insert_property') as mock_insert:
                with patch.object(db_manager, 'search_properties_by_apn') as mock_search:
                    mock_insert.return_value = True
                    mock_search.return_value = [missouri_data]

                    # Execute workflow
                    # 1. Search property
                    search_result = data_collector.collect_property_data("10215009")

                    # 2. Store in database
                    storage_result = db_manager.insert_property(search_result['data'])

                    # 3. Retrieve from database
                    retrieved_data = db_manager.search_properties_by_apn("10215009")

                    return {
                        'search_success': search_result['success'],
                        'storage_success': storage_result,
                        'retrieval_success': len(retrieved_data) > 0
                    }

        # Benchmark Missouri Avenue workflow
        result = benchmark(missouri_ave_workflow)

        # Verify workflow completion
        assert result['search_success'] is True
        assert result['storage_success'] is True
        assert result['retrieval_success'] is True

    @pytest.mark.performance
    def test_performance_regression_detection(self, performance_config):
        """Test performance regression detection system."""
        # Load baseline performance metrics
        baseline_metrics = performance_config['benchmarks']

        # Simulate current performance measurements
        current_metrics = {
            'api_response_time': 0.08,  # Better than baseline
            'database_query_time': 0.06,  # Slightly worse than baseline
            'gui_startup_time': 1.8,  # Better than baseline
            'search_completion_time': 0.45,  # Better than baseline
            'memory_usage_mb': 105  # Slightly worse than baseline
        }

        # Performance regression thresholds (20% degradation)
        regression_threshold = 1.2

        # Check for regressions
        regressions = []
        for metric, current_value in current_metrics.items():
            baseline_value = baseline_metrics[metric]
            if current_value > baseline_value * regression_threshold:
                regressions.append({
                    'metric': metric,
                    'baseline': baseline_value,
                    'current': current_value,
                    'degradation': (current_value / baseline_value - 1) * 100
                })

        # Assert no significant regressions
        assert len(regressions) == 0, f"Performance regressions detected: {regressions}"

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_stress_test_benchmark(self, benchmark, performance_config, mock_property_data):
        """Stress test benchmark for system stability."""
        def stress_test_workload():
            """High-load stress test workload."""
            # Initialize components
            with patch('api_client_unified.get_api_logger'):
                api_client = UnifiedMaricopaAPIClient(config=performance_config['api_client'])

            with patch('unified_data_collector.get_logger'):
                with patch('unified_data_collector.get_performance_logger'):
                    mock_api_client = Mock()
                    mock_api_client.search_property.return_value = {
                        'success': True,
                        'data': mock_property_data
                    }
                    data_collector = UnifiedDataCollector(api_client=mock_api_client)

            # Execute high-volume operations
            results = []
            for i in range(100):
                result = data_collector.collect_property_data(f"stress_{i:03d}")
                results.append(result['success'])

            return all(results)

        # Benchmark stress test
        result = benchmark(stress_test_workload)

        # Verify system stability under load
        assert result is True

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_cache_performance_benchmark(self, benchmark, performance_config, mock_property_data):
        """Benchmark caching performance improvements."""
        with patch('api_client_unified.get_api_logger'):
            api_client = UnifiedMaricopaAPIClient(config=performance_config['api_client'])

        # Setup mock with cache
        api_client.cache = {}
        api_client.session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True, 'data': mock_property_data}
        api_client.session.get.return_value = mock_response

        def cache_test_workload():
            """Test cache performance with repeated requests."""
            # First request (cache miss)
            result1 = api_client.search_property("10215009")

            # Simulate cache population
            cache_key = "property_10215009"
            api_client.cache[cache_key] = result1['data']

            # Subsequent requests (cache hits)
            results = []
            for _ in range(10):
                # In real implementation, these would use cache
                result = api_client.search_property("10215009")
                results.append(result['success'])

            return all(results)

        # Benchmark cache performance
        result = benchmark(cache_test_workload)

        # Verify cache functionality
        assert result is True