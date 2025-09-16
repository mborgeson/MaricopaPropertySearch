#!/usr/bin/env python3
"""
Comprehensive Test Script for Maricopa Property Search Data Collection Methods
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

from api_client import MaricopaAPIClient
from config_manager import ConfigManager
from database_manager import DatabaseManager
from tax_scraper import MaricopaTaxScraper
from recorder_scraper import MaricopaRecorderScraper
from web_scraper import WebScraperManager

# Configure logging for test output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('comprehensive_test_results.log')
    ]
)

logger = logging.getLogger(__name__)

class ComprehensiveDataTest:
    """Test suite for all data collection methods"""
    
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
            self.config_manager = ConfigManager()
            logger.info("✓ Config Manager initialized")
            
            # Initialize API client
            self.api_client = MaricopaAPIClient(self.config_manager)
            logger.info("✓ API Client initialized")
            
            # Initialize database manager
            self.db_manager = DatabaseManager()
            logger.info("✓ Database Manager initialized")
            
            # Test database connection
            if self.db_manager.test_connection():
                logger.info("✓ Database connection verified")
            else:
                logger.warning("⚠ Database connection failed - some tests may be limited")
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
                logger.info("✅ API Status: HEALTHY")
                self.passed_tests.append("API Status Check")
                return True
            else:
                logger.warning(f"⚠ API Status: {status}")
                self.warnings.append(f"API status unclear: {status}")
                return False
                
        except Exception as e:
            logger.error(f"❌ API Status Check Failed: {e}")
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
                logger.info("✅ Property Details Retrieved Successfully")
                logger.info(f"   Property ID: {property_data.get('property_id', 'N/A')}")
                logger.info(f"   Owner: {property_data.get('owner_name', 'N/A')}")
                logger.info(f"   Address: {property_data.get('property_address', 'N/A')}")
                logger.info(f"   Assessed Value: ${property_data.get('assessed_value', 'N/A'):,}" if property_data.get('assessed_value') else "   Assessed Value: N/A")
                
                self.results['property_details'] = property_data
                self.passed_tests.append("Property Details")
                return True
            else:
                logger.error("❌ Property Details: No data returned")
                self.failed_tests.append("Property Details: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"❌ Property Details Failed: {e}")
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
                logger.info("✅ Tax Information Retrieved Successfully")
                logger.info(f"   Current Tax Year: {tax_data.get('tax_year', 'N/A')}")
                logger.info(f"   Tax Amount: ${tax_data.get('tax_amount', 'N/A'):,}" if tax_data.get('tax_amount') else "   Tax Amount: N/A")
                logger.info(f"   Exemptions: {tax_data.get('exemptions', 'N/A')}")
                logger.info(f"   Payment Status: {tax_data.get('payment_status', 'N/A')}")
                
                self.results['tax_information'] = tax_data
                self.passed_tests.append("Tax Information")
                return True
            else:
                logger.error("❌ Tax Information: No data returned")
                self.failed_tests.append("Tax Information: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"❌ Tax Information Failed: {e}")
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
                logger.info(f"✅ Sales History Retrieved: {len(sales_data)} records")
                
                for i, sale in enumerate(sales_data[:3]):  # Show first 3 sales
                    logger.info(f"   Sale {i+1}:")
                    logger.info(f"     Date: {sale.get('sale_date', 'N/A')}")
                    logger.info(f"     Price: ${sale.get('sale_price', 'N/A'):,}" if sale.get('sale_price') else "     Price: N/A")
                    logger.info(f"     Type: {sale.get('sale_type', 'N/A')}")
                
                if len(sales_data) > 3:
                    logger.info(f"   ... and {len(sales_data) - 3} more records")
                
                self.results['sales_history'] = sales_data
                self.passed_tests.append("Sales History")
                return True
            else:
                logger.warning("⚠ Sales History: No sales records found")
                self.warnings.append("No sales history found")
                self.results['sales_history'] = []
                return True  # Not finding sales is not necessarily an error
                
        except Exception as e:
            logger.error(f"❌ Sales History Failed: {e}")
            logger.error(traceback.format_exc())
            self.failed_tests.append(f"Sales History: {str(e)}")
            return False
    
    def test_property_documents(self):
        """Test get_property_documents method"""
        logger.info("\n" + "="*50)
        logger.info(f"TESTING: Property Documents for APN {self.test_apn}")
        logger.info("="*50)
        
        try:
            documents = self.api_client.get_property_documents(self.test_apn)
            
            if documents:
                logger.info(f"✅ Property Documents Retrieved: {len(documents)} documents")
                
                for i, doc in enumerate(documents[:3]):  # Show first 3 documents
                    logger.info(f"   Document {i+1}:")
                    logger.info(f"     Type: {doc.get('document_type', 'N/A')}")
                    logger.info(f"     Date: {doc.get('document_date', 'N/A')}")
                    logger.info(f"     Description: {doc.get('description', 'N/A')}")
                
                if len(documents) > 3:
                    logger.info(f"   ... and {len(documents) - 3} more documents")
                
                self.results['property_documents'] = documents
                self.passed_tests.append("Property Documents")
                return True
            else:
                logger.warning("⚠ Property Documents: No documents found")
                self.warnings.append("No property documents found")
                self.results['property_documents'] = []
                return True  # Not finding documents is not necessarily an error
                
        except Exception as e:
            logger.error(f"❌ Property Documents Failed: {e}")
            logger.error(traceback.format_exc())
            self.failed_tests.append(f"Property Documents: {str(e)}")
            return False
    
    def test_comprehensive_property_info(self):
        """Test get_comprehensive_property_info method (integration test)"""
        logger.info("\n" + "="*50)
        logger.info(f"TESTING: Comprehensive Property Info for APN {self.test_apn}")
        logger.info("="*50)
        
        try:
            comprehensive_data = self.api_client.get_comprehensive_property_info(self.test_apn)
            
            if comprehensive_data:
                logger.info("✅ Comprehensive Property Info Retrieved Successfully")
                
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
                logger.error("❌ Comprehensive Property Info: No data returned")
                self.failed_tests.append("Comprehensive Property Info: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"❌ Comprehensive Property Info Failed: {e}")
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
                    logger.info(f"   ✓ Correctly returned None for invalid APN: '{invalid_apn}'")
                else:
                    logger.warning(f"   ⚠ Unexpected result for invalid APN '{invalid_apn}': {result}")
                    error_handling_passed = False
                    
            except Exception as e:
                logger.info(f"   ✓ Correctly handled exception for invalid APN '{invalid_apn}': {str(e)}")
        
        if error_handling_passed:
            self.passed_tests.append("Error Handling")
            logger.info("✅ Error Handling: PASSED")
        else:
            self.failed_tests.append("Error Handling: Some invalid inputs produced unexpected results")
            logger.warning("⚠ Error Handling: Some issues detected")
        
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
                    logger.info(f"✅ Backup APN {backup_apn} worked!")
                    self.test_apn = backup_apn  # Use this APN for remaining tests
                    self.results['property_details'] = property_data
                    self.passed_tests.append(f"Backup APN {backup_apn}")
                    return True
                else:
                    logger.info(f"   No data for backup APN: {backup_apn}")
            except Exception as e:
                logger.info(f"   Error with backup APN {backup_apn}: {e}")
        
        logger.error("❌ All APNs failed")
        self.failed_tests.append("All test APNs failed")
        return False
    
    def generate_summary_report(self):
        """Generate comprehensive test summary"""
        logger.info("\n" + "="*70)
        logger.info("COMPREHENSIVE TEST RESULTS SUMMARY")
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
            logger.info("\n✅ PASSED TESTS:")
            for test in self.passed_tests:
                logger.info(f"   ✓ {test}")
        
        if self.failed_tests:
            logger.info("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                logger.info(f"   ✗ {test}")
        
        if self.warnings:
            logger.info("\n⚠ WARNINGS:")
            for warning in self.warnings:
                logger.info(f"   ⚠ {warning}")
        
        # Overall assessment
        logger.info(f"\n{'='*70}")
        if len(self.failed_tests) == 0:
            logger.info("🎉 OVERALL STATUS: ALL TESTS PASSED!")
            if self.warnings:
                logger.info("   (Some warnings noted above)")
        elif len(self.passed_tests) > len(self.failed_tests):
            logger.info("⚠ OVERALL STATUS: MOSTLY WORKING (Some issues detected)")
        else:
            logger.info("❌ OVERALL STATUS: SIGNIFICANT ISSUES DETECTED")
        
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
            logger.info(f"📄 Detailed results saved to: {results_file}")
        except Exception as e:
            logger.error(f"Failed to save results file: {e}")
    
    def run_all_tests(self):
        """Run complete test suite"""
        logger.info("🚀 Starting Comprehensive Data Collection Test Suite")
        logger.info(f"Target APN: {self.test_apn}")
        logger.info(f"Backup APNs: {', '.join(self.backup_apns)}")
        
        if not self.setup():
            logger.error("❌ Setup failed - cannot continue with tests")
            return False
        
        # Run all tests
        tests = [
            self.test_api_status,
            self.test_property_details,
            self.test_with_backup_apns,  # Try backups if needed
            self.test_tax_information,
            self.test_sales_history,
            self.test_property_documents,
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
    print("MARICOPA PROPERTY SEARCH - COMPREHENSIVE DATA TEST")
    print("=" * 70)
    
    test_suite = ComprehensiveDataTest()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed - check output above for details")
        sys.exit(1)

if __name__ == "__main__":
    main()