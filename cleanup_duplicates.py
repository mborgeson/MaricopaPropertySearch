#!/usr/bin/env python
"""
Cleanup Duplicate Methods Script
Removes duplicate methods that were accidentally added during integration
"""
import os


def main():
        print("Cleaning up duplicate methods...")
    
    main_window_path = "src/gui/enhanced_main_window.py"
    
    # Read the file
with open(main_window_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the duplicate section and remove it
    # The duplicates start at line 2687 with "def setup_keyboard_shortcuts"
    lines = content.split('\n')
    
    # Find where the duplicates start (around line 2687)
    duplicate_start = -1
    for i, line in enumerate(lines):
        if i > 2600 and "def setup_keyboard_shortcuts(self):" in line:
            duplicate_start = i
            break
    
    if duplicate_start != -1:
        print(f"Found duplicate methods starting at line {duplicate_start + 1}")
        
        # Remove everything from the duplicate start to the end of the duplicate methods
        # The duplicates end before the final "def closeEvent" method
        closeEvent_line = -1
        for i in range(duplicate_start, len(lines)):
            if "def closeEvent(self, event):" in lines[i]:
                closeEvent_line = i
                break
        
        if closeEvent_line != -1:
        print(f"Removing duplicate methods from line {duplicate_start + 1} to {closeEvent_line}")
            # Keep everything before duplicates and from closeEvent onwards
            cleaned_lines = lines[:duplicate_start] + lines[closeEvent_line:]
            cleaned_content = '\n'.join(cleaned_lines)
            
            # Write back the cleaned content
            with open(main_window_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
        print("Duplicate methods removed successfully!")
        print(f"File size reduced by {len(lines) - len(cleaned_lines)} lines")
        else:
        print("Could not find closeEvent method to determine end of duplicates")
    else:
        print("No duplicate methods found")
    
    # Verify the cleanup
    with open(main_window_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    methods_to_check = [
        "setup_keyboard_shortcuts",
        "setup_enhanced_toolbar", 
        "setup_results_table_context_menu",
        "refresh_selected_property",
        "copy_apn_to_clipboard"
    ]
        print("\nVerification:")
    for method in methods_to_check:
        count = content.count(f"def {method}")
        if count == 1:
        print(f"✓ {method}: {count} occurrence (correct)")
        else:
        print(f"✗ {method}: {count} occurrences (should be 1)")

if __name__ == "__main__":
    main()