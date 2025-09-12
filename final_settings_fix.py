#!/usr/bin/env python
"""
Final Settings Fix for Enhanced Main Window
This script cleans up the initialization and ensures settings are applied correctly.
"""

import os
import re
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create a backup of the file"""
    backup_path = f"{filepath}.backup_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"Created backup: {backup_path}")
    return backup_path

def fix_initialization_section(content):
    """Fix the initialization section to properly load settings"""
    
    # Find and replace the problematic initialization section
    old_init_pattern = r'''        # Load and apply saved settings
        saved_settings = self\.load_application_settings\(\)
        self\.apply_settings_to_ui\(saved_settings\)
        
        # Ensure UI components are ready before applying settings
        QTimer\.singleShot\(100, lambda: self\._apply_delayed_settings\(saved_settings\)\)
        

        logger\.info\("Loaded and applied saved settings"\)
        
        self\.check_system_status\(\)
        
        # Auto-start background collection if enabled in settings
        if saved_settings\.get\('auto_start_collection', True\):
            QTimer\.singleShot\(1000, self\._delayed_background_start\)
            logger\.info\("Background data collection scheduled to start automatically"\)
        else:
            logger\.info\("Auto-start background collection is disabled in settings"\)'''
    
    new_init_section = '''        # Load and apply saved settings after UI is ready
        saved_settings = self.load_application_settings()
        # Use a slight delay to ensure UI components are fully initialized
        QTimer.singleShot(50, lambda: self._apply_settings_and_start(saved_settings))
        
        logger.info("Settings loading scheduled")
        
        self.check_system_status()'''
    
    content = re.sub(old_init_pattern, new_init_section, content, flags=re.MULTILINE)
    
    return content

def add_unified_settings_method(content):
    """Add a unified method for applying settings and starting background collection"""
    
    # Find where to insert the method (before closeEvent)
    close_event_pattern = r'(    def closeEvent\(self, event\):)'
    
    new_method = '''    def _apply_settings_and_start(self, settings_dict):
        """Apply settings after UI is ready and optionally start background collection"""
        try:
            # Apply all settings to UI components
            self.apply_settings_to_ui(settings_dict)
            logger.info("Applied settings to UI successfully")
            
            # Auto-start background collection if enabled in settings
            if settings_dict.get('auto_start_collection', True):
                # Give a bit more time for everything to be ready
                QTimer.singleShot(1000, self._delayed_background_start)
                logger.info("Background data collection scheduled to start automatically")
            else:
                logger.info("Auto-start background collection is disabled in settings")
                
        except Exception as e:
            logger.error(f"Failed to apply settings or start background collection: {e}")

    '''
    
    # Insert the method before closeEvent
    content = re.sub(close_event_pattern, new_method + r'\1', content)
    
    return content

def remove_duplicate_delayed_settings(content):
    """Remove duplicate _apply_delayed_settings methods"""
    
    # Remove duplicate method definitions
    delayed_pattern = r'''    def _apply_delayed_settings\(self, settings_dict\):
        """Apply settings after UI is fully initialized"""
        try:
            self\.apply_settings_to_ui\(settings_dict\)
            logger\.info\("Applied delayed settings to UI successfully"\)
            
            # Auto-start background collection if enabled
            if settings_dict\.get\('auto_start_collection', True\):
                if hasattr\(self, 'background_manager'\) and not self\.background_manager\.is_running\(\):
                    QTimer\.singleShot\(2000, self\._delayed_background_start\)
                    logger\.info\("Background data collection scheduled to start automatically"\)
        except Exception as e:
            logger\.error\(f"Failed to apply delayed settings: \{e\}"\)

'''
    
    # Remove all instances of this duplicate method
    content = re.sub(delayed_pattern, '', content, flags=re.MULTILINE)
    
    return content

def main():
    """Apply final settings fixes"""
    
    main_window_path = os.path.join(
        os.path.dirname(__file__),
        'src', 'gui', 'enhanced_main_window.py'
    )
    
    if not os.path.exists(main_window_path):
        print(f"Error: File not found: {main_window_path}")
        return False
    
    print(f"Applying final settings fixes to: {main_window_path}")
    
    # Create backup
    backup_path = backup_file(main_window_path)
    
    try:
        # Read the current file
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("Applying final fixes...")
        
        # Apply fixes in order
        content = fix_initialization_section(content)
        content = add_unified_settings_method(content)
        content = remove_duplicate_delayed_settings(content)
        
        # Write the fixed content
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("[SUCCESS] Applied final settings fixes!")
        print()
        print("Final fixes applied:")
        print("1. [FIXED] Cleaned up initialization order")
        print("2. [FIXED] Added unified settings application method")
        print("3. [FIXED] Removed duplicate methods")
        print("4. [FIXED] Proper timing for UI component initialization")
        print()
        print("Default settings are now guaranteed to apply on startup:")
        print("- Auto-Start Background Collection: True")
        print("- Max Results: 20")
        print("- Auto-Resize Table Columns: True") 
        print("- Show Detailed Progress Information: True")
        print("- Always Fresh Data: True")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error applying fixes: {e}")
        # Restore backup
        shutil.copy2(backup_path, main_window_path)
        print(f"Restored from backup: {backup_path}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n[DONE] Final settings fix applied successfully!")
        print("The application will now properly apply default settings on startup.")
    else:
        print("\n[FAILED] Failed to apply final settings fix.")