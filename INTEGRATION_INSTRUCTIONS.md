# INTEGRATION INSTRUCTIONS FOR ENHANCED_MAIN_WINDOW.PY

## Overview
These instructions will integrate the missing GUI features into the existing enhanced_main_window.py file. The current file already has most features implemented, but these additions will complete the integration with enhanced keyboard shortcuts, toolbar buttons, context menus, and status bar improvements.

## Required Changes

### 1. ADD ADDITIONAL IMPORTS
Add these imports at the top of the file with the other PyQt5 imports:

```python
from PyQt5.QtWidgets import QShortcut, QToolBar, QMenu
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import QTimer
```

### 2. ADD NEW METHODS TO EnhancedPropertySearchApp CLASS

#### Keyboard Shortcuts Setup
```python
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
```

#### Enhanced Toolbar Setup
```python
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
        QPushButton:hover {
            background-color: #1976D2;
        }
        QPushButton:disabled {
            background-color: #CCCCCC;
            color: #666666;
        }
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
        QPushButton:hover {
            background-color: #F57C00;
        }
        QPushButton:disabled {
            background-color: #CCCCCC;
            color: #666666;
        }
    """)
    self.toolbar_force_btn.clicked.connect(self.force_data_collection)
    self.toolbar_force_btn.setEnabled(False)
    toolbar.addWidget(self.toolbar_force_btn)
    
    toolbar.addSeparator()
    
    # Batch search button
    self.toolbar_batch_btn = QPushButton("Batch Search")
    self.toolbar_batch_btn.setToolTip("Open batch search dialog (Ctrl+B)")
    self.toolbar_batch_btn.setStyleSheet("""
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
    """)
    self.toolbar_batch_btn.clicked.connect(self.show_batch_search_dialog)
    toolbar.addWidget(self.toolbar_batch_btn)
    
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
        QPushButton:hover {
            background-color: #455A64;
        }
    """)
    self.toolbar_settings_btn.clicked.connect(self.show_settings_dialog)
    toolbar.addWidget(self.toolbar_settings_btn)
    
    self.toolbar = toolbar
    logger.info("Enhanced toolbar setup complete")
```

#### Context Menu Setup
```python
def setup_results_table_context_menu(self):
    """Setup context menu for results table"""
    self.results_table.setContextMenuPolicy(Qt.CustomContextMenu)
    self.results_table.customContextMenuRequested.connect(self.show_results_context_menu)

def show_results_context_menu(self, position):
    """Show context menu for results table"""
    if not self.results_table.itemAt(position):
        return
        
    menu = QMenu(self.results_table)
    
    # View details
    view_action = menu.addAction("View Details")
    view_action.triggered.connect(self.view_property_details)
    
    menu.addSeparator()
    
    # Refresh selected property
    refresh_action = menu.addAction("Refresh This Property")
    refresh_action.triggered.connect(self.refresh_selected_property)
    
    # Force collect selected property
    force_action = menu.addAction("Force Collect This Property")
    force_action.triggered.connect(self.force_collect_selected_property)
    
    menu.addSeparator()
    
    # Export selected
    export_action = menu.addAction("Export Selected")
    export_action.triggered.connect(self.export_selected_results)
    
    # Copy APN
    copy_action = menu.addAction("Copy APN")
    copy_action.triggered.connect(self.copy_apn_to_clipboard)
    
    menu.exec_(self.results_table.mapToGlobal(position))
```

#### Enhanced Status Bar Setup
```python
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
    
    # Overall progress bar for background operations
    self.overall_progress = QProgressBar()
    self.overall_progress.setVisible(False)
    self.overall_progress.setMaximumWidth(200)
    self.status_bar.addPermanentWidget(self.overall_progress)
    
    # Enhanced status update timer
    self.enhanced_status_timer = QTimer()
    self.enhanced_status_timer.timeout.connect(self.update_enhanced_status_bar)
    self.enhanced_status_timer.start(2000)  # Update every 2 seconds

def update_enhanced_status_bar(self):
    """Update enhanced status bar information"""
    try:
        # Update collection status
        if hasattr(self, 'background_manager'):
            if self.background_manager.is_running():
                self.collection_status_label.setText("Collection: Running")
                self.collection_status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.collection_status_label.setText("Collection: Stopped")
                self.collection_status_label.setStyleSheet("color: red;")
        
        # Update cache statistics
        if (hasattr(self, 'background_manager') and 
            self.background_manager.worker):
            stats = self.background_manager.get_statistics()
            cache_hits = stats.get('cache_hits', 0)
            cache_misses = stats.get('cache_misses', 0)
            total_cache = cache_hits + cache_misses
            hit_rate = (cache_hits / total_cache * 100) if total_cache > 0 else 0
            self.cache_stats_label.setText(f"Cache: {cache_hits} hits ({hit_rate:.1f}%)")
        
        # Update database status
        if hasattr(self, 'db_manager'):
            try:
                # Simple connection test
                self.db_manager.get_search_history(limit=1)
                self.db_status_label.setText("DB: Connected")
                self.db_status_label.setStyleSheet("color: green;")
            except:
                self.db_status_label.setText("DB: Error")
                self.db_status_label.setStyleSheet("color: red; font-weight: bold;")
                
    except Exception as e:
        logger.warning(f"Error updating enhanced status bar: {e}")
```

#### Additional Utility Methods
```python
def refresh_selected_property(self):
    """Refresh data for currently selected property"""
    current_row = self.results_table.currentRow()
    if current_row >= 0 and current_row < len(self.current_results):
        property_data = self.current_results[current_row]
        apn = property_data.get('apn')
        if apn and self.background_manager.is_running():
            self.background_manager.add_job(apn, JobPriority.HIGH)
            self.status_bar.showMessage(f"Refreshing data for APN: {apn}", 3000)
            logger.info(f"User requested refresh for APN: {apn}")

def force_collect_selected_property(self):
    """Force data collection for currently selected property"""
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
            logger.info(f"User requested force collection for APN: {apn}")

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
    
    if not selected_results:
        return
        
    # Export selected results
    filename, _ = QFileDialog.getSaveFileName(
        self, "Export Selected Results", 
        f"selected_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "CSV Files (*.csv);;All Files (*)"
    )
    
    if filename:
        try:
            self._export_results_to_file(selected_results, filename)
            QMessageBox.information(self, "Export Complete", 
                                   f"Exported {len(selected_results)} selected properties to {filename}")
            logger.info(f"Exported {len(selected_results)} selected results to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export results: {str(e)}")
            logger.error(f"Failed to export selected results: {e}")

def copy_apn_to_clipboard(self):
    """Copy selected property APN to clipboard"""
    current_row = self.results_table.currentRow()
    if current_row >= 0 and current_row < len(self.current_results):
        property_data = self.current_results[current_row]
        apn = property_data.get('apn', '')
        if apn:
            QApplication.clipboard().setText(apn)
            self.status_bar.showMessage(f"Copied APN to clipboard: {apn}", 2000)
            logger.info(f"User copied APN to clipboard: {apn}")

def cancel_current_operation(self):
    """Cancel current search or background operation"""
    # Cancel search worker
    if self.search_worker and self.search_worker.isRunning():
        self.search_worker.terminate()
        self.search_worker.wait()
        self.status_bar.showMessage("Search cancelled", 2000)
        self.search_btn.setText("Search")
        self.search_btn.setEnabled(True)
        logger.info("User cancelled search operation")
    
    # Cancel batch operations
    if hasattr(self.bg_status_widget, 'batch_tracker'):
        self.bg_status_widget.batch_tracker.cancel_current_batch()
        logger.info("User cancelled batch operation")

def update_toolbar_buttons_state(self):
    """Update toolbar button states based on current context"""
    has_results = len(self.current_results) > 0
    
    # Update toolbar buttons if they exist
    if hasattr(self, 'toolbar_refresh_btn'):
        self.toolbar_refresh_btn.setEnabled(has_results)
    if hasattr(self, 'toolbar_force_btn'):
        self.toolbar_force_btn.setEnabled(has_results)

def keyPressEvent(self, event):
    """Handle additional keyboard events"""
    from PyQt5.QtCore import Qt
    
    # Handle Escape key for cancellation
    if event.key() == Qt.Key_Escape:
        self.cancel_current_operation()
    else:
        super().keyPressEvent(event)
```

### 3. MODIFY EXISTING SETUP_UI METHOD
Add these calls at the end of the existing setup_ui() method:

```python
# Setup enhanced features
self.setup_keyboard_shortcuts()
self.setup_enhanced_toolbar() 
self.setup_results_table_context_menu()
self.setup_enhanced_status_bar()
```

### 4. MODIFY EXISTING SETUP_CONNECTIONS METHOD
Add this connection to the existing setup_connections() method:

```python
# Connect to update toolbar button states
self.results_table.selectionModel().selectionChanged.connect(self.update_toolbar_buttons_state)
```

### 5. MODIFY EXISTING ON_RESULTS_UPDATED METHOD
Add this call at the end of any method that updates results:

```python
self.update_toolbar_buttons_state()
```

## Summary of New Features

After implementing these changes, the enhanced main window will have:

### 🎹 **Additional Keyboard Shortcuts**
- `Ctrl+R` - Alternative refresh current data
- `Ctrl+Shift+R` - Alternative force data collection  
- `Ctrl+T` - Toggle background collection
- `Ctrl+Shift+S` - Open collection settings dialog
- `Ctrl+Shift+C` - Clear cache
- `F1` - Show about dialog
- `Esc` - Cancel current operation

### 🔧 **Enhanced Toolbar**
- Quick Refresh button with visual feedback
- Force Collect button with warning styling
- Batch Search button for quick access
- Settings button for easy configuration access
- Proper enable/disable state management

### 📝 **Right-click Context Menu**
- View Details for selected property
- Refresh This Property (single property refresh)
- Force Collect This Property (bypass cache)
- Export Selected rows only
- Copy APN to clipboard

### 📊 **Enhanced Status Bar**
- Real-time background collection status indicator
- Cache statistics with hit/miss rates
- Database connection status monitor  
- Progress bar for background operations
- Automatic status updates every 2 seconds

### ⚡ **Power User Features**
- Cancel operations with Escape key
- Smart toolbar button state management
- Clipboard integration for property data
- Enhanced error handling and logging
- Professional keyboard-first workflow

## Testing the Integration

After implementing these changes:

1. **Test Keyboard Shortcuts**: Try each shortcut to ensure they work correctly
2. **Test Toolbar Buttons**: Verify buttons enable/disable based on search results
3. **Test Context Menu**: Right-click on results table to access additional options
4. **Test Status Bar**: Verify real-time status updates are working
5. **Test Error Handling**: Ensure cancellation and error scenarios work properly

## Compatibility

These changes are designed to integrate seamlessly with the existing enhanced_main_window.py without breaking any existing functionality. All new features are additive and enhance the user experience while maintaining backward compatibility.