#!/usr/bin/env python
"""
Comprehensive Diagnostic for RUN_APPLICATION.py
Identifies all issues preventing proper execution
"""

import sys
import os
import subprocess
from pathlib import Path
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class ApplicationDiagnostic:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.successes = []

    def check_imports(self):
        """Check if all imports in RUN_APPLICATION.py work"""
        print("\n[1] Checking Imports...")

        try:
            # Try importing main components
            from src.config_manager import ConfigManager
            self.successes.append("ConfigManager imports successfully")

            from src.threadsafe_database_manager import ThreadSafeDatabaseManager
            self.successes.append("ThreadSafeDatabaseManager imports successfully")

            from src.gui.enhanced_main_window import EnhancedPropertySearchApp
            self.successes.append("EnhancedPropertySearchApp imports successfully")

            from src.logging_config import setup_logging
            self.successes.append("Logging setup imports successfully")

        except ImportError as e:
            self.issues.append(f"Import Error: {e}")
            return False
        except Exception as e:
            self.issues.append(f"Unexpected import error: {e}")
            return False

        return True

    def check_config_files(self):
        """Check if configuration files exist"""
        print("\n[2] Checking Configuration Files...")

        config_files = [
            (".env", "Environment configuration"),
            ("config/config.ini", "Main configuration"),
        ]

        for file_path, description in config_files:
            full_path = project_root / file_path
            if full_path.exists():
                self.successes.append(f"{description} found: {file_path}")
            else:
                self.warnings.append(f"{description} missing: {file_path}")

                # Check for example file
                example_path = project_root / f"{file_path}.example"
                if example_path.exists():
                    self.warnings.append(f"  -> Example found: {file_path}.example (copy this to {file_path})")

    def check_directories(self):
        """Check if required directories exist"""
        print("\n[3] Checking Directory Structure...")

        required_dirs = [
            "src",
            "src/gui",
            "config",
            "logs",
            "cache",
            "exports",
        ]

        for dir_path in required_dirs:
            full_path = project_root / dir_path
            if full_path.exists():
                self.successes.append(f"Directory exists: {dir_path}")
            else:
                self.issues.append(f"Directory missing: {dir_path}")
                # Try to create it
                try:
                    full_path.mkdir(parents=True, exist_ok=True)
                    self.warnings.append(f"  -> Created missing directory: {dir_path}")
                except:
                    self.issues.append(f"  -> Failed to create directory: {dir_path}")

    def check_database_config(self):
        """Check database configuration"""
        print("\n[4] Checking Database Configuration...")

        try:
            from src.config_manager import ConfigManager
            config = ConfigManager()

            # Check database settings
            if hasattr(config, 'get_database_enabled'):
                db_enabled = config.get_database_enabled()
                self.successes.append(f"Database enabled: {db_enabled}")

                if db_enabled:
                    # Try to get database config
                    try:
                        db_config = config.get_database_config()
                        if db_config:
                            self.successes.append("Database configuration loaded")
                    except Exception as e:
                        self.warnings.append(f"Database config error: {e}")
            else:
                self.issues.append("ConfigManager missing get_database_enabled method")

        except Exception as e:
            self.issues.append(f"Cannot check database config: {e}")

    def check_gui_dependencies(self):
        """Check PyQt5 and GUI dependencies"""
        print("\n[5] Checking GUI Dependencies...")

        try:
            from PyQt5.QtWidgets import QApplication
            self.successes.append("PyQt5 available")

            # Check if we can create QApplication
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            self.successes.append("QApplication can be created")

        except ImportError:
            self.issues.append("PyQt5 not installed or not working")
        except Exception as e:
            self.issues.append(f"GUI dependency error: {e}")

    def test_application_launch(self):
        """Try to actually run the application in test mode"""
        print("\n[6] Testing Application Launch...")

        run_app_path = project_root / "RUN_APPLICATION.py"

        if not run_app_path.exists():
            self.issues.append("RUN_APPLICATION.py not found!")
            return

        # Try a dry run (just imports and checks, no GUI)
        try:
            # Create a test script that imports and checks
            test_code = '''
import sys
sys.path.insert(0, r"{root}")
sys.path.insert(0, r"{src}")

# Try the critical imports from RUN_APPLICATION.py
from src.config_manager import ConfigManager
from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.logging_config import setup_logging

# Check functions
config = ConfigManager()
print("Config loaded")

# Don't actually create GUI or database
print("Import test successful")
'''.format(root=project_root, src=project_root / "src")

            result = subprocess.run(
                [sys.executable, "-c", test_code],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                self.successes.append("Application imports work correctly")
            else:
                self.issues.append(f"Application import test failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.warnings.append("Application test timed out")
        except Exception as e:
            self.issues.append(f"Application launch test error: {e}")

    def generate_report(self):
        """Generate diagnostic report"""
        print("\n" + "="*70)
        print(" DIAGNOSTIC REPORT FOR RUN_APPLICATION.py")
        print("="*70)

        if self.issues:
            print(f"\n[CRITICAL] ISSUES ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")

        if self.warnings:
            print(f"\n[WARNING] WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        if self.successes:
            print(f"\n[OK] WORKING COMPONENTS ({len(self.successes)}):")
            for success in self.successes[:5]:  # Show first 5
                print(f"  [OK] {success}")
            if len(self.successes) > 5:
                print(f"  ... and {len(self.successes)-5} more")

        print("\n" + "="*70)

        if not self.issues:
            print(" [OK] NO CRITICAL ISSUES FOUND")
        else:
            print(f" [WARNING] {len(self.issues)} CRITICAL ISSUES NEED ATTENTION")

        print("="*70)

        # Generate fix suggestions
        if self.issues:
            print("\n[FIXES] SUGGESTED FIXES:")
            for i, issue in enumerate(self.issues, 1):
                print(f"\n{i}. Issue: {issue}")

                # Suggest fixes based on issue type
                if "Import Error" in issue:
                    print("   Fix: Check if module exists and is in correct location")
                elif "Directory missing" in issue:
                    print("   Fix: Create the missing directory or check path")
                elif "ConfigManager" in issue:
                    print("   Fix: Verify config_manager.py has all required methods")
                elif "PyQt5" in issue:
                    print("   Fix: Install PyQt5: pip install PyQt5")
                elif "configuration missing" in issue:
                    print("   Fix: Copy .env.example to .env and configure")

    def run_diagnostic(self):
        """Run all diagnostic checks"""
        print("Starting Application Diagnostic...")
        print("-" * 50)

        self.check_imports()
        self.check_config_files()
        self.check_directories()
        self.check_database_config()
        self.check_gui_dependencies()
        self.test_application_launch()

        self.generate_report()

        return len(self.issues) == 0

def main():
    diagnostic = ApplicationDiagnostic()
    success = diagnostic.run_diagnostic()

    print("\n" + "="*70)
    print(" NEXT STEPS:")
    print("="*70)

    if success:
        print("\n1. Run the application:")
        print("   python RUN_APPLICATION.py")
    else:
        print("\n1. Fix the critical issues listed above")
        print("2. Run this diagnostic again to verify")
        print("3. Use hive-mind wizard for systematic fixes:")
        print("   npx claude-flow hive-mind wizard")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())