import logging
import os
import sqlite3
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PyQt5.QtCore import (
    QAbstractAnimation,
    QDate,
    QEasingCurve,
    QEventLoop,
    QMutex,
    QMutexLocker,
    QObject,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QRect,
    QRunnable,
    QSequentialAnimationGroup,
    QSettings,
    QSize,
    Qt,
    QThread,
    QThreadPool,
    QTimer,
)
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QFont,
    QFontMetrics,
    QIcon,
    QLinearGradient,
    QMovie,
    QPainter,
    QPalette,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QButtonGroup,
    QCalendarWidget,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
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
    QMessageBox,
    QProgressBar,
    QProgressDialog,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

# QtCharts import - PyQt5 version
try:
    from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis

except ImportError:
    # Fallback if QtChart not available
    QChart = QChartView = QLineSeries = QValueAxis = None

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from src.background_data_collector import BackgroundDataCollectionManager, JobPriority
from src.batch_processing_manager import BatchProcessingManager

# MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
# MIGRATED: from database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.enhanced_config_manager import EnhancedConfigManager
from src.threadsafe_database_manager import ThreadSafeDatabaseManager

try:
    # MIGRATED: from api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
except ImportError:
    UnifiedMaricopaAPIClient = None
# Optional imports - only if they exist
try:
    # MIGRATED: from batch_api_client import BatchAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
try:
    from src.api_client_unified import UnifiedMaricopaAPIClient
except ImportError:
    pass

except ImportError:
    UnifiedMaricopaAPIClient = None

try:
from src.batch_search_engine import BatchSearchEngine

except ImportError:
    BatchSearchEngine = None
# Import existing GUI components
try:
from src.gui.gui_enhancements_dialogs import ApplicationSettingsDialog

except ImportError:
    ApplicationSettingsDialog = None
# All other GUI components can be imported on-demand

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Placeholder classes for missing components
class PropertySearchEngine:
    """Placeholder search engine for property queries"""
    def __init__(self, db_manager):
        self.db_manager = db_manager
    def search_properties(
        self,
        search_term,
        filters=None,
        include_tax_history=False,
        include_sales_history=False,
    ):
        """Search for properties based on the search term"""
    try:
            # For now, return mock data to allow GUI to function
            if not search_term:
                return []

            # Create some mock results for testing
            mock_results = []
            for i in range(3):
                mock_results.append(
                    {
                        "apn": f"123-45-{i+100:03d}",
                        "address": f"{1000+i} Example St, Phoenix, AZ 85001",
                        "owner_name": f"John Doe {i+1}",
                        "property_type": "Residential",
                        "year_built": 2000 + i,
                        "square_feet": 1500 + (i * 100),
                        "bedrooms": 3,
                        "bathrooms": 2,
                        "market_value": 300000 + (i * 50000),
                        "assessed_value": 250000 + (i * 40000),
                        "last_sale_date": "2023-01-01",
                        "last_sale_amount": 280000 + (i * 30000),
                    }
                )

            return mock_results
    except Exception as e:
            logger.error(f"Search error in PropertySearchEngine: {e}")
            return []


class PerformanceMetrics:
    """Placeholder performance metrics tracker"""
    def __init__(self):
        self.searches = []
        self.total_time = 0
    def record_search(self, search_term, result_count, search_time):
        """Record a search operation"""
        self.searches.append(
            {"term": search_term, "count": result_count, "time": search_time}
        )
        self.total_time += search_time
    def get_summary(self):
        """Get performance summary"""
        if not self.searches:
            return {
                "total_searches": 0,
                "avg_time": 0.0,
                "success_rate": 0.0,
                "cache_hits": 0,
            }

        return {
            "total_searches": len(self.searches),
            "avg_time": self.total_time / len(self.searches),
            "success_rate": 100.0,  # Mock success rate
            "cache_hits": 0,
        }


class BackupManager:
    """Placeholder backup manager"""
    def __init__(self, db_manager):
        self.db_manager = db_manager
    def create_backup(self):
        """Create a database backup"""
    try:
            # Mock backup creation
            backup_path = "backup_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".db"
            logger.info(f"Mock backup created: {backup_path}")
            return backup_path
    except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return None


class DataValidator:
    """Placeholder data validator"""
    def __init__(self, db_manager):
        self.db_manager = db_manager
    def validate_all_data(self):
        """Validate all database data"""
        # Return mock validation results
        return {"properties": [], "tax_records": [], "sales_records": []}


class PropertyDetailsWidget(QWidget):
    """Widget for displaying detailed property information"""
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.current_apn = None
        self.setup_ui()
    def setup_ui(self):
        """Set up the property details UI"""
        layout = QVBoxLayout(self)

        # Property information display
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        layout.addWidget(self.info_text)

        # Set placeholder text
        self.info_text.setPlainText(
            "Select a property from the search results to view details here."
        )
    def load_property_data(self, apn):
        """Load detailed data for a property"""
        self.current_apn = apn
    try:
            # Mock property details
            details = f"""
Property Details for APN: {apn}

Basic Information:
- APN: {apn}
- Address: 1234 Example Street, Phoenix, AZ 85001
- Owner: John Doe
- Property Type: Residential

Property Characteristics:
- Year Built: 2005
- Square Feet: 1,800
- Bedrooms: 3
- Bathrooms: 2
- Lot Size: 0.25 acres

Valuation:
- Market Value: $350,000
- Assessed Value: $290,000
- Tax Assessment: $3,200/year

Recent Sales History:
- Last Sale: 2021-03-15 for $320,000
- Previous Sale: 2018-07-22 for $280,000

Tax History:
- 2023: $3,200
- 2022: $3,100
- 2021: $2,950

This is mock data for development purposes.
            """

            self.info_text.setPlainText(details)

    except Exception as e:
            logger.error(f"Failed to load property data for {apn}: {e}")
            self.info_text.setPlainText(f"Error loading data for APN {apn}: {str(e)}")


class PerformanceDashboard(QWidget):
    """Dashboard for performance monitoring"""
    def __init__(self, performance_metrics):
        super().__init__()
        self.performance_metrics = performance_metrics
        self.setup_ui()
    def setup_ui(self):
        """Set up the performance dashboard UI"""
        layout = QVBoxLayout(self)

        # Performance overview
        overview_group = QGroupBox("Performance Overview")
        overview_layout = QGridLayout(overview_group)

        self.total_searches_label = QLabel("0")
        self.avg_time_label = QLabel("0.00s")
        self.success_rate_label = QLabel("100%")

        overview_layout.addWidget(QLabel("Total Searches:"), 0, 0)
        overview_layout.addWidget(self.total_searches_label, 0, 1)
        overview_layout.addWidget(QLabel("Average Time:"), 1, 0)
        overview_layout.addWidget(self.avg_time_label, 1, 1)
        overview_layout.addWidget(QLabel("Success Rate:"), 2, 0)
        overview_layout.addWidget(self.success_rate_label, 2, 1)

        layout.addWidget(overview_group)

        # Chart placeholder
        chart_group = QGroupBox("Performance Chart")
        chart_layout = QVBoxLayout(chart_group)
        chart_placeholder = QLabel("Performance chart would be displayed here")
        chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_placeholder.setMinimumHeight(200)
        chart_placeholder.setStyleSheet(
            "border: 1px solid #ccc; background-color: #f9f9f9;"
        )
        chart_layout.addWidget(chart_placeholder)

        layout.addWidget(chart_group)
        layout.addStretch()


class SearchHistoryWidget(QWidget):
    """Widget for displaying search history"""
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.search_history = []
        self.setup_ui()
    def setup_ui(self):
        """Set up the search history UI"""
        layout = QVBoxLayout(self)

        # History list
        self.history_list = QListWidget()
        layout.addWidget(self.history_list)

        # Clear button
        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self.clear_history)
        layout.addWidget(clear_btn)
    def add_search(self, search_term, result_count, search_time):
        """Add a search to history"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        history_text = f"{timestamp} - '{search_term}' ({result_count} results, {search_time:.2f}s)"

        item = QListWidgetItem(history_text)
        self.history_list.insertItem(0, item)

        # Keep only last 50 items
        while self.history_list.count() > 50:
            self.history_list.takeItem(self.history_list.count() - 1)
    def clear_history(self):
        """Clear all search history"""
        self.history_list.clear()


class SystemHealthWidget(QWidget):
    """Widget for monitoring system health"""
    def __init__(self, db_manager, background_manager):
        super().__init__()
        self.db_manager = db_manager
        self.background_manager = background_manager
        self.setup_ui()
    def setup_ui(self):
        """Set up the system health UI"""
        layout = QVBoxLayout(self)

        # System status
        status_group = QGroupBox("System Status")
        status_layout = QGridLayout(status_group)

        self.db_status_label = QLabel("Connected")
        self.memory_usage_label = QLabel("150 MB")
        self.cpu_usage_label = QLabel("5%")

        status_layout.addWidget(QLabel("Database:"), 0, 0)
        status_layout.addWidget(self.db_status_label, 0, 1)
        status_layout.addWidget(QLabel("Memory:"), 1, 0)
        status_layout.addWidget(self.memory_usage_label, 1, 1)
        status_layout.addWidget(QLabel("CPU:"), 2, 0)
        status_layout.addWidget(self.cpu_usage_label, 2, 1)

        layout.addWidget(status_group)
        layout.addStretch()


class BackgroundStatusWidget(QWidget):
    """Widget for displaying background collection status"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
    def setup_ui(self):
        """Set up the background status UI"""
        layout = QVBoxLayout(self)

        # Status display
        self.status_label = QLabel("Idle")
        self.progress_bar = QProgressBar()
        self.job_count_label = QLabel("Jobs: 0 pending, 0 active, 0 completed")

        layout.addWidget(QLabel("Collection Status:"))
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.job_count_label)
    def update_status(self, status_dict):
        """Update the status display"""
    try:
            if isinstance(status_dict, dict):
                status = status_dict.get("status", "Unknown")
                pending = status_dict.get("pending_jobs", 0)
                active = status_dict.get("active_jobs", 0)
                completed = status_dict.get("completed_jobs", 0)

                self.status_label.setText(status)
                self.job_count_label.setText(
                    f"Jobs: {pending} pending, {active} active, {completed} completed"
                )

                # Update progress bar
                total_jobs = pending + active + completed
                if total_jobs > 0:
                    progress = int((completed / total_jobs) * 100)
                    self.progress_bar.setValue(progress)
                else:
                    self.progress_bar.setValue(0)
    except Exception as e:
            logger.error(f"Failed to update background status: {e}")


class DataValidationWidget(QWidget):
    """Widget for displaying data validation results"""
    def __init__(self, data_validator):
        super().__init__()
        self.data_validator = data_validator
        self.setup_ui()
    def setup_ui(self):
        """Set up the data validation UI"""
        layout = QVBoxLayout(self)

        # Validation status
        self.validation_label = QLabel("No validation performed")
        layout.addWidget(self.validation_label)

        # Issues list
        self.issues_list = QListWidget()
        layout.addWidget(self.issues_list)

        # Validate button
        validate_btn = QPushButton("Run Validation")
        validate_btn.clicked.connect(self.run_validation)
        layout.addWidget(validate_btn)
    def update_results(self, validation_results):
        """Update validation results display"""
        self.issues_list.clear()

        total_issues = 0
        for category, issues in validation_results.items():
            if isinstance(issues, list):
                total_issues += len(issues)
                for issue in issues:
                    self.issues_list.addItem(f"{category}: {issue}")

        if total_issues == 0:
            self.validation_label.setText("✓ All data valid")
            self.validation_label.setStyleSheet("color: green;")
        else:
            self.validation_label.setText(f"⚠ {total_issues} issues found")
            self.validation_label.setStyleSheet("color: orange;")
    def run_validation(self):
        """Run data validation"""
    try:
            results = self.data_validator.validate_all_data()
            self.update_results(results)
    except Exception as e:
            logger.error(f"Validation failed: {e}")


# Placeholder dialog classes
class CollectionProgressDialog(QDialog):
    """Dialog for monitoring collection progress"""
    def __init__(self, background_manager):
        super().__init__()
        self.background_manager = background_manager
        self.setWindowTitle("Data Collection Progress")
        self.setModal(False)
        self.resize(500, 300)
        self.setup_ui()
    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)

        self.progress_bar = QProgressBar()
        self.status_label = QLabel("Collection in progress...")

        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    def update_progress(self):
        """Update progress display"""
        if self.background_manager:
            status = self.background_manager.get_collection_status()
            # Update UI based on status
            pass


class BatchSearchDialog(QDialog):
    """Dialog for batch search operations"""

    search_completed = Signal(list)
    def __init__(self, batch_manager):
        super().__init__()
        self.batch_manager = batch_manager
        self.setWindowTitle("Batch Search")
        self.setModal(True)
        self.resize(400, 200)
        self.setup_ui()
    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Batch search functionality not yet implemented"))

        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)


class ExportDialog(QDialog):
    """Dialog for exporting search results"""
    def __init__(self, results, db_manager):
        super().__init__()
        self.results = results
        self.db_manager = db_manager
        self.setWindowTitle("Export Results")
        self.setModal(True)
        self.resize(400, 200)
        self.setup_ui()
    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Export {len(self.results)} results"))
        layout.addWidget(QLabel("Export functionality not yet implemented"))

        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)


class SettingsDialog(QDialog):
    """Dialog for application settings"""
    def __init__(self, db_manager, background_manager):
        super().__init__()
        self.db_manager = db_manager
        self.background_manager = background_manager
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Settings dialog not yet implemented"))

        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)


class BackupRestoreDialog(QDialog):
    """Dialog for backup and restore operations"""
    def __init__(self, backup_manager):
        super().__init__()
        self.backup_manager = backup_manager
        self.setWindowTitle("Backup & Restore")
        self.setModal(True)
        self.resize(500, 300)
        self.setup_ui()
    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Backup & Restore functionality not yet implemented"))

        # Buttons
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)


class CollectionQueueViewer(QDialog):
    """Dialog for viewing the collection queue"""
    def __init__(self, background_manager):
        super().__init__()
        self.background_manager = background_manager
        self.setWindowTitle("Collection Queue")
        self.setModal(True)
        self.resize(600, 400)
        self.setup_ui()
    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Collection queue viewer not yet implemented"))

        # Buttons
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)


class AdvancedFiltersWidget(QWidget):
    """Advanced filters widget for search refinement"""
    def __init__(self):
        super().__init__()
        self.init_ui()
    def init_ui(self):
        """Initialize the advanced filters UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Property type filter
        type_group = QGroupBox("Property Type")
        type_layout = QHBoxLayout(type_group)

        self.residential_cb = QCheckBox("Residential")
        self.commercial_cb = QCheckBox("Commercial")
        self.vacant_cb = QCheckBox("Vacant Land")

        type_layout.addWidget(self.residential_cb)
        type_layout.addWidget(self.commercial_cb)
        type_layout.addWidget(self.vacant_cb)
        layout.addWidget(type_group)

        # Value range filter
        value_group = QGroupBox("Property Value Range")
        value_layout = QGridLayout(value_group)

        value_layout.addWidget(QLabel("Min Value:"), 0, 0)
        self.min_value_edit = QLineEdit()
        self.min_value_edit.setPlaceholderText("$0")
        value_layout.addWidget(self.min_value_edit, 0, 1)

        value_layout.addWidget(QLabel("Max Value:"), 0, 2)
        self.max_value_edit = QLineEdit()
        self.max_value_edit.setPlaceholderText("$1,000,000+")
        value_layout.addWidget(self.max_value_edit, 0, 3)

        layout.addWidget(value_group)

        # Year built filter
        year_group = QGroupBox("Year Built")
        year_layout = QHBoxLayout(year_group)

        year_layout.addWidget(QLabel("From:"))
        self.year_from_edit = QLineEdit()
        self.year_from_edit.setPlaceholderText("1900")
        year_layout.addWidget(self.year_from_edit)

        year_layout.addWidget(QLabel("To:"))
        self.year_to_edit = QLineEdit()
        self.year_to_edit.setPlaceholderText("2025")
        year_layout.addWidget(self.year_to_edit)

        layout.addWidget(year_group)

        # Filter buttons
        button_layout = QHBoxLayout()

        self.apply_btn = QPushButton("Apply Filters")
        self.clear_btn = QPushButton("Clear All")

        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Connect signals
        self.clear_btn.clicked.connect(self.clear_filters)
    def clear_filters(self):
        """Clear all filter values"""
        self.residential_cb.setChecked(False)
        self.commercial_cb.setChecked(False)
        self.vacant_cb.setChecked(False)
        self.min_value_edit.clear()
        self.max_value_edit.clear()
        self.year_from_edit.clear()
        self.year_to_edit.clear()
    def get_filters(self):
        """Get current filter values as dictionary"""
        return {
            "property_types": {
                "residential": self.residential_cb.isChecked(),
                "commercial": self.commercial_cb.isChecked(),
                "vacant": self.vacant_cb.isChecked(),
            },
            "value_range": {
                "min": self.min_value_edit.text(),
                "max": self.max_value_edit.text(),
            },
            "year_built": {
                "from": self.year_from_edit.text(),
                "to": self.year_to_edit.text(),
            },
        }


class NotificationArea(QWidget):
    """A notification area for displaying system messages"""
    def __init__(self):
        super().__init__()
        self.setMaximumHeight(100)
        self.setStyleSheet(
            """
            QWidget {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """
        )

        layout = QVBoxLayout(self)
        self.message_label = QLabel("Ready")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
    def show_message(self, message: str, message_type: str = "info"):
        """Show a notification message"""
        colors = {
            "info": "#d4edda",
            "warning": "#fff3cd",
            "error": "#f8d7da",
            "success": "#d1ecf1",
        }

        self.message_label.setText(message)
        color = colors.get(message_type, colors["info"])
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {color};
                border: 1px solid #ccc;
                border-radius: 5px;
            }}
        """
        )


class StatusIndicator(QWidget):
    """Visual status indicator widget"""
    def __init__(self):
        super().__init__()
        self.setFixedSize(20, 20)
        self.status = "idle"  # idle, working, success, error
    def set_status(self, status: str):
        """Set the status and update visual appearance"""
        self.status = status
        self.update()
    def paintEvent(self, event):
        """Custom paint event for the status indicator"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        colors = {
            "idle": QColor(128, 128, 128),  # Gray
            "working": QColor(255, 165, 0),  # Orange
            "success": QColor(0, 255, 0),  # Green
            "error": QColor(255, 0, 0),  # Red
        }

        color = colors.get(self.status, colors["idle"])
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(), 2))
        painter.drawEllipse(2, 2, 16, 16)


class AnimatedProgressBar(QProgressBar):
    """Enhanced progress bar with animations"""
    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #05B8CC, stop:1 #0D7377);
                border-radius: 3px;
            }
        """
        )

        # Add animation
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    def set_animated_value(self, value: int):
        """Set value with smooth animation"""
        self.animation.setStartValue(self.value())
        self.animation.setEndValue(value)
        self.animation.start()


class SearchMetricsWidget(QWidget):
    """Widget for displaying search metrics"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.reset_metrics()
    def setup_ui(self):
        """Set up the metrics UI"""
        layout = QGridLayout(self)

        # Metrics labels
        self.total_searches_label = QLabel("0")
        self.avg_time_label = QLabel("0.00s")
        self.success_rate_label = QLabel("0%")
        self.cache_hits_label = QLabel("0")

        # Add labels with descriptions
        layout.addWidget(QLabel("Total Searches:"), 0, 0)
        layout.addWidget(self.total_searches_label, 0, 1)
        layout.addWidget(QLabel("Avg Time:"), 1, 0)
        layout.addWidget(self.avg_time_label, 1, 1)
        layout.addWidget(QLabel("Success Rate:"), 2, 0)
        layout.addWidget(self.success_rate_label, 2, 1)
        layout.addWidget(QLabel("Cache Hits:"), 3, 0)
        layout.addWidget(self.cache_hits_label, 3, 1)
    def update_metrics(self, metrics: Dict[str, Any]):
        """Update the displayed metrics"""
        self.total_searches_label.setText(str(metrics.get("total_searches", 0)))
        self.avg_time_label.setText(f"{metrics.get('avg_time', 0.0):.2f}s")
        self.success_rate_label.setText(f"{metrics.get('success_rate', 0.0):.1f}%")
        self.cache_hits_label.setText(str(metrics.get("cache_hits", 0)))
    def reset_metrics(self):
        """Reset all metrics to zero"""
        self.update_metrics({})


class DatabaseConnectionWidget(QWidget):
    """Widget for managing database connections"""
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setup_ui()
    def setup_ui(self):
        """Set up the database connection UI"""
        layout = QVBoxLayout(self)

        # Connection status
        self.status_label = QLabel("Checking connection...")
        layout.addWidget(self.status_label)

        # Database info
        info_layout = QGridLayout()
        self.db_path_label = QLabel("N/A")
        self.db_size_label = QLabel("N/A")
        self.tables_count_label = QLabel("N/A")

        info_layout.addWidget(QLabel("Database:"), 0, 0)
        info_layout.addWidget(self.db_path_label, 0, 1)
        info_layout.addWidget(QLabel("Size:"), 1, 0)
        info_layout.addWidget(self.db_size_label, 1, 1)
        info_layout.addWidget(QLabel("Tables:"), 2, 0)
        info_layout.addWidget(self.tables_count_label, 2, 1)

        layout.addLayout(info_layout)

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_property_data)
        layout.addWidget(self.refresh_btn)

        # Initial status update
        self.update_status()
    def update_status(self):
        """Update the database connection status"""
    try:
            # Check connection
            if self.db_manager.test_connection():
                self.status_label.setText("✓ Connected")
                self.status_label.setStyleSheet("color: green;")

                # Update database info
                db_info = self.db_manager.get_database_info()
                self.db_path_label.setText(db_info.get("path", "N/A"))
                self.db_size_label.setText(f"{db_info.get('size_mb', 0):.1f} MB")
                self.tables_count_label.setText(str(db_info.get("table_count", 0)))

            else:
                self.status_label.setText("✗ Disconnected")
                self.status_label.setStyleSheet("color: red;")

    except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            logger.error(f"Database connection check failed: {e}")


class RecentSearchesWidget(QWidget):
    """Widget for displaying recent searches"""

    search_selected = Signal(str)  # Emitted when a search is selected
    def __init__(self):
        super().__init__()
        self.max_items = 10
        self.setup_ui()
    def setup_ui(self):
        """Set up the recent searches UI"""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Recent Searches")
        header.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(header)

        # Search list
        self.search_list = QListWidget()
        self.search_list.setMaximumHeight(150)
        self.search_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.search_list)

        # Clear button
        clear_btn = QPushButton("Clear History")
        clear_btn.setMaximumWidth(100)
        clear_btn.clicked.connect(self.clear_history)
        layout.addWidget(clear_btn)
    def add_search(self, search_term: str):
        """Add a search term to the recent list"""
        # Remove if already exists
        for i in range(self.search_list.count()):
            if self.search_list.item(i).text() == search_term:
                self.search_list.takeItem(i)
                break

        # Add to top
        item = QListWidgetItem(search_term)
        self.search_list.insertItem(0, item)

        # Remove excess items
        while self.search_list.count() > self.max_items:
            self.search_list.takeItem(self.search_list.count() - 1)
    def _on_item_clicked(self, item):
        """Handle item click"""
        self.search_selected.emit(item.text())
    def clear_history(self):
        """Clear all search history"""
        self.search_list.clear()


class QuickStatsWidget(QWidget):
    """Widget for displaying quick database statistics"""
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setup_ui()
        self.update_stats()
    def setup_ui(self):
        """Set up the quick stats UI"""
        layout = QGridLayout(self)

        # Stat labels
        self.property_count_label = QLabel("0")
        self.tax_records_label = QLabel("0")
        self.sales_records_label = QLabel("0")
        self.last_update_label = QLabel("Never")

        # Style labels
        for label in [
            self.property_count_label,
            self.tax_records_label,
            self.sales_records_label,
        ]:
            label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Add to layout
        layout.addWidget(QLabel("Properties:"), 0, 0)
        layout.addWidget(self.property_count_label, 0, 1)
        layout.addWidget(QLabel("Tax Records:"), 1, 0)
        layout.addWidget(self.tax_records_label, 1, 1)
        layout.addWidget(QLabel("Sales Records:"), 2, 0)
        layout.addWidget(self.sales_records_label, 2, 1)
        layout.addWidget(QLabel("Last Update:"), 3, 0)
        layout.addWidget(self.last_update_label, 3, 1)
    def update_stats(self):
        """Update the quick statistics"""
    try:
            stats = self.db_manager.get_quick_stats()
            self.property_count_label.setText(f"{stats.get('property_count', 0):,}")
            self.tax_records_label.setText(f"{stats.get('tax_records', 0):,}")
            self.sales_records_label.setText(f"{stats.get('sales_records', 0):,}")

            last_update = stats.get("last_update")
            if last_update:
                self.last_update_label.setText(last_update)
            else:
                self.last_update_label.setText("Never")

    except Exception as e:
            logger.error(f"Failed to update quick stats: {e}")


class EnhancedMainWindow(QMainWindow):
    """Enhanced main window with modern UI and advanced features"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Maricopa County Property Search - Enhanced")
        self.setGeometry(100, 100, 1400, 900)

        # Initialize core components
        self.db_manager = None
        self.search_engine = None
        self.background_manager = None
        self.batch_manager = None
        self.performance_metrics = None
        self.backup_manager = None

        # UI components
        self.results_table = None
        self.search_input = None
        self.status_bar = None
        self.notification_area = None
        self.property_details = None
        self.search_history = None
        self.performance_dashboard = None

        # Background processing
        self.current_search_thread = None
        self.progress_dialog = None
        self.collection_dialog = None

        # Initialize database first
        self.init_database()

        # Then initialize other components
        self.init_components()

        # Set up UI
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_status_bar()

        # Apply modern styling
        self.apply_modern_style()

        # Connect signals
        self.connect_signals()

        # Initialize background services
        self.init_background_services()

        # Load settings
        self.load_settings()

        logger.info("Enhanced main window initialized successfully")
    def init_database(self):
        """Initialize database manager"""
    try:
            # Initialize ConfigManager first
            self.config_manager = EnhancedConfigManager()

            # Initialize DatabaseManager with config
            self.db_manager = ThreadSafeDatabaseManager(self.config_manager)
            if self.db_manager.test_connection():
                logger.info("Database connection established")
            else:
                raise Exception("Database connection test failed")
    except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            QMessageBox.critical(
                self, "Database Error", f"Failed to initialize database: {str(e)}"
            )
    def init_components(self):
        """Initialize all core components"""
    try:
            # Search engine
            if self.db_manager:
                self.search_engine = PropertySearchEngine(self.db_manager)
            else:
                self.search_engine = None

            # Performance metrics
            self.performance_metrics = PerformanceMetrics()

            # Background data collector
            if self.db_manager:
    try:
                    self.background_manager = BackgroundDataCollectionManager(
                        self.db_manager
                    )
    except Exception as e:
                    logger.warning(f"Background manager initialization failed: {e}")
                    self.background_manager = None
            else:
                self.background_manager = None

            # Batch processing manager
            if self.db_manager and self.background_manager:
    try:
                    self.batch_manager = BatchProcessingManager(
                        db_manager=self.db_manager,
                        background_collector=self.background_manager,
                    )
    except Exception as e:
                    logger.warning(f"Batch manager initialization failed: {e}")
                    self.batch_manager = None
            else:
                self.batch_manager = None

            # Backup manager
            if self.db_manager:
                self.backup_manager = BackupManager(self.db_manager)
            else:
                self.backup_manager = None

            # Data validator
            if self.db_manager:
                self.data_validator = DataValidator(self.db_manager)
            else:
                self.data_validator = None

            logger.info(
                "Component initialization completed (some components may be disabled)"
            )

    except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            # Don't show critical error dialog, just log it
            # The UI should still be usable with limited functionality
    def setup_ui(self):
        """Set up the main user interface"""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Add notification area at the top
        self.notification_area = NotificationArea()
        main_layout.addWidget(self.notification_area)

        # Create main splitter (horizontal)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        # Left panel (search and controls)
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)

        # Center panel (results and details)
        center_panel = self.create_center_panel()
        main_splitter.addWidget(center_panel)

        # Right panel (status and tools)
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)

        # Set splitter proportions
        main_splitter.setSizes([300, 700, 400])
    def create_left_panel(self):
        """Create the left panel with search controls"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Search section
        search_group = QGroupBox("Property Search")
        search_layout = QVBoxLayout(search_group)

        # Search input with enhanced features
        search_container = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter APN, address, or owner name...")
        self.search_input.returnPressed.connect(self.perform_search)
        search_container.addWidget(self.search_input)

        # Search button with icon
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.perform_search)
        self.search_btn.setDefault(True)
        search_container.addWidget(self.search_btn)

        search_layout.addLayout(search_container)

        # Advanced search toggle
        self.advanced_toggle = QCheckBox("Advanced Search")
        self.advanced_toggle.toggled.connect(self.toggle_advanced_search)
        search_layout.addWidget(self.advanced_toggle)

        # Advanced filters (initially hidden)
        self.advanced_filters = AdvancedFiltersWidget()
        self.advanced_filters.setVisible(False)
        search_layout.addWidget(self.advanced_filters)

        layout.addWidget(search_group)

        # Recent searches
        self.recent_searches = RecentSearchesWidget()
        self.recent_searches.search_selected.connect(self.set_search_term)
        layout.addWidget(self.recent_searches)

        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout(actions_group)

        # Batch search button
        batch_btn = QPushButton("Batch Search")
        batch_btn.clicked.connect(self.show_batch_search)
        actions_layout.addWidget(batch_btn)

        # Data collection button
        collect_btn = QPushButton("Start Data Collection")
        collect_btn.clicked.connect(self.start_background_collection)
        actions_layout.addWidget(collect_btn)

        # Export button
        export_btn = QPushButton("Export Results")
        export_btn.clicked.connect(self.show_export_dialog)
        actions_layout.addWidget(export_btn)

        layout.addWidget(actions_group)

        # Database stats
        if self.db_manager:
            self.quick_stats = QuickStatsWidget(self.db_manager)
        else:
            self.quick_stats = QLabel("Database not available")
        layout.addWidget(self.quick_stats)

        layout.addStretch()

        return panel
    def create_center_panel(self):
        """Create the center panel with results and details"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Create tab widget for different views
        self.main_tabs = QTabWidget()
        layout.addWidget(self.main_tabs)

        # Results tab
        results_tab = self.create_results_tab()
        self.main_tabs.addTab(results_tab, "Search Results")

        # Property details tab
        if self.db_manager:
            self.property_details = PropertyDetailsWidget(self.db_manager)
        else:
            self.property_details = QLabel(
                "Database not available for property details"
            )
        self.main_tabs.addTab(self.property_details, "Property Details")

        # Performance dashboard tab
        self.performance_dashboard = PerformanceDashboard(self.performance_metrics)
        self.main_tabs.addTab(self.performance_dashboard, "Performance")

        return panel
    def create_results_tab(self):
        """Create the results tab with enhanced table"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Search progress bar
        self.search_progress = AnimatedProgressBar()
        self.search_progress.setVisible(False)
        layout.addWidget(self.search_progress)

        # Results table
        self.results_table = QTableWidget()
        self.setup_results_table()
        layout.addWidget(self.results_table)

        # Results summary
        self.results_summary = QLabel("No search performed")
        layout.addWidget(self.results_summary)

        return tab
    def create_right_panel(self):
        """Create the right panel with status and tools"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Create tab widget for right panel
        right_tabs = QTabWidget()
        layout.addWidget(right_tabs)

        # Status tab
        status_tab = self.create_status_tab()
        right_tabs.addTab(status_tab, "Status")

        # Search history tab
        if self.db_manager:
            self.search_history = SearchHistoryWidget(self.db_manager)
        else:
            self.search_history = QLabel("Database not available for search history")
        right_tabs.addTab(self.search_history, "History")

        # System health tab
        if self.db_manager and self.background_manager:
            system_health = SystemHealthWidget(self.db_manager, self.background_manager)
        else:
            system_health = QLabel("System health monitoring not available")
        right_tabs.addTab(system_health, "Health")

        return panel
    def create_status_tab(self):
        """Create the status tab"""
        tab = QScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)

        # Background collection status
        bg_group = QGroupBox("Background Collection")
        bg_layout = QVBoxLayout(bg_group)

        self.bg_status_widget = BackgroundStatusWidget()
        bg_layout.addWidget(self.bg_status_widget)

        # Collection controls
        controls_layout = QHBoxLayout()

        self.start_collection_btn = QPushButton("Start")
        self.start_collection_btn.clicked.connect(self.start_background_collection)
        controls_layout.addWidget(self.start_collection_btn)

        self.pause_collection_btn = QPushButton("Pause")
        self.pause_collection_btn.clicked.connect(self.pause_background_collection)
        controls_layout.addWidget(self.pause_collection_btn)

        self.stop_collection_btn = QPushButton("Stop")
        self.stop_collection_btn.clicked.connect(self.stop_background_collection)
        controls_layout.addWidget(self.stop_collection_btn)

        bg_layout.addLayout(controls_layout)
        layout.addWidget(bg_group)

        # Search metrics
        metrics_group = QGroupBox("Search Metrics")
        metrics_layout = QVBoxLayout(metrics_group)

        self.search_metrics = SearchMetricsWidget()
        metrics_layout.addWidget(self.search_metrics)

        layout.addWidget(metrics_group)

        # Database connection
        db_group = QGroupBox("Database")
        db_layout = QVBoxLayout(db_group)

        if self.db_manager:
            self.db_connection = DatabaseConnectionWidget(self.db_manager)
        else:
            self.db_connection = QLabel("Database connection not available")
        db_layout.addWidget(self.db_connection)

        layout.addWidget(db_group)

        # Data validation
        validation_group = QGroupBox("Data Validation")
        validation_layout = QVBoxLayout(validation_group)

        if hasattr(self, "data_validator") and self.data_validator:
            self.data_validation = DataValidationWidget(self.data_validator)
        else:
            self.data_validation = QLabel("Data validation not available")
        validation_layout.addWidget(self.data_validation)

        layout.addWidget(validation_group)

        layout.addStretch()

        tab.setWidget(content)
        tab.setWidgetResizable(True)

        return tab
    def setup_results_table(self):
        """Set up the enhanced results table"""
        # Define columns
        columns = [
            "APN",
            "Address",
            "Owner",
            "Property Type",
            "Year Built",
            "Square Feet",
            "Bedrooms",
            "Bathrooms",
            "Market Value",
            "Assessed Value",
            "Last Sale Date",
            "Last Sale Amount",
            "Data Status",
            "Last Updated",
        ]

        self.results_table.setColumnCount(len(columns))
        self.results_table.setHorizontalHeaderLabels(columns)

        # Configure table properties
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.results_table.setSortingEnabled(True)

        # Enable context menu
        self.results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(
            self.show_results_context_menu
        )

        # Connect selection change
        self.results_table.itemSelectionChanged.connect(self.on_selection_changed)

        # Set column widths
        header = self.results_table.horizontalHeader()
        for i, width in enumerate(
            [100, 200, 150, 120, 80, 80, 80, 80, 100, 100, 100, 120, 100, 100]
        ):
            if i < len(columns):
                header.resizeSection(i, width)
    def setup_menu_bar(self):
        """Set up the enhanced menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        # Import/Export actions
        import_action = QAction("Import Data", self)
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)

        export_action = QAction("Export Results", self)
        export_action.triggered.connect(self.show_export_dialog)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        # Backup actions
        backup_action = QAction("Create Backup", self)
        backup_action.triggered.connect(self.create_backup)
        file_menu.addAction(backup_action)

        restore_action = QAction("Restore Backup", self)
        restore_action.triggered.connect(self.show_backup_restore)
        file_menu.addAction(restore_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Search menu
        search_menu = menubar.addMenu("Search")

        batch_search_action = QAction("Batch Search", self)
        batch_search_action.triggered.connect(self.show_batch_search)
        search_menu.addAction(batch_search_action)

        advanced_search_action = QAction("Advanced Search", self)
        advanced_search_action.triggered.connect(self.toggle_advanced_search)
        search_menu.addAction(advanced_search_action)

        # Data menu
        data_menu = menubar.addMenu("Data")

        collection_action = QAction("Start Collection", self)
        collection_action.triggered.connect(self.start_background_collection)
        data_menu.addAction(collection_action)

        queue_action = QAction("View Queue", self)
        queue_action.triggered.connect(self.show_collection_queue)
        data_menu.addAction(queue_action)

        validate_action = QAction("Validate Data", self)
        validate_action.triggered.connect(self.validate_data)
        data_menu.addAction(validate_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

        stats_action = QAction("Collection Statistics", self)
        stats_action.triggered.connect(self.show_collection_stats)
        tools_menu.addAction(stats_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    def setup_toolbar(self):
        """Set up the toolbar"""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)

        # Search action
        search_action = QAction("Search", self)
        search_action.triggered.connect(self.perform_search)
        toolbar.addAction(search_action)

        toolbar.addSeparator()

        # Collection actions
        start_action = QAction("Start Collection", self)
        start_action.triggered.connect(self.start_background_collection)
        toolbar.addAction(start_action)

        pause_action = QAction("Pause Collection", self)
        pause_action.triggered.connect(self.pause_background_collection)
        toolbar.addAction(pause_action)

        stop_action = QAction("Stop Collection", self)
        stop_action.triggered.connect(self.stop_background_collection)
        toolbar.addAction(stop_action)

        toolbar.addSeparator()

        # Export action
        export_action = QAction("Export", self)
        export_action.triggered.connect(self.show_export_dialog)
        toolbar.addAction(export_action)
    def setup_status_bar(self):
        """Set up the enhanced status bar"""
        self.status_bar = self.statusBar()

        # Status indicator
        self.status_indicator = StatusIndicator()
        self.status_bar.addPermanentWidget(self.status_indicator)

        # Progress bar for operations
        self.status_progress = QProgressBar()
        self.status_progress.setVisible(False)
        self.status_progress.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.status_progress)

        # Memory usage label
        self.memory_label = QLabel("Memory: 0 MB")
        self.status_bar.addPermanentWidget(self.memory_label)

        # Database status
        self.db_status_label = QLabel("DB: Connected")
        self.status_bar.addPermanentWidget(self.db_status_label)

        # Set initial message
        self.status_bar.showMessage("Ready")
    def apply_modern_style(self):
        """Apply modern styling to the application"""
        style = """
        QMainWindow {
            background-color: #f5f5f5;
        }

        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
        }

        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #45a049;
        }

        QPushButton:pressed {
            background-color: #3d8b40;
        }

        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }

        QLineEdit {
            padding: 8px;
            border: 2px solid #ddd;
            border-radius: 4px;
            font-size: 12px;
        }

        QLineEdit:focus {
            border-color: #4CAF50;
        }

        QTableWidget {
            gridline-color: #e0e0e0;
            background-color: white;
            alternate-background-color: #f9f9f9;
        }

        QTableWidget::item:selected {
            background-color: #2196F3;
            color: white;
        }

        QHeaderView::section {
            background-color: #e0e0e0;
            padding: 8px;
            border: 1px solid #c0c0c0;
            font-weight: bold;
        }

        QTabWidget::pane {
            border: 1px solid #c0c0c0;
            background-color: white;
        }

        QTabBar::tab {
            background-color: #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }

        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 1px solid white;
        }

        QScrollBar:vertical {
            border: none;
            background: #f0f0f0;
            width: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:vertical {
            background: #c0c0c0;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background: #a0a0a0;
        }
        """

        self.setStyleSheet(style)
    def connect_signals(self):
        """Connect all signal handlers"""
        # Background manager signals
        if self.background_manager:
            self.background_manager.progress_updated.connect(
                self.update_background_status
            )
            self.background_manager.collection_finished.connect(
                self.on_collection_finished
            )
            self.background_manager.error_occurred.connect(self.handle_background_error)

        # Search engine signals (if any)
        # Add more signal connections as needed
    def init_background_services(self):
        """Initialize background services"""
    try:
            # Start background data collector
            if self.background_manager:
    try:
                    if (
                        hasattr(self.background_manager, "is_running")
                        and not self.background_manager.is_running()
                    ):
                        self.background_manager.start()
                        logger.info("Background data collector started")
    except Exception as e:
                    logger.warning(f"Failed to start background data collector: {e}")

                # Update status initially and setup periodic updates
    try:
                    if hasattr(self.background_manager, "get_collection_status"):
                        status = self.background_manager.get_collection_status()
                        if hasattr(self, "bg_status_widget"):
                            self.bg_status_widget.update_status(status)
    except Exception as e:
                    logger.warning(f"Failed to get initial background status: {e}")

                # Set up timer for status updates
                self.status_timer = QTimer()
                self.status_timer.timeout.connect(self.update_background_status)
                self.status_timer.start(5000)  # Update every 5 seconds
            else:
                logger.info(
                    "Background manager not available, skipping background services"
                )

    except Exception as e:
            logger.error(f"Failed to initialize background services: {e}")
    def load_settings(self):
        """Load application settings"""
    try:
            settings = QSettings("PropertySearch", "Enhanced")

            # Restore window geometry
            geometry = settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)

            # Restore window state
            state = settings.value("windowState")
            if state:
                self.restoreState(state)

            logger.info("Settings loaded successfully")

    except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    def save_settings(self):
        """Save application settings"""
    try:
            settings = QSettings("PropertySearch", "Enhanced")

            # Save window geometry and state
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())

            logger.info("Settings saved successfully")

    except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    def closeEvent(self, event):
        """Handle application close event"""
    try:
            # Save settings
            self.save_settings()

            # Stop background services
            if self.background_manager and self.background_manager.is_running():
                self.background_manager.stop()

            # Clean up any ongoing operations
            if self.current_search_thread and self.current_search_thread.isRunning():
                self.current_search_thread.quit()
                self.current_search_thread.wait()

            event.accept()
            logger.info("Application closed successfully")

    except Exception as e:
            logger.error(f"Error during application close: {e}")
            event.accept()

    # Search functionality
    def perform_search(self):
        """Perform property search with enhanced features"""
        search_term = self.search_input.text().strip()
        if not search_term:
            self.notification_area.show_message("Please enter a search term", "warning")
            return

        if not self.search_engine:
            self.notification_area.show_message("Search engine not available", "error")
            return

    try:
            # Start performance tracking
            search_start = time.time()

            # Update UI state
            self.search_btn.setEnabled(False)
            self.search_progress.setVisible(True)
            self.search_progress.set_animated_value(0)
            self.status_indicator.set_status("working")
            self.status_bar.showMessage("Searching...")

            # Add to recent searches
            self.recent_searches.add_search(search_term)

            # Get advanced filters if enabled
            filters = {}
            if self.advanced_toggle.isChecked():
                filters = self.advanced_filters.get_filters()

            # Perform search
            self.search_progress.set_animated_value(50)

            results = self.search_engine.search_properties(
                search_term,
                filters=filters,
                include_tax_history=True,
                include_sales_history=True,
            )

            self.search_progress.set_animated_value(100)

            # Store results for later use
            self.last_search_results = results

            # Update results table
            self.populate_results_table(results)

            # Update metrics
            search_time = time.time() - search_start
            self.update_search_metrics(search_term, len(results), search_time)

            # Update UI state
            self.search_btn.setEnabled(True)
            self.search_progress.setVisible(False)
            self.status_indicator.set_status("success")
            self.status_bar.showMessage(
                f"Search completed: {len(results)} results found"
            )

            # Show notification
            self.notification_area.show_message(
                f"Search completed successfully. Found {len(results)} properties.",
                "success",
            )

    except Exception as e:
            logger.error(f"Search error: {e}")

            # Update UI state
            self.search_btn.setEnabled(True)
            self.search_progress.setVisible(False)
            self.status_indicator.set_status("error")
            self.status_bar.showMessage("Search failed")

            # Show error
            self.notification_area.show_message(f"Search failed: {str(e)}", "error")
            QMessageBox.critical(self, "Search Error", f"Search failed: {str(e)}")
    def populate_results_table(self, results: List[Dict[str, Any]]):
        """Populate the results table with enhanced data"""
    try:
            self.results_table.setRowCount(len(results))

            for row, property_data in enumerate(results):
                # Basic property information
                self.results_table.setItem(
                    row, 0, QTableWidgetItem(str(property_data.get("apn", "")))
                )
                self.results_table.setItem(
                    row, 1, QTableWidgetItem(str(property_data.get("address", "")))
                )
                self.results_table.setItem(
                    row, 2, QTableWidgetItem(str(property_data.get("owner_name", "")))
                )
                self.results_table.setItem(
                    row,
                    3,
                    QTableWidgetItem(str(property_data.get("property_type", ""))),
                )
                self.results_table.setItem(
                    row, 4, QTableWidgetItem(str(property_data.get("year_built", "")))
                )

                # Property details
                self.results_table.setItem(
                    row, 5, QTableWidgetItem(str(property_data.get("square_feet", "")))
                )
                self.results_table.setItem(
                    row, 6, QTableWidgetItem(str(property_data.get("bedrooms", "")))
                )
                self.results_table.setItem(
                    row, 7, QTableWidgetItem(str(property_data.get("bathrooms", "")))
                )

                # Financial information
                market_value = property_data.get("market_value", 0)
                assessed_value = property_data.get("assessed_value", 0)
                last_sale_amount = property_data.get("last_sale_amount", 0)

                self.results_table.setItem(
                    row,
                    8,
                    QTableWidgetItem(f"${market_value:,}" if market_value else ""),
                )
                self.results_table.setItem(
                    row,
                    9,
                    QTableWidgetItem(f"${assessed_value:,}" if assessed_value else ""),
                )

                # Sales information
                last_sale_date = property_data.get("last_sale_date", "")
                self.results_table.setItem(
                    row, 10, QTableWidgetItem(str(last_sale_date))
                )
                self.results_table.setItem(
                    row,
                    11,
                    QTableWidgetItem(
                        f"${last_sale_amount:,}" if last_sale_amount else ""
                    ),
                )

                # Data collection status
                apn = property_data.get("apn", "")
                status_info = self._get_data_collection_status(apn)
                status_item = QTableWidgetItem(status_info["text"])

                # Color code status
                if status_info["complete"]:
                    status_item.setBackground(QColor(200, 255, 200))  # Light green
                elif status_info["collecting"]:
                    status_item.setBackground(QColor(255, 255, 200))  # Light yellow
                else:
                    status_item.setBackground(QColor(255, 200, 200))  # Light red

                self.results_table.setItem(row, 12, status_item)

                # Last update time
                last_update = self._get_last_update_time(apn)
                self.results_table.setItem(row, 13, QTableWidgetItem(last_update))

    except Exception as e:
            logger.error(f"Error populating results table: {e}")

        # Update results summary
        self.results_summary.setText(f"Showing {len(results)} results")

        # Auto-resize columns
        self.results_table.resizeColumnsToContents()
    def _get_data_collection_status(self, apn: str) -> Dict[str, Any]:
        """Get data collection status for an APN"""
    try:
            # If no database manager, return default status
            if not self.db_manager:
                return {"text": "No DB", "complete": False, "collecting": False}

            # Try to get tax and sales records
    try:
                tax_records = self.db_manager.get_tax_history(apn)
                sales_records = self.db_manager.get_sales_history(apn)
    except:
                # If methods don't exist, return unknown status
                return {"text": "Unknown", "complete": False, "collecting": False}

            # Ensure we have lists to work with
            if not isinstance(tax_records, list):
                tax_records = []
            if not isinstance(sales_records, list):
                sales_records = []

            has_tax = len(tax_records) > 0
            has_sales = len(sales_records) > 0

            # Check if collection is in progress
            collecting = False
            if self.background_manager:
    try:
                    bg_status = self.background_manager.get_collection_status()
                    active_jobs = bg_status.get("active_jobs", [])

                    # Handle case where active_jobs might be an integer (count) or a list (job objects)
                    if isinstance(active_jobs, (list, tuple)):
                        # active_jobs is a list/tuple of job objects
                        collecting = apn in [
                            job.get("apn", "")
                            for job in active_jobs
                            if isinstance(job, dict)
                        ]
                    elif isinstance(active_jobs, int) and active_jobs > 0:
                        # active_jobs is a count - we can't determine specific APN status
                        # but we know jobs are running, so assume this APN might be collecting
                        # This is a fallback - ideally we'd have better job tracking
                        collecting = False  # Conservative approach: don't assume this APN is being collected
    except:
                    # If background manager methods fail, assume not collecting
                    collecting = False

            if has_tax and has_sales:
                return {"text": "Complete", "complete": True, "collecting": False}
            elif collecting:
                return {"text": "Collecting...", "complete": False, "collecting": True}
            elif has_tax or has_sales:
                return {"text": "Partial", "complete": False, "collecting": False}
            else:
                return {"text": "Queued", "complete": False, "collecting": False}

    except Exception as e:
            logger.error(f"Error checking data status for {apn}: {e}")
            return {"text": "Unknown", "complete": False, "collecting": False}
    def _get_last_update_time(self, apn: str) -> str:
        """Get last update time for an APN"""
    try:
            # This would need to be implemented in the database manager
            # For now, return a placeholder
            return "Recent"
    except:
                return "Unknown"
    def handle_search_error(self, error_message: str):
        """Handle search errors gracefully"""
        logger.error(f"Search error: {error_message}")

        # Update UI
        self.search_btn.setEnabled(True)
        self.search_progress.setVisible(False)
        self.status_indicator.set_status("error")

        # Show error message
        QMessageBox.critical(self, "Search Error", error_message)
        self.notification_area.show_message(f"Search failed: {error_message}", "error")
    def update_search_metrics(
        self, search_term: str, result_count: int, search_time: float
    ):
        """Update search performance metrics"""
    try:
            # Record search metrics
            self.performance_metrics.record_search(
                search_term, result_count, search_time
            )

            # Update metrics display
            metrics = self.performance_metrics.get_summary()
            self.search_metrics.update_metrics(metrics)

            # Add to search history
            self.search_history.add_search(search_term, result_count, search_time)

    except Exception as e:
            logger.error(f"Failed to update search metrics: {e}")

    # Background collection methods
    def start_background_collection(self):
        """Start background data collection"""
    try:
            if not self.background_manager:
                self.notification_area.show_message(
                    "Background manager not available", "error"
                )
                return

            # Get selected APNs from results table
            selected_apns = self.get_selected_apns()

            if not selected_apns:
                # If no selection, show dialog for batch collection
                self.show_collection_dialog()
                return

            # Start collection for selected APNs
            success_count = 0
            for apn in selected_apns:
                if self.background_manager.add_collection_job(apn):
                    success_count += 1

            if success_count > 0:
                self.notification_area.show_message(
                    f"Started data collection for {success_count} properties", "success"
                )
            else:
                self.notification_area.show_message(
                    "Failed to start data collection", "error"
                )

    except Exception as e:
            logger.error(f"Failed to start background collection: {e}")
            self.notification_area.show_message(f"Collection error: {str(e)}", "error")
    def pause_background_collection(self):
        """Pause background data collection"""
    try:
            if self.background_manager:
                self.background_manager.pause()
                self.notification_area.show_message("Data collection paused", "info")
    except Exception as e:
            logger.error(f"Failed to pause collection: {e}")
    def stop_background_collection(self):
        """Stop background data collection"""
    try:
            if self.background_manager:
                self.background_manager.stop()
                self.notification_area.show_message("Data collection stopped", "info")
    except Exception as e:
            logger.error(f"Failed to stop collection: {e}")
    def show_collection_dialog(self):
        """Show the collection progress dialog"""
        if not self.collection_dialog:
            self.collection_dialog = CollectionProgressDialog(self.background_manager)

        # Position dialog relative to main window
        self.collection_dialog.move(
            self.geometry().center() - self.collection_dialog.rect().center()
        )

        self.collection_dialog.show()
    def auto_collect_missing_data(self):
        """Automatically collect missing data for current results"""
    try:
            if not hasattr(self, "last_search_results") or not self.last_search_results:
                self.notification_area.show_message(
                    "No search results to collect data for", "warning"
                )
                return

            missing_data_apns = []
            for property_data in self.last_search_results:
                apn = property_data.get("apn")
                if apn:
                    status = self._get_data_collection_status(apn)
                    if not status["complete"]:
                        missing_data_apns.append(apn)

            if missing_data_apns:
                # Start collection for APNs with missing data
                added_jobs = 0
                for apn in missing_data_apns:
                    if self.background_manager.add_collection_job(apn):
                        added_jobs += 1

                self.notification_area.show_message(
                    f"Started collection for {added_jobs} properties with missing data",
                    "success",
                )
            else:
                self.notification_area.show_message(
                    "All properties have complete data", "info"
                )

    except Exception as e:
            logger.error(f"Auto-collect failed: {e}")
            self.notification_area.show_message(
                f"Auto-collect failed: {str(e)}", "error"
            )
    def get_selected_apns(self) -> List[str]:
        """Get APNs from selected table rows"""
        selected_apns = []
    try:
            selected_rows = set()
            for item in self.results_table.selectedItems():
                selected_rows.add(item.row())

            for row in selected_rows:
                apn_item = self.results_table.item(row, 0)  # APN is in first column
                if apn_item:
                    selected_apns.append(apn_item.text())

    except Exception as e:
            logger.error(f"Failed to get selected APNs: {e}")

        return selected_apns

    # Collection status and progress
    def update_background_status(self, status_dict=None):
        """Update background collection status display"""
        if status_dict is None and self.background_manager:
    try:
                status_dict = self.background_manager.get_collection_status()
    except:
                    status_dict = {
                    "status": "Unknown",
                    "pending_jobs": 0,
                    "active_jobs": 0,
                    "completed_jobs": 0,
                }

        if status_dict and hasattr(self, "bg_status_widget"):
            self.bg_status_widget.update_status(status_dict)

        self.check_system_status()
    def check_system_status(self):
        """Check overall system status"""
    try:
            # Check database connection
            if self.db_manager:
    try:
                    if (
                        hasattr(self.db_manager, "test_connection")
                        and not self.db_manager.test_connection()
                    ):
                        self.db_status_label.setText("DB: Disconnected")
                        self.db_status_label.setStyleSheet("color: red;")
                    else:
                        self.db_status_label.setText("DB: Connected")
                        self.db_status_label.setStyleSheet("color: green;")
    except:
                        self.db_status_label.setText("DB: Error")
                    self.db_status_label.setStyleSheet("color: orange;")
            else:
                self.db_status_label.setText("DB: Not Available")
                self.db_status_label.setStyleSheet("color: red;")

            # Update quick stats
            if hasattr(self.quick_stats, "update_stats"):
    try:
                    self.quick_stats.update_stats()
    except:
            pass  # Ignore quick stats errors

            # Update database connection widget
            if hasattr(self.db_connection, "update_status"):
    try:
                    self.db_connection.update_status()
    except:
            pass  # Ignore connection widget errors

    except Exception as e:
            logger.error(f"System status check failed: {e}")
    def on_collection_finished(self, results: Dict[str, Any]):
        """Handle collection completion"""
    try:
            success_count = results.get("successful_collections", 0)
            failed_count = results.get("failed_collections", 0)

            message = f"Collection completed: {success_count} successful"
            if failed_count > 0:
                message += f", {failed_count} failed"

            self.notification_area.show_message(message, "success")

            # Refresh any displayed data
            self.refresh_displayed_data()

    except Exception as e:
            logger.error(f"Error handling collection completion: {e}")
    def handle_background_error(self, error_message: str):
        """Handle background collection errors"""
        logger.error(f"Background collection error: {error_message}")
        self.notification_area.show_message(
            f"Collection error: {error_message}", "error"
        )
    def refresh_displayed_data(self):
        """Refresh currently displayed data"""
    try:
            # If we have current results, refresh their status
            if hasattr(self, "last_search_results") and self.last_search_results:
                self.populate_results_table(self.last_search_results)

            # Update quick stats
            self.quick_stats.update_stats()

            # Update property details if shown
            if (
                hasattr(self.property_details, "current_apn")
                and self.property_details.current_apn
            ):
                self.property_details.load_property_data(
                    self.property_details.current_apn
                )

    except Exception as e:
            logger.error(f"Failed to refresh displayed data: {e}")
    def refresh_property_data(self):
        """CRASH-SAFE Force refresh property data by clearing cache and reloading details"""
    try:
            # Comprehensive safety checks first
            if not hasattr(self, "property_data") or not self.property_data:
                QMessageBox.warning(
                    self, "Error", "No property data available for refresh."
                )
                return

            apn = (
                self.property_data.get("apn")
                if isinstance(self.property_data, dict)
                else None
            )
            if not apn:
                QMessageBox.warning(
                    self, "Error", "No APN available for refresh operation."
                )
                return

            # Initialize progress dialog with proper error handling
            progress = None
    try:
                progress = QProgressDialog(
                    "Preparing refresh operation...", "Cancel", 0, 100, self
                )
                progress.setWindowModality(Qt.WindowModal)
                progress.setMinimumDuration(0)  # Show immediately
                progress.show()
                progress.setValue(10)

    except Exception as progress_error:
                logger.warning(f"Failed to create progress dialog: {progress_error}")
                # Continue without progress dialog

    try:
                # SAFE cache clearing with comprehensive error handling
                if progress:
                    progress.setValue(20)
                    progress.setLabelText("Clearing cached data...")

                cache_cleared = False
                if self.background_manager:
    try:
                        if (
                            hasattr(self.background_manager, "worker")
                            and self.background_manager.worker
                        ):
                            if hasattr(self.background_manager.worker, "cache"):
    try:
                                    self.background_manager.worker.cache.clear_apn_cache(
                                        apn
                                    )
                                    cache_cleared = True
                                    logger.info(f"Cleared cache for APN {apn}")
    except Exception as cache_error:
                                    logger.warning(
                                        f"Failed to clear cache for APN {apn}: {cache_error}"
                                    )
                                    # Don't fail the entire operation for cache clearing issues
                            else:
                                logger.debug("Background worker has no cache attribute")
                        else:
                            logger.debug(
                                "Background manager has no worker or worker is None"
                            )
    except Exception as manager_error:
                        logger.warning(
                            f"Error accessing background manager for cache clear: {manager_error}"
                        )

                if progress:
                    progress.setValue(40)
                    progress.setLabelText("Checking background collection service...")

                # SAFE background collection with comprehensive checks
                collection_success = False
                if self.background_manager:
    try:
                        # Check if background service is running
                        is_running = False
                        if hasattr(self.background_manager, "is_running"):
    try:
                                is_running = self.background_manager.is_running()
    except Exception as running_check_error:
                                logger.warning(
                                    f"Error checking if background service is running: {running_check_error}"
                                )

                        if is_running:
                            if progress:
                                progress.setValue(60)
                                progress.setLabelText(
                                    "Queuing fresh data collection..."
                                )

                            # SAFE data collection request
    try:
                                if hasattr(
                                    self.background_manager, "collect_data_for_apn"
                                ):
                                    success = (
                                        self.background_manager.collect_data_for_apn(
                                            apn, JobPriority.CRITICAL, force_fresh=True
                                        )
                                    )

                                    if success:
                                        collection_success = True
                                        if progress:
                                            progress.setValue(90)
                                            progress.setLabelText(
                                                "Collection queued successfully..."
                                            )

                                        logger.info(
                                            f"Successfully queued fresh data collection for APN {apn}"
                                        )
                                    else:
                                        logger.warning(
                                            f"Failed to queue data collection for APN {apn}"
                                        )
                                else:
                                    logger.error(
                                        "Background manager missing collect_data_for_apn method"
                                    )

    except Exception as collection_error:
                                logger.error(
                                    f"Error requesting data collection for APN {apn}: {collection_error}"
                                )
                        else:
                            logger.info(
                                "Background collection service is not running - using database refresh"
                            )

    except Exception as bg_service_error:
                        logger.error(
                            f"Error with background collection service: {bg_service_error}"
                        )
                else:
                    logger.warning("No background manager available for refresh")

                if progress:
                    progress.setValue(80)
                    progress.setLabelText("Refreshing display...")

                # SAFE property details reload
                reload_success = False
    try:
                    if hasattr(self, "load_property_details"):
                        self.load_property_details()
                        reload_success = True
                        logger.info(
                            f"Successfully reloaded property details for APN {apn}"
                        )
                    else:
                        logger.error("Dialog missing load_property_details method")

    except Exception as reload_error:
                    logger.error(
                        f"Error reloading property details for APN {apn}: {reload_error}"
                    )

                if progress:
                    progress.setValue(100)

                # Show appropriate success message
                if collection_success:
                    QMessageBox.information(
                        self,
                        "Refresh Started",
                        f"Fresh data collection started for APN {apn}.\n"
                        "The dialog will refresh automatically when complete.",
                    )
                elif reload_success:
                    QMessageBox.information(
                        self,
                        "Data Refreshed",
                        "Property data has been refreshed with current database contents.",
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Partial Refresh",
                        "Refresh completed but some operations may have failed.\n"
                        "Check the application logs for more details.",
                    )

    except Exception as main_error:
                logger.error(
                    f"Error in main refresh operation for APN {apn}: {main_error}"
                )
                QMessageBox.critical(
                    self,
                    "Refresh Error",
                    f"Error during refresh operation: {str(main_error)}\n"
                    "Please try again or restart the application if problems persist.",
                )

    finally:
                # SAFE progress dialog cleanup
                if progress:
    try:
                        progress.close()
                        progress.deleteLater()
    except Exception as cleanup_error:
                        logger.warning(
                            f"Error cleaning up progress dialog: {cleanup_error}"
                        )

    except Exception as e:
            # ULTIMATE CRASH PREVENTION - catch absolutely everything
            logger.error(
                f"CRITICAL: Unhandled error in refresh_property_data for APN {getattr(self, 'property_data', {}).get('apn', 'unknown')}: {e}"
            )
import traceback

        traceback.print_exc()

            # Show error but keep application running
    try:
                QMessageBox.critical(
                    self,
                    "Critical Refresh Error",
                    f"A critical error occurred during refresh:\n{str(e)}\n\n"
                    "The application will continue running.\n"
                    "Please restart the application if problems persist.",
                )
    except:
                # Even the error dialog failed - just log it
                logger.error(
                    "Failed to show critical error dialog - application may be in unstable state"
                )

    # UI interaction methods
    def toggle_advanced_search(self, checked: bool):
        """Toggle advanced search filters visibility"""
        self.advanced_filters.setVisible(checked)

        # Adjust window size if needed
        if checked:
            self.resize(self.width(), self.height() + 100)
        else:
            self.resize(self.width(), max(600, self.height() - 100))
    def set_search_term(self, search_term: str):
        """Set the search term in the input field"""
        self.search_input.setText(search_term)
        self.search_input.selectAll()
    def on_selection_changed(self):
        """Handle table selection changes"""
    try:
            selected_rows = set()
            for item in self.results_table.selectedItems():
                selected_rows.add(item.row())

            if len(selected_rows) == 1:
                # Single selection - show property details
                row = list(selected_rows)[0]
                apn_item = self.results_table.item(row, 0)
                if apn_item:
                    apn = apn_item.text()
                    self.property_details.load_property_data(apn)

            # Update status message
            if len(selected_rows) > 0:
                self.status_bar.showMessage(f"{len(selected_rows)} properties selected")
            else:
                self.status_bar.showMessage("Ready")

    except Exception as e:
            logger.error(f"Selection change error: {e}")
    def show_results_context_menu(self, position):
        """Show context menu for results table"""
    try:
            item = self.results_table.itemAt(position)
            if not item:
                return

            menu = QMenu()

            # View details action
            view_action = menu.addAction("View Details")
            view_action.triggered.connect(
                lambda: self.view_property_details(item.row())
            )

            # Collection actions
            menu.addSeparator()
            collect_action = menu.addAction("Collect Data")
            collect_action.triggered.connect(lambda: self.collect_selected_data())

            # Check if this APN is in active jobs
            status = self.background_manager.get_collection_status()
            active_jobs = status.get("active_jobs", 0)

            if active_jobs > 0 and self.background_manager.worker:
                # Add option to prioritize this collection
                prioritize_action = menu.addAction("Prioritize Collection")
                prioritize_action.triggered.connect(
                    lambda: self.prioritize_collection(item.row())
                )

            menu.addSeparator()

            # Export actions
            export_action = menu.addAction("Export Selected")
            export_action.triggered.connect(self.export_selected_results)

            # Show menu
            menu.exec(self.results_table.mapToGlobal(position))

    except Exception as e:
            logger.error(f"Context menu error: {e}")
    def view_property_details(self, row: int):
        """View detailed information for a property"""
    try:
            apn_item = self.results_table.item(row, 0)
            if apn_item:
                apn = apn_item.text()
                self.property_details.load_property_data(apn)

                # Switch to property details tab
                for i in range(self.main_tabs.count()):
                    if self.main_tabs.tabText(i) == "Property Details":
                        self.main_tabs.setCurrentIndex(i)
                        break

    except Exception as e:
            logger.error(f"Failed to view property details: {e}")
    def collect_selected_data(self):
        """Collect data for selected properties"""
    try:
            selected_apns = self.get_selected_apns()
            if not selected_apns:
                self.notification_area.show_message("No properties selected", "warning")
                return

            added_jobs = 0
            for apn in selected_apns:
                if self.background_manager.add_collection_job(apn):
                    added_jobs += 1

            if added_jobs > 0:
                self.notification_area.show_message(
                    f"Started collection for {added_jobs} selected properties",
                    "success",
                )
            else:
                self.notification_area.show_message(
                    "Failed to start collection", "error"
                )

    except Exception as e:
            logger.error(f"Failed to collect selected data: {e}")
    def prioritize_collection(self, row: int):
        """Prioritize collection for a specific property"""
    try:
            apn_item = self.results_table.item(row, 0)
            if apn_item:
                apn = apn_item.text()
                if hasattr(self.background_manager, "prioritize_job"):
                    self.background_manager.prioritize_job(apn)
                    self.notification_area.show_message(
                        f"Prioritized collection for {apn}", "info"
                    )

    except Exception as e:
            logger.error(f"Failed to prioritize collection: {e}")

    # Dialog and window methods
    def show_batch_search(self):
        """Show batch search dialog"""
    try:
            dialog = BatchSearchDialog(self.batch_manager)
            dialog.search_completed.connect(self.handle_batch_search_results)
            dialog.exec()
    except Exception as e:
            logger.error(f"Failed to show batch search dialog: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to open batch search: {str(e)}"
            )
    def handle_batch_search_results(self, results: List[Dict[str, Any]]):
        """Handle batch search results"""
    try:
            # Store results for later use
            self.last_search_results = results

            # Populate results table
            self.populate_results_table(results)

            # Switch to results tab
            self.main_tabs.setCurrentIndex(0)

            # Show success message
            self.notification_area.show_message(
                f"Batch search completed: {len(results)} properties found", "success"
            )

    except Exception as e:
            logger.error(f"Failed to handle batch search results: {e}")
    def show_export_dialog(self):
        """Show export dialog"""
    try:
            # Get current results
            results = getattr(self, "last_search_results", [])
            if not results:
                self.notification_area.show_message("No results to export", "warning")
                return

            dialog = ExportDialog(results, self.db_manager)
            dialog.exec()
    except Exception as e:
            logger.error(f"Failed to show export dialog: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to open export dialog: {str(e)}"
            )
    def export_selected_results(self):
        """Export selected results only"""
    try:
            selected_apns = self.get_selected_apns()
            if not selected_apns:
                self.notification_area.show_message("No properties selected", "warning")
                return

            # Filter results to selected APNs
            if hasattr(self, "last_search_results"):
                selected_results = [
                    result
                    for result in self.last_search_results
                    if result.get("apn") in selected_apns
                ]

                dialog = ExportDialog(selected_results, self.db_manager)
                dialog.exec()
            else:
                self.notification_area.show_message(
                    "No results available for export", "warning"
                )

    except Exception as e:
            logger.error(f"Failed to export selected results: {e}")
    def show_settings(self):
        """Show settings dialog"""
    try:
            dialog = SettingsDialog(self.db_manager, self.background_manager)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Apply any setting changes
                self.apply_settings_changes()
    except Exception as e:
            logger.error(f"Failed to show settings dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open settings: {str(e)}")
    def apply_settings_changes(self):
        """Apply changes from settings dialog"""
    try:
            # This would apply any settings that were changed
            # For now, just show a notification
            self.notification_area.show_message("Settings applied", "success")
    except Exception as e:
            logger.error(f"Failed to apply settings: {e}")
    def show_collection_queue(self):
        """Show collection queue viewer"""
    try:
            dialog = CollectionQueueViewer(self.background_manager)
            dialog.exec()
    except Exception as e:
            logger.error(f"Failed to show collection queue: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to open collection queue: {str(e)}"
            )
    def show_collection_stats(self):
        """Show collection statistics"""
        status = self.background_manager.get_collection_status()
        stats = status.get("statistics", {})
        cache_stats = status.get("cache_stats", {})

        # Create a detailed statistics dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Collection Statistics")
        dialog.setModal(True)
        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)

        # Statistics text
        stats_text = QTextEdit()
        stats_text.setReadOnly(True)

        stats_content = f"""
Collection Statistics:

Overall Performance:
- Total Jobs Processed: {stats.get('total_jobs_processed', 0)}
- Successful Collections: {stats.get('successful_collections', 0)}
- Failed Collections: {stats.get('failed_collections', 0)}
- Success Rate: {stats.get('success_rate_percent', 0):.1f}%
- Average Processing Time: {stats.get('avg_processing_time', 0):.2f} seconds

Cache Performance:
- Cache Hits: {cache_stats.get('hits', 0)}
- Cache Misses: {cache_stats.get('misses', 0)}
- Cache Hit Rate: {cache_stats.get('hit_rate_percent', 0):.1f}%

Current Status:
- Status: {status.get('status', 'Unknown')}
- Pending Jobs: {status.get('pending_jobs', 0)}
- Active Jobs: {status.get('active_jobs', 0)}
- Completed Jobs: {status.get('completed_jobs', 0)}
        """

        stats_text.setPlainText(stats_content)
        layout.addWidget(stats_text)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()
    def create_backup(self):
        """Create a database backup"""
    try:
            if not self.backup_manager:
                self.notification_area.show_message(
                    "Backup manager not available", "error"
                )
                return

            # Show progress
            self.status_progress.setVisible(True)
            self.status_progress.setRange(0, 0)  # Indeterminate progress

            # Create backup
            backup_path = self.backup_manager.create_backup()

            # Hide progress
            self.status_progress.setVisible(False)

            if backup_path:
                self.notification_area.show_message(
                    f"Backup created: {backup_path}", "success"
                )
                QMessageBox.information(
                    self,
                    "Backup Complete",
                    f"Database backup created successfully:\n{backup_path}",
                )
            else:
                self.notification_area.show_message("Backup failed", "error")

    except Exception as e:
            self.status_progress.setVisible(False)
            logger.error(f"Backup creation failed: {e}")
            self.notification_area.show_message(f"Backup failed: {str(e)}", "error")
    def show_backup_restore(self):
        """Show backup and restore dialog"""
    try:
            dialog = BackupRestoreDialog(self.backup_manager)
            dialog.exec()
    except Exception as e:
            logger.error(f"Failed to show backup/restore dialog: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to open backup dialog: {str(e)}"
            )
    def validate_data(self):
        """Run data validation"""
    try:
            # Show progress
            self.status_progress.setVisible(True)
            self.status_progress.setRange(0, 0)
            self.status_bar.showMessage("Validating data...")

            # Run validation
            validation_results = self.data_validator.validate_all_data()

            # Hide progress
            self.status_progress.setVisible(False)
            self.status_bar.showMessage("Validation complete")

            # Update validation widget
            self.data_validation.update_results(validation_results)

            # Show summary
            total_issues = sum(len(issues) for issues in validation_results.values())
            if total_issues == 0:
                self.notification_area.show_message(
                    "Data validation passed - no issues found", "success"
                )
            else:
                self.notification_area.show_message(
                    f"Data validation found {total_issues} issues", "warning"
                )

    except Exception as e:
            self.status_progress.setVisible(False)
            logger.error(f"Data validation failed: {e}")
            self.notification_area.show_message(f"Validation failed: {str(e)}", "error")
    def import_data(self):
        """Import data from external source"""
    try:
            # This would implement data import functionality
            # For now, show a placeholder message
            QMessageBox.information(
                self, "Import Data", "Data import functionality not yet implemented."
            )
    except Exception as e:
            logger.error(f"Data import failed: {e}")
    def show_about(self):
        """Show about dialog"""
        about_text = """
        Maricopa County Property Search - Enhanced

        Version: 2.0.0

        A comprehensive property search application for Maricopa County
        with advanced data collection and analysis capabilities.

        Features:
        • Advanced property search with filters
        • Background data collection
        • Batch processing
        • Performance monitoring
        • Data validation and backup
        • Modern responsive UI

        © 2024 Property Search Solutions
        """

        QMessageBox.about(self, "About", about_text)
    def _update_dialog_status(self):
        """CRASH-SAFE Periodically update dialog status"""
    try:
            if not hasattr(self, "background_manager") or not self.background_manager:
                return

            # SAFE status retrieval
    try:
                status = self.background_manager.get_collection_status()
                if hasattr(self, "bg_status_widget") and self.bg_status_widget:
    try:
                        self.bg_status_widget.update_status(status)
    except Exception as widget_error:
                        logger.warning(f"Error updating status widget: {widget_error}")
    except Exception as status_error:
                logger.warning(f"Error getting collection status: {status_error}")

            # SAFE collection completion check
    try:
                if (
                    hasattr(self, "collection_in_progress")
                    and self.collection_in_progress
                ):
                    if hasattr(self, "property_data") and self.property_data:
                        apn = (
                            self.property_data.get("apn")
                            if isinstance(self.property_data, dict)
                            else None
                        )
                        if (
                            apn
                            and hasattr(self.background_manager, "worker")
                            and self.background_manager.worker
                        ):
    try:
                                if hasattr(
                                    self.background_manager.worker, "active_jobs"
                                ):
                                    if (
                                        apn
                                        not in self.background_manager.worker.active_jobs
                                    ):
                                        # Collection completed, refresh safely
                                        self.collection_in_progress = False
                                        if hasattr(self, "load_property_details"):
    try:
                                                self.load_property_details()
    except Exception as load_error:
                                                logger.error(
                                                    f"Error loading property details after completion: {load_error}"
                                                )
    except Exception as job_check_error:
                                logger.warning(
                                    f"Error checking active jobs: {job_check_error}"
                                )
    except Exception as completion_error:
                logger.warning(
                    f"Error checking collection completion: {completion_error}"
                )

    except Exception as e:
            logger.warning(f"Error in _update_dialog_status: {e}")
            # Don't re-raise - just log and continue
    def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Property Search Enhanced")
    app.setApplicationVersion("2.0.0")

    # Set application style
    app.setStyle("Fusion")

    try:
        # Create and show main window
        window = EnhancedMainWindow()
        window.show()

        # Run application
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        QMessageBox.critical(
            None, "Startup Error", f"Failed to start application: {str(e)}"
        )
        sys.exit(1)


# Alias for backward compatibility
EnhancedPropertySearchApp = EnhancedMainWindow

if __name__ == "__main__":
    main()
