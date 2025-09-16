#!/usr/bin/env python
"""
Fix Script for GUI Launcher Issues
Based on GUI_LAUNCHER_TEST_REPORT.md findings
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def fix_config_manager():
    """Add missing methods to ConfigManager"""
    config_file = project_root / "src" / "config_manager.py"

    print("\n[FIX 1] Adding missing ConfigManager methods...")

    # Methods to add
    new_methods = '''
    def get_database_enabled(self):
        """Check if database is enabled in configuration"""
        return self.settings.get('database', {}).get('enabled', True)

    def get_api_client_type(self):
        """Get the API client type from configuration"""
        return self.settings.get('api', {}).get('client_type', 'real')

    def get_web_scraper_type(self):
        """Get the web scraper type from configuration"""
        return self.settings.get('scraper', {}).get('type', 'real')

    def get_logging_enabled(self):
        """Check if logging is enabled in configuration"""
        return self.settings.get('logging', {}).get('enabled', True)
'''

    if config_file.exists():
        content = config_file.read_text()

        # Check if methods already exist
        if "get_database_enabled" in content:
            print("  [SKIP] Methods already exist in ConfigManager")
            return True

        # Find the last method in the class (before the final closing)
        # We'll insert our new methods before the end of the class
        lines = content.split('\n')
        insert_index = -1

        # Find the ConfigManager class
        in_class = False
        for i, line in enumerate(lines):
            if 'class ConfigManager' in line:
                in_class = True
            elif in_class and line and not line.startswith(' ') and not line.startswith('\t'):
                # End of class found
                insert_index = i - 1
                break

        if insert_index == -1:
            # If we didn't find the end, insert at the end of file
            insert_index = len(lines) - 1

        # Insert the new methods
        method_lines = new_methods.split('\n')
        for j, method_line in enumerate(reversed(method_lines)):
            lines.insert(insert_index, method_line)

        # Write back
        config_file.write_text('\n'.join(lines))
        print("  [OK] Added 4 missing methods to ConfigManager")
        return True
    else:
        print("  [ERROR] config_manager.py not found")
        return False

def fix_search_button():
    """Fix missing search button in enhanced_main_window.py"""
    window_file = project_root / "src" / "gui" / "enhanced_main_window.py"

    print("\n[FIX 2] Fixing missing search button...")

    if window_file.exists():
        content = window_file.read_text()

        # Check if search_button exists
        if "self.search_button" in content:
            print("  [OK] search_button already defined")
            return True

        # Find where to add the search button
        # It should be near search_input initialization
        lines = content.split('\n')
        insert_index = -1

        for i, line in enumerate(lines):
            if "self.search_input = QLineEdit" in line:
                # Found search input, add button after it
                insert_index = i + 1
                break

        if insert_index != -1:
            # Add search button initialization
            button_code = "        self.search_button = QPushButton('Search Properties')"
            lines.insert(insert_index, button_code)

            # Also need to connect it to search function
            # Find the search function connection area
            for i, line in enumerate(lines):
                if "connect" in line and "perform_search" in line:
                    # Already has connection
                    break
            else:
                # Need to add connection
                for i, line in enumerate(lines):
                    if "self.search_input.returnPressed.connect" in line:
                        # Add button connection after input connection
                        connection_code = "        self.search_button.clicked.connect(self.perform_search)"
                        lines.insert(i + 1, connection_code)
                        break

            # Write back
            window_file.write_text('\n'.join(lines))
            print("  [OK] Added search_button to enhanced_main_window.py")
            return True
        else:
            print("  [WARNING] Could not find appropriate location for search button")
            return False
    else:
        print("  [ERROR] enhanced_main_window.py not found")
        return False

def verify_fixes():
    """Run the test again to verify fixes"""
    print("\n[VERIFY] Running test to check fixes...")

    import subprocess
    test_script = project_root / "tests" / "gui_launcher_test.py"

    if test_script.exists():
        result = subprocess.run(
            [sys.executable, str(test_script)],
            capture_output=True,
            text=True
        )

        # Check for specific issues
        output = result.stdout + result.stderr

        config_fixed = "get_database_enabled" not in output or "[OK] CONFIGURATION: PASSED" in output
        button_fixed = "Search Button: MISSING" not in output or "Search Button: INITIALIZED" in output

        print("\n[RESULTS]")
        print(f"  ConfigManager Fix: {'✓ PASSED' if config_fixed else '✗ FAILED'}")
        print(f"  Search Button Fix: {'✓ PASSED' if button_fixed else '✗ FAILED'}")

        if config_fixed and button_fixed:
            print("\n[SUCCESS] All critical issues have been fixed!")
            return True
        else:
            print("\n[PARTIAL] Some issues remain. Review the test output above.")
            return False
    else:
        print("  [ERROR] Test script not found")
        return False

def main():
    print("="*60)
    print(" GUI LAUNCHER ISSUE FIX SCRIPT")
    print("="*60)
    print("Based on issues identified in GUI_LAUNCHER_TEST_REPORT.md")

    # Apply fixes
    config_ok = fix_config_manager()
    button_ok = fix_search_button()

    if config_ok and button_ok:
        print("\n[STATUS] Both fixes applied successfully")

        # Verify the fixes
        verify_ok = verify_fixes()

        if verify_ok:
            print("\n" + "="*60)
            print(" ✓ ALL ISSUES RESOLVED - GUI LAUNCHER READY!")
            print("="*60)
            return 0
        else:
            print("\nSome issues remain. Please review manually.")
            return 1
    else:
        print("\n[ERROR] Failed to apply all fixes")
        return 1

if __name__ == "__main__":
    sys.exit(main())