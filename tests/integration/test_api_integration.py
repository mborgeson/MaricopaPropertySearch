#!/usr/bin/env python
"""
Test script for real Maricopa County API integration
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
# MIGRATED: from api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
from logging_config import setup_logging
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager

def test_api_integration():
    """Test the real API integration"""
    
    # Setup logging
    setup_logging()
    
    print("Testing Maricopa County API Integration...")
    print("=" * 50)
    
    try:
        # Initialize components
        config_manager = EnhancedConfigManager()
        api_client = UnifiedMaricopaAPIClient(config_manager)
        
        # Test API status (mock data is fine for this)
        print("\n1. Testing API status...")
        status = api_client.get_api_status()
        print(f"   API Status: {status.get('status', 'Unknown')}")
        
        # Test a real search - use a sample APN
        test_apn = "13304014A"
        print(f"\n2. Testing property search for APN: {test_apn}")
        
        try:
            property_data = api_client.search_by_apn(test_apn)
            if property_data:
                print(f"   [OK] Found property data for {test_apn}")
                print(f"   Owner: {property_data.get('owner_name', 'N/A')}")
                print(f"   Address: {property_data.get('property_address', 'N/A')}")
            else:
                print(f"   [ERROR] No property data found for {test_apn}")
        except Exception as e:
            print(f"   [ERROR] Error searching for {test_apn}: {e}")
        
        # Test comprehensive data collection
        print(f"\n3. Testing comprehensive property data collection for APN: {test_apn}")
        
        try:
            comprehensive_data = api_client.get_comprehensive_property_info(test_apn)
            if comprehensive_data:
                print(f"   [OK] Retrieved comprehensive data")
                print(f"   Latest assessed value: ${comprehensive_data.get('latest_assessed_value', 'N/A')}")
                print(f"   Year built: {comprehensive_data.get('year_built', 'N/A')}")
                print(f"   Living area: {comprehensive_data.get('living_area_sqft', 'N/A')} sq ft")
                
                # Check for detailed data sources
                detailed_data = comprehensive_data.get('detailed_data', {})
                print(f"   Data sources: {list(detailed_data.keys())}")
                
                # Check valuation history
                if 'valuation_history' in comprehensive_data:
                    val_count = len(comprehensive_data['valuation_history'])
                    print(f"   Valuation records: {val_count}")
                
            else:
                print(f"   [ERROR] No comprehensive data found for {test_apn}")
        except Exception as e:
            print(f"   [ERROR] Error getting comprehensive data: {e}")
        
        # Test search functionality
        print(f"\n4. Testing property search...")
        
        try:
            # Search for a common property type
            search_results = api_client.search_all_property_types("1330", limit=5)
            
            total_results = sum(len(results) for results in search_results.values())
            print(f"   [OK] Search returned {total_results} total results")
            
            for category, results in search_results.items():
                if results:
                    print(f"   {category}: {len(results)} results")
                    
        except Exception as e:
            print(f"   [ERROR] Error in property search: {e}")
        
        print(f"\n5. Testing tax history endpoint...")
        
        try:
            tax_history = api_client.get_tax_history(test_apn)
            if tax_history:
                print(f"   [OK] Retrieved {len(tax_history)} tax records")
                if tax_history:
                    latest = tax_history[0]
                    print(f"   Latest tax year: {latest.get('TaxYear', 'N/A')}")
                    print(f"   Full cash value: ${latest.get('FullCashValue', 'N/A')}")
            else:
                print(f"   [ERROR] No tax history found")
        except Exception as e:
            print(f"   [ERROR] Error getting tax history: {e}")
        
        print("\n" + "=" * 50)
        print("[OK] API Integration test completed!")
        print("Check the logs for detailed information about API calls.")
        
        # Clean up
        api_client.close()
        
    except Exception as e:
        print(f"\n[ERROR] API Integration test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_api_integration()
    sys.exit(0 if success else 1)