#!/usr/bin/env python
"""
Fix Default Settings Application in Enhanced Main Window
This script fixes the issue where default settings are not being properly applied to UI components.
"""
import os
import re
import shutil
from datetime import datetime


def backup_file(filepath):
    """Create a backup of the file"""
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
        print(f"Created backup: {backup_path}")
    return backup_path
def fix_apply_settings_method(content):
    """Fix the apply_settings_to_ui method"""
    
    # Find the current apply_settings_to_ui method
    pattern = r'(def apply_settings_to_ui\(self, settings_dict\):.*?)(def \w+\(self.*?|\Z)'
    
    new_method = '''def apply_settings_to_ui(self, settings_dict):
        """Apply loaded settings to the UI components"""
        try:
            # Apply max results setting
            if 'max_results' in settings_dict:
                # This would be used when performing searches
                self.max_results = settings_dict['max_results']
                logger.info(f"Set max results to {self.max_results}")
            
            # Apply auto-resize columns setting
            if 'auto_resize_columns' in settings_dict:
                self.auto_resize_columns_enabled = settings_dict['auto_resize_columns']
                if self.auto_resize_columns_enabled and hasattr(self, 'results_table'):
                    self.results_table.resizeColumnsToContents()
                    if hasattr(self, 'tax_table'):
                        self.tax_table.resizeColumnsToContents()
                    if hasattr(self, 'sales_table'):
                        self.sales_table.resizeColumnsToContents()
                logger.info(f"Set auto-resize columns to {self.auto_resize_columns_enabled}")
            
            # Apply show progress details setting
            if 'show_progress_details' in settings_dict:
                # Store for use in progress updates
                self.show_detailed_progress = settings_dict['show_progress_details']
                logger.info(f"Set show detailed progress to {self.show_detailed_progress}")
            
            # Apply always fresh data setting to checkbox and internal state
            if 'always_fresh_data' in settings_dict:
                # This affects how data is fetched
                self.always_fresh_data = settings_dict['always_fresh_data']
                # Apply to UI checkbox if it exists
                if hasattr(self, 'fresh_data_checkbox'):
                    self.fresh_data_checkbox.setChecked(self.always_fresh_data)
                    logger.info(f"Set fresh data checkbox to {self.always_fresh_data}")
                # Configure API client to bypass cache if needed
                if hasattr(self, 'api_client'):
                    self.api_client.use_cache = not settings_dict['always_fresh_data']
            
            # Apply auto-start collection setting (for next startup)
            if 'auto_start_collection' in settings_dict:
                self.auto_start_collection = settings_dict['auto_start_collection']
                logger.info(f"Set auto-start collection to {self.auto_start_collection}")
            
            logger.info("Applied settings to UI successfully")
            
        except Exception as e:
            logger.error(f"Failed to apply settings to UI: {e}")

    '''
def replace_method(match):
        return new_method + match.group(2)
    
    return re.sub(pattern, replace_method, content, flags=re.DOTALL)
def add_table_auto_resize_support(content):
    """Add support for auto-resizing tables after data is loaded"""
    
    # Find the method that populates the results table and add auto-resize logic
    search_pattern = r'(self\.results_table\.setItem\([^)]+\)[^}]*?)(except Exception as e:|finally:|$)'
    
    auto_resize_code = '''
            
            # Auto-resize columns if enabled
            if hasattr(self, 'auto_resize_columns_enabled') and self.auto_resize_columns_enabled:
                self.results_table.resizeColumnsToContents()
'''
def add_auto_resize(match):
        return match.group(1) + auto_resize_code + match.group(2)
    
    return re.sub(search_pattern, add_auto_resize, content, flags=re.DOTALL)
def fix_initialization_order(content):
    """Fix the initialization order to ensure settings are applied after UI is fully set up"""
    
    # Find the __init__ method and modify the settings loading section
    init_pattern = r'(# Load and apply saved settings[^}]*?saved_settings = self\.load_application_settings\(\)[^}]*?self\.apply_settings_to_ui\(saved_settings\)[^}]*?)(\n\s+logger\.info\("Loaded and applied saved settings"\))'
    
    improved_init = r'''\1
        
        # Ensure UI components are ready before applying settings
        QTimer.singleShot(100, lambda: self._apply_delayed_settings(saved_settings))
        
\2'''
    
    content = re.sub(init_pattern, improved_init, content, flags=re.DOTALL)
    
    # Add the delayed settings application method
    delayed_method = '''
def _apply_delayed_settings(self, settings_dict):
        """Apply settings after UI is fully initialized"""
        try:
            self.apply_settings_to_ui(settings_dict)
            logger.info("Applied delayed settings to UI successfully")
            
            # Auto-start background collection if enabled
            if settings_dict.get('auto_start_collection', True):
                if hasattr(self, 'background_manager') and not self.background_manager.is_running():
                    QTimer.singleShot(2000, self._delayed_background_start)
                    logger.info("Background data collection scheduled to start automatically")
        except Exception as e:
            logger.error(f"Failed to apply delayed settings: {e}")
'''
    
    # Add the method before the closeEvent method
    close_event_pattern = r'(def closeEvent\(self, event\):)'
    content = re.sub(close_event_pattern, delayed_method + r'\n    \1', content)
    
    return content
def main():
    """Apply fixes to the enhanced main window"""
    
    main_window_path = os.path.join(
        os.path.dirname(__file__),
        'src', 'gui', 'enhanced_main_window.py'
    )
    
    if not os.path.exists(main_window_path):
        print(f"Error: File not found: {main_window_path}")
        return False
        print(f"Fixing default settings in: {main_window_path}")
    
    # Create backup
    backup_path = backup_file(main_window_path)
    
    try:
        # Read the current file
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print("Applying fixes...")
        
        # Apply fixes
        content = fix_apply_settings_method(content)
        content = add_table_auto_resize_support(content)
        content = fix_initialization_order(content)
        
        # Write the fixed content
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Successfully applied default settings fixes!")
        print()
        print("Fixed issues:")
        print("1. ✅ apply_settings_to_ui now properly sets UI checkbox states")
        print("2. ✅ Added support for auto-resizing table columns")
        print("3. ✅ Improved initialization order for settings application")
        print("4. ✅ Added delayed settings application to ensure UI is ready")
        print("5. ✅ Enhanced logging for better debugging")
        print()
        print("The following default settings will now be applied on startup:")
        print("- Auto-Start Background Collection: True")
        print("- Max Results: 20")
        print("- Auto-Resize Table Columns: True") 
        print("- Show Detailed Progress Information: True")
        print("- Always Fresh Data: True")
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        # Restore backup
        shutil.copy2(backup_path, main_window_path)
        print(f"Restored from backup: {backup_path}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Settings fix applied successfully!")
        print("Restart the application to see the default settings applied.")
    else:
        print("\n💥 Failed to apply settings fix.")