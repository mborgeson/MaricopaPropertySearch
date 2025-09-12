#!/usr/bin/env python
"""
Cleanup Fix Files
Optional script to clean up temporary files created during the settings fix.
"""

import os

def main():
    """Clean up temporary files created during the settings fix"""
    
    files_to_remove = [
        "fix_default_settings.py",
        "fix_default_settings_simple.py", 
        "final_settings_fix.py",
        "test_settings.py",
        "verify_settings.py",
        "src/gui/enhanced_main_window_fixed.py"
    ]
    
    files_to_keep = [
        "DEFAULT_SETTINGS_FIX_SUMMARY.md",  # Keep the summary
        # All backup files will be preserved
    ]
    
    print("Cleaning up temporary fix files...")
    print()
    
    removed_count = 0
    
    for filepath in files_to_remove:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"Removed: {filepath}")
                removed_count += 1
            except Exception as e:
                print(f"Could not remove {filepath}: {e}")
        else:
            print(f"Not found: {filepath}")
    
    print()
    print(f"Cleanup complete. Removed {removed_count} temporary files.")
    print()
    print("Files preserved:")
    print("- DEFAULT_SETTINGS_FIX_SUMMARY.md (documentation)")
    print("- All backup files (*.backup_*)")
    print("- src/gui/enhanced_main_window.py (fixed main file)")

if __name__ == "__main__":
    main()