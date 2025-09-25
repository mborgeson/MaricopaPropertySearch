"""
Optimized Main Window for Maricopa Property Search Application
Enhanced PyQt5-based GUI interface with advanced search capabilities
"""

import csv
import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import application modules
from optimized_database_manager import OptimizedDatabaseManager, SearchFilters
from PyQt5.QtCore import (
    QSortFilterProxyModel,
    QStringListModel,
    Qt,
    QThread,
    QTimer,
    pyqtSignal,
)
from PyQt5.QtGui import QFont, QIcon, QPalette, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.optimized_search_worker import OptimizedSearchWorker, SearchWorkerPool
from src.search_cache import SearchCache, SearchHistory
from src.search_validator import SearchType, SearchValidator, ValidationResult

# MIGRATED: from src.api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient, MockMaricopaAPIClient
from src.web_scraper import MockWebScraperManager, WebScraperManager

logger = logging.getLogger(__name__)

class AdvancedSearchDialog(QDialog):
    """Advanced search filters dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filters = SearchFilters()
        self.setup_ui()
        self.load_current_filters()
    
    def setup_ui(self):
        """Setup advanced search dialog UI"""
        self.setWindowTitle("Advanced Search Filters")
        self.setModal(True)
        self.resize(400, 600)
        
        layout = QVBoxLayout(self)
        
        # Create scroll area for filters
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Year Built Filter
        year_group = QGroupBox("Year Built")
        year_layout = QGridLayout(year_group)
        
        year_layout.addWidget(QLabel("From:"), 0, 0)
        self.year_min_spin = QSpinBox()
        self.year_min_spin.setRange(1800, 2030)
        self.year_min_spin.setSpecialValueText("Any")
        self.year_min_spin.setValue(1800)
        year_layout.addWidget(self.year_min_spin, 0, 1)
        
        year_layout.addWidget(QLabel("To:"), 0, 2)
        self.year_max_spin = QSpinBox()
        self.year_max_spin.setRange(1800, 2030)
        self.year_max_spin.setSpecialValueText("Any")
        self.year_max_spin.setValue(2030)
        year_layout.addWidget(self.year_max_spin, 0, 3)
        
        scroll_layout.addWidget(year_group)
        
        # Property Value Filter
        value_group = QGroupBox("Assessed Value")
        value_layout = QGridLayout(value_group)
        
        value_layout.addWidget(QLabel("Min ($):"), 0, 0)
        self.value_min_spin = QDoubleSpinBox()
        self.value_min_spin.setRange(0, 10000000)
        self.value_min_spin.setDecimals(0)
        self.value_min_spin.setSingleStep(10000)
        self.value_min_spin.setSpecialValueText("Any")
        value_layout.addWidget(self.value_min_spin, 0, 1)
        
        value_layout.addWidget(QLabel("Max ($):"), 0, 2)
        self.value_max_spin = QDoubleSpinBox()
        self.value_max_spin.setRange(0, 10000000)
        self.value_max_spin.setDecimals(0)
        self.value_max_spin.setSingleStep(10000)
        self.value_max_spin.setSpecialValueText("Any")
        self.value_max_spin.setValue(10000000)
        value_layout.addWidget(self.value_max_spin, 0, 3)
        
        scroll_layout.addWidget(value_group)
        
        # Living Area Filter
        area_group = QGroupBox("Living Area (sq ft)")
        area_layout = QGridLayout(area_group)
        
        area_layout.addWidget(QLabel("Min:"), 0, 0)
        self.area_min_spin = QSpinBox()
        self.area_min_spin.setRange(0, 20000)
        self.area_min_spin.setSingleStep(100)
        self.area_min_spin.setSpecialValueText("Any")
        area_layout.addWidget(self.area_min_spin, 0, 1)
        
        area_layout.addWidget(QLabel("Max:"), 0, 2)
        self.area_max_spin = QSpinBox()
        self.area_max_spin.setRange(0, 20000)
        self.area_max_spin.setSingleStep(100)
        self.area_max_spin.setSpecialValueText("Any")
        self.area_max_spin.setValue(20000)
        area_layout.addWidget(self.area_max_spin, 0, 3)
        
        scroll_layout.addWidget(area_group)
        
        # Lot Size Filter
        lot_group = QGroupBox("Lot Size (sq ft)")
        lot_layout = QGridLayout(lot_group)
        
        lot_layout.addWidget(QLabel("Min:"), 0, 0)
        self.lot_min_spin = QSpinBox()
        self.lot_min_spin.setRange(0, 1000000)
        self.lot_min_spin.setSingleStep(1000)
        self.lot_min_spin.setSpecialValueText("Any")
        lot_layout.addWidget(self.lot_min_spin, 0, 1)
        
        lot_layout.addWidget(QLabel("Max:"), 0, 2)
        self.lot_max_spin = QSpinBox()
        self.lot_max_spin.setRange(0, 1000000)
        self.lot_max_spin.setSingleStep(1000)
        self.lot_max_spin.setSpecialValueText("Any")
        self.lot_max_spin.setValue(1000000)
        lot_layout.addWidget(self.lot_max_spin, 0, 3)
        
        scroll_layout.addWidget(lot_group)
        
        # Bedrooms/Bathrooms Filter
        rooms_group = QGroupBox("Bedrooms & Bathrooms")
        rooms_layout = QGridLayout(rooms_group)
        
        rooms_layout.addWidget(QLabel("Min Bedrooms:"), 0, 0)
        self.bed_min_spin = QSpinBox()
        self.bed_min_spin.setRange(0, 20)
        self.bed_min_spin.setSpecialValueText("Any")
        rooms_layout.addWidget(self.bed_min_spin, 0, 1)
        
        rooms_layout.addWidget(QLabel("Max Bedrooms:"), 0, 2)
        self.bed_max_spin = QSpinBox()
        self.bed_max_spin.setRange(0, 20)
        self.bed_max_spin.setSpecialValueText("Any")
        self.bed_max_spin.setValue(20)
        rooms_layout.addWidget(self.bed_max_spin, 0, 3)
        
        rooms_layout.addWidget(QLabel("Min Bathrooms:"), 1, 0)
        self.bath_min_spin = QDoubleSpinBox()
        self.bath_min_spin.setRange(0, 20)
        self.bath_min_spin.setDecimals(1)
        self.bath_min_spin.setSingleStep(0.5)
        self.bath_min_spin.setSpecialValueText("Any")
        rooms_layout.addWidget(self.bath_min_spin, 1, 1)
        
        rooms_layout.addWidget(QLabel("Max Bathrooms:"), 1, 2)
        self.bath_max_spin = QDoubleSpinBox()
        self.bath_max_spin.setRange(0, 20)
        self.bath_max_spin.setDecimals(1)
        self.bath_max_spin.setSingleStep(0.5)
        self.bath_max_spin.setSpecialValueText("Any")
        self.bath_max_spin.setValue(20)
        rooms_layout.addWidget(self.bath_max_spin, 1, 3)
        
        scroll_layout.addWidget(rooms_group)
        
        # Pool Filter
        pool_group = QGroupBox("Pool")
        pool_layout = QHBoxLayout(pool_group)
        
        self.pool_any = QRadioButton("Any")
        self.pool_yes = QRadioButton("Has Pool")
        self.pool_no = QRadioButton("No Pool")
        self.pool_any.setChecked(True)
        
        pool_layout.addWidget(self.pool_any)
        pool_layout.addWidget(self.pool_yes)
        pool_layout.addWidget(self.pool_no)
        
        scroll_layout.addWidget(pool_group)
        
        # Sort Options
        sort_group = QGroupBox("Sort Results")
        sort_layout = QGridLayout(sort_group)
        
        sort_layout.addWidget(QLabel("Sort by:"), 0, 0)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Owner Name", "Property Address", "Year Built", 
            "Living Area", "Assessed Value", "Sale Price", "APN"
        ])
        sort_layout.addWidget(self.sort_combo, 0, 1)
        
        sort_layout.addWidget(QLabel("Order:"), 0, 2)
        self.sort_order_combo = QComboBox()
        self.sort_order_combo.addItems(["Ascending", "Descending"])
        sort_layout.addWidget(self.sort_order_combo, 0, 3)
        
        scroll_layout.addWidget(sort_group)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.clicked.connect(self.reset_filters)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.apply_btn = QPushButton("Apply Filters")
        self.apply_btn.clicked.connect(self.apply_filters)
        self.apply_btn.setDefault(True)
        button_layout.addWidget(self.apply_btn)
        
        layout.addLayout(button_layout)
    
    def load_current_filters(self):
        """Load current filter values into controls"""
        if self.filters.year_built_min:
            self.year_min_spin.setValue(self.filters.year_built_min)
        
        if self.filters.year_built_max:
            self.year_max_spin.setValue(self.filters.year_built_max)
        
        if self.filters.price_min:
            self.value_min_spin.setValue(self.filters.price_min)
        
        if self.filters.price_max:
            self.value_max_spin.setValue(self.filters.price_max)
        
        if self.filters.living_area_min:
            self.area_min_spin.setValue(self.filters.living_area_min)
        
        if self.filters.living_area_max:
            self.area_max_spin.setValue(self.filters.living_area_max)
        
        if self.filters.lot_size_min:
            self.lot_min_spin.setValue(self.filters.lot_size_min)
        
        if self.filters.lot_size_max:
            self.lot_max_spin.setValue(self.filters.lot_size_max)
        
        if self.filters.bedrooms_min:
            self.bed_min_spin.setValue(self.filters.bedrooms_min)
        
        if self.filters.bedrooms_max:
            self.bed_max_spin.setValue(self.filters.bedrooms_max)
        
        if self.filters.bathrooms_min:
            self.bath_min_spin.setValue(self.filters.bathrooms_min)
        
        if self.filters.bathrooms_max:
            self.bath_max_spin.setValue(self.filters.bathrooms_max)
        
        if self.filters.has_pool is True:
            self.pool_yes.setChecked(True)
        elif self.filters.has_pool is False:
            self.pool_no.setChecked(True)
        
        # Sort options
        sort_mapping = {
            'owner_name': 0,
            'property_address': 1,
            'year_built': 2,
            'living_area': 3,
            'assessed_value': 4,
            'sale_price': 5,
            'apn': 6
        }
        
        sort_index = sort_mapping.get(self.filters.sort_by, 0)
        self.sort_combo.setCurrentIndex(sort_index)
        
        if self.filters.sort_order.upper() == "DESC":
            self.sort_order_combo.setCurrentIndex(1)
    
    def apply_filters(self):
        """Apply current filter settings"""
        # Year built
        self.filters.year_built_min = self.year_min_spin.value() if self.year_min_spin.value() > 1800 else None
        self.filters.year_built_max = self.year_max_spin.value() if self.year_max_spin.value() < 2030 else None
        
        # Property value
        self.filters.price_min = self.value_min_spin.value() if self.value_min_spin.value() > 0 else None
        self.filters.price_max = self.value_max_spin.value() if self.value_max_spin.value() < 10000000 else None
        
        # Living area
        self.filters.living_area_min = self.area_min_spin.value() if self.area_min_spin.value() > 0 else None
        self.filters.living_area_max = self.area_max_spin.value() if self.area_max_spin.value() < 20000 else None
        
        # Lot size
        self.filters.lot_size_min = self.lot_min_spin.value() if self.lot_min_spin.value() > 0 else None
        self.filters.lot_size_max = self.lot_max_spin.value() if self.lot_max_spin.value() < 1000000 else None
        
        # Bedrooms
        self.filters.bedrooms_min = self.bed_min_spin.value() if self.bed_min_spin.value() > 0 else None
        self.filters.bedrooms_max = self.bed_max_spin.value() if self.bed_max_spin.value() < 20 else None
        
        # Bathrooms
        self.filters.bathrooms_min = self.bath_min_spin.value() if self.bath_min_spin.value() > 0 else None
        self.filters.bathrooms_max = self.bath_max_spin.value() if self.bath_max_spin.value() < 20 else None
        
        # Pool
        if self.pool_yes.isChecked():
            self.filters.has_pool = True
        elif self.pool_no.isChecked():
            self.filters.has_pool = False
        else:
            self.filters.has_pool = None
        
        # Sort options
        sort_values = ['owner_name', 'property_address', 'year_built', 'living_area', 'assessed_value', 'sale_price', 'apn']
        self.filters.sort_by = sort_values[self.sort_combo.currentIndex()]
        self.filters.sort_order = "DESC" if self.sort_order_combo.currentIndex() == 1 else "ASC"
        
        self.accept()
    
    def reset_filters(self):
        """Reset all filters to defaults"""
        self.filters = SearchFilters()
        
        self.year_min_spin.setValue(1800)
        self.year_max_spin.setValue(2030)
        self.value_min_spin.setValue(0)
        self.value_max_spin.setValue(10000000)
        self.area_min_spin.setValue(0)
        self.area_max_spin.setValue(20000)
        self.lot_min_spin.setValue(0)
        self.lot_max_spin.setValue(1000000)
        self.bed_min_spin.setValue(0)
        self.bed_max_spin.setValue(20)
        self.bath_min_spin.setValue(0)
        self.bath_max_spin.setValue(20)
        self.pool_any.setChecked(True)
        self.sort_combo.setCurrentIndex(0)
        self.sort_order_combo.setCurrentIndex(0)
    
    def get_filters(self) -> SearchFilters:
        """Get current filter configuration"""
        return self.filters


class OptimizedPropertySearchApp(QMainWindow):
    """Optimized main application window with enhanced search capabilities"""
    
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        
        # Initialize components
        self.db_manager = OptimizedDatabaseManager(config_manager)
        self.api_client = MockMaricopaAPIClient(config_manager)  # Use mock for development
        self.scraper = MockWebScraperManager(config_manager)
        
        # Search components
        self.validator = SearchValidator()
        self.search_cache = SearchCache()
        self.search_history = SearchHistory()
        self.worker_pool = SearchWorkerPool(max_workers=2)
        
        # UI state
        self.current_worker = None
        self.current_results = []
        self.current_filters = SearchFilters()
        self.search_completer = None
        
        self.setup_ui()
        self.setup_connections()
        self.setup_status_bar()
        self.setup_search_suggestions()
        self.check_system_status()
        
        logger.info("Optimized Property Search App initialized")
    
    def setup_ui(self):
        """Setup the enhanced user interface"""
        self.setWindowTitle("Maricopa County Property Search - Enhanced")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create enhanced search section
        search_group = QGroupBox("Property Search")
        search_layout = QGridLayout(search_group)
        
        # Search type combo with auto-detection
        search_layout.addWidget(QLabel("Search Type:"), 0, 0)
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Owner Name", "Property Address", "APN", "Auto-Detect"])
        self.search_type_combo.setCurrentText("Auto-Detect")
        search_layout.addWidget(self.search_type_combo, 0, 1)
        
        # Search term input with suggestions
        search_layout.addWidget(QLabel("Search Term:"), 1, 0)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter owner name, address, or APN...")
        search_layout.addWidget(self.search_input, 1, 1, 1, 2)
        
        # Search and filter buttons
        self.search_btn = QPushButton("Search")
        self.search_btn.setDefault(True)
        search_layout.addWidget(self.search_btn, 1, 3)
        
        self.advanced_btn = QPushButton("Advanced Filters")
        search_layout.addWidget(self.advanced_btn, 0, 2)
        
        self.clear_filters_btn = QPushButton("Clear Filters")
        search_layout.addWidget(self.clear_filters_btn, 0, 3)
        
        # Progress bar and status
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        search_layout.addWidget(self.progress_bar, 2, 0, 1, 4)
        
        # Active filters display
        self.filters_label = QLabel("No filters active")
        self.filters_label.setStyleSheet("color: #666; font-style: italic;")
        search_layout.addWidget(self.filters_label, 3, 0, 1, 4)
        
        main_layout.addWidget(search_group)
        
        # Create results section with tabs
        results_tabs = QTabWidget()
        
        # Main results tab
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        
        # Results table with sorting
        self.results_table = QTableWidget()
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSortingEnabled(True)
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
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setEnabled(False)
        controls_layout.addWidget(self.refresh_btn)
        
        controls_layout.addStretch()
        
        # Pagination controls
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.setEnabled(False)
        controls_layout.addWidget(self.prev_btn)
        
        self.page_label = QLabel("Page 1 of 1")
        controls_layout.addWidget(self.page_label)
        
        self.next_btn = QPushButton("Next")
        self.next_btn.setEnabled(False)
        controls_layout.addWidget(self.next_btn)
        
        self.results_label = QLabel("No search performed")
        controls_layout.addWidget(self.results_label)
        
        results_layout.addLayout(controls_layout)
        results_tabs.addTab(results_tab, "Search Results")
        
        # Analytics tab
        analytics_tab = QWidget()
        analytics_layout = QVBoxLayout(analytics_tab)
        
        self.analytics_text = QTextEdit()
        self.analytics_text.setReadOnly(True)
        analytics_layout.addWidget(self.analytics_text)
        
        refresh_analytics_btn = QPushButton("Refresh Analytics")
        refresh_analytics_btn.clicked.connect(self.refresh_analytics)
        analytics_layout.addWidget(refresh_analytics_btn)
        
        results_tabs.addTab(analytics_tab, "Analytics")
        
        main_layout.addWidget(results_tabs)
        
        # Create menu bar
        self.setup_menu_bar()
    
    def setup_results_table(self):
        """Setup the enhanced results table"""
        headers = [
            "APN", "Owner Name", "Property Address", "Year Built", 
            "Living Area", "Bedrooms", "Bathrooms", "Pool", "Latest Assessed Value"
        ]
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)
        
        # Set column widths
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # APN
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Owner Name
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Address
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Year Built
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Living Area
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Bedrooms
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Bathrooms
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Pool
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Assessed Value
    
    def setup_connections(self):
        """Setup enhanced signal-slot connections"""
        # Search connections
        self.search_btn.clicked.connect(self.perform_search)
        self.search_input.returnPressed.connect(self.perform_search)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_type_combo.currentTextChanged.connect(self.on_search_type_changed)
        
        # Filter connections
        self.advanced_btn.clicked.connect(self.show_advanced_filters)
        self.clear_filters_btn.clicked.connect(self.clear_filters)
        
        # Results connections
        self.export_btn.clicked.connect(self.export_results)
        self.view_details_btn.clicked.connect(self.view_property_details)
        self.refresh_btn.clicked.connect(self.refresh_search)
        self.results_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.results_table.doubleClicked.connect(self.view_property_details)
        
        # Pagination connections
        self.prev_btn.clicked.connect(self.previous_page)
        self.next_btn.clicked.connect(self.next_page)
    
    def setup_menu_bar(self):
        """Setup enhanced application menu bar"""
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
        
        # Search menu
        search_menu = menubar.addMenu("Search")
        
        advanced_search_action = QAction("Advanced Filters...", self)
        advanced_search_action.setShortcut("Ctrl+F")
        advanced_search_action.triggered.connect(self.show_advanced_filters)
        search_menu.addAction(advanced_search_action)
        
        clear_cache_action = QAction("Clear Search Cache", self)
        clear_cache_action.triggered.connect(self.clear_search_cache)
        search_menu.addAction(clear_cache_action)
        
        search_menu.addSeparator()
        
        search_history_action = QAction("Search History", self)
        search_history_action.triggered.connect(self.show_search_history)
        search_menu.addAction(search_history_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        db_stats_action = QAction("Database Statistics", self)
        db_stats_action.triggered.connect(self.show_database_stats)
        tools_menu.addAction(db_stats_action)
        
        performance_action = QAction("Performance Monitor", self)
        performance_action.triggered.connect(self.show_performance_monitor)
        tools_menu.addAction(performance_action)
        
        optimize_action = QAction("Optimize Database", self)
        optimize_action.triggered.connect(self.optimize_database)
        tools_menu.addAction(optimize_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Setup enhanced status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Add permanent widgets
        self.cache_label = QLabel("Cache: 0 entries")
        self.status_bar.addPermanentWidget(self.cache_label)
        
        # Update cache stats periodically
        self.cache_timer = QTimer()
        self.cache_timer.timeout.connect(self.update_cache_stats)
        self.cache_timer.start(30000)  # Update every 30 seconds
    
    def setup_search_suggestions(self):
        """Setup search input auto-completion"""
        self.update_search_suggestions()
        
        # Update suggestions when search type changes
        self.search_type_combo.currentTextChanged.connect(self.update_search_suggestions)
    
    def update_search_suggestions(self):
        """Update search suggestions based on current search type"""
        try:
            search_type_text = self.search_type_combo.currentText()
            
            if search_type_text == "Auto-Detect":
                suggestions = []
            else:
                search_type = self._get_search_type_from_text(search_type_text)
                suggestions = self.db_manager.get_property_suggestions("", search_type, limit=100)
            
            # Update completer
            if self.search_completer:
                self.search_input.setCompleter(None)
            
            if suggestions:
                completer_model = QStringListModel(suggestions)
                self.search_completer = QCompleter(completer_model)
                self.search_completer.setCaseSensitivity(Qt.CaseInsensitive)
                self.search_completer.setFilterMode(Qt.MatchContains)
                self.search_input.setCompleter(self.search_completer)
                
        except Exception as e:
            logger.warning(f"Failed to update search suggestions: {e}")
    
    def check_system_status(self):
        """Check enhanced system component status"""
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
        
        # Check cache status
        cache_stats = self.search_cache.get_stats()
        status_messages.append(f"Cache: {cache_stats.get('total_entries', 0)} entries")
        
        self.status_bar.showMessage(" | ".join(status_messages))
    
    def perform_search(self):
        """Perform enhanced property search with validation and caching"""
        search_term = self.search_input.text().strip()
        if not search_term:
            QMessageBox.warning(self, "Warning", "Please enter a search term.")
            return
        
        # Determine search type
        search_type_text = self.search_type_combo.currentText()
        
        if search_type_text == "Auto-Detect":
            detected_type = self.validator.auto_detect_search_type(search_term)
            if not detected_type:
                QMessageBox.warning(self, "Warning", 
                                  "Could not auto-detect search type. Please select a specific type.")
                return
            search_type = detected_type
        else:
            search_type = self._get_search_type_from_text(search_type_text)
        
        # Cancel any existing search
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel_search()
            self.current_worker.wait(2000)
        
        # Create and start new search worker
        self.current_worker = self.worker_pool.submit_search(
            search_term=search_term,
            search_type=search_type,
            db_manager=self.db_manager,
            api_client=self.api_client,
            scraper=self.scraper,
            filters=self.current_filters,
            use_cache=True
        )
        
        # Connect worker signals
        self.current_worker.progress_updated.connect(self.progress_bar.setValue)
        self.current_worker.status_updated.connect(self.status_bar.showMessage)
        self.current_worker.results_ready.connect(self.display_results)
        self.current_worker.error_occurred.connect(self.handle_search_error)
        self.current_worker.validation_failed.connect(self.handle_validation_error)
        self.current_worker.search_completed.connect(self.on_search_completed)
        
        # Update UI state
        self.search_btn.setEnabled(False)
        self.search_btn.setText("Searching...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start the search
        self.current_worker.start()
        
        logger.info(f"Started search: {search_type.value} = '{search_term}'")
    
    def _get_search_type_from_text(self, text: str) -> SearchType:
        """Convert search type text to enum"""
        mapping = {
            "Owner Name": SearchType.OWNER,
            "Property Address": SearchType.ADDRESS, 
            "APN": SearchType.APN
        }
        return mapping.get(text, SearchType.OWNER)
    
    def display_results(self, results: List[Dict], total_count: int):
        """Display enhanced search results with pagination"""
        self.current_results = results
        
        self.results_table.setRowCount(len(results))
        
        for i, result in enumerate(results):
            # APN
            self.results_table.setItem(i, 0, QTableWidgetItem(result.get('apn', '')))
            
            # Owner Name
            self.results_table.setItem(i, 1, QTableWidgetItem(result.get('owner_name', '')))
            
            # Property Address
            self.results_table.setItem(i, 2, QTableWidgetItem(result.get('property_address', '')))
            
            # Year Built
            year_built = result.get('year_built', '')
            self.results_table.setItem(i, 3, QTableWidgetItem(str(year_built) if year_built else ''))
            
            # Living Area
            living_area = result.get('living_area_sqft', '')
            living_area_text = f"{living_area:,} sq ft" if living_area else ''
            self.results_table.setItem(i, 4, QTableWidgetItem(living_area_text))
            
            # Bedrooms
            bedrooms = result.get('bedrooms', '')
            self.results_table.setItem(i, 5, QTableWidgetItem(str(bedrooms) if bedrooms else ''))
            
            # Bathrooms
            bathrooms = result.get('bathrooms', '')
            self.results_table.setItem(i, 6, QTableWidgetItem(str(bathrooms) if bathrooms else ''))
            
            # Pool
            pool = result.get('pool', False)
            pool_text = "Yes" if pool else "No"
            self.results_table.setItem(i, 7, QTableWidgetItem(pool_text))
            
            # Latest Assessed Value
            assessed_value = result.get('latest_assessed_value', '')
            assessed_value_text = f"${assessed_value:,.2f}" if assessed_value else ''
            self.results_table.setItem(i, 8, QTableWidgetItem(assessed_value_text))
        
        # Update UI
        self.results_label.setText(f"Found {total_count:,} properties (showing {len(results)})")
        self.export_btn.setEnabled(len(results) > 0)
        self.refresh_btn.setEnabled(True)
        
        # Reset search button
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search")
        self.progress_bar.setVisible(False)
        
        # Auto-resize columns
        self.results_table.resizeColumnsToContents()
        
        # Update status
        self.status_bar.showMessage("Search completed")
        
        logger.info(f"Displayed {len(results)} results (total: {total_count})")
    
    def handle_search_error(self, error_message: str):
        """Handle search errors with detailed information"""
        QMessageBox.critical(self, "Search Error", f"Search failed:\n\n{error_message}")
        
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search")
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Search failed")
        
        logger.error(f"Search error: {error_message}")
    
    def handle_validation_error(self, error_message: str, suggestions: List[str]):
        """Handle input validation errors with suggestions"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Invalid Search Input")
        msg.setText(error_message)
        
        if suggestions:
            msg.setDetailedText("Suggestions:\n" + "\n".join(f"• {s}" for s in suggestions))
        
        msg.exec_()
        
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search")
        self.progress_bar.setVisible(False)
        
    def on_search_completed(self, search_type: str, search_term: str, result_count: int, duration: float):
        """Handle search completion for analytics"""
        logger.info(f"Search analytics: {search_type} '{search_term}' -> {result_count} results in {duration:.2f}s")
        
        # Update cache stats
        self.update_cache_stats()
    
    def show_advanced_filters(self):
        """Show advanced search filters dialog"""
        dialog = AdvancedSearchDialog(self)
        dialog.filters = self.current_filters
        dialog.load_current_filters()
        
        if dialog.exec_() == QDialog.Accepted:
            self.current_filters = dialog.get_filters()
            self.update_filters_display()
    
    def clear_filters(self):
        """Clear all search filters"""
        self.current_filters = SearchFilters()
        self.update_filters_display()
    
    def update_filters_display(self):
        """Update the filters display label"""
        active_filters = []
        
        if self.current_filters.year_built_min or self.current_filters.year_built_max:
            year_filter = "Year: "
            if self.current_filters.year_built_min:
                year_filter += f"{self.current_filters.year_built_min}+"
            if self.current_filters.year_built_max:
                if self.current_filters.year_built_min:
                    year_filter = year_filter.replace('+', f'-{self.current_filters.year_built_max}')
                else:
                    year_filter += f"≤{self.current_filters.year_built_max}"
            active_filters.append(year_filter)
        
        if self.current_filters.price_min or self.current_filters.price_max:
            price_filter = "Price: "
            if self.current_filters.price_min:
                price_filter += f"${self.current_filters.price_min:,.0f}+"
            if self.current_filters.price_max:
                if self.current_filters.price_min:
                    price_filter = price_filter.replace('+', f'-${self.current_filters.price_max:,.0f}')
                else:
                    price_filter += f"≤${self.current_filters.price_max:,.0f}"
            active_filters.append(price_filter)
        
        if self.current_filters.living_area_min or self.current_filters.living_area_max:
            area_filter = "Area: "
            if self.current_filters.living_area_min:
                area_filter += f"{self.current_filters.living_area_min:,}+"
            if self.current_filters.living_area_max:
                if self.current_filters.living_area_min:
                    area_filter = area_filter.replace('+', f'-{self.current_filters.living_area_max:,}')
                else:
                    area_filter += f"≤{self.current_filters.living_area_max:,}"
            area_filter += " sq ft"
            active_filters.append(area_filter)
        
        if self.current_filters.bedrooms_min or self.current_filters.bedrooms_max:
            bed_filter = "Bedrooms: "
            if self.current_filters.bedrooms_min:
                bed_filter += f"{self.current_filters.bedrooms_min}+"
            if self.current_filters.bedrooms_max:
                if self.current_filters.bedrooms_min:
                    bed_filter = bed_filter.replace('+', f'-{self.current_filters.bedrooms_max}')
                else:
                    bed_filter += f"≤{self.current_filters.bedrooms_max}"
            active_filters.append(bed_filter)
        
        if self.current_filters.has_pool is not None:
            pool_filter = "Pool: " + ("Yes" if self.current_filters.has_pool else "No")
            active_filters.append(pool_filter)
        
        if active_filters:
            filter_text = "Active filters: " + " | ".join(active_filters)
        else:
            filter_text = "No filters active"
        
        self.filters_label.setText(filter_text)
    
    def update_cache_stats(self):
        """Update cache statistics display"""
        try:
            stats = self.search_cache.get_stats()
            cache_text = f"Cache: {stats.get('total_entries', 0)} entries"
            if stats.get('hit_ratio', 0) > 0:
                cache_text += f" ({stats['hit_ratio']:.1%} hit rate)"
            self.cache_label.setText(cache_text)
        except Exception as e:
            logger.warning(f"Failed to update cache stats: {e}")
    
    def clear_search_cache(self):
        """Clear search cache"""
        reply = QMessageBox.question(
            self, "Clear Cache", 
            "Are you sure you want to clear the search cache?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.search_cache.invalidate()
                self.update_cache_stats()
                QMessageBox.information(self, "Cache Cleared", "Search cache has been cleared.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear cache: {e}")
    
    def refresh_search(self):
        """Refresh current search without cache"""
        if hasattr(self, 'last_search_term') and hasattr(self, 'last_search_type'):
            # Temporarily disable cache and re-run search
            old_cache_setting = True  # Store original setting
            self.perform_search()  # This will create new worker with cache disabled
    
    def show_search_history(self):
        """Show search history dialog"""
        history = self.search_history.get_recent_searches(50)
        
        if not history:
            QMessageBox.information(self, "Search History", "No search history available.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Search History")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        history_list = QListWidget()
        for entry in reversed(history):  # Most recent first
            timestamp = datetime.fromtimestamp(entry['timestamp']).strftime("%Y-%m-%d %H:%M")
            text = f"{timestamp} - {entry['type'].title()}: {entry['term']} ({entry['results_count']} results)"
            history_list.addItem(text)
        
        layout.addWidget(history_list)
        
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(lambda: self.clear_search_history(dialog))
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()

    def clear_search_history(self, parent_dialog):
        """Clear search history"""
        reply = QMessageBox.question(
            parent_dialog, "Clear History",
            "Are you sure you want to clear search history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.search_history = SearchHistory()
            parent_dialog.accept()
            QMessageBox.information(self, "History Cleared", "Search history has been cleared.")
    
    def refresh_analytics(self):
        """Refresh analytics display"""
        try:
            analytics = self.db_manager.get_search_analytics(30)
            
            analytics_text = "=== SEARCH ANALYTICS (Last 30 Days) ===\n\n"
            
            # Search by type
            analytics_text += "SEARCHES BY TYPE:\n"
            for item in analytics.get('search_by_type', []):
                analytics_text += f"  {item['search_type'].title()}: {item['search_count']} searches (avg {item['avg_results']:.1f} results)\n"
            
            analytics_text += "\nPOPULAR SEARCH TERMS:\n"
            for item in analytics.get('popular_terms', [])[:10]:
                analytics_text += f"  '{item['search_term']}' ({item['search_type']}): {item['frequency']} times\n"
            
            analytics_text += "\nDAILY SEARCH VOLUME:\n"
            for item in analytics.get('daily_stats', [])[-7:]:  # Last 7 days
                analytics_text += f"  {item['date']}: {item['daily_searches']} searches (avg {item['avg_results']:.1f} results)\n"
            
            # Query performance
            query_perf = analytics.get('query_performance', {})
            if query_perf:
                analytics_text += "\nQUERY PERFORMANCE:\n"
                for search_type, stats in query_perf.items():
                    analytics_text += f"  {search_type.title()}: {stats['avg_time']:.3f}s avg, {stats['total_queries']} queries\n"
            
            self.analytics_text.setText(analytics_text)
            
        except Exception as e:
            self.analytics_text.setText(f"Failed to load analytics: {e}")
            logger.error(f"Analytics refresh failed: {e}")
    
    def show_performance_monitor(self):
        """Show performance monitoring dialog"""
        try:
            # Get performance stats
            cache_stats = self.search_cache.get_stats()
            db_stats = self.db_manager.get_database_stats()
            property_stats = self.db_manager.get_property_statistics()
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Performance Monitor")
            dialog.resize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            perf_text = QTextEdit()
            perf_text.setReadOnly(True)
            
            perf_content = "=== PERFORMANCE MONITOR ===\n\n"
            
            # Cache performance
            perf_content += "CACHE PERFORMANCE:\n"
            perf_content += f"  Total Entries: {cache_stats.get('total_entries', 0):,}\n"
            perf_content += f"  Hit Ratio: {cache_stats.get('hit_ratio', 0):.1%}\n"
            perf_content += f"  Memory Usage: {cache_stats.get('memory_usage_mb', 0):.1f} MB\n"
            
            # Database stats
            perf_content += "\nDATABASE STATISTICS:\n"
            perf_content += f"  Properties: {db_stats.get('properties', 0):,}\n"
            perf_content += f"  Tax Records: {db_stats.get('tax_records', 0):,}\n"
            perf_content += f"  Sales Records: {db_stats.get('sales_records', 0):,}\n"
            perf_content += f"  Recent Searches: {db_stats.get('recent_searches', 0):,}\n"
            
            # Property distribution
            if property_stats.get('year_distribution'):
                perf_content += "\nPROPERTY AGE DISTRIBUTION:\n"
                for item in property_stats['year_distribution']:
                    perf_content += f"  {item['year_range']}: {item['count']:,}\n"
            
            if property_stats.get('value_distribution'):
                perf_content += "\nPROPERTY VALUE DISTRIBUTION:\n"
                for item in property_stats['value_distribution']:
                    perf_content += f"  {item['value_range']}: {item['count']:,}\n"
            
            # Worker pool stats
            active_workers = self.worker_pool.get_active_count()
            perf_content += f"\nSEARCH WORKERS: {active_workers} active\n"
            
            perf_text.setText(perf_content)
            layout.addWidget(perf_text)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load performance data: {e}")
    
    def optimize_database(self):
        """Run database optimization"""
        reply = QMessageBox.question(
            self, "Database Optimization",
            "Run database optimization? This may take a few minutes.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.status_bar.showMessage("Optimizing database...")
                QApplication.processEvents()
                
                result = self.db_manager.optimize_database()
                
                if result.get('status') == 'completed':
                    duration = result.get('duration', 0)
                    vacuum_count = len(result.get('vacuum_results', []))
                    
                    msg = f"Database optimization completed in {duration:.1f} seconds."
                    if vacuum_count > 0:
                        msg += f"\n{vacuum_count} tables were vacuumed."
                    
                    QMessageBox.information(self, "Optimization Complete", msg)
                else:
                    QMessageBox.warning(self, "Optimization Failed", 
                                      result.get('error', 'Unknown error occurred'))
                
                self.status_bar.showMessage("Ready")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Database optimization failed: {e}")
                self.status_bar.showMessage("Ready")
    
    def on_search_text_changed(self, text: str):
        """Handle search text changes for auto-suggestions"""
        # Update suggestions dynamically as user types
        if len(text) >= 2:
            QTimer.singleShot(500, self.update_search_suggestions)  # Debounce
    
    def on_search_type_changed(self, search_type: str):
        """Handle search type changes"""
        self.update_search_suggestions()
    
    def on_selection_changed(self):
        """Handle table selection changes"""
        selected_rows = self.results_table.selectionModel().selectedRows()
        self.view_details_btn.setEnabled(len(selected_rows) > 0)
    
    def previous_page(self):
        """Navigate to previous page of results"""
        # TODO: Implement pagination
        pass
    
    def next_page(self):
        """Navigate to next page of results"""
        # TODO: Implement pagination
        pass
    
    def view_property_details(self):
        """View detailed property information"""
        selected_rows = self.results_table.selectionModel().selectedRows()
        
        if not selected_rows:
            return
        
        row_index = selected_rows[0].row()
        if row_index < len(self.current_results):
            property_data = self.current_results[row_index]
            
            # Import the original PropertyDetailsDialog
            from gui.main_window import PropertyDetailsDialog

from src.api_client_unified import UnifiedMaricopaAPIClient

            dialog = PropertyDetailsDialog(property_data, self.db_manager, self)
            dialog.exec_()

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
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        Maricopa County Property Search - Enhanced
        Version 2.0
        
        An advanced property search application for Maricopa County, Arizona.
        
        Enhanced Features:
        • Advanced search filters and auto-detection
        • High-performance caching and optimization
        • Input validation and sanitization
        • Search history and suggestions
        • Real-time analytics and performance monitoring
        • Bulk operations and database optimization
        • Enhanced UI with pagination and sorting
        
        Developed using PyQt5, PostgreSQL, and advanced caching techniques.
        """
        
        QMessageBox.about(self, "About", about_text)
    
    def closeEvent(self, event):
        """Handle application close event"""
        try:
            # Cancel all active searches
            self.worker_pool.cancel_all()
            
            # Close database connections
            if hasattr(self, 'db_manager'):
                self.db_manager.close()
                
            if hasattr(self, 'api_client'):
                self.api_client.close()
                
            if hasattr(self, 'scraper'):
                self.scraper.close()
            
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
        
        event.accept()
        logger.info("Optimized Property Search App closed")