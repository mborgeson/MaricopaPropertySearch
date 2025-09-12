#!/usr/bin/env python
"""
Enhanced Batch Search Dialog
Advanced GUI dialog that integrates with the batch search integration manager
Provides comprehensive batch/parallel search functionality with real-time progress tracking
"""

import os
import csv
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QWidget, QPushButton, QLabel, QCheckBox, QComboBox, QSpinBox,
    QGroupBox, QTextEdit, QProgressBar, QFileDialog, QMessageBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QFrame, QScrollArea, QListWidget, QListWidgetItem,
    QButtonGroup, QRadioButton, QSlider, QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor

from src.batch_search_integration import (
    BatchSearchIntegrationManager, 
    BatchSearchJobType,
    BatchSearchResult,
    BatchSearchSummary
)
from src.logging_config import get_logger

logger = get_logger(__name__)


class EnhancedBatchSearchDialog(QDialog):
    """Enhanced dialog for comprehensive batch search operations"""
    
    # Signals for communicating with main window
    batch_started = pyqtSignal(str)  # job_id
    batch_progress = pyqtSignal(str, float, str)  # job_id, progress, status
    batch_completed = pyqtSignal(str, object)  # job_id, BatchSearchSummary
    batch_failed = pyqtSignal(str, str)  # job_id, error_message
    
    def __init__(self, integration_manager: BatchSearchIntegrationManager, parent=None):
        super().__init__(parent)
        self.integration_manager = integration_manager
        self.current_job_id = None
        self.batch_results = None
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._update_progress_display)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the enhanced batch search dialog UI"""
        self.setWindowTitle("Enhanced Batch Property Search")
        self.setModal(True)
        self.resize(800, 700)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create tabbed interface
        tab_widget = QTabWidget()
        
        # Tab 1: Input and Configuration
        input_tab = QWidget()
        self.setup_input_tab(input_tab)
        tab_widget.addTab(input_tab, "Search Input")
        
        # Tab 2: Processing Options
        options_tab = QWidget()
        self.setup_options_tab(options_tab)
        tab_widget.addTab(options_tab, "Processing Options")
        
        # Tab 3: Progress and Results
        progress_tab = QWidget()
        self.setup_progress_tab(progress_tab)
        tab_widget.addTab(progress_tab, "Progress & Results")
        
        layout.addWidget(tab_widget)
        
        # Bottom button panel
        self.setup_button_panel(layout)
    
    def setup_input_tab(self, tab):
        """Setup the input and basic configuration tab"""
        layout = QVBoxLayout(tab)
        
        # Search type and method selection
        config_group = QGroupBox("Search Configuration")
        config_layout = QGridLayout(config_group)
        
        # Search type
        config_layout.addWidget(QLabel("Search Type:"), 0, 0)
        self.search_type = QComboBox()
        self.search_type.addItems(["APN", "Property Address", "Owner Name"])
        config_layout.addWidget(self.search_type, 0, 1)
        
        # Job type
        config_layout.addWidget(QLabel("Operation Type:"), 0, 2)
        self.job_type = QComboBox()
        self.job_type.addItem("Basic Search", BatchSearchJobType.BASIC_SEARCH)
        self.job_type.addItem("Comprehensive Search", BatchSearchJobType.COMPREHENSIVE_SEARCH)
        self.job_type.addItem("Validation Only", BatchSearchJobType.VALIDATION_SEARCH)
        self.job_type.addItem("Data Enhancement", BatchSearchJobType.BULK_ENHANCEMENT)
        config_layout.addWidget(self.job_type, 0, 3)
        
        layout.addWidget(config_group)
        
        # Input methods
        input_group = QGroupBox("Search Input Methods")
        input_layout = QVBoxLayout(input_group)
        
        # Manual text input
        input_layout.addWidget(QLabel("Enter search terms (one per line):"))
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(
            "Examples:\\n"
            "For APNs: 123-45-678, 234-56-789\\n"
            "For Addresses: 123 Main St Phoenix AZ, 456 Oak Ave Scottsdale AZ\\n"
            "For Owner Names: John Smith, Jane Doe"
        )
        self.input_text.textChanged.connect(self._update_search_count)
        input_layout.addWidget(self.input_text)
        
        # File import options
        file_layout = QHBoxLayout()
        
        import_txt_btn = QPushButton("Import Text File")
        import_txt_btn.clicked.connect(lambda: self.import_from_file('txt'))
        file_layout.addWidget(import_txt_btn)
        
        import_csv_btn = QPushButton("Import CSV File")
        import_csv_btn.clicked.connect(lambda: self.import_from_file('csv'))
        file_layout.addWidget(import_csv_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.input_text.clear)
        file_layout.addWidget(clear_btn)
        
        file_layout.addStretch()
        input_layout.addLayout(file_layout)
        
        # Search count display
        self.search_count_label = QLabel("Search items: 0")
        self.search_count_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        input_layout.addWidget(self.search_count_label)
        
        layout.addWidget(input_group)
        
        # Quick validation
        validation_group = QGroupBox("Input Validation")
        validation_layout = QHBoxLayout(validation_group)
        
        validate_btn = QPushButton("Validate Input")
        validate_btn.clicked.connect(self._validate_input)
        validation_layout.addWidget(validate_btn)
        
        self.validation_status = QLabel("Not validated")
        validation_layout.addWidget(self.validation_status)
        
        validation_layout.addStretch()
        
        layout.addWidget(validation_group)
    
    def setup_options_tab(self, tab):
        """Setup processing options tab"""
        layout = QVBoxLayout(tab)
        
        # Performance settings
        performance_group = QGroupBox("Performance Settings")
        performance_layout = QFormLayout(performance_group)
        
        # Concurrency control
        self.max_concurrent = QSpinBox()
        self.max_concurrent.setRange(1, 10)
        self.max_concurrent.setValue(3)
        self.max_concurrent.setToolTip("Number of parallel searches (1-10). Higher values = faster but more resource intensive.")
        performance_layout.addRow("Max Concurrent Searches:", self.max_concurrent)
        
        # Timeout settings
        self.request_timeout = QSpinBox()
        self.request_timeout.setRange(10, 300)
        self.request_timeout.setValue(30)
        self.request_timeout.setSuffix(" seconds")
        performance_layout.addRow("Request Timeout:", self.request_timeout)
        
        layout.addWidget(performance_group)
        
        # Data collection options
        collection_group = QGroupBox("Data Collection Options")
        collection_layout = QVBoxLayout(collection_group)
        
        self.enable_background_collection = QCheckBox("Enable background data collection after search")
        self.enable_background_collection.setChecked(True)
        self.enable_background_collection.setToolTip("Automatically enhance search results with additional data")
        collection_layout.addWidget(self.enable_background_collection)
        
        self.comprehensive_data = QCheckBox("Collect comprehensive property data")
        self.comprehensive_data.setChecked(True)
        self.comprehensive_data.setToolTip("Include tax records, sales history, and detailed property information")
        collection_layout.addWidget(self.comprehensive_data)
        
        self.enable_web_scraping = QCheckBox("Enable web scraping for additional data")
        self.enable_web_scraping.setChecked(False)
        self.enable_web_scraping.setToolTip("Use web scraping to gather additional property details (slower)")
        collection_layout.addWidget(self.enable_web_scraping)
        
        layout.addWidget(collection_group)
        
        # Output options
        output_group = QGroupBox("Output Options")
        output_layout = QVBoxLayout(output_group)
        
        self.auto_export = QCheckBox("Auto-export results to CSV")
        self.auto_export.setChecked(False)
        output_layout.addWidget(self.auto_export)
        
        # Export location
        export_layout = QHBoxLayout()
        export_layout.addWidget(QLabel("Export Location:"))
        
        self.export_location = QLineEdit()
        self.export_location.setPlaceholderText("Choose export directory...")
        export_layout.addWidget(self.export_location)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_export_location)
        export_layout.addWidget(browse_btn)
        
        output_layout.addLayout(export_layout)
        
        layout.addWidget(output_group)
        
        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)
        
        # Error handling
        self.continue_on_errors = QCheckBox("Continue processing if individual searches fail")
        self.continue_on_errors.setChecked(True)
        advanced_layout.addRow("Error Handling:", self.continue_on_errors)
        
        # Retry settings
        self.max_retries = QSpinBox()
        self.max_retries.setRange(0, 5)
        self.max_retries.setValue(2)
        advanced_layout.addRow("Max Retries per Item:", self.max_retries)
        
        layout.addWidget(advanced_group)
        
        layout.addStretch()
    
    def setup_progress_tab(self, tab):
        """Setup progress tracking and results display tab"""
        layout = QVBoxLayout(tab)
        
        # Overall progress
        progress_group = QGroupBox("Batch Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        # Progress bar
        self.overall_progress = QProgressBar()
        self.overall_progress.setVisible(False)
        progress_layout.addWidget(self.overall_progress)
        
        # Status display
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Ready to start batch search")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        # Time elapsed
        self.time_label = QLabel("Elapsed: 00:00")
        status_layout.addWidget(self.time_label)
        
        progress_layout.addLayout(status_layout)
        
        # Statistics display
        stats_layout = QGridLayout()
        
        self.stats_labels = {
            'processed': QLabel("Processed: 0"),
            'successful': QLabel("Successful: 0"),
            'failed': QLabel("Failed: 0"),
            'rate': QLabel("Rate: 0 items/sec")
        }
        
        row = 0
        for key, label in self.stats_labels.items():
            label.setStyleSheet("font-weight: bold;")
            stats_layout.addWidget(label, row // 2, row % 2)
            row += 1
        
        progress_layout.addLayout(stats_layout)
        
        layout.addWidget(progress_group)
        
        # Detailed results table
        results_group = QGroupBox("Search Results Preview")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "Identifier", "Status", "Processing Time", "API Calls", "Error"
        ])
        
        # Configure table
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Identifier column
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Time
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # API calls
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Error
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        results_layout.addWidget(self.results_table)
        
        layout.addWidget(results_group)
    
    def setup_button_panel(self, layout):
        """Setup bottom button panel"""
        button_layout = QHBoxLayout()
        
        # Action buttons
        self.start_btn = QPushButton("Start Batch Search")
        self.start_btn.clicked.connect(self.start_batch_search)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.start_btn)
        
        self.cancel_btn = QPushButton("Cancel Operation")
        self.cancel_btn.clicked.connect(self.cancel_batch_search)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        
        # Export and results buttons  
        export_btn = QPushButton("Export Results")
        export_btn.clicked.connect(self.export_results)
        export_btn.setEnabled(False)
        self.export_btn = export_btn
        button_layout.addWidget(export_btn)
        
        # Dialog buttons
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _update_search_count(self):
        """Update search count display"""
        text = self.input_text.toPlainText().strip()
        if text:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            count = len(lines)
        else:
            count = 0
        
        self.search_count_label.setText(f"Search items: {count}")
        
        # Enable/disable start button based on input
        self.start_btn.setEnabled(count > 0 and self.current_job_id is None)
    
    def _validate_input(self):
        """Validate search input format"""
        text = self.input_text.toPlainText().strip()
        if not text:
            self.validation_status.setText("No input provided")
            self.validation_status.setStyleSheet("color: red;")
            return
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        search_type = self.search_type.currentText().lower()
        
        valid_count = 0
        invalid_count = 0
        
        for line in lines:
            if search_type == "apn":
                # Basic APN format validation (xxx-xx-xxx)
                if len(line) >= 7 and ('-' in line or len(line) >= 9):
                    valid_count += 1
                else:
                    invalid_count += 1
            elif search_type == "property address":
                # Basic address validation (has some text and likely state)
                if len(line) > 10 and any(state in line.upper() for state in ['AZ', 'ARIZONA']):
                    valid_count += 1
                else:
                    invalid_count += 1
            else:  # Owner name
                # Basic name validation (has at least two words)
                if len(line.split()) >= 2:
                    valid_count += 1
                else:
                    invalid_count += 1
        
        if invalid_count == 0:
            self.validation_status.setText(f"All {valid_count} items valid")
            self.validation_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.validation_status.setText(f"{valid_count} valid, {invalid_count} invalid")
            self.validation_status.setStyleSheet("color: orange; font-weight: bold;")
    
    def _browse_export_location(self):
        """Browse for export location"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Export Directory",
            self.export_location.text() or os.path.expanduser("~/Documents")
        )
        if directory:
            self.export_location.setText(directory)
    
    def import_from_file(self, file_type):
        """Import search terms from file"""
        if file_type == 'txt':
            filename, _ = QFileDialog.getOpenFileName(
                self, "Import Text File", "",
                "Text Files (*.txt);;All Files (*)"
            )
        else:  # CSV
            filename, _ = QFileDialog.getOpenFileName(
                self, "Import CSV File", "",
                "CSV Files (*.csv);;All Files (*)"
            )
        
        if not filename:
            return
        
        try:
            if file_type == 'txt':
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.input_text.setPlainText(content)
            else:  # CSV
                content_lines = []
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row and row[0].strip():  # Take first column, skip empty
                            content_lines.append(row[0].strip())
                
                self.input_text.setPlainText('\\n'.join(content_lines))
            
            QMessageBox.information(self, "Import Successful", 
                                  f"Imported {len(content_lines if file_type == 'csv' else content.split())} items")
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Error reading file: {str(e)}")
    
    def start_batch_search(self):
        """Start the batch search operation"""
        # Get search terms
        text = self.input_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter search terms.")
            return
        
        search_terms = [line.strip() for line in text.split('\n') if line.strip()]
        if not search_terms:
            QMessageBox.warning(self, "Warning", "No valid search terms found.")
            return
        
        # Get search configuration
        search_type = self.search_type.currentText().lower()
        if search_type == "property address":
            search_type = "address"
        elif search_type == "owner name":
            search_type = "owner"
        else:
            search_type = "apn"
        
        job_type = self.job_type.currentData()
        
        # Confirm if large batch
        if len(search_terms) > 50:
            reply = QMessageBox.question(
                self, "Large Batch Confirmation",
                f"You are about to process {len(search_terms)} items. This may take significant time and resources.\\n\\nContinue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        # Update UI state
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.overall_progress.setVisible(True)
        self.overall_progress.setRange(0, 100)
        self.overall_progress.setValue(0)
        
        # Clear previous results
        self.results_table.setRowCount(0)
        self.batch_results = None
        
        # Start the batch search
        try:
            self.current_job_id = self.integration_manager.execute_batch_search(
                identifiers=search_terms,
                search_type=search_type,
                job_type=job_type,
                max_concurrent=self.max_concurrent.value(),
                enable_background_collection=self.enable_background_collection.isChecked(),
                progress_callback=self._progress_callback
            )
            
            # Start progress monitoring
            self.batch_start_time = time.time()
            self.progress_timer.start(1000)  # Update every second
            
            self.status_label.setText(f"Starting batch {job_type.value} for {len(search_terms)} items...")
            
            # Emit signal
            self.batch_started.emit(self.current_job_id)
            
            logger.info(f"Started batch search job {self.current_job_id} with {len(search_terms)} items")
            
        except Exception as e:
            self._handle_batch_error(f"Failed to start batch search: {str(e)}")
    
    def cancel_batch_search(self):
        """Cancel the current batch search"""
        if not self.current_job_id:
            return
        
        reply = QMessageBox.question(
            self, "Cancel Confirmation", 
            "Are you sure you want to cancel the batch search?\\n\\nPartially completed results will be lost.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.integration_manager.cancel_job(self.current_job_id)
                if success:
                    self._reset_ui_state()
                    self.status_label.setText("Batch search cancelled by user")
                    logger.info(f"Cancelled batch search job {self.current_job_id}")
                else:
                    QMessageBox.warning(self, "Cancel Failed", "Could not cancel the batch operation.")
            except Exception as e:
                QMessageBox.critical(self, "Cancel Error", f"Error cancelling batch: {str(e)}")
    
    def _progress_callback(self, job_id: str, progress: float, status_message: str):
        """Handle progress updates from integration manager"""
        if job_id != self.current_job_id:
            return
        
        # Update progress bar
        self.overall_progress.setValue(int(progress))
        
        # Update status
        self.status_label.setText(status_message)
        
        # Emit signal for external monitoring
        self.batch_progress.emit(job_id, progress, status_message)
        
        # Check if completed
        if progress >= 100.0:
            self._handle_batch_completion()
    
    def _update_progress_display(self):
        """Update time and statistics display"""
        if not self.current_job_id or not hasattr(self, 'batch_start_time'):
            return
        
        # Update elapsed time
        elapsed = time.time() - self.batch_start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        self.time_label.setText(f"Elapsed: {minutes:02d}:{seconds:02d}")
        
        # Update statistics if we have job status
        try:
            status = self.integration_manager.get_job_status(self.current_job_id)
            if status:
                # Update statistics labels
                processed = status.get('completed_items', 0)
                total = status.get('total_items', 1)
                successful = status.get('successful_items', 0) 
                failed = processed - successful
                
                self.stats_labels['processed'].setText(f"Processed: {processed}/{total}")
                self.stats_labels['successful'].setText(f"Successful: {successful}")
                self.stats_labels['failed'].setText(f"Failed: {failed}")
                
                if elapsed > 0:
                    rate = processed / elapsed
                    self.stats_labels['rate'].setText(f"Rate: {rate:.1f} items/sec")
        except Exception as e:
            logger.debug(f"Error updating progress display: {e}")
    
    def _handle_batch_completion(self):
        """Handle batch search completion"""
        if not self.current_job_id:
            return
        
        try:
            # Get final results
            self.batch_results = self.integration_manager.get_job_results(self.current_job_id)
            
            if self.batch_results:
                # Update UI
                self._reset_ui_state()
                self._display_results(self.batch_results)
                
                # Auto-export if enabled
                if self.auto_export.isChecked() and self.export_location.text():
                    self._auto_export_results()
                
                # Show completion message
                QMessageBox.information(
                    self, "Batch Search Complete",
                    f"Processed {self.batch_results.total_items} items:\\n"
                    f"Successful: {self.batch_results.successful_items}\\n"
                    f"Failed: {self.batch_results.failed_items}\\n"
                    f"Total time: {self.batch_results.total_processing_time:.1f} seconds"
                )
                
                # Emit completion signal
                self.batch_completed.emit(self.current_job_id, self.batch_results)
                
                logger.info(f"Batch search {self.current_job_id} completed successfully")
            else:
                self._handle_batch_error("No results received from batch operation")
                
        except Exception as e:
            self._handle_batch_error(f"Error handling batch completion: {str(e)}")
    
    def _handle_batch_error(self, error_message: str):
        """Handle batch search errors"""
        self._reset_ui_state()
        self.status_label.setText(f"Error: {error_message}")
        
        QMessageBox.critical(self, "Batch Search Error", error_message)
        
        if self.current_job_id:
            self.batch_failed.emit(self.current_job_id, error_message)
            logger.error(f"Batch search {self.current_job_id} failed: {error_message}")
        
        self.current_job_id = None
    
    def _reset_ui_state(self):
        """Reset UI to initial state"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.export_btn.setEnabled(self.batch_results is not None)
        self.overall_progress.setVisible(False)
        self.progress_timer.stop()
        self.current_job_id = None
    
    def _display_results(self, summary: BatchSearchSummary):
        """Display batch results in the results table"""
        self.results_table.setRowCount(len(summary.results))
        
        for row, result in enumerate(summary.results):
            # Identifier
            self.results_table.setItem(row, 0, QTableWidgetItem(result.identifier))
            
            # Status
            status_item = QTableWidgetItem("Success" if result.success else "Failed")
            if result.success:
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            else:
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            self.results_table.setItem(row, 1, status_item)
            
            # Processing time
            time_item = QTableWidgetItem(f"{result.processing_time:.2f}s")
            self.results_table.setItem(row, 2, time_item)
            
            # API calls
            api_item = QTableWidgetItem(str(result.api_calls_used))
            self.results_table.setItem(row, 3, api_item)
            
            # Error message
            error_item = QTableWidgetItem(result.error_message or "")
            self.results_table.setItem(row, 4, error_item)
        
        # Enable export button
        self.export_btn.setEnabled(True)
    
    def _auto_export_results(self):
        """Auto-export results if enabled"""
        if not self.batch_results or not self.export_location.text():
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"batch_search_results_{timestamp}.csv"
            filepath = os.path.join(self.export_location.text(), filename)
            
            success = self.integration_manager.export_results_to_csv(self.current_job_id, filepath)
            
            if success:
                self.status_label.setText(f"Results auto-exported to: {filename}")
            else:
                logger.warning("Auto-export failed")
        except Exception as e:
            logger.error(f"Auto-export error: {e}")
    
    def export_results(self):
        """Export batch results to file"""
        if not self.batch_results:
            QMessageBox.warning(self, "No Results", "No batch results to export.")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"batch_search_results_{timestamp}.csv"
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Batch Results", default_filename,
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if filename:
            try:
                success = self.integration_manager.export_results_to_csv(self.current_job_id, filename)
                
                if success:
                    QMessageBox.information(
                        self, "Export Successful", 
                        f"Batch results exported to:\\n{filename}"
                    )
                else:
                    QMessageBox.critical(self, "Export Failed", "Failed to export results.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Error exporting results: {str(e)}")
    
    def get_batch_results(self) -> Optional[BatchSearchSummary]:
        """Get the batch search results"""
        return self.batch_results
    
    def load_settings(self):
        """Load saved settings"""
        # This could load from QSettings or config file
        # For now, use reasonable defaults
        pass
    
    def save_settings(self):
        """Save current settings"""
        # This could save to QSettings or config file
        pass
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        if self.current_job_id:
            reply = QMessageBox.question(
                self, "Close Confirmation",
                "Batch search is still running. Cancel and close?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.integration_manager.cancel_job(self.current_job_id)
            else:
                event.ignore()
                return
        
        self.save_settings()
        event.accept()