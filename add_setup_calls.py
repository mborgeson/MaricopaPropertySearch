#!/usr/bin/env python
"""
Add Setup Calls Script
Adds the missing setup calls to the setup_ui method
"""
def main():
        print("Adding setup calls to setup_ui method...")
    
    main_window_path = "src/gui/enhanced_main_window.py"
    
    # Read the file
    with open(main_window_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if setup calls already exist
    if "self.setup_keyboard_shortcuts()" in content:
        print("Setup calls already exist!")
        return
    
    # Add setup calls after the status timer
    setup_calls = '''
        # Setup enhanced features
        self.setup_keyboard_shortcuts()
        self.setup_enhanced_toolbar() 
        self.setup_results_table_context_menu()
        self.setup_enhanced_status_bar()'''
    
    # Replace the status timer section
    old_pattern = '''        self.status_timer.start(2000)  # Update every 2 seconds'''
    new_pattern = '''        self.status_timer.start(2000)  # Update every 2 seconds''' + setup_calls
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print("Added setup calls after status timer initialization")
        
        # Write back the content
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Setup calls added successfully!")
    else:
        print("Could not find status timer initialization to add setup calls")
    
    # Also add the toolbar button state connection to setup_connections
    if "self.update_toolbar_buttons_state" not in content:
        print("Adding toolbar button state connection...")
        
        old_conn = '''        self.bg_status_widget.batch_tracker.batch_completed.connect(self._on_batch_collection_completed)'''
        new_conn = old_conn + '''
        self.results_table.selectionModel().selectionChanged.connect(self.update_toolbar_buttons_state)'''
        
        if old_conn in content:
            content = content.replace(old_conn, new_conn)
            
            # Write back the content
            with open(main_window_path, 'w', encoding='utf-8') as f:
                f.write(content)
        print("Added toolbar button state connection")
        else:
        print("Could not find batch_completed connection to add toolbar state connection")

if __name__ == "__main__":
    main()