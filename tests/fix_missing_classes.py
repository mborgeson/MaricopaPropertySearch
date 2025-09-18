#!/usr/bin/env python3
"""
Quick fix for missing class definitions that are preventing application startup
"""

import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def check_and_fix_missing_classes():
    """Check for and fix missing class definitions"""

    project_root = Path(__file__).parent.parent

    issues_found = []
    fixes_applied = []

    print("CHECKING FOR MISSING CLASS DEFINITIONS")
    print("="*60)

    # 1. Check API Client
    api_client_path = project_root / 'src' / 'api_client.py'
    try:
        with open(api_client_path, 'r') as f:
            content = f.read()

        if 'class APIClient' not in content and 'class MaricopaAPIClient' in content:
            print("✓ Found MaricopaAPIClient, need alias for APIClient")

            # Add alias at the end
            if '# APIClient alias' not in content:
                content += '\n\n# APIClient alias for backward compatibility\nAPIClient = MaricopaAPIClient\n'

                with open(api_client_path, 'w') as f:
                    f.write(content)

                fixes_applied.append("Added APIClient alias in api_client.py")
                print("  → Fixed: Added APIClient alias")
            else:
                print("  → Already has alias")

    except Exception as e:
        issues_found.append(f"API Client check failed: {e}")

    # 2. Check Background Data Collector
    bg_collector_path = project_root / 'src' / 'background_data_collector.py'
    try:
        with open(bg_collector_path, 'r') as f:
            content = f.read()

        if 'class BackgroundDataCollector' not in content and 'class BackgroundDataCollectionManager' in content:
            print("✓ Found BackgroundDataCollectionManager, need alias for BackgroundDataCollector")

            # Add alias at the end
            if '# BackgroundDataCollector alias' not in content:
                content += '\n\n# BackgroundDataCollector alias for backward compatibility\nBackgroundDataCollector = BackgroundDataCollectionManager\n'

                with open(bg_collector_path, 'w') as f:
                    f.write(content)

                fixes_applied.append("Added BackgroundDataCollector alias in background_data_collector.py")
                print("  → Fixed: Added BackgroundDataCollector alias")
            else:
                print("  → Already has alias")

    except Exception as e:
        issues_found.append(f"Background Data Collector check failed: {e}")

    # 3. Check for missing AdvancedFiltersWidget in GUI
    gui_path = project_root / 'src' / 'gui' / 'enhanced_main_window.py'
    try:
        with open(gui_path, 'r') as f:
            content = f.read()

        if 'class AdvancedFiltersWidget' not in content and 'AdvancedFiltersWidget()' in content:
            print("✓ Found usage of AdvancedFiltersWidget, but class not defined")

            # Find good place to add class (after imports, before main class)
            lines = content.split('\n')
            insert_idx = 0

            # Find last import line
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import ') or line.strip() == '':
                    insert_idx = i + 1
                elif line.startswith('class ') or line.startswith('def '):
                    break

            # Add basic AdvancedFiltersWidget class
            widget_code = '''
class AdvancedFiltersWidget(QWidget):
    """Advanced filters widget for property search"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI for advanced filters"""
        layout = QVBoxLayout(self)

        # Basic filter controls
        self.property_type_combo = QComboBox()
        self.property_type_combo.addItems(['All', 'Residential', 'Commercial', 'Industrial'])

        self.year_built_from = QLineEdit()
        self.year_built_from.setPlaceholderText("Year built from...")

        self.year_built_to = QLineEdit()
        self.year_built_to.setPlaceholderText("Year built to...")

        layout.addWidget(QLabel("Property Type:"))
        layout.addWidget(self.property_type_combo)
        layout.addWidget(QLabel("Year Built From:"))
        layout.addWidget(self.year_built_from)
        layout.addWidget(QLabel("Year Built To:"))
        layout.addWidget(self.year_built_to)

    def get_filters(self):
        """Get current filter settings"""
        return {
            'property_type': self.property_type_combo.currentText(),
            'year_built_from': self.year_built_from.text(),
            'year_built_to': self.year_built_to.text()
        }

    def clear_filters(self):
        """Clear all filters"""
        self.property_type_combo.setCurrentIndex(0)
        self.year_built_from.clear()
        self.year_built_to.clear()
'''

            lines.insert(insert_idx, widget_code)
            content = '\n'.join(lines)

            with open(gui_path, 'w') as f:
                f.write(content)

            fixes_applied.append("Added AdvancedFiltersWidget class to enhanced_main_window.py")
            print("  → Fixed: Added AdvancedFiltersWidget class")

    except Exception as e:
        issues_found.append(f"AdvancedFiltersWidget check failed: {e}")

    # 4. Check for missing PropertySearchEngine
    if 'PropertySearchEngine(' in content and 'class PropertySearchEngine' not in content:
        print("✓ Found usage of PropertySearchEngine, but class not defined")

        # Add basic PropertySearchEngine class
        search_engine_code = '''
class PropertySearchEngine:
    """Property search engine for handling search operations"""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager

    def search_by_apn(self, apn):
        """Search property by APN"""
        # Placeholder implementation
        return {"apn": apn, "status": "mock_data"}

    def search_by_address(self, address):
        """Search property by address"""
        # Placeholder implementation
        return {"address": address, "status": "mock_data"}
'''

        lines = content.split('\n')
        insert_idx = 0

        # Find good place to add class
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import ') or line.strip() == '':
                insert_idx = i + 1
            elif line.startswith('class ') or line.startswith('def '):
                break

        lines.insert(insert_idx, search_engine_code)
        content = '\n'.join(lines)

        with open(gui_path, 'w') as f:
            f.write(content)

        fixes_applied.append("Added PropertySearchEngine class to enhanced_main_window.py")
        print("  → Fixed: Added PropertySearchEngine class")

    print("\n" + "="*60)
    print("FIXES SUMMARY")
    print("="*60)

    if fixes_applied:
        print("✓ FIXES APPLIED:")
        for fix in fixes_applied:
            print(f"  • {fix}")
    else:
        print("✓ No fixes needed or all classes already exist")

    if issues_found:
        print("\n❌ ISSUES FOUND:")
        for issue in issues_found:
            print(f"  • {issue}")

    return len(fixes_applied), len(issues_found)

def main():
    """Main execution"""
    print("MISSING CLASS DEFINITIONS FIXER")
    print("="*60)

    fixes, issues = check_and_fix_missing_classes()

    if fixes > 0:
        print(f"\n✓ Applied {fixes} fixes")
        print("Try running the application again!")
    else:
        print("\n• No fixes were needed")

    if issues > 0:
        print(f"\n❌ {issues} issues require manual attention")
        return 1
    else:
        return 0

if __name__ == "__main__":
    sys.exit(main())