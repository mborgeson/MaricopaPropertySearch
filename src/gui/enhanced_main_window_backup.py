#!/usr/bin/env python
"""
Enhanced Main Window with Background Data Collection
Integrates automatic background data collection for seamless user experience
"""

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget, QTableWidget, 
    QTableWidgetItem, QTextEdit, QProgressBar, QMessageBox,
    QComboBox, QSpinBox, QCheckBox, QGroupBox, QSplitter,
    QHeaderView, QApplication, QStatusBar, QMenuBar, QMenu,
    QAction, QFileDialog, QDialog, QFrame, QSizePolicy,
    QSlider, QFormLayout, QListWidget, QListWidgetItem,
    QPushButton, QButtonGroup, QRadioButton, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QObject
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor, QPalette
from typing import Dict, List, Optional, Any
import json
import csv
from pathlib import Path
from datetime import datetime
import traceback

# Import application modules
# MIGRATED: from database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
# MIGRATED: from api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient, MockMaricopaAPIClient
from web_scraper import WebScraperManager, MockWebScraperManager
from background_data_collector import BackgroundDataCollectionManager, JobPriority
from user_action_logger import UserActionLogger, get_user_action_logger

# Import centralized logging
from logging_config import get_logger, get_search_logger, get_performance_logger, log_exception

# Import GUI enhancement dialogs
from gui.gui_enhancements_dialogs import (
    ApplicationSettingsDialog, DataCollectionSettingsDialog, CacheManagementDialog,
    BatchSearchDialog, ParallelProcessingDialog, DataSourceConfigurationDialog
)

logger = get_logger(__name__)
search_logger = get_search_logger(__name__)
perf_logger = get_performance_logger(__name__)


class EnhancedSearchWorker(QThread):
    """Enhanced search worker that triggers background data collection"""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    background_collection_started = pyqtSignal(int)  # number of jobs queued
    
    def __init__(self, search_type, search_term, db_manager, api_client, scraper, background_manager):
        super().__init__()
        self.search_type = search_type
        self.search_term = search_term
        self.db_manager = db_manager
        self.api_client = api_client
        self.scraper = scraper
        self.background_manager = background_manager
    
    def run(self):
        """Execute search and trigger background enhancement"""
        try:
            self.status_updated.emit(f"Searching {self.search_type}: {self.search_term}...")
            
            results = []
            
            if self.search_type == "owner":
                results = self._search_by_owner()
            elif self.search_type == "address":  
                results = self._search_by_address()
            elif self.search_type == "apn":
                results = self._search_by_apn()
            
            self.progress_updated.emit(90)
            self.status_updated.emit(f"Found {len(results)} properties")
            
            # Log search
            self.db_manager.log_search(self.search_type, self.search_term, len(results))
            
            # Trigger smart background data collection for results
            if results and self.background_manager.is_running():
                jobs_queued = self.background_manager.enhance_search_results(results, max_properties=25)
                if jobs_queued > 0:
                    self.background_collection_started.emit(jobs_queued)
                    logger.info(f"Queued {jobs_queued} properties for prioritized background data enhancement")
                    # Emit status update immediately
                    self.status_updated.emit(f"Auto-collecting data for {jobs_queued} properties...")
                else:
                    logger.info("No new properties queued (already have recent data or in progress)")
                    self.status_updated.emit("All properties have recent data or are being processed")
            
            self.progress_updated.emit(100)
            self.results_ready.emit(results)
            
        except Exception as e:
            logger.error(f"Search worker error: {e}")
            self.error_occurred.emit(str(e))
    
    def _search_by_owner(self) -> List[Dict]:
        """Search by owner name"""
        results = []
        
        # Search database first
        self.status_updated.emit("Searching database...")
        self.progress_updated.emit(25)
        
        db_results = self.db_manager.search_properties_by_owner(self.search_term)
        results.extend(db_results)
        
        # If no database results, try API
        if not db_results:
            self.status_updated.emit("Searching API...")
            self.progress_updated.emit(50)
            
            comprehensive_results = self.api_client.search_all_property_types(self.search_term)
            for category, props in comprehensive_results.items():
                for prop in props:
                    self.db_manager.insert_property(prop)
                results.extend(props)
        
        # If still no results, try web scraping
        if not results:
            self.status_updated.emit("Web scraping...")
            self.progress_updated.emit(75)
            
            scrape_results = self.scraper.search_by_owner_name(self.search_term)
            results.extend(scrape_results)
        
        return results
    
    def _search_by_address(self) -> List[Dict]:
        """Search by address"""
        results = []
        
        self.status_updated.emit("Searching database...")
        self.progress_updated.emit(50)
        
        results = self.db_manager.search_properties_by_address(self.search_term)
        
        if not results:
            self.status_updated.emit("Searching API...")
            comprehensive_results = self.api_client.search_all_property_types(self.search_term)
            for category, props in comprehensive_results.items():
                for prop in props:
                    self.db_manager.insert_property(prop)
                results.extend(props)
        
        # Fallback demo data for testing
        if not results:
            self.status_updated.emit("Using demo data...")
            demo_property = {
                'apn': '13304014A',
                'owner_name': 'DEMO PROPERTY OWNER',
                'property_address': self.search_term,
                'mailing_address': 'PO BOX 12345, PHOENIX, AZ 85001',
                'year_built': 2009,
                'living_area_sqft': 303140,
                'lot_size_sqft': 185582,
                'bedrooms': 14,
                'land_use_code': 'MFR'
            }
            results.append(demo_property)
        
        return results
    
    def _search_by_apn(self) -> List[Dict]:
        """Search by APN"""
        results = []
        
        self.status_updated.emit("Searching database...")
        self.progress_updated.emit(33)
        
        db_result = self.db_manager.get_property_by_apn(self.search_term)
        if db_result:
            results.append(db_result)
        else:
            self.status_updated.emit("Searching API...")
            self.progress_updated.emit(66)
            
            api_result = self.api_client.search_by_apn(self.search_term)
            if api_result:
                self.db_manager.insert_property(api_result)
                results.append(api_result)
            else:
                self.status_updated.emit("Web scraping...")
                scrape_result = self.scraper.scrape_property_by_apn(self.search_term)
                if scrape_result:
                    results.append(scrape_result)
        
        return results


class BatchCollectionTracker(QObject):
    """Tracks batch data collection operations"""
    
    # Signals for batch progress
    batch_started = pyqtSignal(int)  # total_properties
    batch_progress = pyqtSignal(int, int)  # completed, total
    batch_completed = pyqtSignal(dict)  # results summary
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.batch_active = False
        self.batch_apns = []
        self.batch_completed_count = 0
        self.batch_start_time = None
        self.batch_results = {}
        
    def start_batch(self, apns):
        """Start tracking a new batch collection"""
        self.batch_active = True
        self.batch_apns = list(apns)
        self.batch_completed_count = 0
        self.batch_start_time = datetime.now()
        self.batch_results = {}
        self.batch_started.emit(len(apns))
        logger.info(f"Batch collection started for {len(apns)} properties")
        
    def update_batch_progress(self, apn, result):
        """Update progress for a completed APN in the batch"""
        if not self.batch_active or apn not in self.batch_apns:
            return
            
        self.batch_results[apn] = result
        self.batch_completed_count += 1
        self.batch_progress.emit(self.batch_completed_count, len(self.batch_apns))
        
        # Check if batch is complete
        if self.batch_completed_count >= len(self.batch_apns):
            self._complete_batch()
    
    def _complete_batch(self):
        """Complete the batch operation"""
        if not self.batch_active:
            return
            
        batch_time = (datetime.now() - self.batch_start_time).total_seconds()
        
        # Calculate statistics
        successful = sum(1 for r in self.batch_results.values() 
                        if not r.get('error') and not r.get('skipped'))
        failed = sum(1 for r in self.batch_results.values() 
                    if r.get('error'))
        skipped = sum(1 for r in self.batch_results.values() 
                     if r.get('skipped'))
        
        summary = {
            'total_properties': len(self.batch_apns),
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'batch_time_seconds': batch_time,
            'results': self.batch_results
        }
        
        self.batch_active = False
        self.batch_completed.emit(summary)
        logger.info(f"Batch collection completed: {successful} successful, "
                   f"{failed} failed, {skipped} skipped in {batch_time:.1f}s")
    
    def cancel_batch(self):
        """Cancel the current batch"""
        if self.batch_active:
            self.batch_active = False
            logger.info("Batch collection cancelled")
    
    def is_batch_active(self):
        """Check if a batch is currently active"""
        return self.batch_active


class BackgroundCollectionStatusWidget(QWidget):
    """Enhanced widget for displaying background collection status with detailed progress"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Track individual job progress
        self.active_job_widgets = {}  # apn -> progress widget
        
        # Track batch operations - Initialize before setup_ui
        self.batch_tracker = BatchCollectionTracker(self)
        self.batch_tracker.batch_started.connect(self._on_batch_started)
        self.batch_tracker.batch_progress.connect(self._on_batch_progress)
        self.batch_tracker.batch_completed.connect(self._on_batch_completed)
        
        # Now setup UI with batch_tracker available
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the enhanced status widget UI"""
        layout = QVBoxLayout(self)
        
        # Status header with enhanced styling
        header_layout = QHBoxLayout()
        self.status_label = QLabel("Background Collection: Stopped")
        self.status_label.setFont(QFont("Arial", 10, QFont.Bold))
        header_layout.addWidget(self.status_label)
        
        # Add status indicator icon
        self.status_icon = QLabel("●")
        self.status_icon.setFont(QFont("Arial", 14, QFont.Bold))
        self.status_icon.setStyleSheet("color: red;")
        header_layout.addWidget(self.status_icon)
        
        self.start_stop_btn = QPushButton("Start Collection")
        self.start_stop_btn.setMaximumWidth(120)
        header_layout.addWidget(self.start_stop_btn)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Progress information with enhanced layout
        info_layout = QGridLayout()
        
        # Row 1: Queue status
        info_layout.addWidget(QLabel("Pending Jobs:"), 0, 0)
        self.pending_label = QLabel("0")
        self.pending_label.setStyleSheet("font-weight: bold; color: orange;")
        info_layout.addWidget(self.pending_label, 0, 1)
        
        info_layout.addWidget(QLabel("Active Jobs:"), 0, 2)
        self.active_label = QLabel("0")
        self.active_label.setStyleSheet("font-weight: bold; color: blue;")
        info_layout.addWidget(self.active_label, 0, 3)
        
        info_layout.addWidget(QLabel("Completed:"), 0, 4)
        self.completed_label = QLabel("0")
        self.completed_label.setStyleSheet("font-weight: bold; color: green;")
        info_layout.addWidget(self.completed_label, 0, 5)
        
        # Row 2: Performance metrics
        info_layout.addWidget(QLabel("Success Rate:"), 1, 0)
        self.success_rate_label = QLabel("0%")
        self.success_rate_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.success_rate_label, 1, 1)
        
        info_layout.addWidget(QLabel("Avg. Time:"), 1, 2)
        self.avg_time_label = QLabel("0.0s")
        self.avg_time_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.avg_time_label, 1, 3)
        
        info_layout.addWidget(QLabel("Cache Hit:"), 1, 4)
        self.cache_hit_label = QLabel("0%")
        self.cache_hit_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.cache_hit_label, 1, 5)
        
        layout.addLayout(info_layout)
        
        # Overall progress bar
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("Overall Progress:"))
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setTextVisible(True)
        self.overall_progress_bar.setFormat("%p% (%v/%m)")
        progress_layout.addWidget(self.overall_progress_bar)
        layout.addLayout(progress_layout)
        
        # Batch collection progress (initially hidden)
        self.batch_progress_group = QGroupBox("Batch Collection Progress")
        self.batch_progress_group.setVisible(False)
        batch_layout = QVBoxLayout(self.batch_progress_group)
        
        # Batch progress info
        batch_info_layout = QHBoxLayout()
        self.batch_status_label = QLabel("Batch Status: Ready")
        batch_info_layout.addWidget(self.batch_status_label)
        
        # Cancel button for batch operations
        self.cancel_batch_btn = QPushButton("Cancel Batch")
        self.cancel_batch_btn.setMaximumWidth(100)
        self.cancel_batch_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        batch_info_layout.addWidget(self.cancel_batch_btn)
        batch_info_layout.addStretch()
        batch_layout.addLayout(batch_info_layout)
        
        # Batch progress bar
        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setTextVisible(True)
        self.batch_progress_bar.setFormat("Collecting %v of %m properties (%p%)")
        batch_layout.addWidget(self.batch_progress_bar)
        
        layout.addWidget(self.batch_progress_group)
        
        # Active jobs progress area
        self.active_jobs_group = QGroupBox("Active Data Collections")
        self.active_jobs_layout = QVBoxLayout(self.active_jobs_group)
        self.active_jobs_group.setVisible(False)
        layout.addWidget(self.active_jobs_group)
        
        # Connect cancel button
        self.cancel_batch_btn.clicked.connect(self.batch_tracker.cancel_batch)
        
        # Set compact but expandable size
        self.setMinimumHeight(120)
        self.setMaximumHeight(400)  # Increased for batch progress
    
    def update_status(self, status_dict: Dict[str, Any]):
        """Update the enhanced status display with detailed progress"""
        is_running = status_dict.get('status') == 'running'
        
        # Update status label and icon
        if is_running:
            self.status_label.setText("Background Collection: Running")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.status_icon.setStyleSheet("color: green;")
            self.start_stop_btn.setText("Stop Collection")
        else:
            self.status_label.setText("Background Collection: Stopped")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.status_icon.setStyleSheet("color: red;")
            self.start_stop_btn.setText("Start Collection")
        
        # Update statistics with enhanced formatting
        pending_jobs = status_dict.get('pending_jobs', 0)
        active_jobs = status_dict.get('active_jobs', 0)
        completed_jobs = status_dict.get('completed_jobs', 0)
        total_jobs = status_dict.get('total_jobs', 0)
        
        self.pending_label.setText(str(pending_jobs))
        self.active_label.setText(str(active_jobs))
        self.completed_label.setText(str(completed_jobs))
        
        # Update performance metrics
        stats = status_dict.get('statistics', {})
        success_rate = stats.get('success_rate_percent', 0)
        avg_time = stats.get('average_processing_time', 0)
        cache_hit_rate = stats.get('cache_hit_rate_percent', 0)
        
        self.success_rate_label.setText(f"{success_rate:.1f}%")
        self.avg_time_label.setText(f"{avg_time:.1f}s")
        self.cache_hit_label.setText(f"{cache_hit_rate:.1f}%")
        
        # Update overall progress bar
        if total_jobs > 0:
            self.overall_progress_bar.setRange(0, total_jobs)
            self.overall_progress_bar.setValue(completed_jobs)
            self.overall_progress_bar.setVisible(True)
        else:
            self.overall_progress_bar.setVisible(False)
        
        # Update active jobs display
        self.update_active_jobs_display(status_dict)
    
    def update_active_jobs_display(self, status_dict: Dict[str, Any]):
        """Update the display of active data collection jobs"""
        active_jobs = status_dict.get('active_jobs', 0)
        
        if active_jobs > 0:
            self.active_jobs_group.setVisible(True)
            self.active_jobs_group.setTitle(f"Active Data Collections ({active_jobs})")
        else:
            self.active_jobs_group.setVisible(False)
    
    def add_active_job_progress(self, apn: str):
        """Add a progress indicator for a specific job"""
        if apn in self.active_job_widgets:
            return
        
        # Create progress widget for this job
        job_widget = QWidget()
        job_layout = QHBoxLayout(job_widget)
        job_layout.setContentsMargins(5, 2, 5, 2)
        
        # APN label
        apn_label = QLabel(f"APN {apn}:")
        apn_label.setMinimumWidth(100)
        job_layout.addWidget(apn_label)
        
        # Progress bar for this specific job
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # Indeterminate
        progress_bar.setMaximumHeight(15)
        job_layout.addWidget(progress_bar)
        
        # Status label
        status_label = QLabel("Collecting...")
        status_label.setMinimumWidth(80)
        status_label.setStyleSheet("color: blue; font-size: 10px;")
        job_layout.addWidget(status_label)
        
        # Add to layout and track
        self.active_jobs_layout.addWidget(job_widget)
        self.active_job_widgets[apn] = {
            'widget': job_widget,
            'progress_bar': progress_bar,
            'status_label': status_label
        }
        
        self.active_jobs_group.setVisible(True)
    
    def update_job_progress(self, apn: str, status: str, progress: int = -1):
        """Update progress for a specific job"""
        if apn in self.active_job_widgets:
            widgets = self.active_job_widgets[apn]
            widgets['status_label'].setText(status)
            
            if progress >= 0:
                widgets['progress_bar'].setRange(0, 100)
                widgets['progress_bar'].setValue(progress)
    
    def remove_active_job_progress(self, apn: str, final_status: str = "Completed"):
        """Remove progress indicator for a completed job"""
        if apn not in self.active_job_widgets:
            return
        
        widgets = self.active_job_widgets[apn]
        
        # Show completion briefly
        widgets['status_label'].setText(final_status)
        widgets['status_label'].setStyleSheet("color: green; font-size: 10px; font-weight: bold;")
        widgets['progress_bar'].setRange(0, 100)
        widgets['progress_bar'].setValue(100)
        
        # Remove after a short delay
        QTimer.singleShot(2000, lambda: self._remove_job_widget(apn))
    
    def _remove_job_widget(self, apn: str):
        """Actually remove the job widget from display"""
        if apn in self.active_job_widgets:
            widget = self.active_job_widgets[apn]['widget']
            self.active_jobs_layout.removeWidget(widget)
            widget.deleteLater()
            del self.active_job_widgets[apn]
            
            # Hide group if no active jobs
            if not self.active_job_widgets:
                self.active_jobs_group.setVisible(False)
    
    def start_batch_tracking(self, apns):
        """Start tracking a batch collection operation"""
        self.batch_tracker.start_batch(apns)
    
    def update_batch_progress(self, apn, result):
        """Update batch progress for a completed APN"""
        self.batch_tracker.update_batch_progress(apn, result)
    
    def _on_batch_started(self, total_properties):
        """Handle batch started signal"""
        self.batch_progress_group.setVisible(True)
        self.batch_status_label.setText(f"Collecting data for {total_properties} properties...")
        self.batch_progress_bar.setRange(0, total_properties)
        self.batch_progress_bar.setValue(0)
        logger.info(f"Batch progress display started for {total_properties} properties")
    
    def _on_batch_progress(self, completed, total):
        """Handle batch progress update"""
        self.batch_progress_bar.setValue(completed)
        percentage = (completed / total * 100) if total > 0 else 0
        self.batch_status_label.setText(f"Collecting... {completed}/{total} complete ({percentage:.0f}%)")
    
    def _on_batch_completed(self, summary):
        """Handle batch completion"""
        total = summary['total_properties']
        successful = summary['successful']
        failed = summary['failed']
        skipped = summary['skipped']
        time_taken = summary['batch_time_seconds']
        
        # Update final status
        self.batch_status_label.setText(
            f"Batch Complete: {successful} successful, {failed} failed, "
            f"{skipped} skipped in {time_taken:.1f}s"
        )
        self.batch_progress_bar.setValue(total)
        
        # Hide the batch progress group after a delay
        QTimer.singleShot(5000, self._hide_batch_progress)
        
        logger.info(f"Batch collection display completed with summary: {summary}")
    
    def _hide_batch_progress(self):
        """Hide batch progress display"""
        self.batch_progress_group.setVisible(False)
        self.batch_status_label.setText("Batch Status: Ready")


class PropertyDetailsDialog(QDialog):
    """Enhanced property details dialog with background data collection"""
    
    def __init__(self, property_data: Dict, db_managerThreadSafeDatabaseManager, 
                 background_manager: BackgroundDataCollectionManager, parent=None):
        super().__init__(parent)
        self.property_data = property_data
        self.db_manager = db_manager
        self.background_manager = background_manager
        self.setup_ui()
        self.load_property_details()
        
        # Connect to background collection signals for this property
        self.background_manager.job_completed.connect(self._on_background_job_completed)
        
        # Track if we have a collection in progress for this property
        self.collection_in_progress = False
        
        # Check if collection is already in progress
        self._check_collection_status()
        
        # AUTOMATIC DATA COLLECTION: Start comprehensive data collection automatically
        # This eliminates the need for manual button clicks
        self._start_automatic_data_collection()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle(f"Property Details - {self.property_data.get('apn', 'Unknown')}")
        self.setModal(True)
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        
        # Add background collection status
        self.status_widget = BackgroundCollectionStatusWidget()
        layout.addWidget(self.status_widget)
        
        # Create tab widget for different sections
        tab_widget = QTabWidget()
        
        # Basic info tab
        basic_tab = QWidget()
        self.setup_basic_info_tab(basic_tab)
        tab_widget.addTab(basic_tab, "Basic Information")
        
        # Tax history tab
        tax_tab = QWidget()
        self.setup_tax_history_tab(tax_tab)
        tab_widget.addTab(tax_tab, "Tax History")
        
        # Sales history tab
        sales_tab = QWidget()
        self.setup_sales_history_tab(sales_tab)
        tab_widget.addTab(sales_tab, "Sales History")
        
        layout.addWidget(tab_widget)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Auto-collect button (using background system)
        auto_collect_btn = QPushButton("Auto-Collect Data (Background)")
        auto_collect_btn.clicked.connect(self.auto_collect_data)
        button_layout.addWidget(auto_collect_btn)
        
        # Manual collect button (immediate)
        manual_collect_btn = QPushButton("Manual Collect (Immediate)")
        manual_collect_btn.clicked.connect(self.manual_collect_data)
        button_layout.addWidget(manual_collect_btn)
        
        # Refresh button for current property data (NEW)
        refresh_btn = QPushButton("Refresh Property Data")
        refresh_btn.clicked.connect(self.refresh_property_data)
        button_layout.addWidget(refresh_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Update status initially and setup periodic updates
        if self.background_manager:
            status = self.background_manager.get_collection_status()
            self.status_widget.update_status(status)
            
            # Set up timer for status updates
            self.status_timer = QTimer()
            self.status_timer.timeout.connect(self._update_dialog_status)
            self.status_timer.start(2000)  # Update every 2 seconds
    
    def setup_basic_info_tab(self, tab):
        """Setup basic information tab"""
        layout = QVBoxLayout(tab)
        
        # Create form layout for property details
        form_layout = QGridLayout()
        
        fields = [
            ("APN:", "apn"),
            ("Owner Name:", "owner_name"),
            ("Property Address:", "property_address"),
            ("Mailing Address:", "mailing_address"),
            ("Legal Description:", "legal_description"),
            ("Land Use Code:", "land_use_code"),
            ("Year Built:", "year_built"),
            ("Living Area (sq ft):", "living_area_sqft"),
            ("Lot Size (sq ft):", "lot_size_sqft"),
            ("Bedrooms:", "bedrooms"),
            ("Bathrooms:", "bathrooms"),
            ("Pool:", "pool"),
            ("Garage Spaces:", "garage_spaces")
        ]
        
        for i, (label_text, field_key) in enumerate(fields):
            label = QLabel(label_text)
            label.setFont(QFont("Arial", 10, QFont.Bold))
            
            value = self.property_data.get(field_key, "N/A")
            if field_key == "pool":
                value = "Yes" if value else "No"
            
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            
            form_layout.addWidget(label, i, 0)
            form_layout.addWidget(value_label, i, 1)
        
        layout.addLayout(form_layout)
        layout.addStretch()
    
    def setup_tax_history_tab(self, tab):
        """Setup tax history tab"""
        layout = QVBoxLayout(tab)
        
        # Add status label for background collection
        self.tax_status_label = QLabel("Tax data status: Checking...")
        self.tax_status_label.setFont(QFont("Arial", 9))
        layout.addWidget(self.tax_status_label)
        
        self.tax_table = QTableWidget()
        self.tax_table.setColumnCount(5)
        self.tax_table.setHorizontalHeaderLabels([
            "Tax Year", "Assessed Value", "Limited Value", "Tax Amount", "Payment Status"
        ])
        
        layout.addWidget(self.tax_table)
    
    def setup_sales_history_tab(self, tab):
        """Setup sales history tab"""
        layout = QVBoxLayout(tab)
        
        # Add status label for background collection
        self.sales_status_label = QLabel("Sales data status: Checking...")
        self.sales_status_label.setFont(QFont("Arial", 9))
        layout.addWidget(self.sales_status_label)
        
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(6)
        self.sales_table.setHorizontalHeaderLabels([
            "Sale Date", "Sale Price", "Seller", "Buyer", "Deed Type", "Recording Number"
        ])
        
        layout.addWidget(self.sales_table)
    
    def load_property_details(self):
        """Load detailed property information"""
        apn = self.property_data.get('apn')
        if not apn:
            return
        
        logger.info(f"PropertyDetailsDialog loading data for APN: {apn}")
        
        # Load tax history
        tax_history = self.db_manager.get_tax_history(apn)
        if tax_history:
            self.tax_status_label.setText(f"Tax data: {len(tax_history)} records found")
            self.tax_status_label.setStyleSheet("color: green;")
        else:
            self.tax_status_label.setText("Tax data: No records found - will auto-collect in background")
            self.tax_status_label.setStyleSheet("color: orange;")
            
        self.populate_tax_table(tax_history)
        
        # Load sales history
        sales_history = self.db_manager.get_sales_history(apn)
        if sales_history:
            self.sales_status_label.setText(f"Sales data: {len(sales_history)} records found")
            self.sales_status_label.setStyleSheet("color: green;")
        else:
            self.sales_status_label.setText("Sales data: No records found - will auto-collect in background")
            self.sales_status_label.setStyleSheet("color: orange;")
            
        self.populate_sales_table(sales_history)
    
    def auto_collect_data(self):
        """Request background data collection for this property with enhanced feedback"""
        apn = self.property_data.get('apn')
        if not apn or not self.background_manager:
            return
        
        if not self.background_manager.is_running():
            reply = QMessageBox.question(self, "Background Collection", 
                                       "Background data collection is not running. "
                                       "Would you like to start it now?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.background_manager.start_collection()
                # Brief delay to allow worker to start
                QTimer.singleShot(500, self.auto_collect_data)
            return
        
        # Request critical priority collection for this APN (user-initiated)
        success = self.background_manager.collect_data_for_apn(apn, JobPriority.CRITICAL)
        
        if success:
            self.collection_in_progress = True
            self._update_collection_progress_display()
            
            # Show success message
            QMessageBox.information(self, "Data Collection Started", 
                                   f"High-priority data collection started for APN {apn}. "
                                   "Progress will be shown below and the dialog will refresh automatically.")
        else:
            QMessageBox.information(self, "Data Collection", 
                                   f"APN {apn} is already being processed or has very recent data.")
    
    def manual_collect_data(self):
        """Immediate data collection (blocking)"""
        apn = self.property_data.get('apn')
        if not apn:
            return
        
        # Show progress dialog
        from PyQt5.QtWidgets import QProgressDialog
        from PyQt5.QtCore import Qt
        
        progress = QProgressDialog("Collecting property data...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        progress.setValue(10)
        
        try:
            # Import the automatic data collector
            from automatic_data_collector import MaricopaDataCollector
            
            progress.setValue(30)
            progress.setLabelText("Initializing collector...")
            
            # Create collector and fetch data
            collector = MaricopaDataCollector(self.db_manager)
            progress.setValue(50)
            progress.setLabelText("Collecting data...")
            
            # Collect data synchronously
            result = collector.collect_data_for_apn_sync(apn)
            progress.setValue(90)
            progress.setLabelText("Saving to database...")
            
            if result and (result.get('tax_data_collected') or result.get('sales_data_collected')):
                # Refresh the dialog with new data
                self.load_property_details()
                progress.setValue(100)
                progress.setLabelText("Data collection complete!")
                
                QMessageBox.information(self, "Success", 
                                      f"Successfully collected data for APN {apn}\n\n"
                                      f"Tax records: {len(result.get('tax_records', []))}\n"
                                      f"Sales records: {len(result.get('sales_records', []))}")
            else:
                QMessageBox.warning(self, "Warning", 
                                  f"Could not collect complete data for APN {apn}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error collecting data: {str(e)}")
        
        finally:
            progress.close()
    
    def _start_automatic_data_collection(self):
        """
        Automatically start comprehensive data collection for this property
        This eliminates the need for manual button clicks
        """
        apn = self.property_data.get('apn')
        if not apn or not self.background_manager:
            return
        
        # Ensure background collection is running
        if not self.background_manager.is_running():
            logger.info("Starting background collection for automatic data collection")
            self.background_manager.start_collection()
            # Brief delay to allow worker to start, then retry
            QTimer.singleShot(1000, self._start_automatic_data_collection)
            return
        
        # Check if we already have recent data to avoid unnecessary collection
        existing_data = self._check_existing_data_freshness(apn)
        
        if existing_data['needs_collection']:
            # Request critical priority collection for this APN (automatic)
            success = self.background_manager.collect_data_for_apn(apn, JobPriority.CRITICAL)
            
            if success:
                self.collection_in_progress = True
                self._update_collection_progress_display()
                logger.info(f"Automatic data collection started for APN {apn}")
                
                # Update status to show automatic collection is in progress
                if hasattr(self, 'status_widget'):
                    self.status_widget.show_message("Automatically collecting comprehensive property data...", "info")
            else:
                logger.info(f"APN {apn} already has recent data or collection in progress")
        else:
            logger.info(f"APN {apn} has fresh data, skipping automatic collection")
    
    def _check_existing_data_freshness(self, apn: str) -> Dict[str, Any]:
        """
        Check if existing data is fresh enough to skip collection
        Returns dict with 'needs_collection' boolean and details
        """
        try:
            # Check tax history freshness
            tax_records = self.db_manager.get_tax_history(apn)
            has_recent_tax = len(tax_records) > 0
            
            # Check sales history freshness  
            sales_records = self.db_manager.get_sales_history(apn)
            has_recent_sales = len(sales_records) > 0
            
            # Check property details freshness
            property_details = self.db_manager.get_property_details(apn)
            has_property_details = property_details is not None
            
            # If we have some data, we might still want to collect more comprehensive data
            # For automatic collection, we'll be more aggressive about collecting
            needs_collection = not (has_recent_tax and has_recent_sales and has_property_details)
            
            return {
                'needs_collection': needs_collection,
                'has_tax_data': has_recent_tax,
                'has_sales_data': has_recent_sales,
                'has_property_details': has_property_details
            }
            
        except Exception as e:
            logger.error(f"Error checking data freshness for APN {apn}: {e}")
            # If we can't check, assume we need collection
            return {'needs_collection': True}
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        # Stop the status timer
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        event.accept()
    
    def _on_background_job_completed(self, apn: str, result: Dict):
        """Handle background job completion with enhanced feedback"""
        if apn == self.property_data.get('apn'):
            logger.info(f"Background collection completed for APN {apn}, refreshing dialog")
            self.collection_in_progress = False
            
            # Refresh the dialog data
            self.load_property_details()
            
            # Update status labels with success
            tax_count = len(result.get('tax_records', []))
            sales_count = len(result.get('sales_records', []))
            
            if hasattr(self, 'tax_status_label'):
                self.tax_status_label.setText(f"Tax data: {tax_count} records collected ✓")
                self.tax_status_label.setStyleSheet("color: green; font-weight: bold;")
                
            if hasattr(self, 'sales_status_label'):
                self.sales_status_label.setText(f"Sales data: {sales_count} records collected ✓")
                self.sales_status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # Show brief success notification (non-blocking)
            self.setWindowTitle(f"Property Details - {apn} [Data Updated ✓]")
            
            # Reset title after 3 seconds
            QTimer.singleShot(3000, lambda: self.setWindowTitle(f"Property Details - {apn}"))
    
    def _check_collection_status(self):
        """Check if collection is currently in progress for this property"""
        if not self.background_manager or not self.background_manager.worker:
            return
            
        apn = self.property_data.get('apn')
        if not apn:
            return
            
        # Check if this APN is in active jobs
        status = self.background_manager.get_collection_status()
        active_jobs = status.get('active_jobs', 0)
        
        if active_jobs > 0 and self.background_manager.worker:
            # Check if our APN is in the active jobs
            if apn in self.background_manager.worker.active_jobs:
                self.collection_in_progress = True
                self._update_collection_progress_display()
    
    def _update_collection_progress_display(self):
        """Update the display to show collection in progress"""
        if self.collection_in_progress:
            apn = self.property_data.get('apn')
            
            if hasattr(self, 'tax_status_label'):
                self.tax_status_label.setText("Tax data: Collection in progress... 🔄")
                self.tax_status_label.setStyleSheet("color: blue; font-style: italic;")
                
            if hasattr(self, 'sales_status_label'):
                self.sales_status_label.setText("Sales data: Collection in progress... 🔄")
                self.sales_status_label.setStyleSheet("color: blue; font-style: italic;")
    
    def refresh_property_data(self):
        """Force refresh property data by clearing cache and reloading details"""
        apn = self.property_data.get('apn')
        if not apn:
            return
        
        # Clear any cached data for this property
        if self.background_manager and self.background_manager.worker:
            self.background_manager.worker.cache.clear_apn_cache(apn)
            logger.info(f"Cleared cache for APN {apn}")
        
        # Show progress dialog
        from PyQt5.QtWidgets import QProgressDialog
        from PyQt5.QtCore import Qt
        
        progress = QProgressDialog("Refreshing property data...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        progress.setValue(30)
        
        try:
            # Force collection of fresh data
            if self.background_manager and self.background_manager.is_running():
                progress.setValue(60)
                progress.setLabelText("Queuing fresh data collection...")
                
                # Force collection by requesting with CRITICAL priority
                success = self.background_manager.collect_data_for_apn(apn, JobPriority.CRITICAL, force_refresh=True)
                
                if success:
                    progress.setValue(90)
                    progress.setLabelText("Collection queued - dialog will refresh automatically...")
                    QMessageBox.information(self, "Refresh Started", 
                                           f"Fresh data collection started for APN {apn}. "
                                           "The dialog will refresh automatically when complete.")
                else:
                    progress.setValue(100)
                    # Fallback to immediate refresh of what we have
                    self.load_property_details()
                    QMessageBox.information(self, "Data Refreshed", "Property data has been refreshed with current database contents.")
            else:
                progress.setValue(100)
                # Just reload from database if background collection isn't running
                self.load_property_details()
                QMessageBox.information(self, "Data Refreshed", "Property data has been refreshed with current database contents.")
        
        except Exception as e:
            logger.error(f"Error refreshing property data for APN {apn}: {e}")
            QMessageBox.critical(self, "Refresh Error", f"Error refreshing property data: {str(e)}")
        
        finally:
            progress.close()
    
    def _update_dialog_status(self):
        """Periodically update dialog status"""
        if self.background_manager:
            status = self.background_manager.get_collection_status()
            self.status_widget.update_status(status)
            
            # Check if our collection completed
            if self.collection_in_progress:
                apn = self.property_data.get('apn')
                if apn and self.background_manager.worker:
                    if apn not in self.background_manager.worker.active_jobs:
                        # Collection completed, refresh
                        self.collection_in_progress = False
                        self.load_property_details()
    
    def populate_tax_table(self, tax_history: List[Dict]):
        """Populate tax history table"""
        if not tax_history:
            # Create placeholder row
            tax_history = [{
                'tax_year': 'No Data Available',
                'assessed_value': None,
                'limited_value': None,
                'tax_amount': None,
                'payment_status': 'Use Auto-Collect or Manual Collect buttons above'
            }]
        
        self.tax_table.setRowCount(len(tax_history))
        
        for i, record in enumerate(tax_history):
            self.tax_table.setItem(i, 0, QTableWidgetItem(str(record.get('tax_year', ''))))
            
            # Handle assessed_value
            assessed_value = record.get('assessed_value')
            assessed_text = f"${assessed_value:,.2f}" if assessed_value is not None else "N/A"
            self.tax_table.setItem(i, 1, QTableWidgetItem(assessed_text))
            
            # Handle limited_value
            limited_value = record.get('limited_value')
            limited_text = f"${limited_value:,.2f}" if limited_value is not None else "N/A"
            self.tax_table.setItem(i, 2, QTableWidgetItem(limited_text))
            
            # Handle tax_amount
            tax_amount = record.get('tax_amount')
            tax_text = f"${tax_amount:,.2f}" if tax_amount is not None else "N/A"
            self.tax_table.setItem(i, 3, QTableWidgetItem(tax_text))
            
            self.tax_table.setItem(i, 4, QTableWidgetItem(record.get('payment_status', '') or 'N/A'))
        
        self.tax_table.resizeColumnsToContents()
    
    def populate_sales_table(self, sales_history: List[Dict]):
        """Populate sales history table"""
        if not sales_history:
            # Create placeholder row
            sales_history = [{
                'sale_date': 'No Data Available',
                'sale_price': None,
                'seller_name': 'Use Auto-Collect or Manual Collect',
                'buyer_name': 'buttons above to fetch data',
                'deed_type': '',
                'recording_number': ''
            }]
        
        self.sales_table.setRowCount(len(sales_history))
        
        for i, record in enumerate(sales_history):
            self.sales_table.setItem(i, 0, QTableWidgetItem(str(record.get('sale_date', ''))))
            
            # Handle sale_price
            sale_price = record.get('sale_price')
            price_text = f"${sale_price:,.2f}" if sale_price is not None else "N/A"
            self.sales_table.setItem(i, 1, QTableWidgetItem(price_text))
            
            self.sales_table.setItem(i, 2, QTableWidgetItem(record.get('seller_name', '')))
            self.sales_table.setItem(i, 3, QTableWidgetItem(record.get('buyer_name', '')))
            self.sales_table.setItem(i, 4, QTableWidgetItem(record.get('deed_type', '')))
            self.sales_table.setItem(i, 5, QTableWidgetItem(record.get('recording_number', '')))
        
        self.sales_table.resizeColumnsToContents()


class EnhancedPropertySearchApp(QMainWindow):
    """Enhanced main application window with background data collection"""
    
    def __init__(self, config_manager):
        super().__init__()
        logger.info("Initializing Enhanced Property Search Application GUI")
        
        self.config = config_manager
        
        try:
            # Initialize components
            logger.debug("Initializing database manager")
            self.db_manager = ThreadSafeDatabaseManager(config_manager)
            
            # Initialize API client
            try:
                logger.debug("Attempting to initialize real API client")
                self.api_client = UnifiedMaricopaAPIClient(config_manager)
                logger.info("Using real Maricopa API client")
            except Exception as e:
                logger.warning(f"Failed to initialize real API client: {e}. Using mock client.")
                self.api_client = MockMaricopaAPIClient(config_manager)
            
            # Initialize web scraper
            try:
                self.scraper = WebScraperManager(config_manager)
                logger.info("Using real web scraper")
            except Exception as e:
                logger.warning(f"Failed to initialize real web scraper: {e}. Using mock scraper.")
                self.scraper = MockWebScraperManager(config_manager)
            
            # Initialize background data collection manager
            self.background_manager = BackgroundDataCollectionManager(self.db_manager)
            logger.info("Background data collection manager initialized")
            
            # Initialize user action logger
            self.user_logger = get_user_action_logger()
            logger.info("User action logger initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize core components: {e}")
            raise
        
        self.search_worker = None
        self.current_results = []
        
        self.setup_ui()
        self.setup_connections()
        self.setup_status_bar()
        self.check_system_status()
        
        # Auto-start background collection with delay to ensure UI is ready
        QTimer.singleShot(1000, self._delayed_background_start)
        logger.info("Background data collection scheduled to start automatically")
    
    def _delayed_background_start(self):
        """Start background collection after UI is fully initialized"""
        try:
            self.background_manager.start_collection()
            logger.info("Background data collection started successfully")
            
            # Update UI to reflect the started collection
            QTimer.singleShot(500, self.update_background_status)
        except Exception as e:
            logger.error(f"Failed to start background collection: {e}")
            self.status_bar.showMessage("Background collection failed to start - check logs")
    
    def setup_ui(self):
        """Setup the main user interface"""
        self.setWindowTitle("Maricopa County Property Search - Enhanced")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Add background collection status widget
        self.bg_status_widget = BackgroundCollectionStatusWidget()
        self.bg_status_widget.start_stop_btn.clicked.connect(self.toggle_background_collection)
        main_layout.addWidget(self.bg_status_widget)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Create search section
        search_group = QGroupBox("Property Search")
        search_layout = QGridLayout(search_group)
        
        # Search type combo
        search_layout.addWidget(QLabel("Search Type:"), 0, 0)
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Property Address", "Owner Name", "APN"])
        search_layout.addWidget(self.search_type_combo, 0, 1)
        
        # Search term input
        search_layout.addWidget(QLabel("Search Term:"), 1, 0)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter owner name, address, or APN...")
        search_layout.addWidget(self.search_input, 1, 1, 1, 2)
        
        # Search button
        self.search_btn = QPushButton("Search")
        self.search_btn.setDefault(True)
        search_layout.addWidget(self.search_btn, 1, 3)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        search_layout.addWidget(self.progress_bar, 2, 0, 1, 4)
        
        main_layout.addWidget(search_group)
        
        # Create results section
        results_group = QGroupBox("Search Results")
        results_layout = QVBoxLayout(results_group)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        self.setup_results_table()
        results_layout.addWidget(self.results_table)
        
        # Results controls
        controls_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("Export Results")
        self.export_btn.setEnabled(False)
        controls_layout.addWidget(self.export_btn)
        
        self.view_details_btn = QPushButton("View Details")
        self.view_details_btn.setEnabled(False)
        controls_layout.addWidget(self.view_details_btn)
        
        # Manual refresh button (NEW)
        self.refresh_btn = QPushButton("Refresh Current")
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setToolTip("Refresh data for currently displayed results")
        controls_layout.addWidget(self.refresh_btn)
        
        # Batch collection button with enhanced styling
        self.collect_all_btn = QPushButton("Collect All Data")
        self.collect_all_btn.setEnabled(False)
        self.collect_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        self.collect_all_btn.setToolTip("Collect complete property data for ALL visible search results")
        controls_layout.addWidget(self.collect_all_btn)
        
        # Force collection button (NEW)
        self.force_collect_btn = QPushButton("Force Collect")
        self.force_collect_btn.setEnabled(False)
        self.force_collect_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        self.force_collect_btn.setToolTip("Force data collection ignoring cache")
        controls_layout.addWidget(self.force_collect_btn)
        
        controls_layout.addStretch()
        
        self.results_label = QLabel("No search performed")
        controls_layout.addWidget(self.results_label)
        
        results_layout.addLayout(controls_layout)
        
        main_layout.addWidget(results_group)
        
        # Create menu bar
        self.setup_menu_bar()
        
        # Create settings dialog
        self.settings_dialog = None
        
        # Set up periodic status updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_background_status)
        self.status_timer.start(2000)  # Update every 2 seconds
    
    def setup_results_table(self):
        """Setup the results table"""
        headers = ["APN", "Owner Name", "Property Address", "Year Built", 
                  "Lot Size (SQFT)", "Data Status", "Last Updated"]
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)
        
        # Set column widths
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # APN
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Owner Name
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Address
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Year Built
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Lot Size
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Data Status
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Last Updated
    
    def setup_connections(self):
        """Setup signal-slot connections"""
        self.search_btn.clicked.connect(self.perform_search)
        self.search_input.returnPressed.connect(self.perform_search)
        self.export_btn.clicked.connect(self.export_results)
        self.view_details_btn.clicked.connect(self.view_property_details)
        self.collect_all_btn.clicked.connect(self.collect_all_data)
        self.results_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.results_table.doubleClicked.connect(self.view_property_details)
        self.refresh_btn.clicked.connect(self.refresh_current_data)
        self.force_collect_btn.clicked.connect(self.force_data_collection)
        
        # Connect background collection signals
        self.background_manager.progress_updated.connect(self.update_background_status)
        self.background_manager.job_completed.connect(self.on_background_job_completed)
        
        # Connect to background manager signals for enhanced progress
        self.background_manager.collection_started.connect(self._setup_worker_connections)
        
        # Connect batch completion to button reset
        self.bg_status_widget.batch_tracker.batch_completed.connect(self._on_batch_collection_completed)
    
    def _setup_worker_connections(self):
        """Setup connections to worker signals when collection starts"""
        if self.background_manager.worker:
            self.background_manager.worker.job_started.connect(self.on_background_job_started)
            self.background_manager.worker.job_failed.connect(self.on_background_job_failed)
            logger.info("Connected to background worker progress signals")
    
    def setup_menu_bar(self):
        """Setup application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        export_action = QAction("Export Results...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings Menu (NEW)
        settings_menu = menubar.addMenu("Settings")
        
        settings_action = QAction("Application Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings_dialog)
        settings_menu.addAction(settings_action)
        
        settings_menu.addSeparator()
        
        # Data Collection Settings
        collection_settings_action = QAction("Data Collection Settings...", self)
        collection_settings_action.triggered.connect(self.show_collection_settings_dialog)
        settings_menu.addAction(collection_settings_action)
        
        # Cache Management
        cache_settings_action = QAction("Cache Management...", self)
        cache_settings_action.triggered.connect(self.show_cache_management_dialog)
        settings_menu.addAction(cache_settings_action)
        
        # Collection menu
        collection_menu = menubar.addMenu("Data Collection")
        
        start_collection_action = QAction("Start Background Collection", self)
        start_collection_action.triggered.connect(lambda: self.background_manager.start_collection())
        collection_menu.addAction(start_collection_action)
        
        stop_collection_action = QAction("Stop Background Collection", self)
        stop_collection_action.triggered.connect(lambda: self.background_manager.stop_collection())
        collection_menu.addAction(stop_collection_action)
        
        collection_menu.addSeparator()
        
        # Manual Refresh Options (NEW)
        refresh_current_action = QAction("Refresh Current Results", self)
        refresh_current_action.setShortcut("F5")
        refresh_current_action.triggered.connect(self.refresh_current_data)
        collection_menu.addAction(refresh_current_action)
        
        force_collect_action = QAction("Force Data Collection", self)
        force_collect_action.setShortcut("Ctrl+F5")
        force_collect_action.triggered.connect(self.force_data_collection)
        collection_menu.addAction(force_collect_action)
        
        clear_cache_action = QAction("Clear Cache", self)
        clear_cache_action.triggered.connect(self.clear_cache)
        collection_menu.addAction(clear_cache_action)
        
        collection_menu.addSeparator()
        
        stats_action = QAction("Collection Statistics", self)
        stats_action.triggered.connect(self.show_collection_stats)
        collection_menu.addAction(stats_action)
        
        # Batch Processing Menu (NEW)
        batch_menu = menubar.addMenu("Batch Processing")
        
        batch_search_action = QAction("Batch Search...", self)
        batch_search_action.setShortcut("Ctrl+B")
        batch_search_action.triggered.connect(self.show_batch_search_dialog)
        batch_menu.addAction(batch_search_action)
        
        batch_menu.addSeparator()
        
        # Parallel Processing Controls
        parallel_config_action = QAction("Parallel Processing Settings...", self)
        parallel_config_action.triggered.connect(self.show_parallel_processing_dialog)
        batch_menu.addAction(parallel_config_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        db_stats_action = QAction("Database Statistics", self)
        db_stats_action.triggered.connect(self.show_database_stats)
        tools_menu.addAction(db_stats_action)
        
        # Data Source Configuration (NEW)
        data_source_action = QAction("Data Source Configuration...", self)
        data_source_action.triggered.connect(self.show_data_source_dialog)
        tools_menu.addAction(data_source_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def check_system_status(self):
        """Check system component status"""
        status_messages = []
        
        # Check database connection
        if self.db_manager.test_connection():
            status_messages.append("DB: Connected")
        else:
            status_messages.append("DB: Disconnected")
        
        # Check API status
        try:
            api_status = self.api_client.get_api_status()
            status_messages.append(f"API: {api_status.get('status', 'Unknown')}")
        except:
            status_messages.append("API: Error")
        
        # Check background collection status
        bg_status = "Running" if self.background_manager.is_running() else "Stopped"
        status_messages.append(f"BG Collection: {bg_status}")
        
        self.status_bar.showMessage(" | ".join(status_messages))
    
    def toggle_background_collection(self):
        """Toggle background data collection"""
        if self.background_manager.is_running():
            self.background_manager.stop_collection()
            logger.info("Background collection stopped by user")
        else:
            self.background_manager.start_collection()
            logger.info("Background collection started by user")
        
        self.check_system_status()
    
    def update_background_status(self, status_dict=None):
        """Update background collection status display"""
        if status_dict is None:
            status_dict = self.background_manager.get_collection_status()
        
        self.bg_status_widget.update_status(status_dict)
        self.check_system_status()
    
    def perform_search(self):
        """Perform property search with background enhancement"""
        search_term = self.search_input.text().strip()
        search_type = self.search_type_combo.currentText()
        
        # Log user search action
        self.user_logger.log_search(search_type, search_term)
        
        if not search_term:
            QMessageBox.warning(self, "Warning", "Please enter a search term.")
            return
        
        search_type_text = self.search_type_combo.currentText()
        search_type = search_type_text.lower().replace(" ", "_")
        if search_type == "property_address":
            search_type = "address"
        elif search_type == "owner_name":
            search_type = "owner"
        
        # Disable controls during search
        self.search_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start enhanced search worker
        self.search_worker = EnhancedSearchWorker(
            search_type, search_term, self.db_manager, 
            self.api_client, self.scraper, self.background_manager
        )
        
        # Connect signals
        self.search_worker.progress_updated.connect(self.progress_bar.setValue)
        self.search_worker.status_updated.connect(self.status_bar.showMessage)
        self.search_worker.results_ready.connect(self.display_results)
        self.search_worker.error_occurred.connect(self.handle_search_error)
        self.search_worker.background_collection_started.connect(self.on_background_collection_started)
        
        self.search_worker.start()
    
    def display_results(self, results: List[Dict]):
        """Display search results with data collection status"""
        self.current_results = results
        
        # Log search results count
        search_type = self.search_type_combo.currentText()
        search_term = self.search_input.text().strip()
        self.user_logger.log_action(
            action_type="SEARCH_RESULTS",
            details={
                "search_type": search_type,
                "search_term": search_term,
                "result_count": len(results)
            }
        )
        
        self.results_table.setRowCount(len(results))
        
        for i, result in enumerate(results):
            apn = result.get('apn', '')
            
            # Handle raw_data - it might be a JSON string that needs parsing
            raw_data = result.get('raw_data', {})
            if isinstance(raw_data, str):
                try:
                    import json
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.threadsafe_database_manager import ThreadSafeDatabaseManager
                    raw_data = json.loads(raw_data)
                except (json.JSONDecodeError, TypeError):
                    raw_data = {}
            elif not isinstance(raw_data, dict):
                raw_data = {}
            
            # APN
            self.results_table.setItem(i, 0, QTableWidgetItem(apn))
            
            # Owner Name
            owner_name = (result.get('owner_name') or 
                         raw_data.get('Owner') or 
                         raw_data.get('Ownership') or 
                         'Owner Info Available')
            self.results_table.setItem(i, 1, QTableWidgetItem(str(owner_name)))
            
            # Property Address
            self.results_table.setItem(i, 2, QTableWidgetItem(result.get('property_address', '')))
            
            # Year Built
            year_built = (result.get('year_built') or 
                         raw_data.get('YearBuilt') or
                         raw_data.get('Year Built'))
            
            year_text = str(year_built) if year_built and str(year_built).isdigit() else 'Available'
            self.results_table.setItem(i, 3, QTableWidgetItem(year_text))
            
            # Lot Size
            lot_size = (result.get('lot_size_sqft') or 
                       raw_data.get('LotSize'))
            
            if lot_size is not None:
                try:
                    clean_size = str(lot_size).replace(',', '')
                    lot_size_text = f"{int(float(clean_size)):,}"
                except (ValueError, TypeError):
                    lot_size_text = 'Available'
            else:
                lot_size_text = 'Available'
            self.results_table.setItem(i, 4, QTableWidgetItem(lot_size_text))
            
            # Data Collection Status
            data_status = self._get_data_collection_status(apn)
            status_item = QTableWidgetItem(data_status['text'])
            
            # Color code the status
            if data_status['complete']:
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            elif data_status['collecting']:
                status_item.setBackground(QColor(255, 255, 200))  # Light yellow
            else:
                status_item.setBackground(QColor(255, 220, 220))  # Light red
            
            self.results_table.setItem(i, 5, status_item)
            
            # Last Updated
            last_updated = self._get_last_update_time(apn)
            self.results_table.setItem(i, 6, QTableWidgetItem(last_updated))
        
        # Update UI
        self.results_label.setText(f"Found {len(results)} properties")
        self.export_btn.setEnabled(len(results) > 0)
        self.collect_all_btn.setEnabled(len(results) > 0)
        self.refresh_btn.setEnabled(len(results) > 0)
        self.force_collect_btn.setEnabled(len(results) > 0)
        
        self.search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Search completed")
        
        # Auto-resize columns
        self.results_table.resizeColumnsToContents()
    
    def _get_data_collection_status(self, apn: str) -> Dict[str, Any]:
        """Get data collection status for an APN"""
        try:
            tax_records = self.db_manager.get_tax_history(apn)
            sales_records = self.db_manager.get_sales_history(apn)
            
            # Ensure we have lists to work with
            if not isinstance(tax_records, list):
                tax_records = []
            if not isinstance(sales_records, list):
                sales_records = []
            
            has_tax = len(tax_records) > 0
            has_sales = len(sales_records) > 0
            
            # Check if collection is in progress
            bg_status = self.background_manager.get_collection_status()
            collecting = apn in [job.get('apn', '') for job in bg_status.get('active_jobs', [])]
            
            if has_tax and has_sales:
                return {'text': 'Complete', 'complete': True, 'collecting': False}
            elif collecting:
                return {'text': 'Collecting...', 'complete': False, 'collecting': True}
            elif has_tax or has_sales:
                return {'text': 'Partial', 'complete': False, 'collecting': False}
            else:
                return {'text': 'Queued', 'complete': False, 'collecting': False}
                
        except Exception as e:
            logger.error(f"Error checking data status for {apn}: {e}")
            # Log the actual type of data causing the issue for debugging
            try:
                tax_type = type(self.db_manager.get_tax_history(apn)).__name__
                sales_type = type(self.db_manager.get_sales_history(apn)).__name__
                logger.debug(f"Data types for {apn}: tax_records={tax_type}, sales_records={sales_type}")
            except:
                pass  # Don't let debug logging cause more errors
            
            return {'text': 'Unknown', 'complete': False, 'collecting': False}
    
    def _get_last_update_time(self, apn: str) -> str:
        """Get last update time for an APN"""
        try:
            # This would need to be implemented in the database manager
            # For now, return a placeholder
            return "Recent"
        except:
            return "Unknown"
    
    def handle_search_error(self, error_message: str):
        """Handle search errors"""
        QMessageBox.critical(self, "Search Error", f"Search failed: {error_message}")
        
        self.search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Search failed")
    
    def on_selection_changed(self):
        """Handle table selection changes"""
        selected_rows = self.results_table.selectionModel().selectedRows()
        self.view_details_btn.setEnabled(len(selected_rows) > 0)
    
    def on_background_collection_started(self, jobs_queued: int):
        """Handle notification that background collection started with enhanced feedback"""
        self.status_bar.showMessage(f"Auto-collection: {jobs_queued} properties queued for data enhancement", 3000)
        
        # Show temporary notification
        if jobs_queued > 5:
            QMessageBox.information(self, "Auto-Collection Started", 
                                   f"Automatically queued {jobs_queued} properties for background data collection. "
                                   f"Watch the status panel for individual progress.")
        
        logger.info(f"Auto-collection started for {jobs_queued} properties from search results")
    
    def on_background_job_started(self, apn: str):
        """Handle background job start"""
        # Add progress indicator for this specific job
        self.bg_status_widget.add_active_job_progress(apn)
        
        # Update results table to show "Collecting" status
        self._update_table_status_for_apn(apn, "Collecting...", QColor(255, 255, 200))
        
        logger.info(f"Background data collection started for APN {apn}")
    
    def on_background_job_failed(self, apn: str, error: str):
        """Handle background job failure"""
        # Remove progress indicator with failure status
        self.bg_status_widget.remove_active_job_progress(apn, "Failed")
        
        # Update batch progress if this APN is part of a batch
        if self.bg_status_widget.batch_tracker.is_batch_active():
            failed_result = {'error': error, 'apn': apn}
            self.bg_status_widget.update_batch_progress(apn, failed_result)
        
        # Update results table to show failure
        self._update_table_status_for_apn(apn, "Failed", QColor(255, 200, 200))
        
        logger.warning(f"Background data collection failed for APN {apn}: {error}")
    
    def on_background_job_completed(self, apn: str, result: Dict):
        """Handle background job completion with enhanced feedback"""
        # Remove progress indicator with success status
        self.bg_status_widget.remove_active_job_progress(apn, "Completed")
        
        # Update batch progress if this APN is part of a batch
        if self.bg_status_widget.batch_tracker.is_batch_active():
            self.bg_status_widget.update_batch_progress(apn, result)
        
        # Refresh the results table for the completed APN
        data_status = self._get_data_collection_status(apn)
        color = QColor(200, 255, 200) if data_status['complete'] else QColor(255, 255, 200)
        self._update_table_status_for_apn(apn, data_status['text'], color)
        
        # Show brief status message
        tax_records = result.get('tax_records', [])
        sales_records = result.get('sales_records', [])
        
        # Ensure we have lists to work with for length calculation
        if not isinstance(tax_records, list):
            tax_records = []
        if not isinstance(sales_records, list):
            sales_records = []
            
        tax_count = len(tax_records)
        sales_count = len(sales_records)
        self.status_bar.showMessage(
            f"Completed data collection for APN {apn} - "
            f"Tax: {tax_count}, Sales: {sales_count}", 5000
        )
        
        logger.info(f"Updated table display for completed collection: APN {apn}")
    
    def _update_table_status_for_apn(self, apn: str, status_text: str, background_color: QColor):
        """Update the results table status for a specific APN"""
        for i in range(self.results_table.rowCount()):
            table_apn = self.results_table.item(i, 0).text()
            if table_apn == apn:
                status_item = QTableWidgetItem(status_text)
                status_item.setBackground(background_color)
                self.results_table.setItem(i, 5, status_item)
                
                # Also update the last updated column
                last_updated_item = QTableWidgetItem(datetime.now().strftime("%H:%M:%S"))
                self.results_table.setItem(i, 6, last_updated_item)
                break
    
    def collect_all_data(self):
        """Queue all current search results for batch data collection with enhanced progress tracking"""
        if not self.current_results:
            QMessageBox.warning(self, "Warning", "No search results to collect data for.")
            return
        
        # Check if batch is already active
        if self.bg_status_widget.batch_tracker.is_batch_active():
            reply = QMessageBox.question(self, "Batch Collection", 
                                       "A batch collection is already in progress. "
                                       "Do you want to cancel it and start a new one?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.bg_status_widget.batch_tracker.cancel_batch()
            else:
                return
        
        if not self.background_manager.is_running():
            reply = QMessageBox.question(self, "Background Collection", 
                                       "Background data collection is not running. "
                                       "Would you like to start it now?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.background_manager.start_collection()
                # Give worker time to start
                QTimer.singleShot(500, self._do_collect_all_data)
            else:
                return
        else:
            self._do_collect_all_data()
    
    def _do_collect_all_data(self):
        """Actually perform the batch data collection with smart filtering"""
        if not self.background_manager.worker:
            QMessageBox.warning(self, "Warning", "Background worker not available.")
            return
        
        # Get all APNs from current results
        all_apns = [result.get('apn') for result in self.current_results if result.get('apn')]
        
        if not all_apns:
            QMessageBox.warning(self, "Warning", "No valid APNs found in search results.")
            return
        
        # Filter APNs to avoid duplicates and recent collections
        apns_to_collect = []
        skipped_reasons = {'already_processing': 0, 'recent_data': 0, 'already_complete': 0}
        
        for apn in all_apns:
            # Check if already being processed
            if apn in self.background_manager.worker.active_jobs:
                skipped_reasons['already_processing'] += 1
                continue
                
            # Check if recently cached
            if self.background_manager.worker.cache.is_cached(apn):
                skipped_reasons['recent_data'] += 1
                continue
                
            # Check completeness of existing data
            try:
                tax_records = self.db_manager.get_tax_history(apn)
                sales_records = self.db_manager.get_sales_history(apn)
                
                # Skip if we have comprehensive data
                if len(tax_records) >= 3 and len(sales_records) >= 1:
                    skipped_reasons['already_complete'] += 1
                    continue
                    
            except Exception as e:
                logger.warning(f"Error checking data completeness for {apn}: {e}")
            
            apns_to_collect.append(apn)
        
        # Show confirmation dialog with details
        total_properties = len(all_apns)
        to_collect = len(apns_to_collect)
        skipped_total = sum(skipped_reasons.values())
        
        confirmation_msg = f"""
        Batch Data Collection Summary:
        
        Total Properties: {total_properties}
        Will Collect: {to_collect}
        Will Skip: {skipped_total}
        
        Skip Reasons:
        • Already Processing: {skipped_reasons['already_processing']}
        • Recent Data Available: {skipped_reasons['recent_data']}
        • Complete Data Available: {skipped_reasons['already_complete']}
        
        This will queue {to_collect} properties for high-priority data collection.
        
        Proceed with batch collection?
        """
        
        if to_collect == 0:
            QMessageBox.information(self, "Batch Collection", 
                                   f"All {total_properties} properties already have current data or are being processed.")
            return
        
        reply = QMessageBox.question(self, "Confirm Batch Collection", confirmation_msg,
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
        
        # Disable the button to prevent duplicate requests
        self.collect_all_btn.setEnabled(False)
        self.collect_all_btn.setText("Batch Collection Active...")
        
        # Start batch tracking
        self.bg_status_widget.start_batch_tracking(apns_to_collect)
        
        # Use the enhanced batch collection method
        batch_result = self.background_manager.collect_batch_data(apns_to_collect, JobPriority.HIGH)
        jobs_added = batch_result.get('jobs_added', 0)
        
        if jobs_added > 0:
            # Update status bar
            self.status_bar.showMessage(f"Batch collection started: {jobs_added} properties queued")
            
            # Show success message
            QMessageBox.information(self, "Batch Collection Started", 
                                   f"Successfully started batch collection for {jobs_added} properties.\n\n"
                                   f"Progress will be shown in the status panel above.\n"
                                   f"Individual property statuses will update in the results table.")
            
            logger.info(f"Batch collection initiated for {jobs_added} properties")
        else:
            QMessageBox.warning(self, "Warning", "No properties were queued for collection.")
            self._reset_collect_all_button()
    
    def _reset_collect_all_button(self):
        """Reset the collect all button to its default state"""
        self.collect_all_btn.setEnabled(True)
        self.collect_all_btn.setText("Collect All Data")
    
    def _on_batch_collection_completed(self, summary: Dict):
        """Handle batch collection completion"""
        # Reset the button
        self._reset_collect_all_button()
        
        # Show completion summary
        total = summary['total_properties']
        successful = summary['successful']
        failed = summary['failed']
        skipped = summary['skipped']
        time_taken = summary['batch_time_seconds']
        
        completion_msg = f"""
        Batch Collection Complete!
        
        Total Properties: {total}
        Successful: {successful}
        Failed: {failed}
        Skipped: {skipped}
        
        Time Taken: {time_taken:.1f} seconds
        Average per Property: {(time_taken / max(total, 1)):.1f}s
        
        Results table has been updated with the latest data.
        """
        
        # Show non-blocking notification
        QMessageBox.information(self, "Batch Collection Complete", completion_msg)
        
        # Update status bar
        self.status_bar.showMessage(
            f"Batch collection completed: {successful} successful, {failed} failed", 10000
        )
        
        logger.info(f"Batch collection completed with summary: {summary}")
    
    def view_property_details(self):
        """View detailed property information with background collection support"""
        selected_rows = self.results_table.selectionModel().selectedRows()
        
        if not selected_rows:
            return
        
        row_index = selected_rows[0].row()
        if row_index < len(self.current_results):
            property_data = self.current_results[row_index]
            
            dialog = PropertyDetailsDialog(property_data, self.db_manager, 
                                         self.background_manager, self)
            dialog.exec_()
    
    def show_collection_stats(self):
        """Show collection statistics"""
        status = self.background_manager.get_collection_status()
        stats = status.get('statistics', {})
        cache_stats = status.get('cache_stats', {})
        
        stats_text = "Background Data Collection Statistics:\n\n"
        stats_text += f"Status: {status.get('status', 'Unknown').title()}\n"
        stats_text += f"Pending Jobs: {status.get('pending_jobs', 0)}\n"
        stats_text += f"Active Jobs: {status.get('active_jobs', 0)}\n"
        stats_text += f"Completed Jobs: {status.get('completed_jobs', 0)}\n"
        stats_text += f"Total Jobs: {status.get('total_jobs', 0)}\n\n"
        
        stats_text += f"Success Rate: {stats.get('success_rate_percent', 0):.1f}%\n"
        stats_text += f"Average Processing Time: {stats.get('average_processing_time', 0):.2f}s\n"
        stats_text += f"Cache Hit Rate: {stats.get('cache_hit_rate_percent', 0):.1f}%\n"
        stats_text += f"Cache Entries: {cache_stats.get('total_entries', 0)}\n"
        
        uptime_seconds = stats.get('uptime_seconds', 0)
        uptime_hours = uptime_seconds / 3600
        stats_text += f"Uptime: {uptime_hours:.1f} hours"
        
        QMessageBox.information(self, "Collection Statistics", stats_text)
    
    def export_results(self):
        """Export search results to CSV"""
        if not self.current_results:
            QMessageBox.warning(self, "Warning", "No results to export.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Results", 
            f"property_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    if self.current_results:
                        writer = csv.DictWriter(csvfile, fieldnames=self.current_results[0].keys())
                        writer.writeheader()
                        writer.writerows(self.current_results)
                
                QMessageBox.information(self, "Success", f"Results exported to {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export results: {e}")
    
    def show_database_stats(self):
        """Show database statistics"""
        stats = self.db_manager.get_database_stats()
        
        stats_text = "Database Statistics:\n\n"
        stats_text += f"Properties: {stats.get('properties', 0):,}\n"
        stats_text += f"Tax Records: {stats.get('tax_records', 0):,}\n"
        stats_text += f"Sales Records: {stats.get('sales_records', 0):,}\n"
        stats_text += f"Recent Searches (7 days): {stats.get('recent_searches', 0):,}"
        
        QMessageBox.information(self, "Database Statistics", stats_text)
    
    def show_settings_dialog(self):
        """Show application settings dialog"""
        dialog = ApplicationSettingsDialog(self.config, self)
        dialog.exec_()
    
    def show_collection_settings_dialog(self):
        """Show data collection settings dialog"""
        dialog = DataCollectionSettingsDialog(self.background_manager, self)
        dialog.exec_()
    
    def show_cache_management_dialog(self):
        """Show cache management dialog"""
        dialog = CacheManagementDialog(self.background_manager, self)
        dialog.exec_()
    
    def refresh_current_data(self):
        """Refresh data for currently displayed results"""
        if not self.current_results:
            QMessageBox.warning(self, "Warning", "No search results to refresh.")
            return
        
        reply = QMessageBox.question(self, "Refresh Current Data", 
                                   f"This will refresh data for {len(self.current_results)} properties. "
                                   "This may take some time. Continue?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Extract APNs and refresh them
            apns = [result.get('apn') for result in self.current_results if result.get('apn')]
            if apns:
                # Use batch collection with normal priority for refresh
                batch_result = self.background_manager.collect_batch_data(apns, JobPriority.NORMAL)
                jobs_added = batch_result.get('jobs_added', 0)
                
                if jobs_added > 0:
                    self.status_bar.showMessage(f"Refresh queued: {jobs_added} properties", 5000)
                    QMessageBox.information(self, "Refresh Started", 
                                           f"Queued {jobs_added} properties for data refresh. "
                                           "Progress will be shown in the status panel.")
                else:
                    QMessageBox.information(self, "Refresh Status", 
                                           "All properties already have recent data or are being processed.")
    
    def force_data_collection(self):
        """Force data collection ignoring cache"""
        if not self.current_results:
            QMessageBox.warning(self, "Warning", "No search results to collect data for.")
            return
        
        reply = QMessageBox.question(self, "Force Data Collection", 
                                   f"This will force fresh data collection for {len(self.current_results)} properties, "
                                   "ignoring any cached data. This may take significant time. Continue?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Clear cache for all current APNs first
            apns = [result.get('apn') for result in self.current_results if result.get('apn')]
            
            if self.background_manager and self.background_manager.worker:
                for apn in apns:
                    self.background_manager.worker.cache.clear_apn_cache(apn)
                
                # Now force collection
                batch_result = self.background_manager.collect_batch_data(apns, JobPriority.CRITICAL)
                jobs_added = batch_result.get('jobs_added', 0)
                
                if jobs_added > 0:
                    self.status_bar.showMessage(f"Force collection started: {jobs_added} properties", 5000)
                    QMessageBox.information(self, "Force Collection Started", 
                                           f"Started forced data collection for {jobs_added} properties. "
                                           "All cached data has been cleared. Progress will be shown in the status panel.")
                else:
                    QMessageBox.warning(self, "Force Collection", "No properties could be queued for collection.")
    
    def clear_cache(self):
        """Clear all cached data"""
        reply = QMessageBox.question(self, "Clear Cache", 
                                   "This will clear all cached property data. "
                                   "Future searches may be slower until data is re-collected. Continue?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                if self.background_manager and self.background_manager.worker:
                    cache_cleared = self.background_manager.worker.cache.clear_all_cache()
                    QMessageBox.information(self, "Cache Cleared", 
                                           f"Successfully cleared {cache_cleared} cached entries.")
                    logger.info(f"User cleared {cache_cleared} cache entries")
                else:
                    QMessageBox.warning(self, "Cache Clear", "Background worker not available to clear cache.")
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
                QMessageBox.critical(self, "Cache Clear Error", f"Error clearing cache: {str(e)}")
    
    def show_batch_search_dialog(self):
        """Show batch search dialog"""
        dialog = BatchSearchDialog(self.db_manager, self.api_client, self.scraper, 
                                   self.background_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            # Results were processed, refresh the main interface if needed
            pass
    
    def show_parallel_processing_dialog(self):
        """Show parallel processing configuration dialog"""
        dialog = ParallelProcessingDialog(self.background_manager, self)
        dialog.exec_()
    
    def show_data_source_dialog(self):
        """Show data source configuration dialog"""
        dialog = DataSourceConfigurationDialog(self.config, self.api_client, self.scraper, self)
        dialog.exec_()
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        Maricopa County Property Search - Enhanced
        Version 2.0 with Background Data Collection
        
        A comprehensive property search application for Maricopa County, Arizona.
        
        NEW Features:
        • Automatic background data collection for search results
        • Non-blocking UI with real-time progress updates
        • Intelligent caching to avoid duplicate requests
        • Priority-based job queue management
        • Thread-safe concurrent data processing
        • Enhanced GUI with comprehensive settings and batch processing
        
        Existing Features:
        • Property search by owner name, address, or APN
        • Database caching for faster searches
        • API integration with Maricopa County services
        • Web scraping fallback for comprehensive coverage
        • Tax and sales history tracking
        • Export capabilities
        
        Developed using PyQt5, PostgreSQL, and async web scraping.
        """
        
        QMessageBox.about(self, "About Enhanced Property Search", about_text)
    
    def closeEvent(self, event):
        """Handle application close event"""
        try:
            # Stop background collection gracefully
            if self.background_manager.is_running():
                logger.info("Stopping background collection for application shutdown...")
                self.background_manager.stop_collection()
            
            if self.search_worker and self.search_worker.isRunning():
                self.search_worker.terminate()
                self.search_worker.wait()
            
            self.db_manager.close()
            self.api_client.close()
            self.scraper.close()
            
            logger.info("Application shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
        
        event.accept()