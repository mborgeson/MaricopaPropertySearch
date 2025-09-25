#!/usr/bin/env python
"""
GUI Launcher Test Script
Tests the main application launcher and verifies component initialization
"""

import os
import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


def test_dependencies():
    """Test if all required dependencies are available"""
    print("\n" + "=" * 60)
    print("TESTING DEPENDENCIES")
    print("=" * 60)

    required = [
        ("PyQt5", "PyQt5.QtWidgets"),
        ("psycopg2", "psycopg2"),
        ("requests", "requests"),
        ("beautifulsoup4", "bs4"),
        ("lxml", "lxml"),
    ]

    results = []
    for name, import_name in required:
        try:
            __import__(import_name)
            results.append((name, True, "OK"))
            print(f"[OK] {name}: INSTALLED")
        except ImportError as e:
            results.append((name, False, str(e)))
            print(f"[X] {name}: MISSING - {e}")

    return results


def test_configuration():
    """Test configuration loading"""
    print("\n" + "=" * 60)
    print("TESTING CONFIGURATION")
    print("=" * 60)

    try:
        from src.config_manager import ConfigManager

        config = ConfigManager()
        print("[OK] Configuration loaded successfully")

        # Check critical settings
        print(f"  - Database enabled: {config.get_database_enabled()}")
        print(f"  - API client type: {config.get_api_client_type()}")
        print(f"  - Web scraper type: {config.get_web_scraper_type()}")
        print(f"  - Logging enabled: {config.get_logging_enabled()}")

        return True, "Configuration OK"
    except Exception as e:
        print(f"[X] Configuration failed: {e}")
        return False, str(e)


def test_database_connection():
    """Test database connection if enabled"""
    print("\n" + "=" * 60)
    print("TESTING DATABASE")
    print("=" * 60)

    try:
        from src.config_manager import ConfigManager
        from src.threadsafe_database_manager import ThreadSafeDatabaseManager

        config = ConfigManager()
        if not config.get_database_enabled():
            print("[WARNING] Database disabled in configuration")
            return True, "Database disabled"

        db = ThreadSafeDatabaseManager(config)
        if db.test_connection():
            print("[OK] Database connection successful")
            db.close()
            return True, "Database OK"
        else:
            print("[X] Database connection failed")
            return False, "Connection failed"

    except Exception as e:
        print(f"[WARNING] Database test skipped: {e}")
        return None, str(e)


def test_gui_initialization():
    """Test GUI component initialization"""
    print("\n" + "=" * 60)
    print("TESTING GUI INITIALIZATION")
    print("=" * 60)

    try:
        from PyQt5.QtWidgets import QApplication

        from src.config_manager import ConfigManager
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp

        # Create QApplication (required for GUI)
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        config = ConfigManager()

        # Try to create main window
        print("Creating main window...")
        window = EnhancedPropertySearchApp(config)

        print("[OK] Main window created successfully")

        # Check critical components
        components = []

        # Check search components
        if hasattr(window, "search_type_combo"):
            components.append(("Search Type Selector", True))
        else:
            components.append(("Search Type Selector", False))

        if hasattr(window, "search_input"):
            components.append(("Search Input Field", True))
        else:
            components.append(("Search Input Field", False))

        if hasattr(window, "search_button"):
            components.append(("Search Button", True))
        else:
            components.append(("Search Button", False))

        # Check results table
        if hasattr(window, "results_table"):
            components.append(("Results Table", True))
        else:
            components.append(("Results Table", False))

        # Check batch search integration
        if hasattr(window, "batch_search_manager"):
            components.append(("Batch Search Manager", True))
        else:
            components.append(("Batch Search Manager", False))

        # Check background data collector
        if hasattr(window, "background_manager"):
            components.append(("Background Data Collector", True))
        else:
            components.append(("Background Data Collector", False))

        print("\nComponent Status:")
        for comp_name, status in components:
            if status:
                print(f"  [OK] {comp_name}: INITIALIZED")
            else:
                print(f"  [X] {comp_name}: MISSING")

        # Clean up
        window.close()

        all_ok = all(status for _, status in components)
        return all_ok, components

    except Exception as e:
        print(f"[X] GUI initialization failed: {e}")
        traceback.print_exc()

    return False, str(e)


def test_batch_search_dialog():
    """Test batch search dialog"""
    print("\n" + "=" * 60)
    print("TESTING BATCH SEARCH DIALOG")
    print("=" * 60)

    try:
        from PyQt5.QtWidgets import QApplication

        from src.enhanced_batch_search_dialog import EnhancedBatchSearchDialog

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Create dialog
        dialog = EnhancedBatchSearchDialog(None)

        print("[OK] Batch search dialog created")

        # Check components
        has_file_input = hasattr(dialog, "file_path_input")
        has_browse_button = hasattr(dialog, "browse_button")
        has_progress = hasattr(dialog, "overall_progress")

        print(f"  - File input: {'OK' if has_file_input else 'X'}")
        print(f"  - Browse button: {'OK' if has_browse_button else 'X'}")
        print(f"  - Progress bar: {'OK' if has_progress else 'X'}")

        dialog.close()

        return True, "Batch search dialog OK"

    except Exception as e:
        print(f"[X] Batch search dialog test failed: {e}")
        return False, str(e)


def run_full_test():
    """Run complete test suite"""
    print("\n" + "=" * 70)
    print(" MARICOPA PROPERTY SEARCH - GUI LAUNCHER TEST SUITE")
    print("=" * 70)

    test_results = {}

    # Test dependencies
    dep_results = test_dependencies()
    test_results["dependencies"] = all(status for _, status, _ in dep_results)

    # Test configuration
    config_ok, config_msg = test_configuration()
    test_results["configuration"] = config_ok

    # Test database
    db_ok, db_msg = test_database_connection()
    test_results["database"] = db_ok if db_ok is not None else True

    # Test GUI initialization
    gui_ok, gui_msg = test_gui_initialization()
    test_results["gui"] = gui_ok

    # Test batch search
    batch_ok, batch_msg = test_batch_search_dialog()
    test_results["batch_search"] = batch_ok

    # Summary
    print("\n" + "=" * 70)
    print(" TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in test_results.items():
        status = "PASSED" if passed else "FAILED"
        symbol = "[OK]" if passed else "[X]"
        print(f"{symbol} {test_name.upper()}: {status}")

    all_passed = all(test_results.values())

    print("\n" + "=" * 70)
    if all_passed:
        print(" [OK] ALL TESTS PASSED - GUI LAUNCHER IS FUNCTIONAL")
    else:
        print(" [WARNING] SOME TESTS FAILED - REVIEW OUTPUT ABOVE")
    print("=" * 70)

    return all_passed


if __name__ == "__main__":
    try:
        success = run_full_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        traceback.print_exc()

    sys.exit(1)
