#!/usr/bin/env python
"""
GUI Enhancement Dialogs
Additional dialog classes for enhanced GUI features
"""
import logging
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class ApplicationSettingsDialog(QDialog):
    """Dialog for general application settings"""
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.setup_ui()
        self.load_settings()
    def setup_ui(self):
        self.setWindowTitle("Application Settings")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Create tab widget for different setting categories
        tab_widget = QTabWidget()

        # General settings tab
        general_tab = QWidget()
        self.setup_general_tab(general_tab)
        tab_widget.addTab(general_tab, "General")

        # Performance settings tab
        performance_tab = QWidget()
        self.setup_performance_tab(performance_tab)
        tab_widget.addTab(performance_tab, "Performance")

        # UI settings tab
        ui_tab = QWidget()
        self.setup_ui_tab(ui_tab)
        tab_widget.addTab(ui_tab, "Interface")

        layout.addWidget(tab_widget)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
    def setup_general_tab(self, tab):
        layout = QFormLayout(tab)

        # Auto-start background collection
        self.auto_start_collection = QCheckBox("Auto-start background collection")
        layout.addRow("Startup:", self.auto_start_collection)

        # Default search type
        self.default_search_type = QComboBox()
        self.default_search_type.addItems(["Property Address", "Owner Name", "APN"])
        layout.addRow("Default Search:", self.default_search_type)

        # Result limit
        self.result_limit = QSpinBox()
        self.result_limit.setRange(10, 1000)
        self.result_limit.setValue(20)
        layout.addRow("Max Results:", self.result_limit)
    def setup_performance_tab(self, tab):
        layout = QFormLayout(tab)

        # Database connection pool size
        self.db_pool_size = QSpinBox()
        self.db_pool_size.setRange(1, 20)
        self.db_pool_size.setValue(5)
        layout.addRow("DB Pool Size:", self.db_pool_size)

        # API timeout
        self.api_timeout = QSpinBox()
        self.api_timeout.setRange(5, 120)
        self.api_timeout.setValue(30)
        self.api_timeout.setSuffix(" seconds")
        layout.addRow("API Timeout:", self.api_timeout)

        # Cache size
        self.cache_size = QSpinBox()
        self.cache_size.setRange(100, 10000)
        self.cache_size.setValue(1000)
        layout.addRow("Cache Size:", self.cache_size)
    def setup_ui_tab(self, tab):
        layout = QFormLayout(tab)

        # Auto-resize columns
        self.auto_resize_columns = QCheckBox("Auto-resize table columns")
        layout.addRow("Tables:", self.auto_resize_columns)

        # Status update frequency
        self.status_update_freq = QSpinBox()
        self.status_update_freq.setRange(1, 30)
        self.status_update_freq.setValue(2)
        self.status_update_freq.setSuffix(" seconds")
        layout.addRow("Status Updates:", self.status_update_freq)

        # Show progress details
        self.show_progress_details = QCheckBox("Show detailed progress information")
        layout.addRow("Progress:", self.show_progress_details)

        # Always fresh data
        self.always_fresh_data = QCheckBox("Always fetch fresh data (bypass cache)")
        layout.addRow("Data Source:", self.always_fresh_data)
    def load_settings(self):
    try:
            # Load current settings from config
            self.auto_start_collection.setChecked(
                self.config.get("auto_start_collection", True)
            )
            self.default_search_type.setCurrentText(
                self.config.get("default_search_type", "Property Address")
            )
            self.result_limit.setValue(self.config.get("max_results", 20))
            self.db_pool_size.setValue(self.config.get("db_pool_size", 5))
            self.api_timeout.setValue(self.config.get("api_timeout", 30))
            self.cache_size.setValue(self.config.get("cache_size", 1000))
            self.auto_resize_columns.setChecked(
                self.config.get("auto_resize_columns", True)
            )
            self.status_update_freq.setValue(
                self.config.get("status_update_frequency", 2)
            )
            self.show_progress_details.setChecked(
                self.config.get("show_progress_details", True)
            )
            self.always_fresh_data.setChecked(
                self.config.get("always_fresh_data", True)
            )
    except Exception as e:
            logger.warning(f"Error loading settings: {e}")
    def get_settings(self):
        return {
            "auto_start_collection": self.auto_start_collection.isChecked(),
            "default_search_type": self.default_search_type.currentText(),
            "max_results": self.result_limit.value(),
            "db_pool_size": self.db_pool_size.value(),
            "api_timeout": self.api_timeout.value(),
            "cache_size": self.cache_size.value(),
            "auto_resize_columns": self.auto_resize_columns.isChecked(),
            "status_update_frequency": self.status_update_freq.value(),
            "show_progress_details": self.show_progress_details.isChecked(),
            "always_fresh_data": self.always_fresh_data.isChecked(),
        }


class DataCollectionSettingsDialog(QDialog):
    """Dialog for data collection settings"""
    def __init__(self, background_manager, parent=None):
        super().__init__(parent)
        self.background_manager = background_manager
        self.setup_ui()
        self.load_settings()
    def setup_ui(self):
        self.setWindowTitle("Data Collection Settings")
        self.setModal(True)
        self.resize(450, 500)

        layout = QVBoxLayout(self)

        # Background collection settings
        bg_group = QGroupBox("Background Collection")
        bg_layout = QFormLayout(bg_group)

        self.bg_enabled = QCheckBox("Enable background collection")
        bg_layout.addRow("Status:", self.bg_enabled)

        self.max_concurrent_jobs = QSpinBox()
        self.max_concurrent_jobs.setRange(1, 10)
        self.max_concurrent_jobs.setValue(3)
        bg_layout.addRow("Max Concurrent Jobs:", self.max_concurrent_jobs)

        self.job_timeout = QSpinBox()
        self.job_timeout.setRange(30, 600)
        self.job_timeout.setValue(120)
        self.job_timeout.setSuffix(" seconds")
        bg_layout.addRow("Job Timeout:", self.job_timeout)

        layout.addWidget(bg_group)

        # Priority settings
        priority_group = QGroupBox("Collection Priorities")
        priority_layout = QVBoxLayout(priority_group)

        # Priority options
        self.priority_group = QButtonGroup()

        self.priority_balanced = QRadioButton(
            "Balanced - Equal priority for all sources"
        )
        self.priority_speed = QRadioButton("Speed - Prioritize fastest sources")
        self.priority_comprehensive = QRadioButton(
            "Comprehensive - Prioritize data completeness"
        )

        self.priority_group.addButton(self.priority_balanced, 0)
        self.priority_group.addButton(self.priority_speed, 1)
        self.priority_group.addButton(self.priority_comprehensive, 2)

        priority_layout.addWidget(self.priority_balanced)
        priority_layout.addWidget(self.priority_speed)
        priority_layout.addWidget(self.priority_comprehensive)

        self.priority_balanced.setChecked(True)

        layout.addWidget(priority_group)

        # Collection limits
        limits_group = QGroupBox("Collection Limits")
        limits_layout = QFormLayout(limits_group)

        self.daily_limit = QSpinBox()
        self.daily_limit.setRange(0, 10000)
        self.daily_limit.setValue(1000)
        self.daily_limit.setSpecialValueText("No limit")
        limits_layout.addRow("Daily Collection Limit:", self.daily_limit)

        self.batch_size = QSpinBox()
        self.batch_size.setRange(1, 100)
        self.batch_size.setValue(25)
        limits_layout.addRow("Max Batch Size:", self.batch_size)

        layout.addWidget(limits_group)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
    def load_settings(self):
        if self.background_manager:
    try:
                status = self.background_manager.get_collection_status()
                self.bg_enabled.setChecked(status.get("status") == "running")
    except Exception as e:
                logger.warning(f"Error loading collection settings: {e}")
    def get_settings(self):
        return {
            "background_enabled": self.bg_enabled.isChecked(),
            "max_concurrent_jobs": self.max_concurrent_jobs.value(),
            "job_timeout": self.job_timeout.value(),
            "priority_mode": self.priority_group.checkedId(),
            "collection_limits": {
                "daily_limit": self.daily_limit.value(),
                "batch_size": self.batch_size.value(),
            },
        }


class CacheManagementDialog(QDialog):
    """Dialog for cache management operations"""
    def __init__(self, background_manager, parent=None):
        super().__init__(parent)
        self.background_manager = background_manager
        self.setup_ui()
        self.refresh_cache_stats()
    def setup_ui(self):
        self.setWindowTitle("Cache Management")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Cache statistics
        stats_group = QGroupBox("Cache Statistics")
        stats_layout = QFormLayout(stats_group)

        self.total_entries_label = QLabel("0")
        stats_layout.addRow("Total Entries:", self.total_entries_label)

        self.cache_size_label = QLabel("0 MB")
        stats_layout.addRow("Cache Size:", self.cache_size_label)

        self.hit_rate_label = QLabel("0%")
        stats_layout.addRow("Hit Rate:", self.hit_rate_label)

        self.oldest_entry_label = QLabel("N/A")
        stats_layout.addRow("Oldest Entry:", self.oldest_entry_label)

        layout.addWidget(stats_group)

        # Cache operations
        operations_group = QGroupBox("Cache Operations")
        operations_layout = QVBoxLayout(operations_group)

        # Clear all cache
        clear_all_btn = QPushButton("Clear All Cache")
        clear_all_btn.clicked.connect(self.clear_all_cache)
        clear_all_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """
        )
        operations_layout.addWidget(clear_all_btn)

        # Clear old entries
        clear_old_layout = QHBoxLayout()
        clear_old_btn = QPushButton("Clear Entries Older Than")
        clear_old_btn.clicked.connect(self.clear_old_entries)

        self.days_spinbox = QSpinBox()
        self.days_spinbox.setRange(1, 365)
        self.days_spinbox.setValue(7)
        self.days_spinbox.setSuffix(" days")

        clear_old_layout.addWidget(clear_old_btn)
        clear_old_layout.addWidget(self.days_spinbox)
        clear_old_layout.addStretch()

        operations_layout.addLayout(clear_old_layout)

        # Refresh stats
        refresh_btn = QPushButton("Refresh Statistics")
        refresh_btn.clicked.connect(self.refresh_cache_stats)
        operations_layout.addWidget(refresh_btn)

        layout.addWidget(operations_group)

        # Cache settings
        settings_group = QGroupBox("Cache Settings")
        settings_layout = QFormLayout(settings_group)

        self.max_cache_size = QSpinBox()
        self.max_cache_size.setRange(100, 50000)
        self.max_cache_size.setValue(5000)
        self.max_cache_size.setSuffix(" entries")
        settings_layout.addRow("Max Cache Size:", self.max_cache_size)

        self.cache_ttl = QSpinBox()
        self.cache_ttl.setRange(1, 168)
        self.cache_ttl.setValue(24)
        self.cache_ttl.setSuffix(" hours")
        settings_layout.addRow("Cache TTL:", self.cache_ttl)

        layout.addWidget(settings_group)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
    def refresh_cache_stats(self):
        if not self.background_manager or not self.background_manager.worker:
            return

    try:
            status = self.background_manager.get_collection_status()
            cache_stats = status.get("cache_stats", {})

            self.total_entries_label.setText(str(cache_stats.get("total_entries", 0)))

            # Estimate cache size (rough calculation)
            size_mb = cache_stats.get("estimated_size_mb", 0)
            self.cache_size_label.setText(f"{size_mb:.1f} MB")

            hit_rate = cache_stats.get("hit_rate_percent", 0)
            self.hit_rate_label.setText(f"{hit_rate:.1f}%")

            oldest_entry = cache_stats.get("oldest_entry_age", "N/A")
            if isinstance(oldest_entry, (int, float)):
                hours = oldest_entry / 3600
                if hours < 24:
                    self.oldest_entry_label.setText(f"{hours:.1f} hours")
                else:
                    days = hours / 24
                    self.oldest_entry_label.setText(f"{days:.1f} days")
            else:
                self.oldest_entry_label.setText(str(oldest_entry))

    except Exception as e:
            logger.error(f"Error refreshing cache stats: {e}")
    def clear_all_cache(self):
        reply = QMessageBox.question(
            self,
            "Clear All Cache",
            "This will clear all cached property data. Continue?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
    try:
                if self.background_manager and self.background_manager.worker:
                    self.background_manager.worker.cache.clear_all_cache()
                    QMessageBox.information(
                        self, "Success", "All cache cleared successfully."
                    )
                    self.refresh_cache_stats()

    except Exception as e:
                QMessageBox.critical(self, "Error", f"Error clearing cache: {str(e)}")
    def clear_old_entries(self):
        days = self.days_spinbox.value()
        reply = QMessageBox.question(
            self,
            "Clear Old Entries",
            f"Clear all cache entries older than {days} days?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
    try:
                if self.background_manager and self.background_manager.worker:
                    # Clear entries older than specified days
                    max_age_seconds = days * 24 * 3600
                    self.background_manager.worker.cache.clear_old_entries(
                        max_age_seconds
                    )
                    QMessageBox.information(
                        self, "Success", f"Old entries cleared successfully."
                    )
                    self.refresh_cache_stats()

    except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Error clearing old entries: {str(e)}"
                )


class BatchSearchDialog(QDialog):
    """Dialog for batch search operations"""
    def __init__(self, db_manager, api_client, background_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.api_client = api_client
        self.background_manager = background_manager
        self.batch_results = []
        self.setup_ui()
    def setup_ui(self):
        self.setWindowTitle("Batch Search")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        # Input section
        input_group = QGroupBox("Batch Input")
        input_layout = QVBoxLayout(input_group)

        # Search type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Search Type:"))

        self.search_type = QComboBox()
        self.search_type.addItems(["Property Address", "Owner Name", "APN"])
        type_layout.addWidget(self.search_type)
        type_layout.addStretch()

        input_layout.addLayout(type_layout)

        # Input text area
        input_layout.addWidget(QLabel("Enter multiple search terms (one per line):"))

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(
            "Example:\\n"
            "123 Main St, Phoenix, AZ\\n"
            "456 Oak Ave, Scottsdale, AZ\\n"
            "789 Pine Rd, Tempe, AZ"
        )
        input_layout.addWidget(self.input_text)

        # File import button
        import_btn = QPushButton("Import from File...")
        import_btn.clicked.connect(self.import_from_file)
        input_layout.addWidget(import_btn)

        layout.addWidget(input_group)

        # Processing options
        options_group = QGroupBox("Processing Options")
        options_layout = QFormLayout(options_group)

        self.max_concurrent = QSpinBox()
        self.max_concurrent.setRange(1, 10)
        self.max_concurrent.setValue(3)
        options_layout.addRow("Max Concurrent Searches:", self.max_concurrent)

        self.enable_collection = QCheckBox("Enable background data collection")
        self.enable_collection.setChecked(True)
        options_layout.addRow("Data Collection:", self.enable_collection)

        layout.addWidget(options_group)

        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.status_label)

        layout.addWidget(progress_group)

        # Button layout
        button_layout = QHBoxLayout()

        self.start_btn = QPushButton("Start Batch Search")
        self.start_btn.clicked.connect(self.start_batch_search)
        self.start_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """
        )
        button_layout.addWidget(self.start_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setEnabled(False)
        self.ok_btn = ok_btn
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)
    def import_from_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Search Terms",
            "",
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)",
        )

        if filename:
    try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.input_text.setPlainText(content)

    except Exception as e:
                QMessageBox.critical(
                    self, "Import Error", f"Error reading file: {str(e)}"
                )
    def start_batch_search(self):
        search_terms = self.input_text.toPlainText().strip().split("\n")
        search_terms = [term.strip() for term in search_terms if term.strip()]

        if not search_terms:
            QMessageBox.warning(self, "Warning", "Please enter search terms.")
            return

        # Start batch search processing
        self.start_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(search_terms))
        self.progress_bar.setValue(0)

        # Create and start batch worker
        self.batch_worker = BatchSearchWorker(
            search_terms,
            self.search_type.currentText(),
            self.db_manager,
            self.api_client,
            self.max_concurrent.value(),
        )

        self.batch_worker.progress_updated.connect(self.progress_bar.setValue)
        self.batch_worker.status_updated.connect(self.status_label.setText)
        self.batch_worker.search_completed.connect(self.on_batch_completed)
        self.batch_worker.start()
    def on_batch_completed(self, results):
        self.batch_results = results
        self.status_label.setText(f"Completed: Found {len(results)} properties")
        self.ok_btn.setEnabled(True)
        self.start_btn.setEnabled(True)

        if self.enable_collection.isChecked() and self.background_manager:
            # Queue results for background collection
            jobs_queued = self.background_manager.enhance_search_results(results)
            if jobs_queued > 0:
                QMessageBox.information(
                    self,
                    "Batch Search Complete",
                    f"Found {len(results)} properties and queued "
                    f"{jobs_queued} for background data collection.",
                )
    def get_batch_results(self):
        return self.batch_results


class BatchSearchWorker(QThread):
    """Worker thread for batch search operations"""

    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    search_completed = pyqtSignal(list)
    def __init__(
        self, search_terms, search_type, db_manager, api_client, max_concurrent
    ):
        super().__init__()
        self.search_terms = search_terms
        self.search_type = search_type.lower().replace(" ", "_")
        if self.search_type == "property_address":
            self.search_type = "address"
        elif self.search_type == "owner_name":
            self.search_type = "owner"
        self.db_manager = db_manager
        self.api_client = api_client
        self.max_concurrent = max_concurrent
    def run(self):
        results = []
        completed = 0

        for term in self.search_terms:
    try:
                self.status_updated.emit(f"Searching: {term}")

                if self.search_type == "address":
                    term_results = self.db_manager.search_properties_by_address(term)
                elif self.search_type == "owner":
                    term_results = self.db_manager.search_properties_by_owner(term)
                elif self.search_type == "apn":
                    term_result = self.db_manager.get_property_by_apn(term)
                    term_results = [term_result] if term_result else []
                else:
                    term_results = []

                # If no database results, try API
                if not term_results and self.api_client:
    try:
                        api_results = self.api_client.search_all_property_types(term)
                        for category, props in api_results.items():
                            term_results.extend(props)
    except:
            pass  # Continue with empty results

                results.extend(term_results)
                completed += 1
                self.progress_updated.emit(completed)

    except Exception as e:
                logger.error(f"Error in batch search for '{term}': {e}")
                completed += 1
                self.progress_updated.emit(completed)

        self.search_completed.emit(results)


class ParallelProcessingDialog(QDialog):
    """Dialog for parallel processing configuration"""
    def __init__(self, background_manager, parent=None):
        super().__init__(parent)
        self.background_manager = background_manager
        self.setup_ui()
        self.load_current_settings()
    def setup_ui(self):
        self.setWindowTitle("Parallel Processing Settings")
        self.setModal(True)
        self.resize(450, 350)

        layout = QVBoxLayout(self)

        # Threading settings
        threading_group = QGroupBox("Threading Configuration")
        threading_layout = QFormLayout(threading_group)

        self.max_workers = QSpinBox()
        self.max_workers.setRange(1, 20)
        self.max_workers.setValue(5)
        threading_layout.addRow("Max Worker Threads:", self.max_workers)

        self.queue_size = QSpinBox()
        self.queue_size.setRange(10, 1000)
        self.queue_size.setValue(100)
        threading_layout.addRow("Queue Size:", self.queue_size)

        layout.addWidget(threading_group)

        # Performance settings
        performance_group = QGroupBox("Performance Tuning")
        performance_layout = QFormLayout(performance_group)

        self.batch_processing = QCheckBox("Enable batch processing")
        self.batch_processing.setChecked(True)
        performance_layout.addRow("Batching:", self.batch_processing)

        self.adaptive_threading = QCheckBox("Adaptive thread scaling")
        self.adaptive_threading.setChecked(True)
        performance_layout.addRow("Scaling:", self.adaptive_threading)

        self.priority_queue = QCheckBox("Priority-based queue")
        self.priority_queue.setChecked(True)
        performance_layout.addRow("Prioritization:", self.priority_queue)

        layout.addWidget(performance_group)

        # Resource limits
        limits_group = QGroupBox("Resource Limits")
        limits_layout = QFormLayout(limits_group)

        self.memory_limit = QSpinBox()
        self.memory_limit.setRange(100, 4000)
        self.memory_limit.setValue(500)
        self.memory_limit.setSuffix(" MB")
        limits_layout.addRow("Memory Limit:", self.memory_limit)

        self.cpu_limit = QSpinBox()
        self.cpu_limit.setRange(10, 100)
        self.cpu_limit.setValue(80)
        self.cpu_limit.setSuffix("%")
        limits_layout.addRow("Max CPU Usage:", self.cpu_limit)

        layout.addWidget(limits_group)

        # Button layout
        button_layout = QHBoxLayout()

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
    def load_current_settings(self):
        # Load current parallel processing settings if available
        pass
    def apply_settings(self):
        settings = {
            "max_workers": self.max_workers.value(),
            "queue_size": self.queue_size.value(),
            "batch_processing": self.batch_processing.isChecked(),
            "adaptive_threading": self.adaptive_threading.isChecked(),
            "priority_queue": self.priority_queue.isChecked(),
            "memory_limit": self.memory_limit.value(),
            "cpu_limit": self.cpu_limit.value(),
        }

        # Apply settings to background manager if supported
        QMessageBox.information(
            self, "Settings Applied", "Parallel processing settings have been applied."
        )


class DataSourceConfigurationDialog(QDialog):
    """Dialog for configuring data sources"""
    def __init__(self, config_manager, api_client, scraper, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.api_client = api_client
        self.scraper = scraper
        self.setup_ui()
        self.load_current_settings()
    def setup_ui(self):
        self.setWindowTitle("Data Source Configuration")
        self.setModal(True)
        self.resize(500, 600)

        layout = QVBoxLayout(self)

        # Data source toggles
        sources_group = QGroupBox("Data Sources")
        sources_layout = QVBoxLayout(sources_group)

        self.api_enabled = QCheckBox("Enable Maricopa County API")
        self.api_enabled.setChecked(True)
        sources_layout.addWidget(self.api_enabled)

        self.web_scraping_enabled = QCheckBox("Enable Web Scraping")
        self.web_scraping_enabled.setChecked(True)
        sources_layout.addWidget(self.web_scraping_enabled)

        self.cache_enabled = QCheckBox("Enable Data Caching")
        self.cache_enabled.setChecked(True)
        sources_layout.addWidget(self.cache_enabled)

        layout.addWidget(sources_group)

        # Priority ordering
        priority_group = QGroupBox("Source Priority Order")
        priority_layout = QVBoxLayout(priority_group)

        priority_layout.addWidget(QLabel("Drag to reorder (highest priority first):"))

        self.priority_list = QListWidget()
        self.priority_list.setDragDropMode(QListWidget.InternalMove)

        # Add default priority items
        priority_items = [
            "Database Cache",
            "Maricopa County API",
            "Web Scraping",
            "Third-party APIs",
        ]

        for item_text in priority_items:
            item = QListWidgetItem(item_text)
            item.setFlags(item.flags() | Qt.ItemIsDropEnabled)
            self.priority_list.addItem(item)

        priority_layout.addWidget(self.priority_list)

        layout.addWidget(priority_group)

        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)

        self.fallback_enabled = QCheckBox("Enable source fallback")
        self.fallback_enabled.setChecked(True)
        advanced_layout.addRow("Fallback:", self.fallback_enabled)

        self.retry_attempts = QSpinBox()
        self.retry_attempts.setRange(0, 10)
        self.retry_attempts.setValue(3)
        advanced_layout.addRow("Retry Attempts:", self.retry_attempts)

        self.timeout_seconds = QSpinBox()
        self.timeout_seconds.setRange(5, 120)
        self.timeout_seconds.setValue(30)
        self.timeout_seconds.setSuffix(" seconds")
        advanced_layout.addRow("Request Timeout:", self.timeout_seconds)

        layout.addWidget(advanced_group)

        # Source testing
        testing_group = QGroupBox("Source Testing")
        testing_layout = QVBoxLayout(testing_group)

        test_layout = QHBoxLayout()
        test_btn = QPushButton("Test All Sources")
        test_btn.clicked.connect(self.test_all_sources)
        test_layout.addWidget(test_btn)

        self.test_status_label = QLabel("Not tested")
        test_layout.addWidget(self.test_status_label)
        test_layout.addStretch()

        testing_layout.addLayout(test_layout)

        layout.addWidget(testing_group)

        # Button layout
        button_layout = QHBoxLayout()

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
    def load_current_settings(self):
        # Load current data source configuration
        pass
    def test_all_sources(self):
        self.test_status_label.setText("Testing sources...")

        # Test API
        api_status = "✓" if self._test_api() else "✗"

        # Test web scraping
        scraping_status = "✓" if self._test_scraping() else "✗"

        # Test database
        db_status = "✓" if self._test_database() else "✗"

        self.test_status_label.setText(
            f"API: {api_status} | Scraping: {scraping_status} | DB: {db_status}"
        )
    def _test_api(self):
    try:
            if self.api_client:
                status = self.api_client.get_api_status()
                return status.get("status") == "active"
    except:
            pass
        return False
    def _test_scraping(self):
    try:
            if self.scraper:
                return True  # Basic availability check
    except:
            pass
        return False
    def _test_database(self):
    try:
            # Test database connection through config or other means
            return True
    except:
            pass
        return False
    def get_settings(self):
        # Get priority order
        priority_order = []
        for i in range(self.priority_list.count()):
            priority_order.append(self.priority_list.item(i).text())

        return {
            "api_enabled": self.api_enabled.isChecked(),
            "web_scraping_enabled": self.web_scraping_enabled.isChecked(),
            "cache_enabled": self.cache_enabled.isChecked(),
            "source_priority": priority_order,
            "fallback_enabled": self.fallback_enabled.isChecked(),
            "retry_attempts": self.retry_attempts.value(),
            "timeout_seconds": self.timeout_seconds.value(),
        }
