#!/usr/bin/env python3
"""
GUI Crash Fix Validation Suite
Tests the crash-safe refresh functions and GUI stability improvements
"""
import os
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock, Mock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock PyQt5 since it may not be available in test environment
class MockQMessageBox:
    @staticmethod
    def warning(parent, title, message):
        print(f"[WARNING] {title}: {message}")

    @staticmethod
    def information(parent, title, message):
        print(f"[INFO] {title}: {message}")

    @staticmethod
    def critical(parent, title, message):
        print(f"[CRITICAL] {title}: {message}")

class MockQProgressDialog:
    def __init__(self, label, cancel, min_val, max_val, parent):
        self.label = label
        self.value = 0
        print(f"[PROGRESS] Created: {label}")
    def setWindowModality(self, modality):
        pass
    def setMinimumDuration(self, duration):
        pass
    def show(self):
        print(f"[PROGRESS] Showing dialog")
def setValue(self, value):
        self.value = value
        print(f"[PROGRESS] Value: {value}%")
def setLabelText(self, text):
        print(f"[PROGRESS] Label: {text}")
def close(self):
        print(f"[PROGRESS] Closing dialog")
def deleteLater(self):
        print(f"[PROGRESS] Deleting dialog")

class MockQt:
    WindowModal = "WindowModal"

# Mock PyQt5 modules
sys.modules['PyQt5'] = MagicMock()
sys.modules['PyQt5.QtWidgets'] = MagicMock()
sys.modules['PyQt5.QtCore'] = MagicMock()
sys.modules['PyQt5.QtWidgets'].QMessageBox = MockQMessageBox
sys.modules['PyQt5.QtWidgets'].QProgressDialog = MockQProgressDialog
sys.modules['PyQt5.QtCore'].Qt = MockQt

try:
    # Import the refresh crash fix functions
import importlib.util

    spec = importlib.util.spec_from_file_location(
        "refresh_crash_fix",
        "/home/mattb/MaricopaPropertySearch/src/gui/refresh_crash_fix.py"
    )
    refresh_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(refresh_module)
        print("✅ Successfully imported crash fix functions")
except Exception as e:
        print(f"❌ Import error for crash fix: {e}")

class TestGUICrashFixes(unittest.TestCase):
    """Test suite for GUI crash fix validation"""
    def setUp(self):
        """Set up test fixtures"""
        # Create mock GUI window
        self.mock_window = Mock()
        self.mock_window.property_data = {"apn": "123-45-678", "owner": "Test Owner"}

        # Mock background manager
        self.mock_background_manager = Mock()
        self.mock_background_manager.is_running.return_value = True
        self.mock_background_manager.collect_data_for_apn.return_value = True
        self.mock_background_manager.worker = Mock()
        self.mock_background_manager.worker.cache = Mock()
        self.mock_background_manager.worker.active_jobs = {}

        self.mock_window.background_manager = self.mock_background_manager
        self.mock_window.load_property_details = Mock()
def test_refresh_property_data_no_property_data(self):
        """Test crash-safe behavior when no property data exists"""
        print("\n🔍 Testing refresh with no property data...")

        # Create window without property data
        window_no_data = Mock()
        window_no_data.property_data = None

        # Execute refresh function with no data
        try:
            refresh_module.refresh_property_data(window_no_data)
        print("✅ Handled missing property data gracefully")
        except Exception as e:
            self.fail(f"Function should handle missing property data: {e}")
def test_refresh_property_data_with_valid_data(self):
        """Test refresh with valid property data"""
        print("\n🔍 Testing refresh with valid property data...")

        try:
            refresh_module.refresh_property_data(self.mock_window)

            # Verify background manager was accessed safely
            self.mock_background_manager.is_running.assert_called_once()
            self.mock_background_manager.collect_data_for_apn.assert_called_once()
            self.mock_window.load_property_details.assert_called_once()
        print("✅ Refresh with valid data completed successfully")
        except Exception as e:
            self.fail(f"Function should handle valid data: {e}")
def test_refresh_property_data_no_background_manager(self):
        """Test crash-safe behavior when background manager is missing"""
        print("\n🔍 Testing refresh with no background manager...")

        window_no_manager = Mock()
        window_no_manager.property_data = {"apn": "123-45-678"}
        window_no_manager.background_manager = None
        window_no_manager.load_property_details = Mock()

        try:
            refresh_module.refresh_property_data(window_no_manager)
        print("✅ Handled missing background manager gracefully")
        except Exception as e:
            self.fail(f"Function should handle missing background manager: {e}")
def test_refresh_property_data_background_service_not_running(self):
        """Test behavior when background service is not running"""
        print("\n🔍 Testing refresh with stopped background service...")

        self.mock_background_manager.is_running.return_value = False

        try:
            refresh_module.refresh_property_data(self.mock_window)
        print("✅ Handled stopped background service gracefully")
        except Exception as e:
            self.fail(f"Function should handle stopped service: {e}")
def test_refresh_property_data_background_manager_exception(self):
        """Test crash-safe behavior when background manager throws exception"""
        print("\n🔍 Testing refresh with background manager exception...")

        self.mock_background_manager.is_running.side_effect = Exception("Test exception")

        try:
            refresh_module.refresh_property_data(self.mock_window)
        print("✅ Handled background manager exception gracefully")
        except Exception as e:
            self.fail(f"Function should handle background manager exceptions: {e}")
def test_update_dialog_status_safe_no_background_manager(self):
        """Test safe status update with no background manager"""
        print("\n🔍 Testing status update with no background manager...")

        window_no_manager = Mock()
        window_no_manager.background_manager = None

        try:
            refresh_module._update_dialog_status_safe(window_no_manager)
        print("✅ Status update handled missing background manager gracefully")
        except Exception as e:
            self.fail(f"Status update should handle missing manager: {e}")
def test_update_dialog_status_safe_with_valid_data(self):
        """Test safe status update with valid data"""
        print("\n🔍 Testing status update with valid data...")

        self.mock_window.status_widget = Mock()
        self.mock_background_manager.get_collection_status.return_value = {"status": "active"}

        try:
            refresh_module._update_dialog_status_safe(self.mock_window)

            # Verify status was retrieved and widget updated
            self.mock_background_manager.get_collection_status.assert_called_once()
            self.mock_window.status_widget.update_status.assert_called_once()
        print("✅ Status update with valid data completed successfully")
        except Exception as e:
            self.fail(f"Status update should work with valid data: {e}")
def test_update_dialog_status_exception_handling(self):
        """Test status update exception handling"""
        print("\n🔍 Testing status update exception handling...")

        self.mock_background_manager.get_collection_status.side_effect = Exception("Status error")

        try:
            refresh_module._update_dialog_status_safe(self.mock_window)
        print("✅ Status update handled exception gracefully")
        except Exception as e:
            self.fail(f"Status update should handle exceptions: {e}")
def test_thread_safety_multiple_calls(self):
        """Test thread safety with multiple concurrent refresh calls"""
        print("\n🔍 Testing thread safety with concurrent calls...")

        errors = []
def worker_thread(thread_id):
            try:
                # Create separate mock window for each thread
                thread_window = Mock()
                thread_window.property_data = {"apn": f"thread-{thread_id}"}
                thread_window.background_manager = Mock()
                thread_window.background_manager.is_running.return_value = True
                thread_window.background_manager.collect_data_for_apn.return_value = True
                thread_window.load_property_details = Mock()

                refresh_module.refresh_property_data(thread_window)

            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")

        # Run multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=5.0)

        # Verify no errors occurred
        self.assertEqual(len(errors), 0, f"Thread safety errors: {errors}")
        print("✅ Thread safety test passed")
def run_gui_integration_tests():
    """Run integration tests for GUI crash fixes"""
        print("\n🔧 Running GUI integration tests...")

    try:
        # Check that crash fix functions exist
        required_functions = ['refresh_property_data', '_update_dialog_status_safe']

        for func_name in required_functions:
            if hasattr(refresh_module, func_name):
        print(f"✅ Function {func_name} exists")
            else:
        print(f"❌ Function {func_name} missing")
                return False

        # Check enhanced_main_window.py exists and has been modified
        gui_file = "/home/mattb/MaricopaPropertySearch/src/gui/enhanced_main_window.py"
        if os.path.exists(gui_file):
        print("✅ Enhanced main window file exists")

            # Check for crash fix signatures in the file
            with open(gui_file, 'r') as f:
                content = f.read()
                if "CRASH-SAFE" in content:
        print("✅ Crash-safe functions appear to be applied")
                else:
        print("⚠️ Crash-safe functions may not be fully applied")
        else:
        print("❌ Enhanced main window file not found")
            return False

        return True

    except Exception as e:
        print(f"❌ GUI integration test failed: {e}")
        return False
def main():
    """Main test runner"""
        print("🚀 Starting GUI Crash Fix Validation Suite")
        print("=" * 60)

    # Run integration tests first
    integration_success = run_gui_integration_tests()

    if not integration_success:
        print("\n❌ Integration tests failed - stopping execution")
        return 1

    # Run unit tests
        print("\n🧪 Running unit tests...")

    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestGUICrashFixes)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    # Summary
        print("\n" + "=" * 60)
        print("📊 GUI CRASH FIX TEST SUMMARY")
        print("=" * 60)

    if result.wasSuccessful():
        print("✅ ALL GUI TESTS PASSED")
        print(f"   Tests run: {result.testsRun}")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        return 0
    else:
        print("❌ SOME GUI TESTS FAILED")
        print(f"   Tests run: {result.testsRun}")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")

        if result.failures:
        print("\n📝 FAILURES:")
            for test, traceback in result.failures:
        print(f"   {test}: {traceback}")

        if result.errors:
        print("\n🔥 ERRORS:")
            for test, traceback in result.errors:
        print(f"   {test}: {traceback}")

        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)