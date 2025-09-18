#!/usr/bin/env python3
"""
Comprehensive End-to-End Application Testing Suite
Tests all application functionality after recent fixes.
"""

import os
import sys
import time
import json
import traceback
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class ComprehensiveApplicationTest:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': [],
            'application_health': 'Unknown',
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }

        # Test paths
        self.project_root = Path(__file__).parent.parent
        self.config_path = self.project_root / 'config' / 'config.ini'
        self.log_dir = self.project_root / 'logs'

    def log_test_result(self, test_name, status, message, duration=0, details=None):
        """Log individual test results"""
        self.results['total_tests'] += 1
        if status == 'PASS':
            self.results['passed_tests'] += 1
        else:
            self.results['failed_tests'] += 1

        test_result = {
            'test_name': test_name,
            'status': status,
            'message': message,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }

        if details:
            test_result['details'] = details

        self.results['test_details'].append(test_result)
        print(f"[{status}] {test_name}: {message}")

    def test_environment_setup(self):
        """Test 1: Environment and Dependencies"""
        print("\n" + "="*80)
        print("TEST 1: ENVIRONMENT AND DEPENDENCIES")
        print("="*80)

        start_time = time.time()

        # Check Python version
        if sys.version_info >= (3, 8):
            self.log_test_result("Python Version", "PASS", f"Python {sys.version}")
        else:
            self.log_test_result("Python Version", "FAIL", f"Python {sys.version} < 3.8")

        # Check required directories
        required_dirs = ['src', 'config', 'logs', 'exports']
        for directory in required_dirs:
            dir_path = self.project_root / directory
            if dir_path.exists():
                self.log_test_result(f"Directory {directory}", "PASS", f"Found at {dir_path}")
            else:
                self.log_test_result(f"Directory {directory}", "FAIL", f"Missing: {dir_path}")

        # Check key files
        key_files = [
            'RUN_APPLICATION.py',
            'config/config.ini',
            'src/config_manager.py',
            'src/database_manager.py',
            'src/gui/enhanced_main_window.py'
        ]

        for file_path in key_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.log_test_result(f"File {file_path}", "PASS", f"Found")
            else:
                self.log_test_result(f"File {file_path}", "FAIL", f"Missing: {full_path}")

        duration = time.time() - start_time
        print(f"Environment setup test completed in {duration:.2f} seconds")

    def test_configuration_management(self):
        """Test 2: Configuration Management"""
        print("\n" + "="*80)
        print("TEST 2: CONFIGURATION MANAGEMENT")
        print("="*80)

        start_time = time.time()

        try:
            from config_manager import ConfigManager
            config_manager = ConfigManager()

            # Test configuration loading
            if hasattr(config_manager, 'config') and config_manager.config:
                self.log_test_result("Config Loading", "PASS", "Configuration loaded successfully")

                # Test database section
                if config_manager.config.has_section('database'):
                    self.log_test_result("Database Config", "PASS", "Database section found")

                    # Check database keys
                    db_keys = ['host', 'port', 'database', 'user', 'password']
                    for key in db_keys:
                        if config_manager.config.has_option('database', key):
                            self.log_test_result(f"DB Config {key}", "PASS", f"Found")
                        else:
                            self.log_test_result(f"DB Config {key}", "FAIL", f"Missing database.{key}")
                else:
                    self.log_test_result("Database Config", "FAIL", "No database section found")
                    self.results['critical_issues'].append("Database configuration section missing")

            else:
                self.log_test_result("Config Loading", "FAIL", "Failed to load configuration")
                self.results['critical_issues'].append("Configuration loading failed")

        except Exception as e:
            self.log_test_result("Config Manager Import", "FAIL", f"Import error: {str(e)}")
            self.results['critical_issues'].append(f"ConfigManager import failed: {str(e)}")

        duration = time.time() - start_time
        print(f"Configuration test completed in {duration:.2f} seconds")

    def test_database_connectivity(self):
        """Test 3: Database Connectivity"""
        print("\n" + "="*80)
        print("TEST 3: DATABASE CONNECTIVITY")
        print("="*80)

        start_time = time.time()

        try:
            from database_manager import DatabaseManager
            from threadsafe_database_manager import ThreadSafeDatabaseManager

            # Test basic database manager
            db_manager = DatabaseManager()
            if hasattr(db_manager, 'test_connection'):
                if db_manager.test_connection():
                    self.log_test_result("Database Connection", "PASS", "Database connection successful")
                else:
                    self.log_test_result("Database Connection", "WARN", "Database connection failed - may be expected")
                    self.results['warnings'].append("Database connection failed - PostgreSQL may not be running")
            else:
                self.log_test_result("Database Test Method", "FAIL", "No test_connection method found")

            # Test thread-safe database manager
            ts_db_manager = ThreadSafeDatabaseManager()
            self.log_test_result("ThreadSafe DB Manager", "PASS", "ThreadSafeDatabaseManager initialized")

        except Exception as e:
            self.log_test_result("Database Manager", "FAIL", f"Error: {str(e)}")
            self.results['critical_issues'].append(f"Database manager error: {str(e)}")

        duration = time.time() - start_time
        print(f"Database test completed in {duration:.2f} seconds")

    def test_api_client(self):
        """Test 4: API Client Functionality"""
        print("\n" + "="*80)
        print("TEST 4: API CLIENT FUNCTIONALITY")
        print("="*80)

        start_time = time.time()

        try:
            from api_client import APIClient

            api_client = APIClient()
            self.log_test_result("API Client Init", "PASS", "APIClient initialized successfully")

            # Test with a sample APN (non-blocking test)
            test_apn = "123-45-678"
            if hasattr(api_client, 'search_property_by_apn'):
                try:
                    # This should be a non-blocking test
                    result = api_client.search_property_by_apn(test_apn, timeout=5)
                    if result:
                        self.log_test_result("API Search Test", "PASS", f"API search returned data")
                    else:
                        self.log_test_result("API Search Test", "WARN", "API search returned no data (expected for test APN)")
                except Exception as api_e:
                    self.log_test_result("API Search Test", "WARN", f"API search failed: {str(api_e)} (may be expected)")
            else:
                self.log_test_result("API Search Method", "FAIL", "search_property_by_apn method not found")

        except Exception as e:
            self.log_test_result("API Client", "FAIL", f"Error: {str(e)}")
            self.results['warnings'].append(f"API client error: {str(e)}")

        duration = time.time() - start_time
        print(f"API client test completed in {duration:.2f} seconds")

    def test_background_data_collection(self):
        """Test 5: Background Data Collection"""
        print("\n" + "="*80)
        print("TEST 5: BACKGROUND DATA COLLECTION")
        print("="*80)

        start_time = time.time()

        try:
            from background_data_collector import BackgroundDataCollector

            collector = BackgroundDataCollector()
            self.log_test_result("Background Collector Init", "PASS", "BackgroundDataCollector initialized")

            # Test collector methods
            if hasattr(collector, 'start_collection'):
                self.log_test_result("Collection Method", "PASS", "start_collection method found")
            else:
                self.log_test_result("Collection Method", "FAIL", "start_collection method missing")

            if hasattr(collector, 'stop_collection'):
                self.log_test_result("Stop Method", "PASS", "stop_collection method found")
            else:
                self.log_test_result("Stop Method", "FAIL", "stop_collection method missing")

        except Exception as e:
            self.log_test_result("Background Collector", "FAIL", f"Error: {str(e)}")
            self.results['critical_issues'].append(f"Background data collection error: {str(e)}")

        duration = time.time() - start_time
        print(f"Background data collection test completed in {duration:.2f} seconds")

    def test_gui_components(self):
        """Test 6: GUI Components (Non-Display Test)"""
        print("\n" + "="*80)
        print("TEST 6: GUI COMPONENTS")
        print("="*80)

        start_time = time.time()

        try:
            # Test GUI imports without initializing display
            import sys

            # Test PyQt5 availability
            try:
                from PyQt5.QtWidgets import QApplication
                self.log_test_result("PyQt5 Import", "PASS", "PyQt5 available")
            except ImportError:
                self.log_test_result("PyQt5 Import", "FAIL", "PyQt5 not available")
                self.results['critical_issues'].append("PyQt5 not available")
                return

            # Test main window import
            try:
                from gui.enhanced_main_window import EnhancedMainWindow
                self.log_test_result("Main Window Import", "PASS", "EnhancedMainWindow imported")
            except ImportError as e:
                self.log_test_result("Main Window Import", "FAIL", f"Import error: {str(e)}")
                self.results['critical_issues'].append(f"EnhancedMainWindow import failed: {str(e)}")

        except Exception as e:
            self.log_test_result("GUI Components", "FAIL", f"Error: {str(e)}")
            self.results['critical_issues'].append(f"GUI component error: {str(e)}")

        duration = time.time() - start_time
        print(f"GUI components test completed in {duration:.2f} seconds")

    def test_logging_system(self):
        """Test 7: Logging System"""
        print("\n" + "="*80)
        print("TEST 7: LOGGING SYSTEM")
        print("="*80)

        start_time = time.time()

        try:
            import logging
            from logging_config import setup_logging

            # Test logging setup
            logger = setup_logging()
            if logger:
                self.log_test_result("Logging Setup", "PASS", "Logging configured successfully")

                # Test logging directories
                if self.log_dir.exists():
                    self.log_test_result("Log Directory", "PASS", f"Log directory exists: {self.log_dir}")
                else:
                    self.log_test_result("Log Directory", "WARN", f"Log directory missing: {self.log_dir}")

                # Test writing a log message
                logger.info("Test log message from comprehensive test suite")
                self.log_test_result("Log Writing", "PASS", "Test log message written")
            else:
                self.log_test_result("Logging Setup", "FAIL", "Logging setup returned None")

        except Exception as e:
            self.log_test_result("Logging System", "FAIL", f"Error: {str(e)}")
            self.results['warnings'].append(f"Logging system error: {str(e)}")

        duration = time.time() - start_time
        print(f"Logging system test completed in {duration:.2f} seconds")

    def test_file_operations(self):
        """Test 8: File Operations"""
        print("\n" + "="*80)
        print("TEST 8: FILE OPERATIONS")
        print("="*80)

        start_time = time.time()

        # Test export directory
        export_dir = self.project_root / 'exports'
        if export_dir.exists():
            self.log_test_result("Export Directory", "PASS", f"Export directory exists")

            # Test write permissions
            test_file = export_dir / 'test_write.txt'
            try:
                with open(test_file, 'w') as f:
                    f.write("Test write operation")
                test_file.unlink()  # Delete test file
                self.log_test_result("Write Permissions", "PASS", "Write permissions verified")
            except Exception as e:
                self.log_test_result("Write Permissions", "FAIL", f"Write test failed: {str(e)}")
        else:
            self.log_test_result("Export Directory", "FAIL", "Export directory missing")

        # Test cache directory
        cache_dir = self.project_root / 'cache'
        if cache_dir.exists():
            self.log_test_result("Cache Directory", "PASS", "Cache directory exists")
        else:
            self.log_test_result("Cache Directory", "WARN", "Cache directory missing")

        duration = time.time() - start_time
        print(f"File operations test completed in {duration:.2f} seconds")

    def run_stress_tests(self):
        """Test 9: Stress Tests"""
        print("\n" + "="*80)
        print("TEST 9: STRESS TESTS")
        print("="*80)

        start_time = time.time()

        # Memory usage test
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024

            if memory_mb < 500:  # Less than 500MB is reasonable
                self.log_test_result("Memory Usage", "PASS", f"Memory usage: {memory_mb:.1f} MB")
            elif memory_mb < 1000:
                self.log_test_result("Memory Usage", "WARN", f"Memory usage: {memory_mb:.1f} MB (high)")
                self.results['warnings'].append(f"High memory usage: {memory_mb:.1f} MB")
            else:
                self.log_test_result("Memory Usage", "FAIL", f"Memory usage: {memory_mb:.1f} MB (excessive)")
                self.results['critical_issues'].append(f"Excessive memory usage: {memory_mb:.1f} MB")

        except ImportError:
            self.log_test_result("Memory Test", "WARN", "psutil not available for memory testing")

        # Configuration loading stress test
        try:
            from config_manager import ConfigManager

            load_times = []
            for i in range(10):
                config_start = time.time()
                config_manager = ConfigManager()
                load_times.append(time.time() - config_start)

            avg_load_time = sum(load_times) / len(load_times)
            if avg_load_time < 0.1:  # Less than 100ms average
                self.log_test_result("Config Load Speed", "PASS", f"Average load time: {avg_load_time:.3f}s")
            else:
                self.log_test_result("Config Load Speed", "WARN", f"Slow config loading: {avg_load_time:.3f}s")

        except Exception as e:
            self.log_test_result("Config Stress Test", "FAIL", f"Error: {str(e)}")

        duration = time.time() - start_time
        print(f"Stress tests completed in {duration:.2f} seconds")

    def analyze_application_health(self):
        """Analyze overall application health"""
        print("\n" + "="*80)
        print("APPLICATION HEALTH ANALYSIS")
        print("="*80)

        total_tests = self.results['total_tests']
        passed_tests = self.results['passed_tests']
        failed_tests = self.results['failed_tests']
        critical_issues = len(self.results['critical_issues'])
        warnings = len(self.results['warnings'])

        if total_tests == 0:
            self.results['application_health'] = 'UNKNOWN'
        else:
            success_rate = passed_tests / total_tests

            if critical_issues == 0 and success_rate >= 0.9:
                self.results['application_health'] = 'EXCELLENT'
            elif critical_issues == 0 and success_rate >= 0.8:
                self.results['application_health'] = 'GOOD'
            elif critical_issues <= 2 and success_rate >= 0.7:
                self.results['application_health'] = 'FAIR'
            else:
                self.results['application_health'] = 'POOR'

        print(f"Overall Health: {self.results['application_health']}")
        print(f"Success Rate: {passed_tests}/{total_tests} ({success_rate*100:.1f}%)")
        print(f"Critical Issues: {critical_issues}")
        print(f"Warnings: {warnings}")

        # Generate recommendations
        if critical_issues > 0:
            self.results['recommendations'].append("Address critical issues before production use")
        if warnings > 3:
            self.results['recommendations'].append("Review and resolve warnings for optimal performance")
        if success_rate < 0.8:
            self.results['recommendations'].append("Investigate and fix failing tests")

    def generate_report(self):
        """Generate comprehensive test report"""
        report_path = self.project_root / 'tests' / 'comprehensive_test_report.json'

        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nDetailed test report saved to: {report_path}")
        return report_path

    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("STARTING COMPREHENSIVE APPLICATION TESTING")
        print("="*80)

        overall_start = time.time()

        try:
            self.test_environment_setup()
            self.test_configuration_management()
            self.test_database_connectivity()
            self.test_api_client()
            self.test_background_data_collection()
            self.test_gui_components()
            self.test_logging_system()
            self.test_file_operations()
            self.run_stress_tests()

        except Exception as e:
            print(f"CRITICAL ERROR during testing: {str(e)}")
            traceback.print_exc()
            self.results['critical_issues'].append(f"Testing framework error: {str(e)}")

        overall_duration = time.time() - overall_start

        self.analyze_application_health()

        print("\n" + "="*80)
        print("TESTING COMPLETE")
        print("="*80)
        print(f"Total Duration: {overall_duration:.2f} seconds")

        report_path = self.generate_report()
        return self.results, report_path

def main():
    """Main test execution"""
    tester = ComprehensiveApplicationTest()
    results, report_path = tester.run_all_tests()

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Application Health: {results['application_health']}")
    print(f"Tests Passed: {results['passed_tests']}")
    print(f"Tests Failed: {results['failed_tests']}")
    print(f"Critical Issues: {len(results['critical_issues'])}")
    print(f"Warnings: {len(results['warnings'])}")

    if results['critical_issues']:
        print("\nCRITICAL ISSUES:")
        for issue in results['critical_issues']:
            print(f"  • {issue}")

    if results['recommendations']:
        print("\nRECOMMENDATIONS:")
        for rec in results['recommendations']:
            print(f"  • {rec}")

    return results['application_health']

if __name__ == "__main__":
    health_status = main()
    sys.exit(0 if health_status in ['EXCELLENT', 'GOOD'] else 1)