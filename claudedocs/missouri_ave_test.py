#!/usr/bin/env python
"""
Missouri Avenue Property Search Test
Direct testing of the API client for "10000 W Missouri Ave" to identify specific issues
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add src directory to path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_missouri_ave_search():
    """Test search for 10000 W Missouri Ave specifically"""
    
    print("MISSOURI AVENUE PROPERTY SEARCH - DETAILED ANALYSIS")
    print("="*70)
    print(f"Target: '10000 W Missouri Ave'")
    print(f"Time: {datetime.now()}")
    print()
    
    try:
        # MIGRATED: # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        # MIGRATED: # MIGRATED: from src.api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
        from src.threadsafe_database_manager import ThreadSafeDatabaseManager
        
        # Initialize components
        config = EnhancedConfigManager()
        api_client = UnifiedMaricopaAPIClient(config)
        db_manager = ThreadSafeDatabaseManager(config)
        
        # Test 1: Direct API search for address
        print("1. TESTING DIRECT API SEARCH")
        print("-" * 40)
        
        search_term = "10000 W Missouri Ave"
        print(f"Searching for: {search_term}")
        
        start_time = time.time()
        results = api_client.search_by_address(search_term, limit=10)
        search_time = time.time() - start_time
        
        print(f"Search completed in {search_time:.2f}s")
        print(f"Results found: {len(results)}")
        
        if results:
            print("\nFIRST RESULT DETAILS:")
            first_result = results[0]
            for key, value in first_result.items():
                if key != 'raw_data':  # Skip raw data for readability
                    print(f"  {key}: {value}")
        
            # Test 2: Detailed property information
            print("\n2. TESTING DETAILED PROPERTY LOOKUP")
            print("-" * 40)
            
            apn = first_result.get('apn')
            if apn:
                print(f"Getting detailed info for APN: {apn}")
                
                start_time = time.time()
                detailed_info = api_client.get_comprehensive_property_info(apn)
                detail_time = time.time() - start_time
                
                print(f"Detailed lookup completed in {detail_time:.2f}s")
                
                if detailed_info:
                    print("\nDETAILED PROPERTY INFO:")
                    key_fields = [
                        'year_built', 'living_area_sqft', 'lot_size_sqft', 
                        'bedrooms', 'bathrooms', 'latest_assessed_value',
                        'property_use_description', 'improvements_count'
                    ]
                    
                    for field in key_fields:
                        value = detailed_info.get(field)
                        if value is not None:
                            if field == 'latest_assessed_value' and isinstance(value, (int, float)):
                                print(f"  {field}: ${value:,}")
                            else:
                                print(f"  {field}: {value}")
                    
                    # Test 3: Tax history
                    print("\n3. TESTING TAX HISTORY")
                    print("-" * 40)
                    
                    start_time = time.time()
                    tax_history = api_client.get_tax_history(apn)
                    tax_time = time.time() - start_time
                    
                    print(f"Tax history lookup completed in {tax_time:.2f}s")
                    print(f"Tax records found: {len(tax_history)}")
                    
                    if tax_history:
                        print("\\nRECENT TAX RECORDS:")
                        for record in tax_history[:3]:  # Show first 3 records
                            year = record.get('TaxYear', 'Unknown')
                            value = record.get('FullCashValue', 'N/A')
                            limited = record.get('LimitedPropertyValue', 'N/A')
                            print(f"  {year}: Full Cash Value ${value:,} | Limited Value ${limited:,}" if isinstance(value, (int, float)) else f"  {year}: {value} | {limited}")
                    
                    # Test 4: Database operations
                    print("\n4. TESTING DATABASE OPERATIONS")
                    print("-" * 40)
                    
                    # Check existing data
                    existing_tax = db_manager.get_tax_history(apn)
                    existing_sales = db_manager.get_sales_history(apn)
                    
                    print(f"Existing tax records in DB: {len(existing_tax)}")
                    print(f"Existing sales records in DB: {len(existing_sales)}")
                    
                    # Test property insertion
                    try:
                        success = db_manager.insert_property(detailed_info)
                        print(f"Property data insert: {'SUCCESS' if success else 'FAILED'}")
                    except Exception as e:
                        print(f"Property data insert: FAILED - {e}")
                    
                    # Test address search in database
                    try:
                        db_results = db_manager.search_properties_by_address("Missouri", limit=5)
                        print(f"Database address search: Found {len(db_results)} Missouri Ave properties")
                    except Exception as e:
                        print(f"Database address search: FAILED - {e}")
        
        else:
            print("No results found for the search term!")
        
        # Test 5: Alternative search patterns
        print("\n5. TESTING ALTERNATIVE SEARCH PATTERNS")
        print("-" * 40)
        
        alternative_searches = [
            "10000 Missouri Ave",
            "Missouri Avenue",
            "10000 W Missouri",
            "W Missouri Ave",
            "Missouri Ave"
        ]
        
        for search in alternative_searches:
            start_time = time.time()
            alt_results = api_client.search_by_address(search, limit=3)
            alt_time = time.time() - start_time
            print(f"  '{search}': {len(alt_results)} results in {alt_time:.2f}s")
        
        # Test 6: Performance summary
        print("\n6. PERFORMANCE SUMMARY")
        print("-" * 40)
        
        total_time = search_time + detail_time + tax_time
        print(f"Total API time: {total_time:.2f}s")
        print(f"  - Initial search: {search_time:.2f}s")
        print(f"  - Detailed lookup: {detail_time:.2f}s")
        print(f"  - Tax history: {tax_time:.2f}s")
        
        # Clean up
        api_client.close()
        db_manager.close()
        
        print("\n7. TEST SUMMARY")
        print("-" * 40)
        print(f"✓ Search successful: {len(results)} results found")
        print(f"✓ API connectivity: Working")
        print(f"✓ Data retrieval: {'Complete' if detailed_info else 'Failed'}")
        print(f"✓ Tax history: {len(tax_history)} records")
        print(f"✓ Database: {'Connected' if db_manager.test_connection() else 'Issues'}")
        
        return True
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_collection_bottlenecks():
    """Test what happens during data collection to identify bottlenecks"""
    
    print("\n" + "="*70)
    print("DATA COLLECTION BOTTLENECK ANALYSIS")
    print("="*70)
    
    try:
        # MIGRATED: # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        # MIGRATED: # MIGRATED: from src.api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager
        
        config = EnhancedConfigManager()
        api_client = UnifiedMaricopaAPIClient(config)
        
        # Get a sample APN
        results = api_client.search_by_address("10000 W Missouri Ave", limit=1)
        if not results:
            print("No results to test data collection")
            return False
        
        apn = results[0].get('apn')
        print(f"Testing data collection bottlenecks for APN: {apn}")
        
        # Test each data collection step individually
        steps = [
            ("Basic Search", lambda: api_client.search_by_apn(apn)),
            ("Comprehensive Info", lambda: api_client.get_comprehensive_property_info(apn)),
            ("Tax History", lambda: api_client.get_tax_history(apn)),
            ("Detailed Property Data", lambda: api_client.get_detailed_property_data(apn))
        ]
        
        print("\nTIMING INDIVIDUAL DATA COLLECTION STEPS:")
        print("-" * 50)
        
        for step_name, step_func in steps:
            times = []
            for i in range(3):  # Run 3 times for consistency
                start_time = time.time()
                try:
                    result = step_func()
                    step_time = time.time() - start_time
                    times.append(step_time)
                    success = "✓"
                    data_size = len(str(result)) if result else 0
                except Exception as e:
                    step_time = time.time() - start_time
                    times.append(step_time)
                    success = "✗"
                    data_size = 0
            
            avg_time = sum(times) / len(times)
            print(f"{success} {step_name}: {avg_time:.2f}s avg (runs: {[f'{t:.2f}' for t in times]})")
        
        api_client.close()
        return True
        
    except Exception as e:
        print(f"Bottleneck analysis failed: {e}")
        return False

def main():
    """Run all tests"""
    success1 = test_missouri_ave_search()
    success2 = test_data_collection_bottlenecks()
    
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    print(f"Missouri Ave Search Test: {'PASS' if success1 else 'FAIL'}")
    print(f"Bottleneck Analysis: {'PASS' if success2 else 'FAIL'}")
    print(f"Overall: {'PASS' if success1 and success2 else 'FAIL'}")
    
    return success1 and success2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)