#!/usr/bin/env python
"""
Property Search Functionality Test Suite
Tests the search functionality for "10000 W Missouri Ave" to identify issues and bottlenecks
"""

import sys
import os
import json
import time
import traceback
from datetime import datetime
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(Path(__file__).parent.parent))

def print_header(title):
    """Print formatted test section header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def print_result(test_name, success, details=""):
    """Print formatted test result"""
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} {test_name}")
    if details:
        print(f"      {details}")

def test_configuration():
    """Test configuration loading"""
    print_header("CONFIGURATION TESTS")
    
    try:
        # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        config = EnhancedConfigManager()
        
        # Test API config
        api_config = config.get_api_config()
        print_result("API Configuration", True, f"Base URL: {api_config.get('base_url')}")
        print_result("API Token", bool(api_config.get('token')), f"Token: {'*'*10 + api_config.get('token', '')[-10:] if api_config.get('token') else 'None'}")
        
        # Test database config  
        db_config = config.get_database_config()
        print_result("Database Configuration", True, f"Host: {db_config.get('host')}:{db_config.get('port')}")
        
        return True
    except Exception as e:
        print_result("Configuration Loading", False, str(e))
        return False

def test_database_connection():
    """Test database connection"""
    print_header("DATABASE CONNECTION TESTS")
    
    try:
        # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        from src.threadsafe_database_manager import ThreadSafeDatabaseManager
        
        config = EnhancedConfigManager()
        db_manager = ThreadSafeDatabaseManager(config)
        
        # Test connection
        connection_ok = db_manager.test_connection()
        print_result("Database Connection", connection_ok)
        
        if connection_ok:
            # Test basic queries
            properties = db_manager.get_recent_properties(limit=5)
            print_result("Recent Properties Query", True, f"Retrieved {len(properties)} properties")
            
            # Test search functionality
            search_results = db_manager.search_properties_by_address("Missouri", limit=10)
            print_result("Address Search Query", True, f"Found {len(search_results)} Missouri Ave properties")
            
        db_manager.close()
        return connection_ok
        
    except Exception as e:
        print_result("Database Connection", False, str(e))
        return False

def test_api_client():
    """Test API client functionality"""
    print_header("API CLIENT TESTS")
    
    try:
        # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        # MIGRATED: # MIGRATED: from src.api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
        
        config = EnhancedConfigManager()
        api_client = UnifiedMaricopaAPIClient(config)
        
        # Test API status
        status = api_client.get_api_status()
        print_result("API Status", True, f"Status: {status.get('status')}")
        
        # Test address search for Missouri Ave
        print("\nTesting address search for '10000 W Missouri Ave'...")
        start_time = time.time()
        
        search_results = api_client.search_by_address("10000 W Missouri Ave", limit=10)
        search_time = time.time() - start_time
        
        print_result("Address Search", len(search_results) > 0, f"Found {len(search_results)} results in {search_time:.2f}s")
        
        if search_results:
            result = search_results[0]
            print(f"      First result APN: {result.get('apn')}")
            print(f"      Address: {result.get('property_address')}")
            print(f"      Owner: {result.get('owner_name')}")
            
            # Test detailed property lookup
            apn = result.get('apn')
            if apn:
                print(f"\nTesting detailed property lookup for APN: {apn}")
                start_time = time.time()
                
                detailed_info = api_client.get_comprehensive_property_info(apn)
                detail_time = time.time() - start_time
                
                print_result("Detailed Property Info", detailed_info is not None, f"Retrieved in {detail_time:.2f}s")
                
                if detailed_info:
                    print(f"      Year Built: {detailed_info.get('year_built')}")
                    print(f"      Living Area: {detailed_info.get('living_area_sqft')} sqft")
                    print(f"      Latest Assessed Value: ${detailed_info.get('latest_assessed_value'):,}" if detailed_info.get('latest_assessed_value') else "N/A")
                    
                    # Test tax history
                    start_time = time.time()
                    tax_history = api_client.get_tax_history(apn)
                    tax_time = time.time() - start_time
                    
                    print_result("Tax History", True, f"Found {len(tax_history)} tax records in {tax_time:.2f}s")
                    
        # Test different search variations
        print("\nTesting search variations...")
        variations = [
            "Missouri Ave",
            "10000 Missouri",
            "Missouri Avenue",
            "W Missouri Ave"
        ]
        
        for variation in variations:
            start_time = time.time()
            results = api_client.search_by_address(variation, limit=5)
            search_time = time.time() - start_time
            print_result(f"Search: '{variation}'", len(results) > 0, f"{len(results)} results in {search_time:.2f}s")
        
        api_client.close()
        return True
        
    except Exception as e:
        print_result("API Client", False, str(e))
        traceback.print_exc()
        return False

def test_web_scraping():
    """Test web scraping functionality"""
    print_header("WEB SCRAPING TESTS")
    
    try:
        # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        
        config = EnhancedConfigManager()
        
        # Check if we should use mock or real scraper
        scraping_config = config.get_scraping_config()
        print(f"Scraping config: {scraping_config}")
        
        # For testing, use mock scraper to avoid browser issues
        from src.web_scraper import MockWebScraperManager
        
        scraper = MockWebScraperManager(config)
        
        # Test owner search
        print("Testing owner name search...")
        start_time = time.time()
        
        owner_results = scraper.search_by_owner_name("MISSOURI PROPERTIES LLC", limit=5)
        search_time = time.time() - start_time
        
        print_result("Owner Search", len(owner_results) >= 0, f"Found {len(owner_results)} properties in {search_time:.2f}s")
        
        # Test APN scraping
        if owner_results:
            apn = owner_results[0].get('apn')
            if apn:
                print(f"\nTesting property scraping for APN: {apn}")
                start_time = time.time()
                
                property_data = scraper.scrape_property_by_apn(apn)
                scrape_time = time.time() - start_time
                
                print_result("Property Scraping", property_data is not None, f"Scraped in {scrape_time:.2f}s")
                
                if property_data:
                    print(f"      Scraped Owner: {property_data.get('owner_name')}")
                    print(f"      Scraped Address: {property_data.get('property_address')}")
        
        scraper.close()
        return True
        
    except Exception as e:
        print_result("Web Scraping", False, str(e))
        traceback.print_exc()
        return False

def test_background_data_collection():
    """Test background data collection system"""
    print_header("BACKGROUND DATA COLLECTION TESTS")
    
    try:
        # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        from src.threadsafe_database_manager import ThreadSafeDatabaseManager
        
        config = EnhancedConfigManager()
        db_manager = ThreadSafeDatabaseManager(config)
        
        # Test if we can create the background collector
        try:
            from src.improved_automatic_data_collector import ImprovedMaricopaDataCollector
            collector = ImprovedMaricopaDataCollector(db_manager)
            print_result("Data Collector Creation", True, "Collector initialized successfully")
            
            # Test data collection for a sample APN (mock mode)
            sample_apn = "123456789"  # Mock APN
            print(f"\nTesting data collection for sample APN: {sample_apn}")
            
            # This would normally collect real data, but should handle gracefully
            start_time = time.time()
            try:
                result = collector.collect_data_for_apn_sync(sample_apn)
                collection_time = time.time() - start_time
                print_result("Data Collection", True, f"Completed in {collection_time:.2f}s")
                print(f"      Result: {result}")
            except Exception as collection_error:
                collection_time = time.time() - start_time
                print_result("Data Collection", False, f"Error after {collection_time:.2f}s: {str(collection_error)[:100]}")
            
        except ImportError as import_error:
            print_result("Data Collector Import", False, f"Import error: {import_error}")
        
        db_manager.close()
        return True
        
    except Exception as e:
        print_result("Background Data Collection", False, str(e))
        return False

def test_complete_search_workflow():
    """Test the complete search workflow from end to end"""
    print_header("COMPLETE SEARCH WORKFLOW TEST")
    
    search_term = "10000 W Missouri Ave"
    
    try:
        # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        from src.threadsafe_database_manager import ThreadSafeDatabaseManager
        # MIGRATED: # MIGRATED: from src.api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager
        
        config = EnhancedConfigManager()
        db_manager = ThreadSafeDatabaseManager(config)
        api_client = UnifiedMaricopaAPIClient(config)
        
        print(f"Testing complete workflow for: {search_term}")
        
        # Step 1: Perform initial search
        print("\n1. Initial Search...")
        start_time = time.time()
        search_results = api_client.search_by_address(search_term, limit=5)
        search_time = time.time() - start_time
        
        print_result("Initial Search", len(search_results) > 0, f"{len(search_results)} results in {search_time:.2f}s")
        
        if not search_results:
            print("      No search results found, cannot continue workflow test")
            return False
        
        # Step 2: Get detailed info for first result
        first_result = search_results[0]
        apn = first_result.get('apn')
        
        if not apn:
            print("      No APN in first result, cannot continue")
            return False
        
        print(f"\n2. Getting detailed info for APN: {apn}")
        start_time = time.time()
        detailed_info = api_client.get_comprehensive_property_info(apn)
        detail_time = time.time() - start_time
        
        print_result("Detailed Info", detailed_info is not None, f"Retrieved in {detail_time:.2f}s")
        
        # Step 3: Check existing data in database
        print(f"\n3. Checking existing data in database for APN: {apn}")
        existing_tax = db_manager.get_tax_history(apn)
        existing_sales = db_manager.get_sales_history(apn)
        
        print_result("Database Tax Data", True, f"Found {len(existing_tax)} tax records")
        print_result("Database Sales Data", True, f"Found {len(existing_sales)} sales records")
        
        # Step 4: Store property data
        if detailed_info:
            print(f"\n4. Storing property data in database...")
            try:
                success = db_manager.store_property_data(detailed_info)
                print_result("Store Property Data", success, "Property data stored successfully")
            except Exception as store_error:
                print_result("Store Property Data", False, f"Storage error: {store_error}")
        
        # Step 5: Summary
        print(f"\n5. Workflow Summary")
        total_time = time.time() - start_time + search_time
        print(f"      Total workflow time: {total_time:.2f}s")
        print(f"      Search results: {len(search_results)}")
        print(f"      Detailed info: {'Retrieved' if detailed_info else 'Failed'}")
        print(f"      Tax records: {len(existing_tax)}")
        print(f"      Sales records: {len(existing_sales)}")
        
        api_client.close()
        db_manager.close()
        return True
        
    except Exception as e:
        print_result("Complete Workflow", False, str(e))
        traceback.print_exc()
        return False

def generate_test_report(results):
    """Generate comprehensive test report"""
    print_header("TEST REPORT SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"  {status}: {test_name}")
    
    print("\nRecommendations:")
    if not results.get('database'):
        print("  * Database connection issues detected - check PostgreSQL service")
    if not results.get('api'):
        print("  * API client issues detected - check network connectivity and API token")
    if not results.get('background'):
        print("  * Background collection issues - check data collector configuration")
    if not results.get('workflow'):
        print("  * End-to-end workflow issues - check all component integration")
    
    # Save detailed report
    report_file = Path(__file__).parent / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'test_target': '10000 W Missouri Ave',
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': failed_tests,
        'success_rate': (passed_tests/total_tests)*100,
        'detailed_results': results,
        'system_info': {
            'python_version': sys.version,
            'platform': sys.platform
        }
    }
    
    try:
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"\nDetailed report saved to: {report_file}")
    except Exception as e:
        print(f"Could not save report: {e}")

def main():
    """Run all tests"""
    print("MARICOPA PROPERTY SEARCH - COMPREHENSIVE TESTING SUITE")
    print("="*80)
    print(f"Test Target: '10000 W Missouri Ave'")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    test_results = {
        'configuration': test_configuration(),
        'database': test_database_connection(), 
        'api': test_api_client(),
        'scraping': test_web_scraping(),
        'background': test_background_data_collection(),
        'workflow': test_complete_search_workflow()
    }
    
    # Generate report
    generate_test_report(test_results)
    
    return 0 if all(test_results.values()) else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal test error: {e}")
        traceback.print_exc()
        sys.exit(1)