#!/usr/bin/env python
"""
Fix Data Collection Issues
Specifically addresses tax and sales data collection problems
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def add_enhanced_collection_methods():
    """Add enhanced data collection methods to the main window"""
    print("\n[DATA FIX] Adding enhanced collection methods")
    print("-" * 50)

    window_file = project_root / "src" / "gui" / "enhanced_main_window.py"

    if window_file.exists():
        with open(window_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Check if enhanced collection method exists
        if "def enhanced_collect_property_data" not in content:
            # Add the method before the last closing brace
            enhanced_method = '''
    def enhanced_collect_property_data(self, apn):
        """Enhanced property data collection with better error handling"""
        if not apn:
            QMessageBox.warning(self, "Warning", "No APN provided for data collection")
            return False

        logger.info(f"Starting enhanced data collection for APN: {apn}")

        try:
            # Initialize collection results
            results = {
                'property': None,
                'tax': None,
                'sales': None,
                'success': False,
                'errors': []
            }

            # Progress dialog
            from PyQt5.QtWidgets import QProgressDialog
            from PyQt5.QtCore import Qt

            progress = QProgressDialog("Collecting property data...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setAutoClose(True)
            progress.setAutoReset(True)
            progress.show()

            # Step 1: Basic property data
            progress.setValue(10)
            progress.setLabelText(f"Collecting basic property data for {apn}...")
            QApplication.processEvents()

            try:
                if hasattr(self, 'api_client') and self.api_client:
                    property_data = self.api_client.get_property_details(apn)
                    if property_data:
                        results['property'] = property_data
                        logger.info(f"Property data collected for {apn}")
                    else:
                        results['errors'].append("No property data found")
                        logger.warning(f"No property data found for {apn}")
                else:
                    results['errors'].append("API client not available")
            except Exception as e:
                error_msg = f"Property data error: {e}"
                results['errors'].append(error_msg)
                logger.error(error_msg)

            if progress.wasCanceled():
                return False

            # Step 2: Tax information
            progress.setValue(40)
            progress.setLabelText(f"Collecting tax information for {apn}...")
            QApplication.processEvents()

            try:
                if hasattr(self, 'api_client') and self.api_client:
                    # Try tax history first
                    tax_data = self.api_client.get_tax_history(apn)
                    if not tax_data:
                        # Try comprehensive tax information
                        tax_data = self.api_client.get_tax_information(apn)

                    if tax_data:
                        results['tax'] = tax_data
                        logger.info(f"Tax data collected for {apn}")
                    else:
                        results['errors'].append("No tax data available")
                        logger.warning(f"No tax data found for {apn}")
                else:
                    results['errors'].append("Cannot get tax data - API not available")
            except Exception as e:
                error_msg = f"Tax data error: {e}"
                results['errors'].append(error_msg)
                logger.error(error_msg)

            if progress.wasCanceled():
                return False

            # Step 3: Sales history
            progress.setValue(70)
            progress.setLabelText(f"Collecting sales history for {apn}...")
            QApplication.processEvents()

            try:
                if hasattr(self, 'api_client') and self.api_client:
                    sales_data = self.api_client.get_sales_history(apn)
                    if sales_data:
                        results['sales'] = sales_data
                        logger.info(f"Sales data collected for {apn}")
                    else:
                        results['errors'].append("No sales history available")
                        logger.warning(f"No sales data found for {apn}")
                else:
                    results['errors'].append("Cannot get sales data - API not available")
            except Exception as e:
                error_msg = f"Sales data error: {e}"
                results['errors'].append(error_msg)
                logger.error(error_msg)

            progress.setValue(90)
            progress.setLabelText("Saving collected data...")
            QApplication.processEvents()

            # Step 4: Store in database if available
            try:
                if hasattr(self, 'db_manager') and self.db_manager:
                    if results['property']:
                        self.db_manager.store_property_data(apn, results['property'])
                    if results['tax']:
                        self.db_manager.store_tax_data(apn, results['tax'])
                    if results['sales']:
                        self.db_manager.store_sales_data(apn, results['sales'])
                    logger.info(f"Data stored in database for {apn}")
            except Exception as e:
                logger.warning(f"Database storage failed: {e}")
                results['errors'].append(f"Database storage failed: {e}")

            progress.setValue(100)

            # Determine success
            results['success'] = bool(results['property'] or results['tax'] or results['sales'])

            # Show results
            if results['success']:
                collected = []
                if results['property']: collected.append("Property")
                if results['tax']: collected.append("Tax")
                if results['sales']: collected.append("Sales")

                message = f"Successfully collected {', '.join(collected)} data for APN {apn}"
                if results['errors']:
                    message += f"\\n\\nWarnings: {'; '.join(results['errors'][:3])}"

                QMessageBox.information(self, "Collection Complete", message)
                logger.info(f"Data collection completed for {apn}: {collected}")
            else:
                error_summary = '; '.join(results['errors'][:3])
                QMessageBox.critical(self, "Collection Failed",
                                   f"Could not collect complete data for APN {apn}\\n\\nErrors: {error_summary}")
                logger.error(f"Data collection failed for {apn}: {error_summary}")

            return results['success']

        except Exception as e:
            logger.error(f"Enhanced collection failed: {e}")
            QMessageBox.critical(self, "Collection Error", f"Data collection failed: {e}")
            return False
'''

            # Find where to insert (before the last class closing)
            lines = content.split('\n')
            insert_index = len(lines) - 5  # Insert near the end

            lines.insert(insert_index, enhanced_method)

            with open(window_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            print("[OK] Added enhanced_collect_property_data method")
            return True

        else:
            print("[INFO] Enhanced collection method already exists")
            return True

    return False

def update_manual_collect_button():
    """Update the manual collect button to use enhanced method"""
    print("\n[DATA FIX] Updating manual collect button")
    print("-" * 50)

    window_file = project_root / "src" / "gui" / "enhanced_main_window.py"

    if window_file.exists():
        with open(window_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Find manual collect method and update it
        if "def manual_collect_data" in content:
            # Replace the method implementation
            original = content

            # Look for the method and replace its content
            lines = content.split('\n')
            method_start = -1
            method_end = -1

            for i, line in enumerate(lines):
                if "def manual_collect_data" in line:
                    method_start = i
                    indent = len(line) - len(line.lstrip())
                    # Find end of method
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip() and not lines[j].startswith(' ' * (indent + 1)):
                            method_end = j
                            break
                    break

            if method_start >= 0:
                new_method = '''    def manual_collect_data(self):
        """Manual data collection with enhanced error handling"""
        selected_items = self.results_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a property from the results table")
            return

        # Get APN from selected row
        row = selected_items[0].row()
        apn_item = self.results_table.item(row, 0)  # APN should be in first column
        if not apn_item:
            QMessageBox.warning(self, "Warning", "No APN found for selected property")
            return

        apn = apn_item.text().strip()
        if not apn:
            QMessageBox.warning(self, "Warning", "Invalid APN selected")
            return

        # Use enhanced collection method
        self.enhanced_collect_property_data(apn)

        # Refresh the results table to show updated data
        self.refresh_results_display()
'''

                if method_end > method_start:
                    lines[method_start:method_end] = new_method.split('\n')
                else:
                    lines[method_start:method_start+10] = new_method.split('\n')

                with open(window_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))

                print("[OK] Updated manual_collect_data method")
                return True

        print("[WARNING] manual_collect_data method not found")
        return False

    return False

def improve_error_handling():
    """Improve error handling in data collection"""
    print("\n[DATA FIX] Improving error handling")
    print("-" * 50)

    # Add better error handling to API client
    api_file = project_root / "src" / "api_client.py"

    if api_file.exists():
        with open(api_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Check if we need to add test_connection method
        if "def test_connection" not in content:
            method = '''
    def test_connection(self):
        """Test if API connection is working"""
        try:
            # Simple test request
            response = self._make_request('/health', timeout=5)
            return response is not None
        except:
            try:
                # Alternative test - just check if we can reach the base URL
                response = self.session.get(self.base_url, timeout=5)
                return response.status_code == 200
            except:
                return False
'''

            # Add the method
            lines = content.split('\n')
            # Find a good place to insert (after __init__)
            for i, line in enumerate(lines):
                if "def __init__" in line and "MaricopaAPIClient" in lines[i-2:i+2]:
                    # Find end of __init__
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip() and not lines[j].startswith(' '):
                            lines.insert(j, method)
                            break
                    break

            with open(api_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            print("[OK] Added test_connection method to API client")

        print("[INFO] API client error handling checked")
        return True

    return False

def main():
    print("=" * 60)
    print(" FIXING DATA COLLECTION ISSUES")
    print("=" * 60)

    fixes_applied = []

    # Apply data collection fixes
    if add_enhanced_collection_methods():
        fixes_applied.append("Enhanced collection methods")

    if update_manual_collect_button():
        fixes_applied.append("Manual collect button")

    if improve_error_handling():
        fixes_applied.append("Error handling improvements")

    # Summary
    print("\n" + "=" * 60)
    print(" DATA COLLECTION FIX SUMMARY")
    print("=" * 60)

    if fixes_applied:
        print(f"\n[OK] Successfully applied {len(fixes_applied)} fixes:")
        for fix in fixes_applied:
            print(f"  - {fix}")
    else:
        print("\n[WARNING] No fixes were applied")

    print("\n[EXPECTED IMPROVEMENTS]")
    print("- Manual Collect should now provide detailed feedback")
    print("- Tax and sales data collection will show progress")
    print("- Better error messages when data isn't available")
    print("- Enhanced data collection with fallback options")

    print("\n[TEST STEPS]")
    print("1. Restart application: python RUN_APPLICATION.py")
    print("2. Search for a property")
    print("3. Select a row and click 'Manual Collect (Immediate)'")
    print("4. Should see progress dialog and detailed results")

    return 0

if __name__ == "__main__":
    sys.exit(main())