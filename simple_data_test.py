#!/usr/bin/env python3
"""
Simple Test Script for Maricopa Property Search Data Collection Methods
Tests all major data collection functionality to verify fixes are working properly.
"""

import sys
import os
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# MIGRATED: from api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
# MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
# MIGRATED: from database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.enhanced_config_manager import EnhancedConfigManager

# Configure logging for test output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class SimpleDataTest:
    """Test suite for core data collection methods"""
    
    def __init__(self):
        self.test_apn = "501-38-034A"
        self.backup_apns = ["501-38-034", "501-38-001", "500-01-001"]
        self.results = {}
        self.config_manager = None
        self.api_client = None
        self.db_manager = None
        
        # Test results tracking
        self.passed_tests = []
        self.failed_tests = []
        self.warnings = []
        
    def setup(self):
        """Initialize all components needed for testing"""
        logger.info("Setting up test environment...")
        
        try:
            # Initialize config manager
            self.config_manager = EnhancedConfigManager()
            logger.info("PASS: Config Manager initialized")
            
            # Initialize API client
            self.api_client = UnifiedMaricopaAPIClient(self.config_manager)
            logger.info("PASS: API Client initialized")
            
            # Initialize database manager with config
            self.db_manager = ThreadSafeDatabaseManager(self.config_manager)
            logger.info("PASS: Database Manager initialized")
            
            # Test database connection
            if self.db_manager.test_connection():
                logger.info("PASS: Database connection verified")
            else:
                logger.warning("WARN: Database connection failed - some tests may be limited")
                self.warnings.append("Database connection not available")
            
            return True
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_api_status(self):
        """Test API connectivity and status"""
        logger.info("\n" + "="*50)
        logger.info("TESTING: API Status and Connectivity")
        logger.info("="*50)
        
        try:
            status = self.api_client.get_api_status()
            
            if status and status.get('status') == 'healthy':
                logger.info("PASS: API Status: HEALTHY")
                self.passed_tests.append("API Status Check")
                return True
            else:
                logger.warning(f"WARN: API Status: {status}")
                self.warnings.append(f"API status unclear: {status}")
                return False
                
        except Exception as e:
            logger.error(f"FAIL: API Status Check Failed: {e}")
            self.failed_tests.append(f"API Status Check: {str(e)}")
            return False
    
    def test_property_details(self):
        """Test get_property_details method"""
        logger.info("\n" + "="*50)
        logger.info(f"TESTING: Property Details for APN {self.test_apn}")
        logger.info("="*50)
        
        try:
            property_data = self.api_client.get_property_details(self.test_apn)
            
            if property_data:
                logger.info("PASS: Property Details Retrieved Successfully")
                logger.info(f"   Property ID: {property_data.get('property_id', 'N/A')}")
                logger.info(f"   Owner: {property_data.get('owner_name', 'N/A')}")
                logger.info(f"   Address: {property_data.get('property_address', 'N/A')}")
                if property_data.get('assessed_value'):
                    logger.info(f"   Assessed Value: ${property_data.get('assessed_value'):,}")
                else:
                    logger.info("   Assessed Value: N/A")
                
                self.results['property_details'] = property_data
                self.passed_tests.append("Property Details")
                return True
            else:
                logger.error("FAIL: Property Details: No data returned")
                self.failed_tests.append("Property Details: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"FAIL: Property Details Failed: {e}")
            logger.error(traceback.format_exc())
            self.failed_tests.append(f"Property Details: {str(e)}")
            return False
    
    def test_tax_information(self):
        """Test get_tax_information method"""
        logger.info("\n" + "="*50)
        logger.info(f"TESTING: Tax Information for APN {self.test_apn}")
        logger.info("="*50)
        
        try:
            tax_data = self.api_client.get_tax_information(self.test_apn)
            
            if tax_data:
                logger.info("PASS: Tax Information Retrieved Successfully")
                logger.info(f"   Current Tax Year: {tax_data.get('tax_year', 'N/A')}")
                if tax_data.get('tax_amount'):
                    logger.info(f"   Tax Amount: ${tax_data.get('tax_amount'):,}")
                else:
                    logger.info("   Tax Amount: N/A")
                logger.info(f"   Exemptions: {tax_data.get('exemptions', 'N/A')}")
                logger.info(f"   Payment Status: {tax_data.get('payment_status', 'N/A')}")
                
                self.results['tax_information'] = tax_data
                self.passed_tests.append("Tax Information")
                return True
            else:
                logger.error("FAIL: Tax Information: No data returned")
                self.failed_tests.append("Tax Information: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"FAIL: Tax Information Failed: {e}")
            logger.error(traceback.format_exc())
            self.failed_tests.append(f"Tax Information: {str(e)}")
            return False
    
    def test_sales_history(self):
        """Test get_sales_history method"""
        logger.info("\n" + "="*50)
        logger.info(f"TESTING: Sales History for APN {self.test_apn}")
        logger.info("="*50)
        
        try:
            sales_data = self.api_client.get_sales_history(self.test_apn, years=5)
            
            if sales_data:
                logger.info(f"PASS: Sales History Retrieved: {len(sales_data)} records")
                
                for i, sale in enumerate(sales_data[:3]):  # Show first 3 sales
                    logger.info(f"   Sale {i+1}:")
                    logger.info(f"     Date: {sale.get('sale_date', 'N/A')}")
                    if sale.get('sale_price'):
                        logger.info(f"     Price: ${sale.get('sale_price'):,}")
                    else:
                        logger.info("     Price: N/A")
                    logger.info(f"     Type: {sale.get('sale_type', 'N/A')}")
                
                if len(sales_data) > 3:
                    logger.info(f"   ... and {len(sales_data) - 3} more records")
                
                self.results['sales_history'] = sales_data
                self.passed_tests.append("Sales History")
                return True
            else:
                logger.warning("WARN: Sales History: No sales records found")
                self.warnings.append("No sales history found")
                self.results['sales_history'] = []
                return True  # Not finding sales is not necessarily an error
                
        except Exception as e:
            logger.error(f"FAIL: Sales History Failed: {e}")
            logger.error(traceback.format_exc())
            self.failed_tests.append(f"Sales History: {str(e)}")
            return False
    
    def test_comprehensive_property_info(self):
        """Test get_comprehensive_property_info method (integration test)"""
        logger.info("\n" + "="*50)
        logger.info(f"TESTING: Comprehensive Property Info for APN {self.test_apn}")
        logger.info("="*50)
        
        try:
            comprehensive_data = self.api_client.get_comprehensive_property_info(self.test_apn)
            
            if comprehensive_data:
                logger.info("PASS: Comprehensive Property Info Retrieved Successfully")
                
                # Check major sections
                sections = ['property_details', 'tax_information', 'sales_history', 'documents']
                for section in sections:
                    if section in comprehensive_data:
                        data = comprehensive_data[section]
                        if isinstance(data, list):
                            logger.info(f"   {section.title()}: {len(data)} items")
                        elif isinstance(data, dict):
                            logger.info(f"   {section.title()}: Available")
                        else:
                            logger.info(f"   {section.title()}: {data}")
                    else:
                        logger.info(f"   {section.title()}: Not available")
                
                self.results['comprehensive_info'] = comprehensive_data
                self.passed_tests.append("Comprehensive Property Info")
                return True
            else:
                logger.error("FAIL: Comprehensive Property Info: No data returned")
                self.failed_tests.append("Comprehensive Property Info: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"FAIL: Comprehensive Property Info Failed: {e}")
            logger.error(traceback.format_exc())
            self.failed_tests.append(f"Comprehensive Property Info: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling with invalid APNs"""
        logger.info("\n" + "="*50)
        logger.info("TESTING: Error Handling with Invalid APNs")
        logger.info("="*50)
        
        invalid_apns = ["INVALID", "000-00-000", "999-99-999Z", ""]
        error_handling_passed = True
        
        for invalid_apn in invalid_apns:
            try:
                logger.info(f"Testing invalid APN: '{invalid_apn}'")
                result = self.api_client.get_property_details(invalid_apn)
                
                if result is None:
                    logger.info(f"   OK: Correctly returned None for invalid APN: '{invalid_apn}'")
                else:
                    logger.warning(f"   WARN: Unexpected result for invalid APN '{invalid_apn}': {result}")
                    error_handling_passed = False
                    
            except Exception as e:
                logger.info(f"   OK: Correctly handled exception for invalid APN '{invalid_apn}': {str(e)}")
        
        if error_handling_passed:
            self.passed_tests.append("Error Handling")
            logger.info("PASS: Error Handling: PASSED")
        else:
            self.failed_tests.append("Error Handling: Some invalid inputs produced unexpected results")
            logger.warning("WARN: Error Handling: Some issues detected")
        
        return error_handling_passed
    
    def test_with_backup_apns(self):
        """Test with backup APNs if primary fails"""
        if self.results.get('property_details'):
            return True  # Primary APN worked
        
        logger.info("\n" + "="*50)
        logger.info("TESTING: Backup APNs (Primary APN failed)")
        logger.info("="*50)
        
        for backup_apn in self.backup_apns:
            logger.info(f"Trying backup APN: {backup_apn}")
            try:
                property_data = self.api_client.get_property_details(backup_apn)
                if property_data:
                    logger.info(f"PASS: Backup APN {backup_apn} worked!")
                    self.test_apn = backup_apn  # Use this APN for remaining tests
                    self.results['property_details'] = property_data
                    self.passed_tests.append(f"Backup APN {backup_apn}")
                    return True
                else:
                    logger.info(f"   No data for backup APN: {backup_apn}")
            except Exception as e:
                logger.info(f"   Error with backup APN {backup_apn}: {e}")
        
        logger.error("FAIL: All APNs failed")
        self.failed_tests.append("All test APNs failed")
        return False
    
    def generate_summary_report(self):
        """Generate comprehensive test summary"""
        logger.info("\n" + "="*70)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("="*70)
        
        total_tests = len(self.passed_tests) + len(self.failed_tests)
        pass_rate = (len(self.passed_tests) / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"Test Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Test APN Used: {self.test_apn}")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {len(self.passed_tests)}")
        logger.info(f"Failed: {len(self.failed_tests)}")
        logger.info(f"Warnings: {len(self.warnings)}")
        logger.info(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.passed_tests:
            logger.info("\nPASSED TESTS:")
            for test in self.passed_tests:
                logger.info(f"   PASS: {test}")
        
        if self.failed_tests:
            logger.info("\nFAILED TESTS:")
            for test in self.failed_tests:
                logger.info(f"   FAIL: {test}")
        
        if self.warnings:
            logger.info("\nWARNINGS:")
            for warning in self.warnings:
                logger.info(f"   WARN: {warning}")
        
        # Overall assessment
        logger.info(f"\n{'='*70}")
        if len(self.failed_tests) == 0:
            logger.info("SUCCESS: ALL TESTS PASSED!")
            if self.warnings:
                logger.info("   (Some warnings noted above)")
        elif len(self.passed_tests) > len(self.failed_tests):
            logger.info("WARN: MOSTLY WORKING (Some issues detected)")
        else:
            logger.info("FAIL: SIGNIFICANT ISSUES DETECTED")
        
        logger.info(f"{'='*70}")
        
        # Save detailed results to file
        self.save_results_to_file()
    
    def save_results_to_file(self):
        """Save detailed test results to JSON file"""
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        summary = {
            'test_timestamp': datetime.now().isoformat(),
            'test_apn': self.test_apn,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'warnings': self.warnings,
            'detailed_results': self.results
        }
        
        try:
            with open(results_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            logger.info(f"FILE: Detailed results saved to: {results_file}")
        except Exception as e:
            logger.error(f"Failed to save results file: {e}")
    
    def run_all_tests(self):
        """Run complete test suite"""
        logger.info("STARTING: Comprehensive Data Collection Test Suite")
        logger.info(f"Target APN: {self.test_apn}")
        logger.info(f"Backup APNs: {', '.join(self.backup_apns)}")
        
        if not self.setup():
            logger.error("FAIL: Setup failed - cannot continue with tests")
            return False
        
        # Run all tests
        tests = [
            self.test_api_status,
            self.test_property_details,
            self.test_with_backup_apns,  # Try backups if needed
            self.test_tax_information,
            self.test_sales_history,
            self.test_comprehensive_property_info,
            self.test_error_handling
        ]
        
        for test_method in tests:
            try:
                test_method()
            except Exception as e:
                logger.error(f"Test method {test_method.__name__} crashed: {e}")
                logger.error(traceback.format_exc())
                self.failed_tests.append(f"{test_method.__name__}: Crashed with {str(e)}")
        
        self.generate_summary_report()
        
        return len(self.failed_tests) == 0

def main():
    """Main test execution"""
    print("=" * 70)
    print("MARICOPA PROPERTY SEARCH - DATA COLLECTION TEST")
    print("=" * 70)
    
    test_suite = SimpleDataTest()
    success = test_suite.run_all_tests()
    
    if success:
        print("\nSUCCESS: All tests completed successfully!")
        return 0
    else:
        print("\nFAIL: Some tests failed - check output above for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())