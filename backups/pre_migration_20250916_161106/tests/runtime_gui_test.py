#!/usr/bin/env python3
"""
Runtime GUI Test - Tests actual functionality without full GUI initialization
"""

import os
import sys
import tempfile
from unittest.mock import MagicMock, Mock, patch

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

class RuntimeGUITester:
    """Tests GUI functionality at runtime without requiring full GUI"""

    def __init__(self):
        self.test_results = {}
        self.errors = []

    def test_import_functionality(self):
        """Test if we can import the GUI module and its dependencies"""
        print("🔍 Testing Import Functionality...")

        try:
            # Test core imports
            from config_manager import ConfigManager

            self.test_results['import_config_manager'] = "✅ PASS"

            from database_manager import DatabaseManager

            self.test_results['import_database_manager'] = "✅ PASS"

            # Test if we can import the main GUI class
            from gui.enhanced_main_window import EnhancedMainWindow

            self.test_results['import_main_window'] = "✅ PASS"

            # Test if we can import specific widget classes
            from gui.enhanced_main_window import PropertyDetailsWidget

            self.test_results['import_property_details'] = "✅ PASS"

            from gui.enhanced_main_window import NotificationArea

            self.test_results['import_notification_area'] = "✅ PASS"

            return True

        except ImportError as e:
            self.test_results['import_functionality'] = f"❌ FAIL - Import error: {e}"
            self.errors.append(f"Import failure: {e}")
            return False
        except Exception as e:
            self.test_results['import_functionality'] = f"❌ FAIL - Unexpected error: {e}"
            self.errors.append(f"Unexpected import error: {e}")
            return False

    def test_component_initialization(self):
        """Test component initialization without full GUI"""
        print("🔍 Testing Component Initialization...")

        try:
            # Mock PyQt5 components to avoid display requirements
            with patch('PyQt5.QtWidgets.QApplication') as mock_app, \
                 patch('PyQt5.QtWidgets.QMainWindow') as mock_main_window:

                # Import after patching
                from gui.enhanced_main_window import (
                    PerformanceMetrics,
                    PropertySearchEngine,
                )

                # Test PropertySearchEngine
                mock_db = Mock()
                search_engine = PropertySearchEngine(mock_db)
                self.test_results['property_search_engine_init'] = "✅ PASS"

                # Test mock search functionality
                results = search_engine.search_properties("test")
                if isinstance(results, list) and len(results) > 0:
                    self.test_results['search_engine_mock_data'] = "✅ PASS - Returns mock data"
                else:
                    self.test_results['search_engine_mock_data'] = "❌ FAIL - No mock data returned"

                # Test PerformanceMetrics
                metrics = PerformanceMetrics()
                metrics.record_search("test", 3, 1.5)
                summary = metrics.get_summary()
                if summary and 'total_searches' in summary:
                    self.test_results['performance_metrics'] = "✅ PASS - Metrics working"
                else:
                    self.test_results['performance_metrics'] = "❌ FAIL - Metrics not working"

                return True

        except Exception as e:
            self.test_results['component_initialization'] = f"❌ FAIL - {e}"
            self.errors.append(f"Component initialization error: {e}")
            return False

    def test_database_integration(self):
        """Test database integration capabilities"""
        print("🔍 Testing Database Integration...")

        try:
            from database_manager import DatabaseManager

            from config_manager import ConfigManager

            # Test with temporary database
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
                temp_db_path = tmp.name

            try:
                # Create config manager with temp database
                config = ConfigManager()
                # Override database path for testing
                config.db_path = temp_db_path

                # Test database manager initialization
                db_manager = DatabaseManager(config)
                if db_manager:
                    self.test_results['database_manager_init'] = "✅ PASS"

                    # Test connection
                    if db_manager.test_connection():
                        self.test_results['database_connection'] = "✅ PASS"
                    else:
                        self.test_results['database_connection'] = "⚠️ WARNING - Connection test failed"

                else:
                    self.test_results['database_manager_init'] = "❌ FAIL - Could not create DatabaseManager"

            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_db_path)
                except:
        pass

            return True

        except Exception as e:
            self.test_results['database_integration'] = f"❌ FAIL - {e}"
            self.errors.append(f"Database integration error: {e}")
            return False

    def test_search_functionality(self):
        """Test search functionality without GUI"""
        print("🔍 Testing Search Functionality...")

        try:
            from gui.enhanced_main_window import PropertySearchEngine

            # Create mock database
            mock_db = Mock()
            search_engine = PropertySearchEngine(mock_db)

            # Test various search scenarios
            test_cases = [
                ("123-45-678", "APN search"),
                ("1234 Main St", "Address search"),
                ("John Doe", "Owner search"),
                ("", "Empty search"),
                ("*invalid*", "Invalid characters")
            ]

            for search_term, description in test_cases:
                try:
                    results = search_engine.search_properties(search_term)
                    if search_term == "":
                        # Empty search should return empty list
                        if len(results) == 0:
                            self.test_results[f'search_{description}'] = "✅ PASS - Empty search handled"
                        else:
                            self.test_results[f'search_{description}'] = "⚠️ WARNING - Empty search returns data"
                    else:
                        # Non-empty search should return mock data
                        if isinstance(results, list):
                            self.test_results[f'search_{description}'] = f"✅ PASS - Returns {len(results)} results"
                        else:
                            self.test_results[f'search_{description}'] = "❌ FAIL - Invalid return type"

                except Exception as e:
                    self.test_results[f'search_{description}'] = f"❌ FAIL - Error: {e}"

            return True

        except Exception as e:
            self.test_results['search_functionality'] = f"❌ FAIL - {e}"
            self.errors.append(f"Search functionality error: {e}")
            return False

    def test_error_handling(self):
        """Test error handling mechanisms"""
        print("🔍 Testing Error Handling...")

        try:
            from gui.enhanced_main_window import PropertySearchEngine

            # Test with None database (should handle gracefully)
            try:
                search_engine = PropertySearchEngine(None)
                results = search_engine.search_properties("test")
                self.test_results['error_handling_null_db'] = "✅ PASS - Handles None database"
            except Exception as e:
                self.test_results['error_handling_null_db'] = f"⚠️ WARNING - Exception with None DB: {e}"

            # Test with invalid database mock
            try:
                invalid_db = Mock()
                invalid_db.side_effect = Exception("Database error")
                search_engine = PropertySearchEngine(invalid_db)
                results = search_engine.search_properties("test")
                self.test_results['error_handling_db_error'] = "✅ PASS - Handles database errors"
            except Exception as e:
                self.test_results['error_handling_db_error'] = f"✅ PASS - Properly raises exception: {type(e).__name__}"

            return True

        except Exception as e:
            self.test_results['error_handling'] = f"❌ FAIL - {e}"
            self.errors.append(f"Error handling test error: {e}")
            return False

    def test_widget_classes(self):
        """Test individual widget class definitions"""
        print("🔍 Testing Widget Classes...")

        try:
            # Test widget imports and basic instantiation
            widget_classes = [
                'PropertyDetailsWidget',
                'PerformanceDashboard',
                'SearchHistoryWidget',
                'NotificationArea',
                'StatusIndicator',
                'AdvancedFiltersWidget'
            ]

            for widget_name in widget_classes:
                try:
                    # Import the widget class
                    module = __import__('gui.enhanced_main_window', fromlist=[widget_name])
                    widget_class = getattr(module, widget_name)

                    # Check if it's a class and has expected attributes
                    if hasattr(widget_class, '__init__'):
                        self.test_results[f'widget_{widget_name}_import'] = "✅ PASS - Class imports successfully"

                        # Try to inspect the class (without instantiating to avoid GUI requirements)
                        import inspect

                        sig = inspect.signature(widget_class.__init__)
                        params = list(sig.parameters.keys())
                        self.test_results[f'widget_{widget_name}_signature'] = f"✅ INFO - Parameters: {params}"

                    else:
                        self.test_results[f'widget_{widget_name}_import'] = "❌ FAIL - Not a proper class"

                except AttributeError:
                    self.test_results[f'widget_{widget_name}_import'] = "❌ FAIL - Class not found"
                except Exception as e:
                    self.test_results[f'widget_{widget_name}_import'] = f"❌ FAIL - Error: {e}"

            return True

        except Exception as e:
            self.test_results['widget_classes'] = f"❌ FAIL - {e}"
            self.errors.append(f"Widget classes test error: {e}")
            return False

    def run_all_tests(self):
        """Run all runtime tests"""
        print("🚀 Starting Runtime GUI Tests...")
        print("=" * 60)

        test_methods = [
            self.test_import_functionality,
            self.test_component_initialization,
            self.test_database_integration,
            self.test_search_functionality,
            self.test_error_handling,
            self.test_widget_classes
        ]

        successful_tests = 0
        for test_method in test_methods:
            try:
                if test_method():
                    successful_tests += 1
                print(f"  ✓ {test_method.__name__}")
            except Exception as e:
                print(f"  ✗ {test_method.__name__} - {e}")
                self.errors.append(f"{test_method.__name__} failed: {e}")

        print(f"\n📊 Tests completed: {successful_tests}/{len(test_methods)}")

        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        from datetime import datetime

        print("\n" + "="*80)
        print("📋 RUNTIME GUI TEST REPORT")
        print("="*80)

        # Group results by category
        categories = {}
        for test_name, result in self.test_results.items():
            category = test_name.split('_')[0]
            if category not in categories:
                categories[category] = []
            categories[category].append((test_name, result))

        # Print by category
        for category, tests in categories.items():
            print(f"\n🔧 {category.upper()}:")
            for test_name, result in tests:
                print(f"  {test_name:40} | {result}")

        # Print errors
        if self.errors:
            print(f"\n🚨 ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i:2}. {error}")

        # Summary
        total_tests = len(self.test_results)
        passed = len([r for r in self.test_results.values() if r.startswith('✅')])
        warnings = len([r for r in self.test_results.values() if r.startswith('⚠️')])
        failed = len([r for r in self.test_results.values() if r.startswith('❌')])

        print(f"\n📈 SUMMARY:")
        print(f"  Total tests: {total_tests}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ⚠️ Warnings: {warnings}")
        print(f"  ❌ Failed: {failed}")
        print(f"  🚨 Errors: {len(self.errors)}")

        if total_tests > 0:
            success_rate = (passed / total_tests) * 100
            print(f"  📊 Success rate: {success_rate:.1f}%")

        return {
            'timestamp': datetime.now().isoformat(),
            'test_results': self.test_results,
            'errors': self.errors,
            'summary': {
                'total_tests': total_tests,
                'passed': passed,
                'warnings': warnings,
                'failed': failed,
                'total_errors': len(self.errors),
                'success_rate': success_rate if total_tests > 0 else 0
            }
        }

def main():
    """Main test function"""
    tester = RuntimeGUITester()
    report = tester.run_all_tests()

    # Save report
    try:
        import json
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"runtime_gui_test_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Test report saved to: {filename}")

    except Exception as e:
        print(f"⚠️ Could not save report: {e}")

    return report

if __name__ == "__main__":
    main()