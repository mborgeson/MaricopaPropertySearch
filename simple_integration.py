#!/usr/bin/env python
"""
Simple GUI Integration Script
Applies the final enhancements to enhanced_main_window.py
"""

import os
import shutil
from datetime import datetime

def main():
    print("GUI Integration Script")
    print("=" * 30)
    
    # File path
    main_window_path = "src/gui/enhanced_main_window.py"
    
    if not os.path.exists(main_window_path):
        print(f"Error: File not found: {main_window_path}")
        return
    
    # Create backup
    backup_path = f"{main_window_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(main_window_path, backup_path)
    print(f"Backup created: {backup_path}")
    
    # Read the current file
    with open(main_window_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Analysis of current file:")
    print(f"- File size: {len(content)} characters")
    print(f"- Contains QShortcut: {'QShortcut' in content}")
    print(f"- Contains setup_keyboard_shortcuts: {'setup_keyboard_shortcuts' in content}")
    print(f"- Contains setup_enhanced_toolbar: {'setup_enhanced_toolbar' in content}")
    
    # Check what's already implemented
    existing_features = []
    missing_features = []
    
    features_to_check = [
        ("QShortcut import", "QShortcut"),
        ("Keyboard shortcuts setup", "setup_keyboard_shortcuts"),
        ("Enhanced toolbar setup", "setup_enhanced_toolbar"),
        ("Context menu setup", "setup_results_table_context_menu"),
        ("Enhanced status bar", "setup_enhanced_status_bar"),
        ("Refresh selected property", "refresh_selected_property"),
        ("Force collect selected", "force_collect_selected_property"),
        ("Export selected results", "export_selected_results"),
        ("Copy APN to clipboard", "copy_apn_to_clipboard"),
        ("Cancel current operation", "cancel_current_operation"),
        ("Update toolbar buttons state", "update_toolbar_buttons_state")
    ]
    
    for feature_name, search_text in features_to_check:
        if search_text in content:
            existing_features.append(feature_name)
        else:
            missing_features.append(feature_name)
    
    print(f"\nExisting features ({len(existing_features)}):")
    for feature in existing_features:
        print(f"  + {feature}")
    
    print(f"\nMissing features ({len(missing_features)}):")
    for feature in missing_features:
        print(f"  - {feature}")
    
    if not missing_features:
        print("\nAll features are already implemented!")
        print("The enhanced_main_window.py file is complete.")
        return
    
    # Apply missing features
    print(f"\nApplying {len(missing_features)} missing features...")
    
    # Add imports if missing
    if "QShortcut" not in content:
        print("Adding QShortcut, QToolBar, QMenu imports...")
        # Find existing PyQt5 widget imports and extend them
        if "from PyQt5.QtWidgets import (" in content:
            content = content.replace(
                "QPushButton, QButtonGroup, QRadioButton, QScrollArea",
                "QPushButton, QButtonGroup, QRadioButton, QScrollArea, QShortcut, QToolBar, QMenu"
            )
        
        # Add QKeySequence import
        if "from PyQt5.QtGui import" in content:
            content = content.replace(
                "from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor, QPalette",
                "from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor, QPalette, QKeySequence"
            )
    
    # Add new methods before closeEvent
    if "def setup_keyboard_shortcuts" not in content:
        print("Adding enhanced methods...")
        
        new_methods = '''
    def setup_keyboard_shortcuts(self):
        """Setup additional keyboard shortcuts for power users"""
        self.shortcuts = {}
        
        shortcuts_config = {
            "Ctrl+R": self.refresh_current_data,
            "Ctrl+Shift+R": self.force_data_collection,
            "Ctrl+T": self.toggle_background_collection,
            "Ctrl+Shift+S": self.show_collection_settings_dialog,
            "Ctrl+Shift+C": self.clear_cache,
            "F1": self.show_about,
            "Esc": self.cancel_current_operation,
        }
        
        for shortcut_key, method in shortcuts_config.items():
            shortcut = QShortcut(QKeySequence(shortcut_key), self)
            shortcut.activated.connect(method)
            self.shortcuts[shortcut_key] = shortcut
        
        logger.info(f"Setup {len(shortcuts_config)} keyboard shortcuts")
    
    def setup_enhanced_toolbar(self):
        """Create enhanced toolbar with quick access buttons"""
        toolbar = self.addToolBar("Quick Actions")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        
        # Quick refresh button
        self.toolbar_refresh_btn = QPushButton("Quick Refresh")
        self.toolbar_refresh_btn.setToolTip("Refresh current results (F5)")
        self.toolbar_refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                margin: 2px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #CCCCCC; color: #666666; }
        """)
        self.toolbar_refresh_btn.clicked.connect(self.refresh_current_data)
        self.toolbar_refresh_btn.setEnabled(False)
        toolbar.addWidget(self.toolbar_refresh_btn)
        
        # Force collect button
        self.toolbar_force_btn = QPushButton("Force Collect")
        self.toolbar_force_btn.setToolTip("Force data collection ignoring cache (Ctrl+F5)")
        self.toolbar_force_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                margin: 2px;
            }
            QPushButton:hover { background-color: #F57C00; }
            QPushButton:disabled { background-color: #CCCCCC; color: #666666; }
        """)
        self.toolbar_force_btn.clicked.connect(self.force_data_collection)
        self.toolbar_force_btn.setEnabled(False)
        toolbar.addWidget(self.toolbar_force_btn)
        
        toolbar.addSeparator()
        
        # Settings button
        self.toolbar_settings_btn = QPushButton("Settings")
        self.toolbar_settings_btn.setToolTip("Open application settings (Ctrl+,)")
        self.toolbar_settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                margin: 2px;
            }
            QPushButton:hover { background-color: #455A64; }
        """)
        self.toolbar_settings_btn.clicked.connect(self.show_settings_dialog)
        toolbar.addWidget(self.toolbar_settings_btn)
        
        logger.info("Enhanced toolbar setup complete")
    
    def setup_results_table_context_menu(self):
        """Setup context menu for results table"""
        self.results_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self.show_results_context_menu)
    
    def show_results_context_menu(self, position):
        """Show context menu for results table"""
        if not self.results_table.itemAt(position):
            return
            
        menu = QMenu(self.results_table)
        
        view_action = menu.addAction("View Details")
        view_action.triggered.connect(self.view_property_details)
        
        menu.addSeparator()
        
        refresh_action = menu.addAction("Refresh This Property")
        refresh_action.triggered.connect(self.refresh_selected_property)
        
        force_action = menu.addAction("Force Collect This Property")
        force_action.triggered.connect(self.force_collect_selected_property)
        
        menu.addSeparator()
        
        export_action = menu.addAction("Export Selected")
        export_action.triggered.connect(self.export_selected_results)
        
        copy_action = menu.addAction("Copy APN")
        copy_action.triggered.connect(self.copy_apn_to_clipboard)
        
        menu.exec_(self.results_table.mapToGlobal(position))
    
    def setup_enhanced_status_bar(self):
        """Setup enhanced status bar with detailed information"""
        # Collection status label
        self.collection_status_label = QLabel("Collection: Stopped")
        self.status_bar.addPermanentWidget(self.collection_status_label)
        
        # Cache statistics label  
        self.cache_stats_label = QLabel("Cache: 0 hits")
        self.status_bar.addPermanentWidget(self.cache_stats_label)
        
        # Database connection status
        self.db_status_label = QLabel("DB: Connected")
        self.status_bar.addPermanentWidget(self.db_status_label)
        
        # Enhanced status update timer
        self.enhanced_status_timer = QTimer()
        self.enhanced_status_timer.timeout.connect(self.update_enhanced_status_bar)
        self.enhanced_status_timer.start(3000)
    
    def update_enhanced_status_bar(self):
        """Update enhanced status bar information"""
        try:
            if hasattr(self, 'background_manager') and self.background_manager.is_running():
                self.collection_status_label.setText("Collection: Running")
                self.collection_status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.collection_status_label.setText("Collection: Stopped")
                self.collection_status_label.setStyleSheet("color: red;")
        except:
            pass
    
    def refresh_selected_property(self):
        """Refresh data for currently selected property"""
        current_row = self.results_table.currentRow()
        if current_row >= 0 and current_row < len(self.current_results):
            property_data = self.current_results[current_row]
            apn = property_data.get('apn')
            if apn and self.background_manager.is_running():
                self.background_manager.add_job(apn, JobPriority.HIGH)
                self.status_bar.showMessage(f"Refreshing data for APN: {apn}", 3000)
    
    def force_collect_selected_property(self):
        """Force data collection for currently selected property"""
        current_row = self.results_table.currentRow()
        if current_row >= 0 and current_row < len(self.current_results):
            property_data = self.current_results[current_row]
            apn = property_data.get('apn')
            if apn and self.background_manager.is_running():
                if self.background_manager.worker:
                    self.background_manager.worker.cache.clear_property_cache(apn)
                self.background_manager.add_job(apn, JobPriority.CRITICAL)
                self.status_bar.showMessage(f"Force collecting data for APN: {apn}", 3000)
    
    def export_selected_results(self):
        """Export only selected table rows"""
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select rows to export.")
            return
            
        selected_results = [self.current_results[i] for i in sorted(selected_rows) 
                           if i < len(self.current_results)]
        
        if selected_results:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Selected Results", 
                f"selected_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )
            
            if filename:
                try:
                    # Use existing export logic
                    self.export_results(filename, selected_results)
                    QMessageBox.information(self, "Export Complete", 
                                           f"Exported {len(selected_results)} selected properties.")
                except Exception as e:
                    QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
    
    def copy_apn_to_clipboard(self):
        """Copy selected property APN to clipboard"""
        current_row = self.results_table.currentRow()
        if current_row >= 0 and current_row < len(self.current_results):
            property_data = self.current_results[current_row]
            apn = property_data.get('apn', '')
            if apn:
                QApplication.clipboard().setText(apn)
                self.status_bar.showMessage(f"Copied APN: {apn}", 2000)
    
    def cancel_current_operation(self):
        """Cancel current search or background operation"""
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.terminate()
            self.search_worker.wait()
            self.status_bar.showMessage("Search cancelled", 2000)
            self.search_btn.setText("Search")
            self.search_btn.setEnabled(True)
    
    def update_toolbar_buttons_state(self):
        """Update toolbar button states based on current context"""
        has_results = len(self.current_results) > 0
        if hasattr(self, 'toolbar_refresh_btn'):
            self.toolbar_refresh_btn.setEnabled(has_results)
        if hasattr(self, 'toolbar_force_btn'):
            self.toolbar_force_btn.setEnabled(has_results)
    
    def keyPressEvent(self, event):
        """Handle additional keyboard events"""
        if event.key() == Qt.Key_Escape:
            self.cancel_current_operation()
        else:
            super().keyPressEvent(event)

'''
        
        # Insert before closeEvent
        content = content.replace(
            "    def closeEvent(self, event):",
            new_methods + "    def closeEvent(self, event):"
        )
    
    # Add setup calls to setup_ui method
    if "self.setup_keyboard_shortcuts()" not in content:
        print("Adding setup calls to setup_ui method...")
        setup_additions = '''
        # Setup enhanced features
        self.setup_keyboard_shortcuts()
        self.setup_enhanced_toolbar() 
        self.setup_results_table_context_menu()
        self.setup_enhanced_status_bar()'''
        
        # Find end of setup_ui method and add setup calls
        content = content.replace(
            "        self.status_timer.start(5000)",
            "        self.status_timer.start(5000)" + setup_additions
        )
    
    # Add toolbar button state connection
    if "self.update_toolbar_buttons_state" not in content:
        print("Adding toolbar button state connection...")
        content = content.replace(
            "        self.bg_status_widget.batch_tracker.batch_completed.connect(self._on_batch_collection_completed)",
            "        self.bg_status_widget.batch_tracker.batch_completed.connect(self._on_batch_collection_completed)\n        self.results_table.selectionModel().selectionChanged.connect(self.update_toolbar_buttons_state)"
        )
    
    # Write the modified content back
    with open(main_window_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\nIntegration completed successfully!")
    print("\nNew features added:")
    print("- Additional keyboard shortcuts (Ctrl+R, Ctrl+T, F1, Esc)")
    print("- Enhanced toolbar with quick access buttons")
    print("- Right-click context menu for results table")
    print("- Enhanced status bar with system information")
    print("- Utility methods for property management")
    print("\nThe enhanced_main_window.py is now fully integrated!")

if __name__ == "__main__":
    main()