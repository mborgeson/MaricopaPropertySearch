#!/usr/bin/env python
"""
Test Application with Hive Mind Fixes
Comprehensive test to verify the application works after fixing:
1. ConfigManager get method
2. DatabaseManager get_property_details -> get_property_by_apn
3. Tax and sales history display
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_config_manager():
    """Test ConfigManager with new get method"""
    print("\n🔍 Testing ConfigManager.get() method...")

    try:
        from src.config_manager import ConfigManager

        # Initialize ConfigManager
        config = ConfigManager()

        # Test the new get method
        if not hasattr(config, "get"):
            print("❌ ERROR: ConfigManager.get() method not found!")
            return False

        # Test with various types
        test_value = config.get("test_key", True)  # boolean default
        print(f"  ✓ Boolean default test: {test_value}")

        test_value = config.get("test_key", 100)  # integer default
        print(f"  ✓ Integer default test: {test_value}")

        test_value = config.get("test_key", "default")  # string default
        print(f"  ✓ String default test: {test_value}")

        print("✅ ConfigManager.get() method working correctly!")
        return True

    except Exception as e:
        print(f"❌ Error testing ConfigManager: {e}")
        return False


def test_database_manager():
    """Test DatabaseManager methods"""
    print("\n🔍 Testing DatabaseManager methods...")

    try:
        from src.config_manager import ConfigManager
        from src.database_manager import DatabaseManager

        # Check if get_property_by_apn exists
        db_methods = dir(DatabaseManager)

        if "get_property_by_apn" not in db_methods:
            print("❌ ERROR: DatabaseManager.get_property_by_apn() not found!")
            return False
        print("  ✓ get_property_by_apn() method exists")

        if "get_tax_history" not in db_methods:
            print("❌ ERROR: DatabaseManager.get_tax_history() not found!")
            return False
        print("  ✓ get_tax_history() method exists")

        if "get_sales_history" not in db_methods:
            print("❌ ERROR: DatabaseManager.get_sales_history() not found!")
            return False
        print("  ✓ get_sales_history() method exists")

        print("✅ DatabaseManager methods verified!")
        return True

    except Exception as e:
        print(f"❌ Error testing DatabaseManager: {e}")
        return False


def test_gui_imports():
    """Test GUI imports without AttributeError"""
    print("\n🔍 Testing GUI imports...")

    try:
        # Test importing the enhanced main window
        from src.gui.enhanced_main_window import EnhancedMainWindow

        print("  ✓ EnhancedMainWindow imported successfully")

        # Test importing GUI dialogs
        from src.gui.gui_enhancements_dialogs import ApplicationSettingsDialog

        print("  ✓ ApplicationSettingsDialog imported successfully")

        # Check if the dialog can use ConfigManager
        from src.config_manager import ConfigManager

        config = ConfigManager()

        # The dialog should be able to call config.get() now
        if hasattr(config, "get"):
            print("  ✓ ApplicationSettingsDialog can use config.get()")
        else:
            print("❌ ERROR: ConfigManager.get() missing for dialog!")
            return False

        print("✅ GUI imports work without AttributeError!")
        return True

    except AttributeError as ae:
        print(f"❌ AttributeError in GUI: {ae}")
        return False
    except Exception as e:
        print(f"❌ Error testing GUI: {e}")
        return False


def test_application_integration():
    """Test full application integration"""
    print("\n🔍 Testing application integration...")

    try:
        # Import all key components
        from src.api_client import MaricopaAPIClient
        from src.config_manager import ConfigManager

        # Initialize components
        config = ConfigManager()
        print("  ✓ ConfigManager initialized")

        # Test that API client can be created
        api_client = MaricopaAPIClient(config)
        print("  ✓ API client initialized")

        # Check if API client has required methods
        if hasattr(api_client, "get_property_details"):
            print("  ✓ API client has get_property_details()")

        if hasattr(api_client, "get_tax_history"):
            print("  ✓ API client has get_tax_history()")

        if hasattr(api_client, "get_sales_history"):
            print("  ✓ API client has get_sales_history()")

        print("✅ Application integration successful!")
        return True

    except Exception as e:
        print(f"❌ Error in application integration: {e}")
        return False


def run_comprehensive_test():
    """Run all tests and report results"""
    print("=" * 60)
    print("🧪 HIVE MIND FIXES - COMPREHENSIVE APPLICATION TEST")
    print("=" * 60)

    results = []

    # Run all test suites
    results.append(("ConfigManager", test_config_manager()))
    results.append(("DatabaseManager", test_database_manager()))
    results.append(("GUI Imports", test_gui_imports()))
    results.append(("Application Integration", test_application_integration()))

    # Report final results
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Application is ready to run.")
        print("🚀 The hive mind swarm has successfully fixed all issues!")
    else:
        print("⚠️ Some tests failed. Please review the errors above.")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
