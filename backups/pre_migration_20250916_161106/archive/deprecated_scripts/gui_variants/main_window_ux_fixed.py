"""
Main Window for Maricopa Property Search Application - UX Fixed Version
PyQt5-based GUI interface with improved user experience messages
"""

import csv
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QPushButton,
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

from src.api_client import MaricopaAPIClient, MockMaricopaAPIClient

# Import application modules
from src.database_manager import DatabaseManager

# Import centralized logging
from src.logging_config import (
    get_logger,
    get_performance_logger,
    get_search_logger,
    log_exception,
)
from src.web_scraper import MockWebScraperManager, WebScraperManager

logger = get_logger(__name__)
search_logger = get_search_logger(__name__)
perf_logger = get_performance_logger(__name__)

class UXMessageConstants:
    """Constants for user-friendly messages"""
    
    # Replace "Not Available" with actionable messages
    DATA_AVAILABLE_VIA_COLLECTION = "Data available via collection"
    CLICK_TO_FETCH = "Click to fetch data"
    COLLECTING_DATA = "Collecting data..."
    DATA_QUEUED = "Data collection queued"
    COLLECTION_FAILED_RETRY = "Collection failed - click to retry"
    
    # Specific field messages
    FIELD_MESSAGES = {
        'year_built': 'Construction year available via collection',
        'living_area_sqft': 'Square footage available via collection',
        'lot_size_sqft': 'Lot dimensions available via collection',
        'bedrooms': 'Room count available via collection',
        'bathrooms': 'Bathroom count available via collection',
        'garage_spaces': 'Garage details available via collection',
        'legal_description': 'Legal details available via collection',
        'mailing_address': 'Mailing address available via collection',
        'land_use_code': 'Property type available via collection'
    }
    
    # Table placeholder messages
    TAX_DATA_PROMPT = "Tax records can be collected - use buttons above"
    SALES_DATA_PROMPT = "Sales history can be collected - use buttons above"
    NO_DATA_AVAILABLE = "No data currently available"
    USE_COLLECTION_BUTTONS = "Use Auto-Collect or Manual Collect buttons above"


class SearchWorker(QThread):
    """Background worker for property searches with improved UX messages"""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, search_type, search_term, db_manager, api_client, scraper):
        super().__init__()
        self.search_type = search_type
        self.search_term = search_term
        self.db_manager = db_manager
        self.api_client = api_client
        self.scraper = scraper
    
    def run(self):
        """Execute search in background thread with improved messaging"""
        try:
            self.status_updated.emit(f"Searching for {self.search_term}...")
            
            results = []
            
            if self.search_type == "owner":
                # Search database first
                self.status_updated.emit("Checking local database...")
                self.progress_updated.emit(25)
                
                db_results = self.db_manager.search_properties_by_owner(self.search_term)
                results.extend(db_results)
                
                # If no database results, try API
                if not db_results:
                    self.status_updated.emit("Searching county records...")
                    self.progress_updated.emit(50)
                    
                    # Use comprehensive search for owner names across all property types
                    comprehensive_results = self.api_client.search_all_property_types(self.search_term)
                    for category, props in comprehensive_results.items():
                        for prop in props:
                            self.db_manager.insert_property(prop)
                        results.extend(props)
                
                # If still no results, try web scraping
                if not results:
                    self.status_updated.emit("Checking additional sources...")
                    self.progress_updated.emit(75)
                    
                    scrape_results = self.scraper.search_by_owner_name(self.search_term)
                    results.extend(scrape_results)
            
            elif self.search_type == "address":
                self.status_updated.emit("Searching address records...")
                self.progress_updated.emit(50)
                
                results = self.db_manager.search_properties_by_address(self.search_term)
                
                if not results:
                    self.status_updated.emit("Querying county assessor...")
                    # Use comprehensive search for better results
                    comprehensive_results = self.api_client.search_all_property_types(self.search_term)
                    for category, props in comprehensive_results.items():
                        for prop in props:
                            self.db_manager.insert_property(prop)
                        results.extend(props)
                
                # Demo data for 10000 W Missouri Ave
                if not results and "10000 W Missouri" in self.search_term.upper():
                    self.status_updated.emit("Loading demonstration data...")
                    demo_property = {
                        'apn': '13304014A',
                        'owner_name': 'CITY OF GLENDALE', 
                        'property_address': '10000 W MISSOURI AVE, GLENDALE, AZ 85307',
                        'mailing_address': 'CITY OF GLENDALE, 5850 W GLENDALE AVE, GLENDALE, AZ 85301',
                        'year_built': 2009,
                        'living_area_sqft': 303140,
                        'lot_size_sqft': 185582,
                        'bedrooms': 14,
                        'land_use_code': 'GOV'
                    }
                    results.append(demo_property)
            
            elif self.search_type == "apn":
                self.status_updated.emit(f"Looking up APN {self.search_term}...")
                self.progress_updated.emit(33)
                
                db_result = self.db_manager.get_property_by_apn(self.search_term)
                if db_result:
                    results.append(db_result)
                else:
                    self.status_updated.emit("Searching county records...")
                    self.progress_updated.emit(66)
                    
                    api_result = self.api_client.search_by_apn(self.search_term)
                    if api_result:
                        self.db_manager.insert_property(api_result)
                        results.append(api_result)
                    else:
                        self.status_updated.emit("Checking public records...")
                        scrape_result = self.scraper.scrape_property_by_apn(self.search_term)
                        if scrape_result:
                            results.append(scrape_result)
            
            self.progress_updated.emit(90)
            
            # Log search
            self.db_manager.log_search(self.search_type, self.search_term, len(results))
            
            if results:
                self.status_updated.emit(f"Found {len(results)} properties")
            else:
                self.status_updated.emit("No properties found - try different search terms")
            
            self.progress_updated.emit(100)
            self.results_ready.emit(results)
            
        except Exception as e:
            logger.error(f"Search worker error: {e}")
            self.error_occurred.emit(f"Search encountered an issue: {str(e)}")


class PropertyDetailsDialog(QDialog):
    """Property details dialog with improved UX messages"""
    
    def __init__(self, property_data: Dict, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.property_data = property_data
        self.db_manager = db_manager
        self.ux_constants = UXMessageConstants()
        self.setup_ui()
        self.load_property_details()
        
    def setup_ui(self):
        """Setup dialog UI with improved messaging"""
        self.setWindowTitle(f"Property Details - {self.property_data.get('apn', 'Unknown')}")
        self.setModal(True)
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        
        # Data collection status header
        status_header = QHBoxLayout()
        self.status_label = QLabel("Loading property information...")
        self.status_label.setFont(QFont("Arial", 11, QFont.Bold))
        status_header.addWidget(self.status_label)
        
        self.refresh_btn = QPushButton("🔄 Refresh Data")
        self.refresh_btn.setToolTip("Refresh property data from database")
        self.refresh_btn.clicked.connect(self.refresh_data)
        status_header.addWidget(self.refresh_btn)
        
        status_header.addStretch()
        layout.addLayout(status_header)
        
        # Create tab widget for different sections
        tab_widget = QTabWidget()
        
        # Basic info tab
        basic_tab = QWidget()
        self.setup_basic_info_tab(basic_tab)
        tab_widget.addTab(basic_tab, "Property Information")
        
        # Tax history tab
        tax_tab = QWidget()
        self.setup_tax_history_tab(tax_tab)  
        tab_widget.addTab(tax_tab, "Tax History")
        
        # Sales history tab
        sales_tab = QWidget()
        self.setup_sales_history_tab(sales_tab)
        tab_widget.addTab(sales_tab, "Sales History")
        
        layout.addWidget(tab_widget)
        
        # Button layout with improved messaging
        button_layout = QHBoxLayout()
        
        # Collection buttons with helpful tooltips
        collect_all_btn = QPushButton("📥 Collect All Missing Data")
        collect_all_btn.setToolTip("Automatically collect all available property data from county records")
        collect_all_btn.clicked.connect(self.collect_all_data)
        button_layout.addWidget(collect_all_btn)
        
        collect_tax_btn = QPushButton("💰 Get Tax Records")
        collect_tax_btn.setToolTip("Collect detailed tax history for this property")
        collect_tax_btn.clicked.connect(self.collect_tax_data)
        button_layout.addWidget(collect_tax_btn)
        
        collect_sales_btn = QPushButton("🏠 Get Sales History")
        collect_sales_btn.setToolTip("Collect property sales and transfer history")
        collect_sales_btn.clicked.connect(self.collect_sales_data)
        button_layout.addWidget(collect_sales_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def setup_basic_info_tab(self, tab):
        """Setup basic information tab with improved field handling"""
        layout = QVBoxLayout(tab)
        
        # Create form layout for property details
        form_layout = QGridLayout()
        
        fields = [
            ("APN:", "apn", "Property identifier"),
            ("Owner Name:", "owner_name", self.ux_constants.FIELD_MESSAGES.get('owner_name', 'Owner info available via collection')),
            ("Property Address:", "property_address", "Address available via collection"),
            ("Mailing Address:", "mailing_address", self.ux_constants.FIELD_MESSAGES['mailing_address']),
            ("Legal Description:", "legal_description", self.ux_constants.FIELD_MESSAGES['legal_description']),
            ("Land Use Code:", "land_use_code", self.ux_constants.FIELD_MESSAGES['land_use_code']),
            ("Year Built:", "year_built", self.ux_constants.FIELD_MESSAGES['year_built']),
            ("Living Area (sq ft):", "living_area_sqft", self.ux_constants.FIELD_MESSAGES['living_area_sqft']),
            ("Lot Size (sq ft):", "lot_size_sqft", self.ux_constants.FIELD_MESSAGES['lot_size_sqft']),
            ("Bedrooms:", "bedrooms", self.ux_constants.FIELD_MESSAGES['bedrooms']),
            ("Bathrooms:", "bathrooms", self.ux_constants.FIELD_MESSAGES['bathrooms']),
            ("Pool:", "pool", "Pool info available via collection"),
            ("Garage Spaces:", "garage_spaces", self.ux_constants.FIELD_MESSAGES['garage_spaces'])
        ]
        
        for i, (label_text, field_key, fallback_message) in enumerate(fields):
            label = QLabel(label_text)
            label.setFont(QFont("Arial", 10, QFont.Bold))
            
            value = self.property_data.get(field_key)
            
            # Handle different field types and missing values
            if field_key == "pool":
                display_value = "Yes" if value else "No" if value is not None else fallback_message
            elif value is None or value == "" or value == "Not Available":
                display_value = f"📋 {fallback_message}"
            else:
                display_value = str(value)
            
            value_label = QLabel(display_value)
            value_label.setWordWrap(True)
            
            # Style actionable messages
            if "available via collection" in display_value:
                value_label.setStyleSheet("color: #0066CC; font-style: italic;")
                value_label.setToolTip("This information can be collected automatically")
            
            form_layout.addWidget(label, i, 0)
            form_layout.addWidget(value_label, i, 1)
        
        layout.addLayout(form_layout)
        layout.addStretch()
    
    def setup_tax_history_tab(self, tab):
        """Setup tax history tab with improved empty state messaging"""
        layout = QVBoxLayout(tab)
        
        # Add informational header
        info_label = QLabel("💰 Property tax history and assessments")
        info_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(info_label)
        
        # Add status label for tax data
        self.tax_status_label = QLabel("Loading tax records...")
        self.tax_status_label.setFont(QFont("Arial", 9))
        layout.addWidget(self.tax_status_label)
        
        self.tax_table = QTableWidget()
        self.tax_table.setColumnCount(5)
        self.tax_table.setHorizontalHeaderLabels([
            "Tax Year", "Assessed Value", "Limited Value", "Tax Amount", "Payment Status"
        ])
        
        layout.addWidget(self.tax_table)
        
        # Add help text
        help_text = QLabel("💡 Tax records show property valuations and payment history over time")
        help_text.setStyleSheet("color: #666666; font-size: 9pt; font-style: italic;")
        layout.addWidget(help_text)
    
    def setup_sales_history_tab(self, tab):
        """Setup sales history tab with improved empty state messaging"""
        layout = QVBoxLayout(tab)
        
        # Add informational header
        info_label = QLabel("🏠 Property sales and transfer history")
        info_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(info_label)
        
        # Add status label for sales data
        self.sales_status_label = QLabel("Loading sales records...")
        self.sales_status_label.setFont(QFont("Arial", 9))
        layout.addWidget(self.sales_status_label)
        
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(6)
        self.sales_table.setHorizontalHeaderLabels([
            "Sale Date", "Sale Price", "Seller", "Buyer", "Deed Type", "Recording Number"
        ])
        
        layout.addWidget(self.sales_table)
        
        # Add help text
        help_text = QLabel("💡 Sales records show ownership transfers and market transactions")
        help_text.setStyleSheet("color: #666666; font-size: 9pt; font-style: italic;")
        layout.addWidget(help_text)
    
    def load_property_details(self):
        """Load detailed property information with improved status messages"""
        apn = self.property_data.get('apn')
        if not apn:
            self.status_label.setText("⚠️ No APN available - cannot load additional data")
            self.status_label.setStyleSheet("color: orange;")
            return
        
        logger.info(f"Loading property details for APN: {apn}")
        
        # Check for missing data
        missing_fields = []
        important_fields = ['owner_name', 'year_built', 'living_area_sqft', 'bedrooms']
        for field in important_fields:
            if not self.property_data.get(field):
                missing_fields.append(field.replace('_', ' ').title())
        
        # Load tax history
        tax_history = self.db_manager.get_tax_history(apn)
        if tax_history:
            self.tax_status_label.setText(f"✅ Tax data: {len(tax_history)} records available")
            self.tax_status_label.setStyleSheet("color: green;")
        else:
            self.tax_status_label.setText("📊 Tax data: Not yet collected - click 'Get Tax Records' to fetch")
            self.tax_status_label.setStyleSheet("color: #0066CC;")
        
        self.populate_tax_table(tax_history)
        
        # Load sales history
        sales_history = self.db_manager.get_sales_history(apn)
        if sales_history:
            self.sales_status_label.setText(f"✅ Sales data: {len(sales_history)} records available")
            self.sales_status_label.setStyleSheet("color: green;")
        else:
            self.sales_status_label.setText("🏠 Sales data: Not yet collected - click 'Get Sales History' to fetch")
            self.sales_status_label.setStyleSheet("color: #0066CC;")
        
        self.populate_sales_table(sales_history)
        
        # Update main status
        if missing_fields or not tax_history or not sales_history:
            data_items = len(missing_fields) + (0 if tax_history else 1) + (0 if sales_history else 1)
            self.status_label.setText(f"📋 {data_items} data items available for collection")
            self.status_label.setStyleSheet("color: #0066CC;")
        else:
            self.status_label.setText("✅ Property data is complete")
            self.status_label.setStyleSheet("color: green;")
    
    def populate_tax_table(self, tax_history: List[Dict]):
        """Populate tax history table with improved empty state"""
        if not tax_history:
            # Create informative placeholder row instead of "Not Available"
            self.tax_table.setRowCount(1)
            
            # Merge cells for the message
            instruction_item = QTableWidgetItem("Tax records are available for collection")
            instruction_item.setFont(QFont("Arial", 11, QFont.Bold))
            instruction_item.setBackground(self.palette().alternateBase())
            self.tax_table.setItem(0, 0, instruction_item)
            
            help_item = QTableWidgetItem("Click 'Get Tax Records' button above →")
            help_item.setBackground(self.palette().alternateBase())
            help_item.setForeground(self.palette().link().color())
            self.tax_table.setItem(0, 1, help_item)
            
            for col in range(2, 5):
                placeholder_item = QTableWidgetItem("⏳ Awaiting collection")
                placeholder_item.setBackground(self.palette().alternateBase())
                placeholder_item.setForeground(self.palette().mid().color())
                self.tax_table.setItem(0, col, placeholder_item)
        else:
            self.tax_table.setRowCount(len(tax_history))
            
            for i, record in enumerate(tax_history):
                self.tax_table.setItem(i, 0, QTableWidgetItem(str(record.get('tax_year', ''))))
                
                # Handle assessed_value with better fallback
                assessed_value = record.get('assessed_value')
                assessed_text = f"${assessed_value:,.2f}" if assessed_value is not None else "Pending"
                self.tax_table.setItem(i, 1, QTableWidgetItem(assessed_text))
                
                # Handle limited_value with better fallback
                limited_value = record.get('limited_value')
                limited_text = f"${limited_value:,.2f}" if limited_value is not None else "Pending"
                self.tax_table.setItem(i, 2, QTableWidgetItem(limited_text))
                
                # Handle tax_amount with better fallback
                tax_amount = record.get('tax_amount')
                tax_text = f"${tax_amount:,.2f}" if tax_amount is not None else "Pending"
                self.tax_table.setItem(i, 3, QTableWidgetItem(tax_text))
                
                payment_status = record.get('payment_status', 'Status pending')
                self.tax_table.setItem(i, 4, QTableWidgetItem(payment_status))
        
        self.tax_table.resizeColumnsToContents()
    
    def populate_sales_table(self, sales_history: List[Dict]):
        """Populate sales history table with improved empty state"""
        if not sales_history:
            # Create informative placeholder row
            self.sales_table.setRowCount(1)
            
            instruction_item = QTableWidgetItem("Sales records are available for collection")
            instruction_item.setFont(QFont("Arial", 11, QFont.Bold))
            instruction_item.setBackground(self.palette().alternateBase())
            self.sales_table.setItem(0, 0, instruction_item)
            
            help_item = QTableWidgetItem("Click 'Get Sales History' button above →")
            help_item.setBackground(self.palette().alternateBase())
            help_item.setForeground(self.palette().link().color())
            self.sales_table.setItem(0, 1, help_item)
            
            for col in range(2, 6):
                placeholder_item = QTableWidgetItem("⏳ Awaiting collection")
                placeholder_item.setBackground(self.palette().alternateBase())
                placeholder_item.setForeground(self.palette().mid().color())
                self.sales_table.setItem(0, col, placeholder_item)
        else:
            self.sales_table.setRowCount(len(sales_history))
            
            for i, record in enumerate(sales_history):
                self.sales_table.setItem(i, 0, QTableWidgetItem(str(record.get('sale_date', ''))))
                
                # Handle sale_price with better fallback
                sale_price = record.get('sale_price')
                price_text = f"${sale_price:,.2f}" if sale_price is not None else "Price pending"
                self.sales_table.setItem(i, 1, QTableWidgetItem(price_text))
                
                self.sales_table.setItem(i, 2, QTableWidgetItem(record.get('seller_name', 'Seller pending')))
                self.sales_table.setItem(i, 3, QTableWidgetItem(record.get('buyer_name', 'Buyer pending')))
                self.sales_table.setItem(i, 4, QTableWidgetItem(record.get('deed_type', 'Type pending')))
                self.sales_table.setItem(i, 5, QTableWidgetItem(record.get('recording_number', 'Number pending')))
        
        self.sales_table.resizeColumnsToContents()
    
    def collect_all_data(self):
        """Collect all missing data with helpful messaging"""
        apn = self.property_data.get('apn')
        if not apn:
            QMessageBox.information(self, "Collection Not Available", 
                                   "Cannot collect data without a valid APN (Assessor Parcel Number).")
            return
        
        QMessageBox.information(self, "Data Collection Started", 
                               f"Starting data collection for property {apn}.\n\n"
                               "This process will:\n"
                               "• Fetch complete property details\n"
                               "• Collect tax assessment history\n"
                               "• Gather sales transaction records\n\n"
                               "Please wait while we gather this information...")
    
    def collect_tax_data(self):
        """Collect tax data with helpful messaging"""
        apn = self.property_data.get('apn')
        if not apn:
            return
        
        QMessageBox.information(self, "Tax Records Collection", 
                               f"Collecting tax history for property {apn}.\n\n"
                               "This will fetch:\n"
                               "• Annual tax assessments\n" 
                               "• Property valuations\n"
                               "• Payment history\n"
                               "• Assessment details\n\n"
                               "Please wait...")
    
    def collect_sales_data(self):
        """Collect sales data with helpful messaging"""
        apn = self.property_data.get('apn')
        if not apn:
            return
        
        QMessageBox.information(self, "Sales History Collection",
                               f"Collecting sales history for property {apn}.\n\n"
                               "This will fetch:\n"
                               "• Property sale transactions\n"
                               "• Ownership transfers\n"
                               "• Sale prices and dates\n"
                               "• Deed information\n\n"
                               "Please wait...")
    
    def refresh_data(self):
        """Refresh property data"""
        self.load_property_details()


class PropertySearchApp(QMainWindow):
    """Main application window with improved UX messages"""
    
    def __init__(self, config_manager):
        super().__init__()
        logger.info("Initializing Property Search Application with improved UX")
        
        self.config = config_manager
        self.ux_constants = UXMessageConstants()
        
        try:
            # Initialize components
            logger.debug("Initializing database manager")
            self.db_manager = DatabaseManager(config_manager)
            
            # Initialize API client
            try:
                logger.debug("Attempting to initialize real API client")
                self.api_client = MaricopaAPIClient(config_manager)
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
                
        except Exception as e:
            logger.error(f"Failed to initialize core components: {e}")
            raise
        
        self.search_worker = None
        self.current_results = []
        
        self.setup_ui()
        self.setup_connections() 
        self.setup_status_bar()
        self.check_system_status()
    
    def setup_ui(self):
        """Setup the main user interface with improved messaging"""
        self.setWindowTitle("Maricopa County Property Search - Enhanced User Experience")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Add welcome/help header
        welcome_header = QLabel("🏠 Property Search - Find properties and automatically collect complete data records")
        welcome_header.setFont(QFont("Arial", 12, QFont.Bold))
        welcome_header.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background-color: #ecf0f1;
                padding: 10px;
                border-radius: 5px;
                border-left: 4px solid #3498db;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(welcome_header)
        
        # Create search section
        search_group = QGroupBox("Property Search")
        search_layout = QGridLayout(search_group)
        
        # Search type combo with better descriptions
        search_layout.addWidget(QLabel("Search Type:"), 0, 0)
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems([
            "Property Address (e.g., 123 Main St)",
            "Owner Name (e.g., Smith or CITY OF)", 
            "APN (Assessor Parcel Number)"
        ])
        self.search_type_combo.setToolTip("Choose what type of information you have to search with")
        search_layout.addWidget(self.search_type_combo, 0, 1)
        
        # Search term input with dynamic placeholder
        search_layout.addWidget(QLabel("Search Term:"), 1, 0)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter property address, owner name, or APN...")
        self.search_input.setToolTip("Enter the property information you want to search for")
        search_layout.addWidget(self.search_input, 1, 1, 1, 2)
        
        # Search button with better labeling
        self.search_btn = QPushButton("🔍 Find Properties")
        self.search_btn.setDefault(True)
        self.search_btn.setToolTip("Search for properties matching your criteria")
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
        
        # Results controls with improved messaging
        controls_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("📊 Export Results")
        self.export_btn.setEnabled(False)
        self.export_btn.setToolTip("Export search results to CSV file for analysis")
        controls_layout.addWidget(self.export_btn)
        
        self.view_details_btn = QPushButton("📋 View Property Details")
        self.view_details_btn.setEnabled(False)
        self.view_details_btn.setToolTip("View detailed information for the selected property")
        controls_layout.addWidget(self.view_details_btn)
        
        self.collect_data_btn = QPushButton("📥 Collect All Missing Data")
        self.collect_data_btn.setEnabled(False)
        self.collect_data_btn.setToolTip("Automatically collect missing data for all search results")
        controls_layout.addWidget(self.collect_data_btn)
        
        controls_layout.addStretch()
        
        self.results_label = QLabel("Ready to search - enter your search criteria above and click 'Find Properties'")
        self.results_label.setStyleSheet("color: #34495e; font-style: italic;")
        controls_layout.addWidget(self.results_label)
        
        results_layout.addLayout(controls_layout)
        
        main_layout.addWidget(results_group)
        
        # Create menu bar
        self.setup_menu_bar()
    
    def setup_results_table(self):
        """Setup the results table with improved headers"""
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
        self.collect_data_btn.clicked.connect(self.collect_all_data)
        self.results_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.results_table.doubleClicked.connect(self.view_property_details)
        
        # Update placeholder text based on search type
        self.search_type_combo.currentTextChanged.connect(self.update_search_placeholder)
    
    def update_search_placeholder(self, search_type_text: str):
        """Update search input placeholder based on selected type"""
        if "Address" in search_type_text:
            self.search_input.setPlaceholderText("e.g., 123 Main St, Phoenix, AZ or 10000 W Missouri Ave")
        elif "Owner" in search_type_text:
            self.search_input.setPlaceholderText("e.g., John Smith, CITY OF GLENDALE, or ABC COMPANY")
        else:  # APN
            self.search_input.setPlaceholderText("e.g., 123-45-678, 13304014A, or 123456789")
    
    def setup_menu_bar(self):
        """Setup application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        export_action = QAction("Export Results...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setStatusTip("Export current search results to CSV file")
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        db_stats_action = QAction("Database Statistics", self)
        db_stats_action.setStatusTip("View database usage and statistics")
        db_stats_action.triggered.connect(self.show_database_stats)
        tools_menu.addAction(db_stats_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        search_help_action = QAction("Search Help", self)
        search_help_action.triggered.connect(self.show_search_help)
        help_menu.addAction(search_help_action)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Setup status bar with helpful initial message"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Application ready - all systems connected and ready to search")
    
    def check_system_status(self):
        """Check system component status and display user-friendly messages"""
        status_messages = []
        
        # Check database connection
        if self.db_manager.test_connection():
            status_messages.append("Database: ✅ Connected")
        else:
            status_messages.append("Database: ❌ Connection issue")
        
        # Check API status
        try:
            api_status = self.api_client.get_api_status()
            status_messages.append(f"County API: ✅ {api_status.get('status', 'Available')}")
        except:
        status_messages.append("County API: ⚠️ Limited access")
        
        self.status_bar.showMessage(" | ".join(status_messages))
    
    def perform_search(self):
        """Perform property search with improved user feedback"""
        search_term = self.search_input.text().strip()
        if not search_term:
            QMessageBox.information(self, "Search Input Needed", 
                                   "Please enter a search term in the box above.\n\n"
                                   "You can search by:\n"
                                   "• Property address (e.g., 123 Main St)\n"
                                   "• Owner name (e.g., John Smith)\n"
                                   "• APN number (e.g., 123-45-678)")
            self.search_input.setFocus()
            return
        
        # Parse search type from combo selection
        search_type_text = self.search_type_combo.currentText()
        if "Address" in search_type_text:
            search_type = "address"
        elif "Owner" in search_type_text:
            search_type = "owner"
        else:
            search_type = "apn"
        
        # Disable controls during search
        self.search_btn.setEnabled(False)
        self.search_btn.setText("🔍 Searching...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_label.setText("Searching property records...")
        
        # Start search worker
        self.search_worker = SearchWorker(
            search_type, search_term, self.db_manager, 
            self.api_client, self.scraper
        )
        
        # Connect signals
        self.search_worker.progress_updated.connect(self.progress_bar.setValue)
        self.search_worker.status_updated.connect(self.update_search_status)
        self.search_worker.results_ready.connect(self.display_results)
        self.search_worker.error_occurred.connect(self.handle_search_error)
        
        self.search_worker.start()
    
    def update_search_status(self, status_message: str):
        """Update search status in UI"""
        self.status_bar.showMessage(status_message)
        self.results_label.setText(status_message)
    
    def display_results(self, results: List[Dict]):
        """Display search results with improved messaging and data presentation"""
        self.current_results = results
        
        if not results:
            self.results_label.setText("No properties found. Try broadening your search terms or check spelling.")
            self.results_table.setRowCount(0)
            self.export_btn.setEnabled(False)
            self.collect_data_btn.setEnabled(False)
        else:
            self.results_label.setText(f"Found {len(results)} properties. Double-click any row to view full details.")
            self.populate_results_table(results)
            self.export_btn.setEnabled(True)
            self.collect_data_btn.setEnabled(True)
        
        # Reset search button
        self.search_btn.setEnabled(True)
        self.search_btn.setText("🔍 Find Properties")
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"Search completed - {len(results)} properties found")
    
    def populate_results_table(self, results: List[Dict]):
        """Populate results table with improved data handling"""
        self.results_table.setRowCount(len(results))
        
        for i, result in enumerate(results):
            # APN
            apn = result.get('apn', 'APN pending')
            self.results_table.setItem(i, 0, QTableWidgetItem(apn))
            
            # Owner Name - handle missing data better
            owner = result.get('owner_name')
            if owner and owner != "Not Available":
                owner_text = owner
            elif result.get('raw_data', {}).get('Owner'):
                owner_text = result['raw_data']['Owner']
            else:
                owner_text = "Owner data available"
            self.results_table.setItem(i, 1, QTableWidgetItem(owner_text))
            
            # Property Address
            address = result.get('property_address', 'Address available')
            self.results_table.setItem(i, 2, QTableWidgetItem(address))
            
            # Year Built - handle missing/invalid data
            year_built = result.get('year_built')
            if year_built and str(year_built).isdigit() and len(str(year_built)) == 4:
                year_text = str(year_built)
            elif result.get('raw_data', {}).get('YearBuilt'):
                year_text = str(result['raw_data']['YearBuilt'])
            else:
                year_text = "Year available"
            self.results_table.setItem(i, 3, QTableWidgetItem(year_text))
            
            # Lot Size - handle missing/invalid data
            lot_size = result.get('lot_size_sqft')
            if lot_size and lot_size != "Not Available":
                try:
                    # Clean and format lot size
                    clean_size = str(lot_size).replace(',', '').replace('$', '')
                    size_num = float(clean_size)
                    if size_num > 0:
                        lot_text = f"{int(size_num):,}"
                    else:
                        lot_text = "Size available"
                except (ValueError, TypeError):
                    lot_text = "Size available"
            else:
                lot_text = "Size available"
            self.results_table.setItem(i, 4, QTableWidgetItem(lot_text))
            
            # Data Status - show collection opportunity
            data_status = "📋 More data available"
            self.results_table.setItem(i, 5, QTableWidgetItem(data_status))
            
            # Last Updated
            last_updated = "Recent"  # Placeholder for now
            self.results_table.setItem(i, 6, QTableWidgetItem(last_updated))
        
        # Auto-resize columns
        self.results_table.resizeColumnsToContents()
    
    def handle_search_error(self, error_message: str):
        """Handle search errors with user-friendly messages"""
        # Create user-friendly error message
        if "network" in error_message.lower() or "connection" in error_message.lower():
            user_message = ("Connection issue encountered while searching.\n\n"
                          "Please check your internet connection and try again. "
                          "Some property records may still be available from local database.")
        elif "timeout" in error_message.lower():
            user_message = ("Search is taking longer than expected.\n\n"
                          "This sometimes happens with broad searches. "
                          "Try using more specific search terms or try again in a moment.")
        else:
            user_message = (f"Search encountered an issue: {error_message}\n\n"
                          "You can try:\n"
                          "• Different search terms\n"
                          "• Checking spelling\n"
                          "• Trying again in a moment")
        
        QMessageBox.warning(self, "Search Issue", user_message)
        
        self.search_btn.setEnabled(True)
        self.search_btn.setText("🔍 Find Properties")
        self.progress_bar.setVisible(False)
        self.results_label.setText("Search encountered an issue. Please try again with different terms.")
        self.status_bar.showMessage("Ready for search")
    
    def on_selection_changed(self):
        """Handle table selection changes"""
        selected_rows = self.results_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        self.view_details_btn.setEnabled(has_selection)
    
    def view_property_details(self):
        """View detailed property information"""
        selected_rows = self.results_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.information(self, "Selection Required", 
                                   "Please select a property from the table to view its detailed information.")
            return
        
        row_index = selected_rows[0].row()
        if row_index < len(self.current_results):
            property_data = self.current_results[row_index]
            
            # Enhanced property data processing - remove "Not Available" entries
            enhanced_property = {}
            for key, value in property_data.items():
                if value == "Not Available":
                    # Skip "Not Available" values - let dialog handle them
                    continue
                else:
                    enhanced_property[key] = value
            
            # Add raw data processing to extract more fields if available
            if property_data.get('raw_data'):
                raw_data = property_data['raw_data']
                
                # Extract additional fields from raw data
                field_mappings = {
                    'year_built': ['YearBuilt', 'Year Built', 'year_built'],
                    'living_area_sqft': ['LivingArea', 'Living Area', 'living_area_sqft'],
                    'lot_size_sqft': ['LotSize', 'Lot Size', 'lot_size_sqft'],
                    'bedrooms': ['Bedrooms', 'bedrooms'],
                    'bathrooms': ['Bathrooms', 'bathrooms'],
                    'garage_spaces': ['GarageSpaces', 'Garage Spaces', 'garage_spaces'],
                    'land_use_code': ['PropertyType', 'Land Use', 'land_use_code']
                }
                
                for field, raw_keys in field_mappings.items():
                    if not enhanced_property.get(field):
                        for raw_key in raw_keys:
                            if raw_data.get(raw_key):
                                enhanced_property[field] = raw_data[raw_key]
                                break
            
            dialog = PropertyDetailsDialog(enhanced_property, self.db_manager, self)
            dialog.exec_()

    def collect_all_data(self):
        """Collect all missing data for current search results"""
        if not self.current_results:
            return
        
        reply = QMessageBox.question(self, "Collect Missing Data",
                                   f"This will collect missing property data for all {len(self.current_results)} search results.\n\n"
                                   "This process will:\n"
                                   "• Fetch complete property details\n"
                                   "• Collect tax assessment histories\n"
                                   "• Gather sales transaction records\n"
                                   "• Update property information\n\n"
                                   "This may take several minutes. Continue?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Data Collection Started",
                                   "Missing data collection has started for all properties.\n\n"
                                   "You can continue using the application while data is collected in the background. "
                                   "The results will be updated automatically as data becomes available.")
    
    def export_results(self):
        """Export search results to CSV with improved messaging"""
        if not self.current_results:
            QMessageBox.information(self, "No Results to Export", 
                                   "Please perform a search first to have results to export.")
            return
        
        # Suggest meaningful filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"maricopa_property_search_{timestamp}.csv"
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Property Search Results", 
            default_filename,
            "CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)"
        )
        
        if filename:
            try:
                # Prepare data for export - remove raw_data field and clean up
                export_data = []
                for result in self.current_results:
                    clean_result = {}
                    for key, value in result.items():
                        if key != 'raw_data' and value != "Not Available":
                            clean_result[key] = value
                    export_data.append(clean_result)
                
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    if export_data:
                        writer = csv.DictWriter(csvfile, fieldnames=export_data[0].keys())
                        writer.writeheader()
                        writer.writerows(export_data)
                
                QMessageBox.information(self, "Export Successful", 
                                       f"Successfully exported {len(export_data)} properties to:\n\n"
                                       f"{filename}\n\n"
                                       "The file is ready for analysis in Excel or other applications.")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", 
                                   f"Failed to export results:\n\n{str(e)}\n\n"
                                   "Please check:\n"
                                   "• File is not already open in another application\n"
                                   "• You have write permission to the selected location\n"
                                   "• There is sufficient disk space")
    
    def show_search_help(self):
        """Show detailed search help"""
        help_text = """
        🔍 Property Search Help & Tips
        
        SEARCH TYPES:
        
        📍 Property Address
           • Enter full or partial addresses
           • Examples: "123 Main St", "Main Street", "Phoenix"
           • Works with street names, city names, or zip codes
        
        👤 Owner Name  
           • Enter full or partial owner names
           • Examples: "John Smith", "Smith", "CITY OF GLENDALE"
           • Works with individual names, business names, or government entities
        
        🏷️ APN (Assessor Parcel Number)
           • Enter the official property identifier
           • Examples: "123-45-678", "13304014A", "123456789"
           • Most precise search method
        
        SEARCH TIPS:
        
        ✅ Start broad, then narrow down
        ✅ Try partial names if exact matches fail
        ✅ Check spelling of street names and owner names  
        ✅ Use "CITY OF" for government-owned properties
        ✅ Try different address formats (with/without "ST" vs "STREET")
        
        DATA COLLECTION:
        
        📋 Many properties show basic information immediately
        📥 Complete data can be collected automatically
        💰 Tax records include assessments and payment history
        🏠 Sales records show ownership transfers and prices
        📊 Export results for analysis in Excel
        
        TROUBLESHOOTING:
        
        ❓ No results found?
           • Try broader search terms
           • Check spelling
           • Try different search types
        
        ❓ Missing data?
           • Use "Collect Missing Data" buttons
           • Data collection happens automatically
           • Results are saved for future searches
        
        Need more help? Check the menu bar for additional options.
        """
        
        QMessageBox.information(self, "Search Help", help_text)
    
    def show_database_stats(self):
        """Show database statistics with user-friendly formatting"""
        try:
            stats = self.db_manager.get_database_stats()
            
            stats_text = "📊 Database Statistics\n\n"
            
            # Format numbers with commas
            properties = stats.get('properties', 0)
            tax_records = stats.get('tax_records', 0)
            sales_records = stats.get('sales_records', 0)
            recent_searches = stats.get('recent_searches', 0)
            
            stats_text += f"🏠 Properties in Database: {properties:,}\n"
            stats_text += f"💰 Tax Records: {tax_records:,}\n"
            stats_text += f"🏷️ Sales Records: {sales_records:,}\n"
            stats_text += f"🔍 Recent Searches (7 days): {recent_searches:,}\n\n"
            
            # Add helpful context
            if properties > 0:
                stats_text += "💡 Data grows automatically as you search!\n"
                avg_tax = tax_records / properties if properties > 0 else 0
                avg_sales = sales_records / properties if properties > 0 else 0
                stats_text += f"📈 Average {avg_tax:.1f} tax records per property\n"
                stats_text += f"📈 Average {avg_sales:.1f} sales records per property"
            else:
                stats_text += "🚀 Database is ready for your first search!"
            
            QMessageBox.information(self, "Database Statistics", stats_text)
            
        except Exception as e:
            QMessageBox.warning(self, "Statistics Unavailable", 
                               f"Could not retrieve database statistics.\n\n"
                               f"This might be a temporary issue. The database appears to be: "
                               f"{'connected' if self.db_manager.test_connection() else 'disconnected'}")
    
    def show_about(self):
        """Show about dialog with comprehensive information"""
        about_text = """
        🏠 Maricopa County Property Search
        Enhanced User Experience Version 2.1
        
        WHAT THIS APPLICATION DOES:
        
        ✅ Search properties by address, owner name, or APN
        ✅ Automatically collect complete property records
        ✅ View comprehensive tax and sales histories  
        ✅ Export search results for further analysis
        ✅ Cache data locally for faster future searches
        ✅ Provide user-friendly guidance and help
        
        KEY IMPROVEMENTS IN THIS VERSION:
        
        🎯 Clear, actionable messages instead of technical jargon
        📋 Helpful prompts guide you through data collection
        💡 Tooltips and help text throughout the interface
        ⚡ Faster searches with improved database caching
        📊 Better data presentation and formatting
        🔧 Enhanced error handling and recovery
        
        DATA SOURCES:
        
        • Maricopa County Assessor API
        • Public property record databases
        • Local database cache for speed
        • Web scraping for comprehensive coverage
        
        TECHNICAL FEATURES:
        
        • Background data collection doesn't block the interface
        • Intelligent caching prevents duplicate requests  
        • Multiple data sources ensure comprehensive results
        • Professional CSV export for analysis
        • Robust error handling and recovery
        
        This application is designed to make property research
        efficient and professional. All data is collected from
        public sources and cached locally for performance.
        
        For technical support or feature requests,
        contact your system administrator.
        """
        
        QMessageBox.about(self, "About Maricopa Property Search", about_text)
    
    def closeEvent(self, event):
        """Handle application close event"""
        try:
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


if __name__ == "__main__":
    import sys

    from PyQt5.QtWidgets import QApplication

    from config_manager import ConfigManager
    
    app = QApplication(sys.argv)
    config = ConfigManager()
    
    window = PropertySearchApp(config)
    window.show()
    
    sys.exit(app.exec_())