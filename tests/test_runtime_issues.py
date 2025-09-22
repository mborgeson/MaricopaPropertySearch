#!/usr/bin/env python
"""
Test script to identify runtime issues with RUN_APPLICATION.py
"""

import sys
import os
from pathlib import Path
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


def test_gui_startup():
    """Test if GUI can start without user interaction"""
    print("\n[TEST] GUI Startup Test")
    print("-" * 40)

    test_code = """
import sys
import os
from pathlib import Path

# Setup paths
project_root = Path(r'{root}')
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Set environment to suppress GUI
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

try:
    from PyQt5.QtWidgets import QApplication
    # MIGRATED: # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
    from src.gui.enhanced_main_window import EnhancedPropertySearchApp

    # Create app
    app = QApplication(sys.argv)

    # Load config
    config = EnhancedConfigManager()

    # Create main window
    window = EnhancedPropertySearchApp(config)

    # Check critical components
    issues = []

    if not hasattr(window, 'search_input'):
        issues.append("Missing: search_input")

    if not hasattr(window, 'results_table'):
        issues.append("Missing: results_table")

    if not hasattr(window, 'batch_search_manager'):
        issues.append("Missing: batch_search_manager")

    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  - {{issue}}")
    else:
        print("GUI initialized successfully")

    # Close immediately
    window.close()
    app.quit()

except Exception as e:
    print(f"ERROR: {{e}}")
    import traceback
    traceback.print_exc()
""".format(
        root=project_root
    )

    result = subprocess.run(
        [sys.executable, "-c", test_code], capture_output=True, text=True, timeout=10
    )

    print("Output:", result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)

    return result.returncode == 0


def test_search_functionality():
    """Test if search function works"""
    print("\n[TEST] Search Functionality")
    print("-" * 40)

    test_code = """
import sys
from pathlib import Path

project_root = Path(r'{root}')
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    # MIGRATED: from src.database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
    # MIGRATED: from src.api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
    # MIGRATED: # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.enhanced_config_manager import EnhancedConfigManager

    config = EnhancedConfigManager()

    # Test database
    db = ThreadSafeDatabaseManager(config)
    if db.test_connection():
        print("Database: OK")
    else:
        print("Database: Failed")

    # Test API client
    api = UnifiedMaricopaAPIClient(config)
    print("API Client: OK")

except Exception as e:
    print(f"ERROR: {{e}}")
""".format(
        root=project_root
    )

    result = subprocess.run(
        [sys.executable, "-c", test_code], capture_output=True, text=True, timeout=5
    )

    print("Output:", result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)

    return result.returncode == 0


def identify_specific_issues():
    """Identify specific runtime issues"""
    print("\n" + "=" * 60)
    print(" RUNTIME ISSUE IDENTIFICATION")
    print("=" * 60)

    issues_found = []

    # Test 1: GUI startup
    if not test_gui_startup():
        issues_found.append("GUI fails to initialize properly")

    # Test 2: Search functionality
    if not test_search_functionality():
        issues_found.append("Search components have issues")

    # Report
    print("\n" + "=" * 60)
    print(" SUMMARY")
    print("=" * 60)

    if issues_found:
        print("\n[ISSUES] Found problems:")
        for issue in issues_found:
            print(f"  - {issue}")

        print("\n[RECOMMENDATION] Use hive-mind wizard:")
        print("  npx claude-flow hive-mind wizard")
        print("\nWizard steps:")
        print("  1. Choose 'Debug and Fix Application Issues'")
        print("  2. Select 'Adaptive' queen for unknown issues")
        print("  3. Point to these specific problems")
    else:
        print("\n[OK] No runtime issues detected")
        print("\nTo run the application:")
        print("  python RUN_APPLICATION.py")


if __name__ == "__main__":
    identify_specific_issues()
