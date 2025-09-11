"""
Load testing and concurrent user simulation
"""

import pytest
import time
import threading
import concurrent.futures
from unittest.mock import Mock, patch
import psutil
import os
from statistics import mean, median, stdev

# Load testing parameters
CONCURRENT_USERS = [1, 5, 10, 25]
SEARCH_DURATION_SECONDS = 30
TARGET_RESPONSE_TIME_95TH = 2.0  # 95th percentile under 2 seconds
TARGET_ERROR_RATE = 0.05  # Less than 5% errors

@pytest.mark.performance
@pytest.mark.slow
class TestConcurrentUserLoad:
    """Test application behavior under concurrent user load"""
    
    def test_single_user_baseline_performance(self, test_database, app_config, performance_timer):
        """Establish baseline performance with single user"""
        
        response_times = []
        
        # Perform 20 searches to establish baseline
        for i in range(20):
            performance_timer.start()
            
            results = test_database.search_properties_by_owner(f"SMITH", limit=10)
            
            elapsed = performance_timer.stop()
            response_times.append(elapsed)
            
            # Small delay between searches
            time.sleep(0.1)
            
        avg_response = mean(response_times)
        max_response = max(response_times)
        percentile_95 = sorted(response_times)[int(len(response_times) * 0.95)]
        
        # Baseline performance requirements
        assert avg_response < 1.0, f"Average response time {avg_response:.3f}s should be < 1s"
        assert max_response < 2.0, f"Max response time {max_response:.3f}s should be < 2s"
        assert percentile_95 < 1.5, f"95th percentile {percentile_95:.3f}s should be < 1.5s"
        
        return {
            'avg_response': avg_response,
            'max_response': max_response,
            '95th_percentile': percentile_95,
            'response_times': response_times
        }
        
    def test_concurrent_database_access(self, test_database, app_config):
        """Test database performance under concurrent access"""
        
        def concurrent_search(user_id, search_term, results_dict):
            """Simulate single user performing searches"""
            user_response_times = []
            user_errors = 0
            
            start_time = time.time()
            
            while time.time() - start_time < 10:  # 10 second test
                try:
                    search_start = time.perf_counter()
                    
                    results = test_database.search_properties_by_owner(
                        f"{search_term}_{user_id % 3}", limit=10
                    )
                    
                    search_time = time.perf_counter() - search_start
                    user_response_times.append(search_time)
                    
                    # Brief pause between searches
                    time.sleep(0.2)
                    
                except Exception as e:
                    user_errors += 1
                    
            results_dict[user_id] = {
                'response_times': user_response_times,
                'errors': user_errors
            }
            
        # Test with different concurrent user counts
        for user_count in CONCURRENT_USERS:
            print(f"\nTesting with {user_count} concurrent users...")
            
            results_dict = {}
            threads = []
            
            # Start concurrent users
            for user_id in range(user_count):
                thread = threading.Thread(
                    target=concurrent_search,
                    args=(user_id, "CONCURRENT_TEST", results_dict)
                )
                threads.append(thread)
                thread.start()
                
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
                
            # Analyze results
            all_response_times = []
            total_errors = 0
            
            for user_results in results_dict.values():
                all_response_times.extend(user_results['response_times'])
                total_errors += user_results['errors']
                
            if all_response_times:
                avg_response = mean(all_response_times)
                percentile_95 = sorted(all_response_times)[int(len(all_response_times) * 0.95)]
                error_rate = total_errors / (len(all_response_times) + total_errors) if (len(all_response_times) + total_errors) > 0 else 0
                
                print(f"  Users: {user_count}, Avg Response: {avg_response:.3f}s, "
                      f"95th Percentile: {percentile_95:.3f}s, Error Rate: {error_rate:.3%}")
                
                # Performance requirements scale with user count
                max_avg_response = 1.0 + (user_count * 0.1)  # Allow some degradation
                max_95th_percentile = 2.0 + (user_count * 0.1)
                
                assert avg_response < max_avg_response, f"Average response {avg_response:.3f}s too high for {user_count} users"
                assert percentile_95 < max_95th_percentile, f"95th percentile {percentile_95:.3f}s too high for {user_count} users"
                assert error_rate < TARGET_ERROR_RATE, f"Error rate {error_rate:.3%} too high"
                
    def test_memory_usage_under_load(self, test_database, app_config):
        """Test memory usage remains stable under load"""
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        def memory_intensive_search(iterations):
            """Perform searches that could cause memory leaks"""
            for i in range(iterations):
                # Large result set search
                results = test_database.search_properties_by_owner("", limit=100)
                
                # Process results (could cause memory accumulation)
                processed = [
                    {
                        'apn': r.get('apn', ''),
                        'owner': r.get('owner_name', ''),
                        'address': r.get('property_address', ''),
                        'value': r.get('assessed_value', 0)
                    }
                    for r in results
                ]
                
                # Explicit cleanup
                del results
                del processed
                
        # Run memory-intensive operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(memory_intensive_search, 20)
                for _ in range(5)
            ]
            
            # Monitor memory during execution
            memory_samples = []
            for _ in range(10):
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                time.sleep(1)
                
            # Wait for completion
            concurrent.futures.wait(futures)
            
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        max_memory = max(memory_samples)
        memory_growth = final_memory - initial_memory
        
        print(f"Memory - Initial: {initial_memory:.2f}MB, Max: {max_memory:.2f}MB, "
              f"Final: {final_memory:.2f}MB, Growth: {memory_growth:.2f}MB")
        
        # Memory requirements
        assert memory_growth < 100, f"Memory growth {memory_growth:.2f}MB too high"
        assert max_memory < initial_memory + 150, f"Peak memory {max_memory:.2f}MB too high"
        
    def test_connection_pool_under_load(self, test_database, app_config):
        """Test database connection pool behavior under load"""
        
        def stress_connections(user_id, duration_seconds):
            """Stress test database connections"""
            start_time = time.time()
            operations = 0
            errors = 0
            
            while time.time() - start_time < duration_seconds:
                try:
                    # Get connection from pool
                    with test_database.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM properties")
                        result = cursor.fetchone()
                        
                    operations += 1
                    
                except Exception as e:
                    errors += 1
                    print(f"Connection error for user {user_id}: {e}")
                    
                # Brief pause
                time.sleep(0.05)
                
            return {'operations': operations, 'errors': errors}
            
        # Test connection pool with high concurrency
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(stress_connections, user_id, 5)
                for user_id in range(20)
            ]
            
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
        total_operations = sum(r['operations'] for r in results)
        total_errors = sum(r['errors'] for r in results)
        error_rate = total_errors / (total_operations + total_errors) if (total_operations + total_errors) > 0 else 0
        
        print(f"Connection pool test - Operations: {total_operations}, Errors: {total_errors}, "
              f"Error Rate: {error_rate:.3%}")
        
        # Connection pool requirements
        assert total_operations > 100, "Should complete substantial number of operations"
        assert error_rate < 0.01, f"Connection error rate {error_rate:.3%} too high"

@pytest.mark.performance
@pytest.mark.slow
class TestScalabilityLimits:
    """Test application scalability limits and breaking points"""
    
    def test_large_result_set_handling(self, test_database, performance_timer):
        """Test handling of large result sets"""
        
        # Create large test dataset if not exists
        self._ensure_large_dataset(test_database, 1000)
        
        result_set_sizes = [10, 50, 100, 500]
        
        for size in result_set_sizes:
            performance_timer.start()
            
            results = test_database.search_properties_by_owner("", limit=size)
            
            elapsed = performance_timer.stop()
            
            print(f"Result set size {size}: {elapsed:.3f}s")
            
            # Performance should scale reasonably
            max_time = 0.5 + (size * 0.002)  # Base time + linear scale
            assert elapsed < max_time, f"Large result set ({size}) took {elapsed:.3f}s, max {max_time:.3f}s"
            assert len(results) <= size, f"Should not return more than {size} results"
            
    def test_sustained_load_performance(self, test_database):
        """Test performance under sustained load over time"""
        
        def sustained_search_load():
            """Generate sustained search load"""
            search_terms = ["SMITH", "JONES", "WILLIAMS", "BROWN", "DAVIS"]
            response_times = []
            
            start_time = time.time()
            
            while time.time() - start_time < SEARCH_DURATION_SECONDS:
                term = search_terms[int(time.time()) % len(search_terms)]
                
                search_start = time.perf_counter()
                
                try:
                    results = test_database.search_properties_by_owner(term, limit=20)
                    search_time = time.perf_counter() - search_start
                    response_times.append(search_time)
                    
                except Exception as e:
                    print(f"Search error: {e}")
                    
                time.sleep(0.1)  # 10 searches per second per user
                
            return response_times
            
        # Run sustained load with multiple users
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(sustained_search_load)
                for _ in range(10)
            ]
            
            all_response_times = []
            for future in concurrent.futures.as_completed(futures):
                all_response_times.extend(future.result())
                
        if all_response_times:
            # Analyze sustained performance
            early_times = all_response_times[:len(all_response_times)//3]
            late_times = all_response_times[-len(all_response_times)//3:]
            
            early_avg = mean(early_times)
            late_avg = mean(late_times)
            overall_avg = mean(all_response_times)
            overall_95th = sorted(all_response_times)[int(len(all_response_times) * 0.95)]
            
            print(f"Sustained load - Early avg: {early_avg:.3f}s, Late avg: {late_avg:.3f}s, "
                  f"Overall avg: {overall_avg:.3f}s, 95th: {overall_95th:.3f}s")
            
            # Performance should not degrade significantly over time
            degradation = late_avg / early_avg if early_avg > 0 else 1
            assert degradation < 1.5, f"Performance degraded {degradation:.2f}x over time"
            assert overall_avg < 1.5, f"Overall average {overall_avg:.3f}s too slow"
            assert overall_95th < TARGET_RESPONSE_TIME_95TH, f"95th percentile {overall_95th:.3f}s exceeds target"
            
    def test_resource_exhaustion_handling(self, test_database, app_config):
        """Test behavior when system resources are exhausted"""
        
        def resource_intensive_operation(operation_id):
            """Simulate resource-intensive operations"""
            try:
                # Memory-intensive operation
                large_data = []
                for i in range(1000):
                    large_data.append({
                        'id': f"{operation_id}_{i}",
                        'data': 'x' * 1000  # 1KB per item
                    })
                    
                # Database-intensive operation
                results = test_database.search_properties_by_owner("", limit=100)
                
                # Processing-intensive operation
                processed = [
                    {
                        'processed_data': str(item).upper(),
                        'length': len(str(item))
                    }
                    for item in large_data[:100]
                ]
                
                return len(processed)
                
            except Exception as e:
                return f"Error: {e}"
                
        # Simulate resource exhaustion
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(resource_intensive_operation, op_id)
                for op_id in range(50)
            ]
            
            results = []
            errors = 0
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=10)
                    if isinstance(result, str) and result.startswith("Error"):
                        errors += 1
                    else:
                        results.append(result)
                except Exception as e:
                    errors += 1
                    
        success_rate = len(results) / (len(results) + errors) if (len(results) + errors) > 0 else 0
        
        print(f"Resource exhaustion test - Successes: {len(results)}, Errors: {errors}, "
              f"Success rate: {success_rate:.3%}")
        
        # Should handle resource pressure gracefully
        assert success_rate > 0.7, f"Success rate {success_rate:.3%} too low under resource pressure"
        
    def _ensure_large_dataset(self, db_manager, min_count):
        """Ensure database has large dataset for testing"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM properties")
                current_count = cursor.fetchone()[0]
                
                if current_count < min_count:
                    # Add more test data
                    for i in range(current_count, min_count):
                        cursor.execute("""
                            INSERT INTO properties (
                                apn, owner_name, property_address, city, zip_code,
                                property_type, assessed_value, market_value,
                                square_feet, year_built, last_updated
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                            )
                        """, (
                            f"LOAD-{i:05d}-{i%100:02d}X",
                            f"LOAD TEST OWNER {i}",
                            f"{1000 + i} LOAD TEST ST",
                            "PHOENIX",
                            "85001",
                            "RESIDENTIAL",
                            150000 + (i * 500),
                            165000 + (i * 500),
                            1200 + (i * 5),
                            1980 + (i % 40)
                        ))
                        
                        # Commit in batches
                        if i % 100 == 0:
                            conn.commit()
                            
                    conn.commit()
                    print(f"Added {min_count - current_count} test properties for load testing")
                    
        except Exception as e:
            print(f"Error creating large dataset: {e}")

@pytest.mark.performance
class TestPerformanceDegradation:
    """Test performance degradation patterns"""
    
    def test_cache_effectiveness_under_load(self, app_config):
        """Test that caching remains effective under load"""
        from search_cache import SearchCache
        
        cache = SearchCache(max_size=100, ttl_seconds=300)
        
        # Populate cache with common searches
        common_searches = [
            ("SMITH", [{"apn": "101-01-001A"}]),
            ("JONES", [{"apn": "102-02-001B"}]),
            ("WILLIAMS", [{"apn": "103-03-001C"}])
        ]
        
        for search_term, results in common_searches:
            cache.put(f"owner_{search_term}", results)
            
        def concurrent_cache_access(user_id, access_count):
            """Simulate concurrent cache access"""
            cache_hits = 0
            cache_misses = 0
            
            for i in range(access_count):
                search_term = common_searches[i % len(common_searches)][0]
                key = f"owner_{search_term}"
                
                result = cache.get(key)
                if result:
                    cache_hits += 1
                else:
                    cache_misses += 1
                    
            return {'hits': cache_hits, 'misses': cache_misses}
            
        # Test cache under concurrent load
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(concurrent_cache_access, user_id, 50)
                for user_id in range(10)
            ]
            
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
        total_hits = sum(r['hits'] for r in results)
        total_misses = sum(r['misses'] for r in results)
        hit_rate = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0
        
        print(f"Cache performance - Hits: {total_hits}, Misses: {total_misses}, "
              f"Hit rate: {hit_rate:.3%}")
        
        # Cache should remain effective under load
        assert hit_rate > 0.8, f"Cache hit rate {hit_rate:.3%} too low"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance", "--tb=short"])