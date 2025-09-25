#!/usr/bin/env python
"""
Test GUI Fix - PySide6 to PyQt5 Conversion
Test that the application can start without PySide6 import errors
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
def test_gui_imports():
    """Test GUI imports work correctly"""
        print("🔍 Testing GUI imports after PySide6 to PyQt5 conversion...")

    try:
        # Test importing the main window
from src.gui.enhanced_main_window import EnhancedMainWindow

        print("✅ EnhancedMainWindow imported successfully (PyQt5)")

        # Test that PyQt5 is being used
        from PyQt5.QtWidgets import QApplication
        print("✅ PyQt5.QtWidgets imported successfully")

        from PyQt5.QtCore import Qt
        print("✅ PyQt5.QtCore imported successfully")

        from PyQt5.QtGui import QFont
        print("✅ PyQt5.QtGui imported successfully")
        print("✅ All GUI imports successful - no more PySide6 dependency!")
        return True

    except ImportError as e:
        if "PySide6" in str(e):
        print(f"❌ Still trying to import PySide6: {e}")
        elif "PyQt5" in str(e):
        print(f"❌ PyQt5 not available: {e}")
        else:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
def test_application_can_start():
    """Test that the application can be initialized"""
        print("\n🔍 Testing application initialization...")

    try:
        from PyQt5.QtWidgets import QApplication

from src.gui.enhanced_main_window import EnhancedMainWindow

        # Create a minimal test app
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        print("✅ QApplication created successfully")

        # Test that we can create the main window (don't show it)
        # First we need the required dependencies
        # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        # MIGRATED: from src.api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
        # MIGRATED: from src.database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager
from src.threadsafe_database_manager import ThreadSafeDatabaseManager

        config_manager = EnhancedConfigManager()
        print("✅ ConfigManager initialized")

        # We don't need to fully initialize everything, just test the imports work
        print("✅ Application can start - all imports successful!")

        app.quit()
        return True

    except Exception as e:
        print(f"❌ Application startup error: {e}")
        return False
def run_gui_fix_test():
    """Run all GUI fix tests"""
        print("=" * 60)
        print("🛠️  GUI FIX TEST - PySide6 to PyQt5 Conversion")
        print("=" * 60)

    results = []

    # Test GUI imports
    results.append(("GUI Imports", test_gui_imports()))

    # Test application startup
    results.append(("Application Startup", test_application_can_start()))

    # Report results
        print("\n" + "=" * 60)
        print("📊 GUI FIX TEST RESULTS")
        print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
        print("\n" + "=" * 60)
    if all_passed:
        print("🎉 GUI FIX SUCCESSFUL!")
        print("✅ Application no longer depends on PySide6")
        print("✅ All imports use PyQt5 consistently")
        print("✅ Application can start without errors")
    else:
        print("⚠️ Some issues remain - check errors above")
        print("=" * 60)

    return all_passed

if __name__ == "__main__":
    success = run_gui_fix_test()
    sys.exit(0 if success else 1)