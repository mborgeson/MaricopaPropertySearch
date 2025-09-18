#!/usr/bin/env python3
"""
Test script for the real Maricopa County property search implementation.
This script tests the actual API and web scraping functionality.
"""

import sys
import os
import logging
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
# MIGRATED: from api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
from web_scraper import WebScraperManager
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_api_client():
    """Test the real API client functionality"""
    logger.info("Testing Maricopa API Client...")
    
    try:
        config = EnhancedConfigManager()
        client = UnifiedMaricopaAPIClient(config)
        
        # Test API status
        logger.info("Testing API status...")
        status = client.get_api_status()
        logger.info(f"API Status: {status}")
        
        # Test APN search with a known test APN (if available)
        test_apn = "117-01-001"  # Example APN format
        logger.info(f"Testing APN search for: {test_apn}")
        
        property_data = client.search_by_apn(test_apn)
        if property_data:
            logger.info(f"Found property data: {list(property_data.keys())}")
            logger.info(f"APN: {property_data.get('apn')}")
            logger.info(f"Owner: {property_data.get('owner_name')}")
            logger.info(f"Address: {property_data.get('property_address')}")
        else:
            logger.info("No property data found")
        
        # Test owner search
        test_owner = "SMITH"
        logger.info(f"Testing owner search for: {test_owner}")
        
        owner_results = client.search_by_owner(test_owner, limit=3)
        logger.info(f"Found {len(owner_results)} properties for owner search")
        
        for i, prop in enumerate(owner_results[:3]):
            logger.info(f"Property {i+1}: APN={prop.get('apn')}, Owner={prop.get('owner_name')}")
        
        # Test address search
        test_address = "123 MAIN ST"
        logger.info(f"Testing address search for: {test_address}")
        
        address_results = client.search_by_address(test_address, limit=3)
        logger.info(f"Found {len(address_results)} properties for address search")
        
        client.close()
        logger.info("API client test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"API client test failed: {e}")
        return False

def test_web_scraper():
    """Test the real web scraper functionality"""
    logger.info("Testing Web Scraper...")
    
    try:
        config = EnhancedConfigManager()
        scraper = WebScraperManager(config)
        
        # Test APN scraping
        test_apn = "117-01-001"
        logger.info(f"Testing web scraping for APN: {test_apn}")
        
        property_data = scraper.scrape_property_by_apn(test_apn)
        if property_data:
            logger.info(f"Scraped property data: {list(property_data.keys())}")
            logger.info(f"APN: {property_data.get('apn')}")
            logger.info(f"Owner: {property_data.get('owner_name')}")
            logger.info(f"Address: {property_data.get('property_address')}")
        else:
            logger.info("No property data scraped")
        
        # Test owner name search
        test_owner = "SMITH"
        logger.info(f"Testing web scraping owner search for: {test_owner}")
        
        search_results = scraper.search_by_owner_name(test_owner, limit=2)
        logger.info(f"Scraped {len(search_results)} properties for owner search")
        
        for i, prop in enumerate(search_results):
            logger.info(f"Property {i+1}: APN={prop.get('apn')}, Owner={prop.get('owner_name')}")
        
        scraper.close()
        logger.info("Web scraper test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Web scraper test failed: {e}")
        return False

def test_data_validation():
    """Test data validation and cleaning functions"""
    logger.info("Testing data validation...")
    
    try:
        config = EnhancedConfigManager()
        client = UnifiedMaricopaAPIClient(config)
        
        # Test APN validation
        valid_apns = ["117-01-001", "11701001", "117.01.001", "117 01 001"]
        invalid_apns = ["", None, "abc", "123", "117-01"]
        
        for apn in valid_apns:
            is_valid = client._validate_apn(apn)
            logger.info(f"APN '{apn}' validation: {is_valid}")
        
        for apn in invalid_apns:
            is_valid = client._validate_apn(apn)
            logger.info(f"APN '{apn}' validation: {is_valid}")
        
        # Test data cleaning
        test_data = {
            'apn': '117-01-001',
            'owner_name': 'John Smith',
            'year_built': '1985',
            'living_area_sqft': '2,500',
            'bathrooms': '2.5',
            'latest_assessed_value': '$350,000.00',
            'empty_field': '',
            'none_field': None
        }
        
        cleaned_data = client._validate_property_data(test_data)
        logger.info(f"Original data keys: {list(test_data.keys())}")
        logger.info(f"Cleaned data keys: {list(cleaned_data.keys())}")
        logger.info(f"Year built type: {type(cleaned_data.get('year_built'))}")
        logger.info(f"Living area type: {type(cleaned_data.get('living_area_sqft'))}")
        logger.info(f"Assessed value type: {type(cleaned_data.get('latest_assessed_value'))}")
        
        client.close()
        logger.info("Data validation test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Data validation test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting comprehensive tests for real implementation...")
    
    tests = [
        ("API Client", test_api_client),
        ("Web Scraper", test_web_scraper),
        ("Data Validation", test_data_validation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name} Test")
        logger.info('='*50)
        
        try:
            success = test_func()
            results[test_name] = success
            
            if success:
                logger.info(f"✅ {test_name} test PASSED")
            else:
                logger.error(f"❌ {test_name} test FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name} test CRASHED: {e}")
            results[test_name] = False
    
    # Print summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info('='*50)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests PASSED! Real implementation is working.")
        return 0
    else:
        logger.error("❌ Some tests FAILED. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())