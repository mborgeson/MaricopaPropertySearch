"""
Performance Test Suite for MaricopaPropertySearch
Tests performance improvements and validates <3 second target
"""

import time
import logging
import asyncio
from typing import Dict, Any, List
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

# MIGRATED: from config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
# MIGRATED: from database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
# MIGRATED: from api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
from api_client_performance_patch import apply_performance_patch
# MIGRATED: from parallel_api_client import HighPerformanceMaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
from performance_optimized_data_collector import PerformanceOptimizedDataCollector
from optimized_web_scraper import OptimizedWebScraperManager
from logging_config import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)

class PerformanceTestSuite:
    """Comprehensive performance testing for property data collection"""
    
    def __init__(self):
        self.config_manager = EnhancedConfigManager()
        self.db_manager = ThreadSafeDatabaseManager(self.config_manager)
        
        # Test APN - "10000 W Missouri Ave" from the issue
        self.test_apn = "12345-67-890"  # Replace with actual APN for Missouri Ave
        self.test_results = {}
        
        logger.info("Performance Test Suite initialized")
    
    def run_all_performance_tests(self) -> Dict[str, Any]:
        """Run all performance tests and compare results"""
        logger.info("Starting comprehensive performance test suite")
        
        test_results = {
            'test_apn': self.test_apn,
            'target_times': {
                'basic_search': 1.0,
                'detailed_data': 2.0,
                'complete_collection': 3.0
            },
            'results': {}
        }
        
        # Test 1: Original API Client (baseline)
        logger.info("=== TEST 1: Original API Client (Baseline) ===")
        test_results['results']['original_api'] = self.test_original_api_client()
        
        # Test 2: Patched API Client
        logger.info("=== TEST 2: Performance-Patched API Client ===")
        test_results['results']['patched_api'] = self.test_patched_api_client()
        
        # Test 3: High-Performance Parallel API Client
        logger.info("=== TEST 3: High-Performance Parallel API Client ===")
        test_results['results']['parallel_api'] = self.test_parallel_api_client()
        
        # Test 4: Performance-Optimized Data Collector
        logger.info("=== TEST 4: Performance-Optimized Data Collector ===")
        test_results['results']['optimized_collector'] = self.test_optimized_data_collector()
        
        # Test 5: Optimized Web Scraper
        logger.info("=== TEST 5: Optimized Web Scraper ===")
        test_results['results']['optimized_scraper'] = self.test_optimized_web_scraper()
        
        # Generate performance comparison report
        test_results['performance_comparison'] = self.generate_performance_comparison(test_results['results'])
        
        logger.info("Performance test suite completed")
        return test_results
    
    def test_original_api_client(self) -> Dict[str, Any]:
        """Test original API client performance (baseline)"""
        try:
            api_client = UnifiedMaricopaAPIClient(self.config_manager)
            
            # Test basic search
            start_time = time.time()
            basic_result = api_client.search_by_apn(self.test_apn)
            basic_time = time.time() - start_time
            
            # Test detailed data collection
            start_time = time.time()
            detailed_result = api_client.get_detailed_property_data(self.test_apn)
            detailed_time = time.time() - start_time
            
            # Test comprehensive data collection
            start_time = time.time()
            comprehensive_result = api_client.get_comprehensive_property_info(self.test_apn)
            comprehensive_time = time.time() - start_time
            
            return {
                'basic_search_time': basic_time,
                'detailed_data_time': detailed_time,
                'comprehensive_time': comprehensive_time,
                'total_time': comprehensive_time,
                'success': bool(comprehensive_result),
                'data_points_collected': len(comprehensive_result) if comprehensive_result else 0
            }
            
        except Exception as e:
            logger.error(f"Error testing original API client: {e}")
            return {
                'error': str(e),
                'success': False,
                'total_time': float('inf')
            }
    
    def test_patched_api_client(self) -> Dict[str, Any]:
        """Test performance-patched API client"""
        try:
            api_client = UnifiedMaricopaAPIClient(self.config_manager)
            patch = apply_performance_patch(api_client)
            
            # Test parallel detailed data collection
            start_time = time.time()
            detailed_result = patch.get_detailed_property_data_parallel(self.test_apn)
            detailed_time = time.time() - start_time
            
            # Test fast comprehensive data collection
            start_time = time.time()
            comprehensive_result = patch.get_comprehensive_property_info_fast(self.test_apn)
            comprehensive_time = time.time() - start_time
            
            # Get cache stats
            cache_stats = patch.get_cache_stats()
            
            return {
                'detailed_data_time': detailed_time,
                'comprehensive_time': comprehensive_time,
                'total_time': comprehensive_time,
                'success': bool(comprehensive_result),
                'data_points_collected': len(comprehensive_result) if comprehensive_result else 0,
                'cache_stats': cache_stats
            }
            
        except Exception as e:
            logger.error(f"Error testing patched API client: {e}")
            return {
                'error': str(e),
                'success': False,
                'total_time': float('inf')
            }
    
    def test_parallel_api_client(self) -> Dict[str, Any]:
        """Test high-performance parallel API client"""
        try:
            api_client = UnifiedMaricopaAPIClient(self.config_manager)
            
            # Test parallel detailed data collection
            start_time = time.time()
            detailed_result = api_client.get_detailed_property_data_fast(self.test_apn)
            detailed_time = time.time() - start_time
            
            # Test parallel comprehensive data collection
            start_time = time.time()
            comprehensive_result = api_client.get_comprehensive_property_info_fast(self.test_apn)
            comprehensive_time = time.time() - start_time
            
            # Get performance stats
            perf_stats = api_client.get_performance_stats()
            
            return {
                'detailed_data_time': detailed_time,
                'comprehensive_time': comprehensive_time,
                'total_time': comprehensive_time,
                'success': bool(comprehensive_result),
                'data_points_collected': len(comprehensive_result) if comprehensive_result else 0,
                'performance_stats': perf_stats
            }
            
        except Exception as e:
            logger.error(f"Error testing parallel API client: {e}")
            return {
                'error': str(e),
                'success': False,
                'total_time': float('inf')
            }
    
    def test_optimized_data_collector(self) -> Dict[str, Any]:
        """Test performance-optimized data collector with progressive loading"""
        try:
            collector = PerformanceOptimizedDataCollector(self.db_manager, self.config_manager)
            
            # Track progressive loading times
            stage_times = {}
            
            def progress_callback(results):
                stage_times[results.stage] = results.collection_time
                logger.info(f"Progressive update - Stage: {results.stage}, Time: {results.collection_time:.3f}s, Progress: {results.completion_percentage:.1f}%")
            
            # Test progressive data collection
            start_time = time.time()
            results = collector.collect_property_data_sync(self.test_apn, callback=progress_callback)
            total_time = time.time() - start_time
            
            # Get performance report
            perf_report = collector.get_performance_report()
            
            return {
                'stage_times': stage_times,
                'total_time': results.collection_time,
                'measured_time': total_time,
                'success': results.completion_percentage == 100.0,
                'data_points_collected': len(results.data),
                'errors': results.errors,
                'performance_report': perf_report
            }
            
        except Exception as e:
            logger.error(f"Error testing optimized data collector: {e}")
            return {
                'error': str(e),
                'success': False,
                'total_time': float('inf')
            }
    
    def test_optimized_web_scraper(self) -> Dict[str, Any]:
        """Test optimized web scraper performance"""
        try:
            scraper = OptimizedWebScraperManager(self.config_manager)
            
            # Test parallel scraping
            start_time = time.time()
            scrape_results = scraper.scrape_property_data_parallel(
                self.test_apn, 
                ['tax', 'sales', 'documents']
            )
            scraping_time = time.time() - start_time
            
            # Get performance report
            perf_report = scraper.get_performance_report()
            
            return {
                'scraping_time': scraping_time,
                'success': bool(scrape_results['results']),
                'data_types_collected': scrape_results['data_collected'],
                'scrape_results': scrape_results,
                'performance_report': perf_report
            }
            
        except Exception as e:
            logger.error(f"Error testing optimized web scraper: {e}")
            return {
                'error': str(e),
                'success': False,
                'scraping_time': float('inf')
            }
        finally:
            try:
                scraper.close_all_drivers()
            except:
                pass
    
    def generate_performance_comparison(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """Generate performance comparison report"""
        comparison = {
            'speed_improvements': {},
            'success_rates': {},
            'target_achievement': {},
            'recommendations': []
        }
        
        # Compare times against original (baseline)
        original_time = results.get('original_api', {}).get('total_time', float('inf'))
        
        for test_name, test_result in results.items():
            if test_name == 'original_api':
                continue
            
            test_time = test_result.get('total_time', float('inf'))
            
            if original_time and original_time != float('inf') and test_time != float('inf'):
                improvement = ((original_time - test_time) / original_time) * 100
                speedup = original_time / test_time if test_time > 0 else 0
                
                comparison['speed_improvements'][test_name] = {
                    'improvement_percentage': improvement,
                    'speedup_factor': speedup,
                    'time_saved': original_time - test_time
                }
        
        # Check target achievement
        targets = {
            'basic_search': 1.0,
            'detailed_data': 2.0, 
            'complete_collection': 3.0
        }
        
        for test_name, test_result in results.items():
            test_time = test_result.get('total_time', float('inf'))
            target_met = test_time <= targets['complete_collection']
            
            comparison['target_achievement'][test_name] = {
                'time': test_time,
                'target': targets['complete_collection'],
                'target_met': target_met,
                'margin': targets['complete_collection'] - test_time
            }
        
        # Generate recommendations
        best_performer = min(results.keys(), 
                           key=lambda x: results[x].get('total_time', float('inf')))
        
        if best_performer:
            best_time = results[best_performer].get('total_time', float('inf'))
            
            if best_time <= 3.0:
                comparison['recommendations'].append(f"SUCCESS: {best_performer} achieves <3 second target ({best_time:.3f}s)")
            else:
                comparison['recommendations'].append(f"NEEDS IMPROVEMENT: Best performer {best_performer} still exceeds 3s target ({best_time:.3f}s)")
        
        return comparison
    
    def print_performance_report(self, test_results: Dict[str, Any]):
        """Print formatted performance report"""
        print("\n" + "="*80)
        print("MARICOPA PROPERTY SEARCH PERFORMANCE TEST RESULTS")
        print("="*80)
        
        print(f"\nTest APN: {test_results['test_apn']}")
        print(f"Target Times: {test_results['target_times']}")
        
        print("\n" + "-"*60)
        print("INDIVIDUAL TEST RESULTS")
        print("-"*60)
        
        for test_name, result in test_results['results'].items():
            print(f"\n{test_name.upper()}:")
            print(f"  Total Time: {result.get('total_time', 'N/A'):.3f}s")
            print(f"  Success: {result.get('success', False)}")
            print(f"  Data Points: {result.get('data_points_collected', 'N/A')}")
            
            if 'error' in result:
                print(f"  ERROR: {result['error']}")
        
        print("\n" + "-"*60)
        print("PERFORMANCE COMPARISON")
        print("-"*60)
        
        comparison = test_results['performance_comparison']
        
        if 'speed_improvements' in comparison:
            print("\nSpeed Improvements vs Original:")
            for test_name, improvement in comparison['speed_improvements'].items():
                print(f"  {test_name}: {improvement['improvement_percentage']:.1f}% faster ({improvement['speedup_factor']:.1f}x speedup)")
        
        print("\nTarget Achievement (3 second goal):")
        for test_name, achievement in comparison['target_achievement'].items():
            status = "✓ PASS" if achievement['target_met'] else "✗ FAIL"
            print(f"  {test_name}: {achievement['time']:.3f}s {status}")
        
        print("\nRecommendations:")
        for rec in comparison['recommendations']:
            print(f"  • {rec}")
        
        print("\n" + "="*80)


def main():
    """Run performance tests"""
    try:
        # Configure logging for performance testing
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create and run test suite
        test_suite = PerformanceTestSuite()
        results = test_suite.run_all_performance_tests()
        
        # Print results
        test_suite.print_performance_report(results)
        
        # Save results to file
        import json
        from datetime import datetime
        
        results_file = Path(__file__).parent / f"performance_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nDetailed results saved to: {results_file}")
        
    except Exception as e:
        logger.error(f"Error running performance tests: {e}")
        raise


if __name__ == "__main__":
    main()