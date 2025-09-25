#!/usr/bin/env python
"""
Test Settings Loading and Application
This script tests the QSettings functionality to verify default values are working.
"""
import os
import sys

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication


def test_qsettings_defaults():
    """Test QSettings default value handling"""
        print("Testing QSettings default value handling...")
    
    # Create a unique settings instance for testing
    settings = QSettings("MaricopaPropertySearchTest", "PropertySearchTest")
    
    # Clear all settings to start fresh
    settings.clear()
    settings.sync()
    
    # Define the same defaults as the application
    defaults = {
        'auto_start_collection': (True, bool),
        'max_results': (20, int),
        'auto_resize_columns': (True, bool),
        'show_progress_details': (True, bool),
        'always_fresh_data': (True, bool)
    }
        print("\nTesting default value retrieval:")
    loaded_settings = {}
    
    # Test loading defaults (same logic as in the app)
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
        print(f"  {key}: {loaded_settings[key]} (type: {type(loaded_settings[key])})")
    
    # Test saving and reloading
        print("\nTesting save and reload:")
    
    # Save the settings
    for key, value in loaded_settings.items():
        settings.setValue(key, value)
    settings.sync()
    
    # Reload and verify
    reloaded_settings = {}
    for key, (default_value, value_type) in defaults.items():
        stored_value = settings.value(key, default_value)
        
        if value_type == bool:
            if isinstance(stored_value, str):
                reloaded_settings[key] = stored_value.lower() == 'true'
            else:
                reloaded_settings[key] = bool(stored_value)
        elif value_type == int:
            reloaded_settings[key] = int(stored_value) if stored_value else default_value
        else:
            reloaded_settings[key] = stored_value
        print(f"  {key}: {reloaded_settings[key]} (type: {type(reloaded_settings[key])})")
    
    # Verify all values match expectations
    expected = {
        'auto_start_collection': True,
        'max_results': 20,
        'auto_resize_columns': True,
        'show_progress_details': True,
        'always_fresh_data': True
    }
        print("\nValidation results:")
    all_correct = True
    for key, expected_value in expected.items():
        actual_value = reloaded_settings[key]
        is_correct = actual_value == expected_value
        status = "[OK]" if is_correct else "[FAIL]"
        print(f"  {key}: {status} Expected: {expected_value}, Got: {actual_value}")
        if not is_correct:
            all_correct = False
    
    # Clean up test settings
    settings.clear()
    settings.sync()
    
    return all_correct
def main():
    """Run settings tests"""
    # Create minimal QApplication for QSettings to work
    if not QApplication.instance():
        app = QApplication(sys.argv)
        print("Maricopa Property Search - Settings Test")
        print("=" * 50)
    
    try:
        success = test_qsettings_defaults()
        
        if success:
        print("\n[SUCCESS] All settings tests passed!")
        print("Default settings should work correctly in the application.")
        else:
        print("\n[ERROR] Some settings tests failed!")
        print("There may be issues with the settings implementation.")
    
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
import traceback

        traceback.print_exc()

    if __name__ == "__main__":
    main()