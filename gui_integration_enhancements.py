#!/usr/bin/env python
"""
GUI Integration Enhancements
Additional keyboard shortcuts and minor UI improvements for the enhanced main window
"""

# Additional keyboard shortcuts to add to the enhanced_main_window.py
ADDITIONAL_SHORTCUTS = {
    "Ctrl+R": "refresh_current_data",  # Alternative refresh shortcut
    "Ctrl+Shift+R": "force_data_collection",  # Alternative force refresh
    "Ctrl+T": "toggle_background_collection",  # Toggle background collection
    "Ctrl+Shift+B": "show_batch_search_dialog",  # Alternative batch search
    "Ctrl+Shift+S": "show_collection_settings_dialog",  # Collection settings
    "Ctrl+Shift+C": "clear_cache",  # Clear cache
    "F1": "show_about",  # Help
    "Esc": "cancel_current_operation",  # Cancel current operation
}

# Additional toolbar buttons configuration
TOOLBAR_BUTTONS = [
    {
        "text": "Quick Refresh",
        "tooltip": "Refresh current results (F5)",
        "icon": "refresh.png",  # Optional icon
        "action": "refresh_current_data",
        "shortcut": "F5",
        "style": "primary"
    },
    {
        "text": "Force Collect",
        "tooltip": "Force data collection ignoring cache (Ctrl+F5)",
        "icon": "force_refresh.png",  # Optional icon
        "action": "force_data_collection", 
        "shortcut": "Ctrl+F5",
        "style": "warning"
    },
    {
        "text": "Batch Search",
        "tooltip": "Open batch search dialog (Ctrl+B)",
        "icon": "batch.png",  # Optional icon
        "action": "show_batch_search_dialog",
        "shortcut": "Ctrl+B",
        "style": "secondary"
    },
    {
        "text": "Settings",
        "tooltip": "Open application settings (Ctrl+,)",
        "icon": "settings.png",  # Optional icon
        "action": "show_settings_dialog",
        "shortcut": "Ctrl+,",
        "style": "secondary"
    }
]

# Status bar enhancements
STATUS_BAR_WIDGETS = [
    "collection_status",  # Background collection status
    "cache_stats",       # Cache hit/miss statistics
    "db_connection",     # Database connection status
    "api_status",        # API client status
    "progress_bar"       # Overall progress indicator
]

# Context menu items for results table
CONTEXT_MENU_ITEMS = [
    {
        "text": "View Details",
        "action": "view_property_details",
        "shortcut": "Enter"
    },
    {
        "text": "Refresh This Property",
        "action": "refresh_selected_property",
        "shortcut": "F5"
    },
    {
        "text": "Force Collect This Property", 
        "action": "force_collect_selected_property",
        "shortcut": "Ctrl+F5"
    },
    "separator",
    {
        "text": "Export Selected",
        "action": "export_selected_results",
        "shortcut": "Ctrl+E"
    },
    {
        "text": "Copy APN",
        "action": "copy_apn_to_clipboard",
        "shortcut": "Ctrl+C"
    }
]
def add_keyboard_shortcuts_to_main_window(main_window):
    """
    Add additional keyboard shortcuts to the main window
    This function should be called in the setup_ui method
    """
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QKeySequence
    from PyQt5.QtWidgets import QShortcut

    # Create shortcuts dictionary to store references
    main_window.shortcuts = {}
    
    for shortcut_key, method_name in ADDITIONAL_SHORTCUTS.items():
        if hasattr(main_window, method_name):
            shortcut = QShortcut(QKeySequence(shortcut_key), main_window)
            shortcut.activated.connect(getattr(main_window, method_name))
            main_window.shortcuts[shortcut_key] = shortcut
def create_enhanced_toolbar(main_window):
    """
    Create an enhanced toolbar with quick access buttons
    """
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QAction, QPushButton, QToolBar
    
    toolbar = main_window.addToolBar("Quick Actions")
    toolbar.setMovable(False)
    toolbar.setFloatable(False)
    
    # Button styles
    styles = {
        "primary": """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """,
        "warning": """
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """,
        "secondary": """
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """
    }
    
    # Create toolbar buttons
    main_window.toolbar_buttons = {}
    
    for button_config in TOOLBAR_BUTTONS:
        if hasattr(main_window, button_config["action"]):
            button = QPushButton(button_config["text"])
            button.setToolTip(button_config["tooltip"])
            button.setStyleSheet(styles.get(button_config["style"], styles["secondary"]))
            button.clicked.connect(getattr(main_window, button_config["action"]))
            
            # Add to toolbar
            toolbar.addWidget(button)
            main_window.toolbar_buttons[button_config["action"]] = button
    
    return toolbar
def add_context_menu_to_results_table(main_window):
    """
    Add context menu to the results table
    """
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QMenu
def show_context_menu(position):
        if not main_window.results_table.itemAt(position):
            return
            
        menu = QMenu(main_window.results_table)
        
        for item in CONTEXT_MENU_ITEMS:
            if item == "separator":
                menu.addSeparator()
            else:
                if hasattr(main_window, item["action"]):
                    action = menu.addAction(item["text"])
                    action.triggered.connect(getattr(main_window, item["action"]))
        
        menu.exec_(main_window.results_table.mapToGlobal(position))
    
    main_window.results_table.setContextMenuPolicy(Qt.CustomContextMenu)
    main_window.results_table.customContextMenuRequested.connect(show_context_menu)
def enhance_status_bar(main_window):
    """
    Enhance the status bar with additional information widgets
    """
    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import QLabel, QProgressBar

    # Collection status label
    main_window.collection_status_label = QLabel("Collection: Stopped")
    main_window.status_bar.addPermanentWidget(main_window.collection_status_label)
    
    # Cache statistics label
    main_window.cache_stats_label = QLabel("Cache: 0 hits")
    main_window.status_bar.addPermanentWidget(main_window.cache_stats_label)
    
    # Database connection status
    main_window.db_status_label = QLabel("DB: Connected")
    main_window.status_bar.addPermanentWidget(main_window.db_status_label)
    
    # Overall progress bar for background operations
    main_window.overall_progress = QProgressBar()
    main_window.overall_progress.setVisible(False)
    main_window.overall_progress.setMaximumWidth(200)
    main_window.status_bar.addPermanentWidget(main_window.overall_progress)
    
    # Timer to update status bar periodically
    status_update_timer = QTimer()
    status_update_timer.timeout.connect(lambda: update_enhanced_status_bar(main_window))
    status_update_timer.start(2000)  # Update every 2 seconds
    main_window.status_update_timer = status_update_timer
def update_enhanced_status_bar(main_window):
    """Update enhanced status bar information"""
    try:
        # Update collection status
        if hasattr(main_window, 'background_manager'):
            if main_window.background_manager.is_running():
                main_window.collection_status_label.setText("Collection: Running")
                main_window.collection_status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                main_window.collection_status_label.setText("Collection: Stopped")
                main_window.collection_status_label.setStyleSheet("color: red;")
        
        # Update cache statistics
        if (hasattr(main_window, 'background_manager') and 
            main_window.background_manager.worker):
            stats = main_window.background_manager.get_statistics()
            cache_hits = stats.get('cache_hits', 0)
            cache_misses = stats.get('cache_misses', 0)
            total_cache = cache_hits + cache_misses
            hit_rate = (cache_hits / total_cache * 100) if total_cache > 0 else 0
            main_window.cache_stats_label.setText(f"Cache: {cache_hits} hits ({hit_rate:.1f}%)")
        
        # Update database status
        if hasattr(main_window, 'db_manager'):
            try:
                # Simple connection test
                main_window.db_manager.get_search_history(limit=1)
                main_window.db_status_label.setText("DB: Connected")
                main_window.db_status_label.setStyleSheet("color: green;")
            except:
                    main_window.db_status_label.setText("DB: Error")
                main_window.db_status_label.setStyleSheet("color: red; font-weight: bold;")
                
    except Exception as e:
        print(f"Error updating status bar: {e}")

# Additional utility methods that can be added to the main window class
ADDITIONAL_METHODS = """
def refresh_selected_property(self):
    \"\"\"Refresh data for currently selected property\"\"\"
    current_row = self.results_table.currentRow()
    if current_row >= 0 and current_row < len(self.current_results):
        property_data = self.current_results[current_row]
        apn = property_data.get('apn')
        if apn and self.background_manager.is_running():
            self.background_manager.add_job(apn, JobPriority.HIGH)
            self.status_bar.showMessage(f"Refreshing data for APN: {apn}", 3000)
def force_collect_selected_property(self):
    \"\"\"Force data collection for currently selected property\"\"\"
    current_row = self.results_table.currentRow()
    if current_row >= 0 and current_row < len(self.current_results):
        property_data = self.current_results[current_row]
        apn = property_data.get('apn')
        if apn and self.background_manager.is_running():
            # Clear cache for this property first
            if self.background_manager.worker:
                self.background_manager.worker.cache.clear_property_cache(apn)
            self.background_manager.add_job(apn, JobPriority.CRITICAL)
            self.status_bar.showMessage(f"Force collecting data for APN: {apn}", 3000)
def export_selected_results(self):
    \"\"\"Export only selected table rows\"\"\"
    selected_rows = set()
    for item in self.results_table.selectedItems():
        selected_rows.add(item.row())
    
    if not selected_rows:
        QMessageBox.information(self, "No Selection", "Please select rows to export.")
        return
        
    selected_results = [self.current_results[i] for i in sorted(selected_rows) 
                       if i < len(self.current_results)]
    
    # Use existing export logic but with filtered results
    self._export_results_data(selected_results, "selected_results")
def copy_apn_to_clipboard(self):
    \"\"\"Copy selected property APN to clipboard\"\"\"
    current_row = self.results_table.currentRow()
    if current_row >= 0 and current_row < len(self.current_results):
        property_data = self.current_results[current_row]
        apn = property_data.get('apn', '')
        if apn:
            QApplication.clipboard().setText(apn)
            self.status_bar.showMessage(f"Copied APN to clipboard: {apn}", 2000)
def cancel_current_operation(self):
    \"\"\"Cancel current search or background operation\"\"\"
    # Cancel search worker
    if self.search_worker and self.search_worker.isRunning():
        self.search_worker.terminate()
        self.search_worker.wait()
        self.status_bar.showMessage("Search cancelled", 2000)
        self.search_btn.setText("Search")
        self.search_btn.setEnabled(True)
    
    # Cancel batch operations
    if hasattr(self.bg_status_widget, 'batch_tracker'):
        self.bg_status_widget.batch_tracker.cancel_current_batch()
def keyPressEvent(self, event):
    \"\"\"Handle additional keyboard events\"\"\"
    # Handle Escape key for cancellation
    if event.key() == Qt.Key_Escape:
        self.cancel_current_operation()
    else:
        super().keyPressEvent(event)
"""

if __name__ == "__main__":
        print("GUI Integration Enhancements")
        print("=" * 50)
        print("This module provides additional enhancements for the enhanced_main_window.py")
        print("Features included:")
        print("- Additional keyboard shortcuts")
        print("- Enhanced toolbar with quick action buttons")
        print("- Context menu for results table")
        print("- Enhanced status bar with detailed information")
        print("- Additional utility methods")
        print()
        print("To integrate these features, add the following to enhanced_main_window.py:")
        print("1. Import this module")
        print("2. Call the enhancement functions in setup_ui()")
        print("3. Add the additional methods to the main window class")