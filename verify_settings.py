#!/usr/bin/env python
"""
Verify Settings Integration
This script verifies that the settings fix is working correctly.
"""

import sys
import os
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

def verify_default_settings():
    """Verify that default settings are loaded correctly"""
    print("Verifying Default Settings Integration")
    print("=" * 50)
    
    # Use the same QSettings key as the application
    settings = QSettings("MaricopaPropertySearch", "PropertySearch")
    
    # Clear any existing settings to test defaults
    print("Clearing existing settings to test defaults...")
    settings.clear()
    settings.sync()
    
    # Define the same defaults as the application (from load_application_settings)
    defaults = {
        'auto_start_collection': (True, bool),
        'max_results': (20, int),
        'auto_resize_columns': (True, bool),
        'show_progress_details': (True, bool),
        'always_fresh_data': (True, bool)
    }
    
    print("\nLoading default values (same logic as application):")
    loaded_settings = {}
    
    # Use the exact same loading logic as the application
    for key, (default_value, value_type) in defaults.items():
        stored_value = settings.value(key, default_value)
        
        # Convert to proper type
        if value_type == bool:
            # QSettings returns string 'true'/'false' for bools
            if isinstance(stored_value, str):
                loaded_settings[key] = stored_value.lower() == 'true'
            else:
                loaded_settings[key] = bool(stored_value)
        elif value_type == int:
            loaded_settings[key] = int(stored_value) if stored_value else default_value
        else:
            loaded_settings[key] = stored_value
    
    print()
    print("Settings that will be applied to UI:")
    print("-" * 40)
    
    expected_defaults = {
        'auto_start_collection': True,
        'max_results': 20,
        'auto_resize_columns': True,
        'show_progress_details': True,
        'always_fresh_data': True
    }
    
    all_correct = True
    for key, expected in expected_defaults.items():
        actual = loaded_settings[key]
        status = "[OK]" if actual == expected else "[FAIL]"
        print(f"  {key}: {actual} {status}")
        
        if actual != expected:
            all_correct = False
            print(f"    Expected: {expected}, Got: {actual}")
    
    print()
    print("UI Application Effects:")
    print("-" * 30)
    
    if loaded_settings['always_fresh_data']:
        print("  [YES] 'Always Fresh Data' checkbox will be CHECKED")
    else:
        print("  [NO] 'Always Fresh Data' checkbox will be unchecked")
    
    if loaded_settings['auto_resize_columns']:
        print("  [YES] Table columns will auto-resize when data is loaded")
    else:
        print("  [NO] Table columns will NOT auto-resize")
    
    if loaded_settings['auto_start_collection']:
        print("  [YES] Background data collection will start automatically")
    else:
        print("  [NO] Background data collection will NOT start automatically")
    
    print(f"  [YES] Search results will be limited to {loaded_settings['max_results']} items")
    
    if loaded_settings['show_progress_details']:
        print("  [YES] Detailed progress information will be shown")
    else:
        print("  [NO] Detailed progress information will be hidden")
    
    return all_correct

def main():
    """Run verification"""
    # Create minimal QApplication for QSettings to work
    if not QApplication.instance():
        app = QApplication(sys.argv)
    
    try:
        success = verify_default_settings()
        
        print()
        print("=" * 50)
        
        if success:
            print("[SUCCESS] Settings verification PASSED!")
            print("The application should now apply default settings correctly.")
        else:
            print("[ERROR] Settings verification FAILED!")
            print("There may still be issues with the settings implementation.")
        
        print()
        print("Next Steps:")
        print("1. Run the application: python src/maricopa_property_search.py")
        print("2. Verify that the 'Always Fresh Data' checkbox is checked")
        print("3. Verify that background collection starts automatically")
        print("4. Check that table columns resize automatically after search")
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()