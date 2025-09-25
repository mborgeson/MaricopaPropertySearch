#!/usr/bin/env python
"""
Systematic Application Testing Script
Tests each component of RUN_APPLICATION.py to identify specific issues
"""
import os
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


class SystematicTester:
    def __init__(self):
        self.results = {}
        self.issues = []
        self.fixes = []
    def test_startup_sequence(self):
        """Test the startup sequence step by step"""
        print("\n[TEST 1] Startup Sequence")
        print("=" * 50)

        steps = []

        # Step 1: Dependencies
    try:
import bs4
import lxml
import psycopg2
import PyQt5
import requests

            steps.append(("Dependencies", True, None))
        print("[OK] Dependencies loaded")
    except ImportError as e:
            steps.append(("Dependencies", False, str(e)))
        print(f"[FAIL] Dependencies: {e}")

        # Step 2: Configuration
    try:
            # MIGRATED: # MIGRATED: # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
            config = EnhancedConfigManager()
            steps.append(("ConfigManager", True, None))
        print("[OK] ConfigManager loaded")

            # Test new methods
    try:
                config.get_database_enabled()
                config.get_api_client_type()
                config.get_web_scraper_type()
                config.get_logging_enabled()
                steps.append(("Config Methods", True, None))
        print("[OK] Config methods work")
    except Exception as e:
                steps.append(("Config Methods", False, str(e)))
        print(f"[FAIL] Config methods: {e}")

    except Exception as e:
            steps.append(("ConfigManager", False, str(e)))
        print(f"[FAIL] ConfigManager: {e}")

        # Step 3: Database
    try:
from src.threadsafe_database_manager import ThreadSafeDatabaseManager

            db = ThreadSafeDatabaseManager(config)
            if db.test_connection():
                steps.append(("Database", True, None))
        print("[OK] Database connection")
                db.close()
            else:
                steps.append(("Database", False, "Connection failed"))
        print("[FAIL] Database connection failed")
    except Exception as e:
            steps.append(("Database", False, str(e)))
        print(f"[WARNING] Database: {e}")

        # Step 4: Logging
    try:
from src.logging_config import setup_logging

            setup_logging()
            steps.append(("Logging", True, None))
        print("[OK] Logging initialized")
    except Exception as e:
            steps.append(("Logging", False, str(e)))
        print(f"[FAIL] Logging: {e}")

        self.results["startup"] = steps
        return all(success for _, success, _ in steps)
    def test_gui_components(self):
        """Test GUI components initialization"""
        print("\n[TEST 2] GUI Components")
        print("=" * 50)

        components = []

    try:
            os.environ["QT_QPA_PLATFORM"] = "offscreen"
            from PyQt5.QtWidgets import QApplication

            # MIGRATED: # MIGRATED: # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
from src.gui.enhanced_main_window import EnhancedPropertySearchApp

            app = QApplication(sys.argv)
            config = EnhancedConfigManager()
            window = EnhancedPropertySearchApp(config)

            # Check components
            checks = [
                ("search_input", "Search input field"),
                ("search_button", "Search button"),
                ("search_btn", "Search button (alt)"),
                ("results_table", "Results table"),
                ("progress_bar", "Progress bar"),
                ("batch_search_manager", "Batch search"),
                ("background_manager", "Background collector"),
                ("search_type_combo", "Search type selector"),
                ("export_btn", "Export button"),
                ("view_details_btn", "View details button"),
            ]

            for attr, desc in checks:
                if hasattr(window, attr):
                    components.append((desc, True, None))
        print(f"[OK] {desc}")
                else:
                    components.append((desc, False, f"Missing: {attr}"))
        print(f"[FAIL] {desc} - Missing: {attr}")

            window.close()
            app.quit()

    except Exception as e:
            components.append(("GUI Init", False, str(e)))
        print(f"[FAIL] GUI initialization: {e}")

        self.results["gui"] = components
        return all(success for _, success, _ in components)
    def test_functionality(self):
        """Test core functionality"""
        print("\n[TEST 3] Core Functionality")
        print("=" * 50)

        functions = []

    try:
            # MIGRATED: from src.api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
from src.background_data_collector import BackgroundDataCollectionManager
from src.web_scraper import WebScraperManager

            # MIGRATED: # MIGRATED: # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager

            config = EnhancedConfigManager()

            # Test API Client
    try:
                api = UnifiedMaricopaAPIClient(config)
                functions.append(("API Client", True, None))
        print("[OK] API Client initialized")
    except Exception as e:
                functions.append(("API Client", False, str(e)))
        print(f"[FAIL] API Client: {e}")

            # Test Web Scraper
    try:
                scraper = WebScraperManager()
                functions.append(("Web Scraper", True, None))
        print("[OK] Web Scraper initialized")
    except Exception as e:
                functions.append(("Web Scraper", False, str(e)))
        print(f"[WARNING] Web Scraper: {e}")

            # Test Background Collector
    try:
                bg = BackgroundDataCollectionManager(None, None, None)
                functions.append(("Background Collector", True, None))
        print("[OK] Background Collector initialized")
    except Exception as e:
                functions.append(("Background Collector", False, str(e)))
        print(f"[FAIL] Background Collector: {e}")

    except Exception as e:
            functions.append(("Functionality", False, str(e)))
        print(f"[FAIL] Functionality test: {e}")

        self.results["functionality"] = functions
        return all(
            success for name, success, _ in functions if "Web Scraper" not in name
        )
    def test_run_application(self):
        """Test actual RUN_APPLICATION.py execution"""
        print("\n[TEST 4] RUN_APPLICATION.py Execution")
        print("=" * 50)

        test_script = """
import sys
import os
import time
from pathlib import Path

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['TESTING'] = '1'

# Run the application briefly
import subprocess
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager

result = subprocess.run(
    [sys.executable, "RUN_APPLICATION.py"],
    capture_output=True,
    text=True,
    timeout=3,
    cwd=r"{root}"
)

if "[START] Starting application..." in result.stdout:
        print("Application starts successfully")
else:
        print("Application failed to start properly")
        print("STDOUT:", result.stdout[:500])
""".format(
            root=project_root
        )

    try:
            result = subprocess.run(
                [sys.executable, "-c", test_script],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if "starts successfully" in result.stdout:
        print("[OK] Application starts")
                self.results["execution"] = [("Execution", True, None)]
                return True
            else:
        print("[FAIL] Application execution issues")
        print("Output:", result.stdout[:500])
                self.results["execution"] = [("Execution", False, result.stdout)]
                return False

    except Exception as e:
        print(f"[FAIL] Execution test: {e}")
            self.results["execution"] = [("Execution", False, str(e))]
            return False
    def generate_report(self):
        """Generate comprehensive report"""
        print("\n" + "=" * 70)
        print(" SYSTEMATIC TEST REPORT")
        print("=" * 70)

        # Count issues
        total_tests = 0
        failed_tests = 0

        for category, tests in self.results.items():
            for name, success, error in tests:
                total_tests += 1
                if not success:
                    failed_tests += 1
                    self.issues.append((category, name, error))

        # Summary
        print(f"\nTests Run: {total_tests}")
        print(f"Passed: {total_tests - failed_tests}")
        print(f"Failed: {failed_tests}")

        if self.issues:
        print("\n[ISSUES FOUND]")
            for cat, name, error in self.issues:
        print(f"\n  Category: {cat}")
        print(f"  Component: {name}")
        print(f"  Error: {error[:100] if error else 'Unknown'}")

                # Suggest fix
                if "ConfigManager" in name:
                    self.fixes.append("Check config_manager.py methods")
                elif "search_button" in name or "Missing: search_button" in error:
                    self.fixes.append(
                        "Add search_button alias in enhanced_main_window.py"
                    )
                elif "Database" in name:
                    self.fixes.append("Verify database configuration in .env")
                elif "Chrome" in str(error):
                    self.fixes.append("Install ChromeDriver or use Playwright")

        if self.fixes:
        print("\n[RECOMMENDED FIXES]")
            for i, fix in enumerate(set(self.fixes), 1):
        print(f"  {i}. {fix}")
        print("\n" + "=" * 70)
        if failed_tests == 0:
        print(" [OK] ALL TESTS PASSED - APPLICATION READY")
        else:
        print(f" [ACTION] {failed_tests} ISSUES NEED ATTENTION")
        print("=" * 70)
    def run_all_tests(self):
        """Run all systematic tests"""
        print("SYSTEMATIC APPLICATION TESTING")
        print("=" * 70)

        # Run tests
        self.test_startup_sequence()
        self.test_gui_components()
        self.test_functionality()
        self.test_run_application()

        # Generate report
        self.generate_report()

        return len(self.issues) == 0
    def main():
    tester = SystematicTester()
    success = tester.run_all_tests()

    if not success:
        print("\n[NEXT STEPS]")
        print("1. Review the issues above")
        print("2. Apply recommended fixes")
        print("3. Run this test again to verify")
        print("\nOr use hive-mind for automated fixing:")
        print('  npx claude-flow hive-mind spawn "Fix issues: [paste issues]" --claude')

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
