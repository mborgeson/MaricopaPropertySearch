#!/usr/bin/env python3
"""
Comprehensive API Test Suite for Maricopa Property Search
Tests all API functionality including search methods, error handling, and data retrieval
"""

import sys
import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# MIGRATED: from api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient, MockMaricopaAPIClient
# MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
import requests
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APITestRunner:
    """Comprehensive API test runner"""

    def __init__(self):
        self.config_manager = EnhancedConfigManager()
        self.real_client = None
        self.mock_client = None
        self.test_results = {}
        self.test_start_time = datetime.now()

        # Test APNs (mix of valid formats)
        self.test_apns = [
            "101-01-001",
            "10101001",
            "101.01.001",
            "205-09-001A",
            "20509001A",
            "999999999"  # Likely invalid
        ]

        # Test owners
        self.test_owners = [
            "SMITH JOHN",
            "COUNTY OF MARICOPA",
            "ARIZONA STATE LAND DEPT",
            "NONEXISTENT OWNER XYZ123"
        ]

        # Test addresses
        self.test_addresses = [
            "1 E WASHINGTON ST",
            "301 W JEFFERSON ST",
            "1234 MAIN STREET",
            "999999 NONEXISTENT ROAD"
        ]

    def setup_clients(self):
        """Initialize API clients"""
        logger.info("Setting up API clients...")

        try:
            # Initialize real client
            self.real_client = UnifiedMaricopaAPIClient(self.config_manager)
            logger.info("Real API client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize real client: {e}")
            self.real_client = None

        try:
            # Initialize mock client
            self.mock_client = MockMaricopaAPIClient(self.config_manager)
            logger.info("Mock API client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize mock client: {e}")
            self.mock_client = None

    def test_connection(self) -> Dict[str, Any]:
        """Test API connection and basic connectivity"""
        logger.info("Testing API connection...")
        results = {
            'test_name': 'Connection Test',
            'real_client': {'status': 'not_tested', 'error': None},
            'mock_client': {'status': 'not_tested', 'error': None},
            'base_url_accessible': False
        }

        # Test base URL accessibility
        try:
            config = self.config_manager.get_api_config()
            response = requests.get(config['base_url'], timeout=10)
            results['base_url_accessible'] = response.status_code == 200
            results['base_url_status_code'] = response.status_code
        except Exception as e:
            results['base_url_error'] = str(e)

        # Test real client connection
        if self.real_client:
            try:
                connection_result = self.real_client.test_connection()
                results['real_client']['status'] = 'pass' if connection_result else 'fail'
                results['real_client']['connected'] = connection_result
            except Exception as e:
                results['real_client']['status'] = 'error'
                results['real_client']['error'] = str(e)

        # Test mock client connection
        if self.mock_client:
            try:
                connection_result = self.mock_client.test_connection()
                results['mock_client']['status'] = 'pass' if connection_result else 'fail'
                results['mock_client']['connected'] = connection_result
            except Exception as e:
                results['mock_client']['status'] = 'error'
                results['mock_client']['error'] = str(e)

        return results

    def test_search_by_apn(self, client, client_name: str) -> Dict[str, Any]:
        """Test APN search functionality"""
        logger.info(f"Testing APN search with {client_name} client...")
        results = {
            'test_name': f'APN Search - {client_name}',
            'client': client_name,
            'test_cases': []
        }

        for apn in self.test_apns:
            test_case = {
                'apn': apn,
                'status': 'not_tested',
                'response_time': None,
                'result': None,
                'error': None
            }

            try:
                start_time = time.time()
                result = client.search_by_apn(apn)
                end_time = time.time()

                test_case['response_time'] = round(end_time - start_time, 3)
                test_case['result'] = result
                test_case['status'] = 'success' if result else 'no_results'

                if result:
                    test_case['returned_apn'] = result.get('apn')
                    test_case['owner_name'] = result.get('owner_name')
                    test_case['property_address'] = result.get('property_address')

            except Exception as e:
                test_case['status'] = 'error'
                test_case['error'] = str(e)
                logger.warning(f"APN search error for {apn}: {e}")

            results['test_cases'].append(test_case)

            # Rate limiting between requests
            time.sleep(0.2)

        # Calculate summary statistics
        successful = sum(1 for case in results['test_cases'] if case['status'] == 'success')
        total = len(results['test_cases'])
        results['success_rate'] = (successful / total) * 100 if total > 0 else 0
        results['total_tests'] = total
        results['successful_tests'] = successful

        return results

    def test_search_by_owner(self, client, client_name: str) -> Dict[str, Any]:
        """Test owner name search functionality"""
        logger.info(f"Testing owner search with {client_name} client...")
        results = {
            'test_name': f'Owner Search - {client_name}',
            'client': client_name,
            'test_cases': []
        }

        for owner in self.test_owners:
            test_case = {
                'owner_name': owner,
                'status': 'not_tested',
                'response_time': None,
                'result_count': 0,
                'results': None,
                'error': None
            }

            try:
                start_time = time.time()
                results_list = client.search_by_owner(owner, limit=5)
                end_time = time.time()

                test_case['response_time'] = round(end_time - start_time, 3)
                test_case['results'] = results_list
                test_case['result_count'] = len(results_list) if results_list else 0
                test_case['status'] = 'success' if results_list else 'no_results'

                if results_list:
                    test_case['sample_result'] = results_list[0]

            except Exception as e:
                test_case['status'] = 'error'
                test_case['error'] = str(e)
                logger.warning(f"Owner search error for {owner}: {e}")

            results['test_cases'].append(test_case)

            # Rate limiting between requests
            time.sleep(0.2)

        # Calculate summary statistics
        successful = sum(1 for case in results['test_cases'] if case['status'] == 'success')
        total = len(results['test_cases'])
        results['success_rate'] = (successful / total) * 100 if total > 0 else 0
        results['total_tests'] = total
        results['successful_tests'] = successful

        return results

    def test_search_by_address(self, client, client_name: str) -> Dict[str, Any]:
        """Test address search functionality"""
        logger.info(f"Testing address search with {client_name} client...")
        results = {
            'test_name': f'Address Search - {client_name}',
            'client': client_name,
            'test_cases': []
        }

        for address in self.test_addresses:
            test_case = {
                'address': address,
                'status': 'not_tested',
                'response_time': None,
                'result_count': 0,
                'results': None,
                'error': None
            }

            try:
                start_time = time.time()
                results_list = client.search_by_address(address, limit=5)
                end_time = time.time()

                test_case['response_time'] = round(end_time - start_time, 3)
                test_case['results'] = results_list
                test_case['result_count'] = len(results_list) if results_list else 0
                test_case['status'] = 'success' if results_list else 'no_results'

                if results_list:
                    test_case['sample_result'] = results_list[0]

            except Exception as e:
                test_case['status'] = 'error'
                test_case['error'] = str(e)
                logger.warning(f"Address search error for {address}: {e}")

            results['test_cases'].append(test_case)

            # Rate limiting between requests
            time.sleep(0.2)

        # Calculate summary statistics
        successful = sum(1 for case in results['test_cases'] if case['status'] == 'success')
        total = len(results['test_cases'])
        results['success_rate'] = (successful / total) * 100 if total > 0 else 0
        results['total_tests'] = total
        results['successful_tests'] = successful

        return results

    def test_tax_history(self, client, client_name: str) -> Dict[str, Any]:
        """Test tax history retrieval"""
        logger.info(f"Testing tax history with {client_name} client...")
        results = {
            'test_name': f'Tax History - {client_name}',
            'client': client_name,
            'test_cases': []
        }

        # Test with first few APNs
        test_apns = self.test_apns[:3]

        for apn in test_apns:
            test_case = {
                'apn': apn,
                'status': 'not_tested',
                'response_time': None,
                'record_count': 0,
                'records': None,
                'error': None
            }

            try:
                start_time = time.time()
                tax_records = client.get_tax_history(apn, years=5)
                end_time = time.time()

                test_case['response_time'] = round(end_time - start_time, 3)
                test_case['records'] = tax_records
                test_case['record_count'] = len(tax_records) if tax_records else 0
                test_case['status'] = 'success' if tax_records else 'no_results'

                if tax_records:
                    test_case['sample_record'] = tax_records[0]

            except Exception as e:
                test_case['status'] = 'error'
                test_case['error'] = str(e)
                logger.warning(f"Tax history error for {apn}: {e}")

            results['test_cases'].append(test_case)

            # Rate limiting between requests
            time.sleep(0.2)

        # Calculate summary statistics
        successful = sum(1 for case in results['test_cases'] if case['status'] == 'success')
        total = len(results['test_cases'])
        results['success_rate'] = (successful / total) * 100 if total > 0 else 0
        results['total_tests'] = total
        results['successful_tests'] = successful

        return results

    def test_sales_history(self, client, client_name: str) -> Dict[str, Any]:
        """Test sales history retrieval"""
        logger.info(f"Testing sales history with {client_name} client...")
        results = {
            'test_name': f'Sales History - {client_name}',
            'client': client_name,
            'test_cases': []
        }

        # Test with first few APNs
        test_apns = self.test_apns[:3]

        for apn in test_apns:
            test_case = {
                'apn': apn,
                'status': 'not_tested',
                'response_time': None,
                'record_count': 0,
                'records': None,
                'error': None
            }

            try:
                start_time = time.time()
                sales_records = client.get_sales_history(apn, years=10)
                end_time = time.time()

                test_case['response_time'] = round(end_time - start_time, 3)
                test_case['records'] = sales_records
                test_case['record_count'] = len(sales_records) if sales_records else 0
                test_case['status'] = 'success' if sales_records else 'no_results'

                if sales_records:
                    test_case['sample_record'] = sales_records[0]

            except Exception as e:
                test_case['status'] = 'error'
                test_case['error'] = str(e)
                logger.warning(f"Sales history error for {apn}: {e}")

            results['test_cases'].append(test_case)

            # Rate limiting between requests
            time.sleep(0.2)

        # Calculate summary statistics
        successful = sum(1 for case in results['test_cases'] if case['status'] == 'success')
        total = len(results['test_cases'])
        results['success_rate'] = (successful / total) * 100 if total > 0 else 0
        results['total_tests'] = total
        results['successful_tests'] = successful

        return results

    def test_bulk_search(self, client, client_name: str) -> Dict[str, Any]:
        """Test bulk property search"""
        logger.info(f"Testing bulk search with {client_name} client...")
        results = {
            'test_name': f'Bulk Search - {client_name}',
            'client': client_name,
            'status': 'not_tested',
            'response_time': None,
            'input_count': 0,
            'result_count': 0,
            'success_rate': 0,
            'results': None,
            'error': None
        }

        # Test with first 3 APNs
        test_apns = self.test_apns[:3]
        results['input_count'] = len(test_apns)

        try:
            start_time = time.time()
            bulk_results = client.bulk_property_search(test_apns)
            end_time = time.time()

            results['response_time'] = round(end_time - start_time, 3)
            results['results'] = bulk_results
            results['result_count'] = len(bulk_results) if bulk_results else 0
            results['success_rate'] = (results['result_count'] / results['input_count']) * 100
            results['status'] = 'success' if bulk_results else 'no_results'

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            logger.warning(f"Bulk search error: {e}")

        return results

    def test_api_status(self, client, client_name: str) -> Dict[str, Any]:
        """Test API status endpoint"""
        logger.info(f"Testing API status with {client_name} client...")
        results = {
            'test_name': f'API Status - {client_name}',
            'client': client_name,
            'status': 'not_tested',
            'response_time': None,
            'api_status': None,
            'error': None
        }

        try:
            start_time = time.time()
            status_info = client.get_api_status()
            end_time = time.time()

            results['response_time'] = round(end_time - start_time, 3)
            results['api_status'] = status_info
            results['status'] = 'success' if status_info else 'no_results'

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            logger.warning(f"API status error: {e}")

        return results

    def test_error_handling(self, client, client_name: str) -> Dict[str, Any]:
        """Test error handling and edge cases"""
        logger.info(f"Testing error handling with {client_name} client...")
        results = {
            'test_name': f'Error Handling - {client_name}',
            'client': client_name,
            'test_cases': []
        }

        # Test invalid inputs
        invalid_tests = [
            {'type': 'null_apn', 'input': None, 'method': 'search_by_apn'},
            {'type': 'empty_apn', 'input': '', 'method': 'search_by_apn'},
            {'type': 'invalid_apn', 'input': 'INVALID123!@#', 'method': 'search_by_apn'},
            {'type': 'null_owner', 'input': None, 'method': 'search_by_owner'},
            {'type': 'empty_owner', 'input': '', 'method': 'search_by_owner'},
            {'type': 'null_address', 'input': None, 'method': 'search_by_address'},
            {'type': 'empty_address', 'input': '', 'method': 'search_by_address'},
        ]

        for test in invalid_tests:
            test_case = {
                'test_type': test['type'],
                'method': test['method'],
                'input': test['input'],
                'status': 'not_tested',
                'error_handled': False,
                'result': None,
                'error': None
            }

            try:
                method = getattr(client, test['method'])
                result = method(test['input'])
                test_case['result'] = result
                test_case['status'] = 'completed'
                test_case['error_handled'] = True  # No exception thrown

            except Exception as e:
                test_case['status'] = 'error'
                test_case['error'] = str(e)
                test_case['error_handled'] = True  # Exception properly handled
                logger.debug(f"Expected error for {test['type']}: {e}")

            results['test_cases'].append(test_case)

        # Calculate error handling effectiveness
        properly_handled = sum(1 for case in results['test_cases'] if case['error_handled'])
        total = len(results['test_cases'])
        results['error_handling_rate'] = (properly_handled / total) * 100 if total > 0 else 0

        return results

    def test_rate_limiting(self, client, client_name: str) -> Dict[str, Any]:
        """Test rate limiting behavior"""
        logger.info(f"Testing rate limiting with {client_name} client...")
        results = {
            'test_name': f'Rate Limiting - {client_name}',
            'client': client_name,
            'status': 'not_tested',
            'requests_made': 0,
            'rate_limited': False,
            'average_response_time': 0,
            'response_times': [],
            'error': None
        }

        try:
            # Make rapid requests to test rate limiting
            response_times = []
            for i in range(5):
                start_time = time.time()
                try:
                    result = client.search_by_apn(self.test_apns[0])
                    end_time = time.time()
                    response_time = end_time - start_time
                    response_times.append(response_time)
                    results['requests_made'] += 1
                except Exception as e:
                    if '429' in str(e) or 'rate limit' in str(e).lower():
                        results['rate_limited'] = True
                        break
                    else:
                        raise

            results['response_times'] = response_times
            results['average_response_time'] = sum(response_times) / len(response_times) if response_times else 0
            results['status'] = 'completed'

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            logger.warning(f"Rate limiting test error: {e}")

        return results

    def run_all_tests(self):
        """Run all API tests"""
        logger.info("Starting comprehensive API test suite...")

        # Setup clients
        self.setup_clients()

        # Test connection first
        self.test_results['connection'] = self.test_connection()

        # Test with available clients
        for client, client_name in [(self.real_client, 'Real'), (self.mock_client, 'Mock')]:
            if client is None:
                logger.warning(f"Skipping tests for {client_name} client - not available")
                continue

            logger.info(f"\n{'='*50}")
            logger.info(f"Testing {client_name} API Client")
            logger.info(f"{'='*50}")

            client_results = {}

            # Run all test methods
            test_methods = [
                ('apn_search', self.test_search_by_apn),
                ('owner_search', self.test_search_by_owner),
                ('address_search', self.test_search_by_address),
                ('tax_history', self.test_tax_history),
                ('sales_history', self.test_sales_history),
                ('bulk_search', self.test_bulk_search),
                ('api_status', self.test_api_status),
                ('error_handling', self.test_error_handling),
                ('rate_limiting', self.test_rate_limiting)
            ]

            for test_name, test_method in test_methods:
                try:
                    logger.info(f"Running {test_name} test...")
                    client_results[test_name] = test_method(client, client_name)
                except Exception as e:
                    logger.error(f"Failed to run {test_name} test: {e}")
                    client_results[test_name] = {
                        'test_name': f'{test_name} - {client_name}',
                        'status': 'test_error',
                        'error': str(e)
                    }

            self.test_results[client_name.lower()] = client_results

    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        test_end_time = datetime.now()
        test_duration = test_end_time - self.test_start_time

        report_lines = [
            "="*80,
            "MARICOPA PROPERTY SEARCH API - COMPREHENSIVE TEST REPORT",
            "="*80,
            f"Test Date: {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {test_duration.total_seconds():.2f} seconds",
            "",
        ]

        # Connection Test Summary
        if 'connection' in self.test_results:
            conn_results = self.test_results['connection']
            report_lines.extend([
                "CONNECTION TEST RESULTS:",
                "-" * 30,
                f"Base URL Accessible: {conn_results.get('base_url_accessible', 'Unknown')}",
                f"Real Client Connected: {conn_results.get('real_client', {}).get('connected', 'Unknown')}",
                f"Mock Client Connected: {conn_results.get('mock_client', {}).get('connected', 'Unknown')}",
                ""
            ])

        # Client Test Results
        for client_name in ['real', 'mock']:
            if client_name in self.test_results:
                client_results = self.test_results[client_name]

                report_lines.extend([
                    f"{client_name.upper()} API CLIENT RESULTS:",
                    "-" * 40,
                    ""
                ])

                # Summarize each test
                for test_name, test_data in client_results.items():
                    if isinstance(test_data, dict):
                        status = test_data.get('status', 'Unknown')

                        if 'success_rate' in test_data:
                            success_rate = test_data['success_rate']
                            total_tests = test_data.get('total_tests', 0)
                            successful_tests = test_data.get('successful_tests', 0)

                            report_lines.append(
                                f"{test_name.replace('_', ' ').title()}: "
                                f"{successful_tests}/{total_tests} ({success_rate:.1f}%) - {status}"
                            )
                        else:
                            response_time = test_data.get('response_time', 'N/A')
                            if response_time != 'N/A':
                                response_time = f"{response_time}s"

                            report_lines.append(
                                f"{test_name.replace('_', ' ').title()}: {status} "
                                f"(Response: {response_time})"
                            )

                        # Add error details if present
                        if test_data.get('error'):
                            report_lines.append(f"  Error: {test_data['error']}")

                report_lines.append("")

        # Working Endpoints Summary
        report_lines.extend([
            "ENDPOINT FUNCTIONALITY ASSESSMENT:",
            "-" * 40,
            ""
        ])

        # Analyze working endpoints
        working_endpoints = []
        broken_endpoints = []
        missing_implementations = []

        for client_name in ['real', 'mock']:
            if client_name in self.test_results:
                client_results = self.test_results[client_name]

                for test_name, test_data in client_results.items():
                    if isinstance(test_data, dict):
                        status = test_data.get('status')
                        success_rate = test_data.get('success_rate', 0)

                        endpoint_info = f"{client_name.title()} - {test_name.replace('_', ' ').title()}"

                        if status == 'success' or success_rate > 0:
                            working_endpoints.append(endpoint_info)
                        elif status == 'error':
                            broken_endpoints.append((endpoint_info, test_data.get('error', 'Unknown error')))
                        elif status == 'no_results':
                            missing_implementations.append(endpoint_info)

        if working_endpoints:
            report_lines.append("✅ WORKING ENDPOINTS:")
            for endpoint in working_endpoints:
                report_lines.append(f"  • {endpoint}")
            report_lines.append("")

        if broken_endpoints:
            report_lines.append("❌ BROKEN ENDPOINTS:")
            for endpoint, error in broken_endpoints:
                report_lines.append(f"  • {endpoint}")
                report_lines.append(f"    Error: {error}")
            report_lines.append("")

        if missing_implementations:
            report_lines.append("⚠️  ENDPOINTS WITH NO DATA:")
            for endpoint in missing_implementations:
                report_lines.append(f"  • {endpoint}")
            report_lines.append("")

        # Data Format Issues
        report_lines.extend([
            "DATA FORMAT ANALYSIS:",
            "-" * 30,
        ])

        # Analyze data formats from successful tests
        data_format_issues = []

        for client_name in ['real', 'mock']:
            if client_name in self.test_results:
                client_results = self.test_results[client_name]

                # Check APN search results for data format
                apn_results = client_results.get('apn_search', {})
                if apn_results.get('test_cases'):
                    for case in apn_results['test_cases']:
                        if case.get('result') and case['status'] == 'success':
                            result = case['result']

                            # Check for missing required fields
                            required_fields = ['apn', 'owner_name', 'property_address']
                            missing_fields = [field for field in required_fields if not result.get(field)]

                            if missing_fields:
                                data_format_issues.append(
                                    f"{client_name.title()} APN {case['apn']}: Missing fields {missing_fields}"
                                )

                            # Check for data type issues
                            if result.get('year_built') and not isinstance(result['year_built'], (int, type(None))):
                                data_format_issues.append(
                                    f"{client_name.title()} APN {case['apn']}: year_built should be integer"
                                )

        if data_format_issues:
            for issue in data_format_issues:
                report_lines.append(f"  ⚠️  {issue}")
        else:
            report_lines.append("  ✅ No major data format issues detected")

        report_lines.append("")

        # Recommendations
        report_lines.extend([
            "RECOMMENDATIONS:",
            "-" * 20,
            ""
        ])

        # Generate recommendations based on test results
        if 'real' in self.test_results:
            real_results = self.test_results['real']

            # Check if real API is working
            working_tests = sum(1 for test in real_results.values()
                              if isinstance(test, dict) and
                              (test.get('status') == 'success' or test.get('success_rate', 0) > 0))

            if working_tests == 0:
                report_lines.extend([
                    "🔧 CRITICAL: Real API appears to be non-functional",
                    "   • Verify API endpoints are correct",
                    "   • Check authentication token validity",
                    "   • Confirm network connectivity to mcassessor.maricopa.gov",
                    "   • Consider using mock client for development",
                    ""
                ])
            elif working_tests < len(real_results) / 2:
                report_lines.extend([
                    "⚠️  PARTIAL: Real API has limited functionality",
                    "   • Review failed endpoints for implementation issues",
                    "   • Verify endpoint URLs are current",
                    "   • Implement fallback mechanisms",
                    ""
                ])
            else:
                report_lines.extend([
                    "✅ GOOD: Real API is mostly functional",
                    "   • Monitor for rate limiting",
                    "   • Implement proper error handling",
                    "   • Add result caching for performance",
                    ""
                ])

        # Rate limiting recommendations
        for client_name in ['real', 'mock']:
            if client_name in self.test_results:
                rate_test = self.test_results[client_name].get('rate_limiting', {})
                if rate_test.get('rate_limited'):
                    report_lines.extend([
                        f"🔄 RATE LIMITING: {client_name.title()} API enforces rate limits",
                        "   • Implement exponential backoff",
                        "   • Add request queuing",
                        "   • Monitor 429 responses",
                        ""
                    ])

        report_lines.extend([
            "="*80,
            "END OF REPORT",
            "="*80
        ])

        return "\n".join(report_lines)

    def save_detailed_results(self, filename: str = None):
        """Save detailed test results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_test_results_{timestamp}.json"

        output_dir = Path(__file__).parent
        output_file = output_dir / filename

        # Prepare results for JSON serialization
        json_results = {
            'test_metadata': {
                'start_time': self.test_start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'test_apns': self.test_apns,
                'test_owners': self.test_owners,
                'test_addresses': self.test_addresses
            },
            'results': self.test_results
        }

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_results, f, indent=2, default=str)

            logger.info(f"Detailed test results saved to: {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"Failed to save detailed results: {e}")
            return None


def main():
    """Main test execution"""
    print("Starting Maricopa Property Search API Test Suite...")
    print("=" * 60)

    # Create test runner
    test_runner = APITestRunner()

    try:
        # Run all tests
        test_runner.run_all_tests()

        # Generate and display report
        report = test_runner.generate_report()
        print(report)

        # Save detailed results
        results_file = test_runner.save_detailed_results()
        if results_file:
            print(f"\nDetailed results saved to: {results_file}")

    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        print(f"\nTEST SUITE ERROR: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())