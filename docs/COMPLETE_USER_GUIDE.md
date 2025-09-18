# Maricopa Property Search - Complete User Guide

![Application Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python Version](https://img.shields.io/badge/Python-3.7%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation Guide](#installation-guide)
3. [First Time Setup](#first-time-setup)
4. [GUI Walkthrough](#gui-walkthrough)
5. [Feature Guide](#feature-guide)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Configuration](#advanced-configuration)
8. [Developer Notes](#developer-notes)

---

## Quick Start

### For Experienced Users

1. **Install Dependencies**
   ```bash
   python -m pip install -r requirements.txt
   playwright install chromium
   ```

2. **Configure Database** (PostgreSQL required)
   ```bash
   # Create database
   createdb maricopa_properties
   # Setup tables
   python scripts/setup_database_tables.py
   ```

3. **Launch Application**
   ```bash
   python RUN_APPLICATION.py
   ```

### For New Users

Follow the [Complete Installation Guide](#installation-guide) below for step-by-step instructions.

---

## Installation Guide

### System Requirements

| Component | Requirement |
|-----------|-------------|
| **Operating System** | Windows 10+, macOS 10.14+, Ubuntu 18.04+ |
| **Python** | 3.7 or higher |
| **Database** | PostgreSQL 12+ (recommended) |
| **Memory** | 4GB RAM minimum, 8GB recommended |
| **Storage** | 1GB free space |
| **Browser** | Chrome/Chromium (for web scraping) |

### Windows Installation (Recommended Path)

#### Step 1: Install Prerequisites

1. **Install Python 3.7+**
   - Download from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH"
   - Verify installation: `python --version`

2. **Install PostgreSQL**
   - Download from [PostgreSQL Downloads](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads)
   - Use these settings during installation:
     - Port: `5433` (avoids conflicts)
     - Password: Remember this for later
     - Locale: English, United States
   - ✅ Add to PATH: `C:\Program Files\PostgreSQL\14\bin`

3. **Install Google Chrome**
   - Download from [chrome.google.com](https://www.google.com/chrome/)
   - Required for web scraping functionality

#### Step 2: Setup Project

1. **Download/Clone Project**
   ```bash
   git clone <repository-url>
   cd MaricopaPropertySearch
   ```

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Browser Drivers**
   ```bash
   playwright install chromium
   ```

#### Step 3: Database Setup

1. **Create Database**
   ```bash
   # Open Command Prompt as Administrator
   createdb -U postgres -p 5433 maricopa_properties
   ```

2. **Setup Database Schema**
   ```bash
   python scripts/setup_database_tables.py
   ```

#### Step 4: Configuration

1. **Copy Environment File**
   ```bash
   copy .env.example .env
   ```

2. **Edit Configuration**
   - Open `config/config.ini`
   - Update database password:
   ```ini
   [database]
   password = your_postgres_password_here
   ```

#### Step 5: Test Installation

```bash
python scripts/test_installation.py
```

Expected output: All tests should pass ✅

#### Step 6: Launch Application

```bash
python RUN_APPLICATION.py
```

### Linux/macOS Installation

#### Prerequisites
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip postgresql postgresql-contrib

# macOS (with Homebrew)
brew install python postgresql
```

#### Setup Process
```bash
# Clone project
git clone <repository-url>
cd MaricopaPropertySearch

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Setup database
sudo -u postgres createdb maricopa_properties
python scripts/setup_database_tables.py

# Configure (edit config/config.ini with your settings)
cp .env.example .env

# Test installation
python scripts/test_installation.py

# Launch application
python RUN_APPLICATION.py
```

---

## First Time Setup

### Initial Configuration Wizard

When you first run the application, you'll see a setup wizard:

1. **Database Connection Test**
   - The application automatically tests database connectivity
   - If failed: Check PostgreSQL service and credentials

2. **API Configuration** (Optional)
   - Enter Maricopa County API token if available
   - Leave blank to use web scraping only

3. **Data Sources Priority**
   - Choose preferred data sources order:
     - API (fastest, requires token)
     - Web Scraping (reliable, slower)
     - Database Cache (fastest for repeat searches)

### Welcome Screen

![Screenshot Description: Main application window with welcome dialog showing quick start instructions, featuring a modern dark interface with clearly labeled buttons for different search types]

The welcome screen provides:
- Quick start instructions
- Feature overview
- System status indicators

---

## GUI Walkthrough

### Main Window Layout

![Screenshot Description: Full application window showing the main interface with search bar at top, results table in center, and status panel at bottom, using a clean professional design]

The main window consists of several key areas:

#### 1. Search Bar (Top)
- **Search Type Selector**: Dropdown to choose search method
- **Search Input Field**: Enter your search criteria
- **Search Button**: Execute the search
- **Clear Button**: Reset search results

#### 2. Results Table (Center)
- **Property List**: Shows found properties with key details
- **Column Headers**: Sortable by APN, Address, Owner, Value
- **Row Selection**: Click to select properties for actions
- **Context Menu**: Right-click for additional options

#### 3. Action Buttons (Right Panel)
- **View Details**: Open detailed property information
- **Manual Collect**: Force immediate data collection
- **Export Results**: Save data to file
- **Refresh Data**: Update property information

#### 4. Background Status Panel (Bottom)
- **Collection Progress**: Shows active data collection jobs
- **Status Messages**: Real-time updates on operations
- **Queue Information**: Number of pending jobs
- **Performance Metrics**: Response times and success rates

#### 5. Menu Bar
- **File**: Export, Import, Settings
- **Tools**: Test Sources, Clear Cache, Diagnostics
- **Help**: User Guide, About, System Info

### Search Interface

![Screenshot Description: Close-up of search interface showing dropdown menu with options for "Property Address", "Owner Name", and "APN", with a text input field and prominent search button]

#### Search Types Available:

1. **Property Address**
   - Enter full or partial street address
   - Example: "10000 W Missouri Ave"
   - Supports wildcards: "Missouri*"

2. **Owner Name**
   - Search by property owner name
   - Example: "John Smith"
   - Partial names supported

3. **APN (Assessor's Parcel Number)**
   - Enter complete APN
   - Example: "123-45-678"
   - Most precise search method

#### Search Features:
- **Auto-complete**: Suggestions based on previous searches
- **Search History**: Dropdown shows recent searches
- **Validation**: Input validation with helpful error messages
- **Progress Indicator**: Visual feedback during search

### Results Display

![Screenshot Description: Results table showing multiple property listings with columns for APN, Address, Owner Name, Property Type, Market Value, and status indicators for data completeness]

#### Column Descriptions:

| Column | Description | Details |
|--------|-------------|---------|
| **APN** | Assessor's Parcel Number | Unique property identifier |
| **Address** | Property Address | Full street address |
| **Owner** | Property Owner | Current owner name |
| **Type** | Property Type | Residential, Commercial, etc. |
| **Market Value** | Current Market Value | Latest assessed value |
| **Last Sale** | Last Sale Date | Most recent transaction |
| **Status** | Data Status | Completeness indicator |

#### Status Indicators:
- 🟢 **Complete**: All data collected
- 🟡 **Partial**: Basic data only
- 🔄 **Collecting**: Data collection in progress
- ❌ **Failed**: Collection failed (click to retry)

### Property Details Window

![Screenshot Description: Detailed property view window with multiple tabs showing Property Info, Tax History, Sales History, and Documents, with comprehensive property details displayed in a professional layout]

The detailed view opens when you double-click a property or click "View Details":

#### Property Information Tab
- **Basic Details**: Address, APN, ownership information
- **Property Characteristics**: Square footage, bedrooms, bathrooms
- **Assessment Information**: Market value, assessed value, tax information
- **Physical Description**: Year built, lot size, property type

#### Tax History Tab
- **Assessment History**: Year-over-year value changes
- **Tax Payments**: Payment history and due dates
- **Exemptions**: Applied tax exemptions
- **Delinquency Status**: Outstanding tax information

#### Sales History Tab
- **Transaction Records**: Complete sales history
- **Price Trends**: Historical price changes
- **Transfer Details**: Sale dates, amounts, parties involved
- **Market Analysis**: Price per square foot trends

#### Documents Tab
- **Assessor Links**: Direct links to county assessor records
- **Recorder Documents**: Links to recorded documents
- **Tax Information**: Links to tax payment portals
- **External Resources**: Additional data sources

### Background Collection Status

![Screenshot Description: Status panel at bottom of application showing active background data collection with progress bars, job counts, and real-time status updates]

The background status panel provides real-time information about data collection:

#### Status Elements:
- **Active Jobs**: Number of properties currently being processed
- **Queue Size**: Number of properties waiting for processing
- **Success Rate**: Percentage of successful collections
- **Average Time**: Typical collection time per property

#### Progress Indicators:
- **Overall Progress**: Global progress bar for all active jobs
- **Individual Jobs**: Specific progress for each property
- **Time Estimates**: Estimated completion times
- **Error Count**: Failed collection attempts

---

## Feature Guide

### Core Search Features

#### 1. Basic Property Search

**Purpose**: Find properties by various criteria
**How to Use**:
1. Select search type from dropdown
2. Enter search criteria
3. Click "Search Properties"
4. Review results in table

**Tips**:
- Use partial addresses for broader results
- Owner name searches support partial matches
- APN searches are most precise

#### 2. Automatic Data Enhancement

**Purpose**: Automatically collect comprehensive data for search results
**How it Works**:
- Top results automatically queued for collection
- Background processing doesn't block user interface
- Priority given to viewed properties

**Benefits**:
- Rich data available when you need it
- Non-blocking user experience
- Intelligent prioritization

#### 3. Manual Data Collection

**Purpose**: Force immediate comprehensive data collection
**When to Use**:
- Need data immediately
- Automatic collection failed
- Want to ensure freshest data

**How to Use**:
1. Select property in results table
2. Click "Manual Collect (Immediate)"
3. Monitor progress dialog
4. View enhanced details when complete

### Advanced Features

#### 1. Batch Processing

**Purpose**: Process multiple properties simultaneously
**Use Cases**:
- Research property portfolios
- Market analysis
- Bulk data collection

**How to Use**:
1. Select multiple properties (Ctrl+click)
2. Choose batch action from menu
3. Monitor progress in status panel

#### 2. Export and Reporting

**Purpose**: Save property data for external analysis
**Available Formats**:
- CSV (Excel compatible)
- Excel (.xlsx)
- JSON (for developers)

**Export Options**:
- Selected properties only
- All search results
- Custom field selection
- Date range filtering

#### 3. Data Source Management

**Purpose**: Control where data comes from
**Available Sources**:
- **API**: Fastest, requires authentication
- **Web Scraping**: Reliable, moderate speed
- **Database Cache**: Fastest for repeat queries

**Configuration**:
- Set source priority in settings
- Enable/disable individual sources
- Configure timeouts and retries

### Performance Features

#### 1. Smart Caching

**Purpose**: Improve performance and reduce server load
**How it Works**:
- Recently accessed data cached locally
- Configurable cache expiration (default 24 hours)
- Automatic cache cleanup

**Benefits**:
- Faster repeat searches
- Reduced network usage
- Better user experience

#### 2. Concurrent Processing

**Purpose**: Process multiple properties simultaneously
**Configuration**:
- Default: 3 concurrent jobs
- Adjustable in settings
- Automatic resource management

**Impact**:
- 3-5x faster bulk operations
- Better resource utilization
- Maintained system responsiveness

#### 3. Progress Monitoring

**Purpose**: Transparent feedback on long-running operations
**Features**:
- Real-time progress bars
- Estimated completion times
- Success/failure rates
- Detailed status messages

---

## Troubleshooting

### Common Issues and Solutions

#### Installation Problems

**Issue**: Python command not recognized
**Solution**:
```bash
# Windows: Add Python to PATH
# Check: python --version
# If fails: Reinstall Python with "Add to PATH" checked
```

**Issue**: PostgreSQL connection failed
**Solution**:
```bash
# Check service status
# Windows: services.msc → PostgreSQL
# Linux: sudo systemctl status postgresql
# Verify credentials in config/config.ini
```

**Issue**: Browser driver installation failed
**Solution**:
```bash
# Reinstall Playwright browsers
playwright install chromium --force
# Or use the script
python scripts/install_chromedriver.py
```

#### Application Startup Issues

**Issue**: Application won't start
**Diagnostic Steps**:
1. Check dependencies: `python scripts/test_installation.py`
2. Verify database: `python scripts/test_db_connection.py`
3. Check logs: `logs/application.log`

**Issue**: GUI doesn't appear
**Solutions**:
- Check display settings (especially on Linux)
- Try: `export DISPLAY=:0` (Linux)
- Update graphics drivers
- Install system Qt libraries

#### Search and Data Collection Issues

**Issue**: Search returns no results
**Troubleshooting**:
1. Check internet connection
2. Test data sources: Tools → Test All Sources
3. Try different search terms
4. Check search type matches your input

**Issue**: Background collection not working
**Solutions**:
1. Check browser installation: Chrome/Chromium required
2. Verify internet connectivity
3. Check logs for specific errors
4. Adjust timeout settings in configuration

**Issue**: Slow performance
**Optimization Steps**:
1. Reduce concurrent jobs in settings
2. Clear cache: Tools → Clear Cache
3. Check database performance
4. Close other resource-intensive applications

#### Data Quality Issues

**Issue**: Incomplete property data
**Possible Causes**:
- Source website temporary issues
- Network connectivity problems
- Data not available for specific property

**Solutions**:
1. Try manual collection: "Manual Collect (Immediate)"
2. Wait and retry later
3. Try different data sources
4. Check specific property on county website

**Issue**: Outdated information
**Solutions**:
1. Use "Refresh Property Data" button
2. Clear cache for specific property
3. Check cache expiration settings
4. Verify source data freshness

### Error Messages Guide

#### Database Errors

**Error**: "Connection timeout while connecting to database"
**Solutions**:
- Check PostgreSQL service status
- Verify network connectivity
- Increase timeout in configuration
- Check firewall settings

**Error**: "Authentication failed for user"
**Solutions**:
- Verify username/password in config.ini
- Check user permissions in PostgreSQL
- Reset password if necessary

#### Web Scraping Errors

**Error**: "Browser automation failed"
**Solutions**:
- Check Chrome/Chromium installation
- Update browser drivers: `playwright install chromium`
- Check website accessibility
- Verify no browser processes running

**Error**: "Element not found on page"
**Causes**:
- Website layout changed
- Page loading timeout
- Network connectivity issues

**Solutions**:
- Update application to latest version
- Increase timeout settings
- Check website manually
- Use alternative data sources

#### API Errors

**Error**: "API authentication failed"
**Solutions**:
- Verify API token in configuration
- Check token expiration
- Contact API provider for support

**Error**: "Rate limit exceeded"
**Solutions**:
- Reduce API request frequency
- Wait before retrying
- Implement request throttling

### Diagnostic Tools

#### Built-in Diagnostics

1. **Test Installation**
   ```bash
   python scripts/test_installation.py
   ```
   Checks all dependencies and configuration

2. **Test Database Connection**
   ```bash
   python scripts/test_db_connection.py
   ```
   Verifies database connectivity and permissions

3. **Test All Sources**
   - Use GUI: Tools → Test All Sources
   - Shows status of API, scraping, and database

#### Log Analysis

**Log Locations**:
- Application logs: `logs/application.log`
- Error logs: `logs/errors.log`
- Performance logs: `logs/performance.log`

**Log Level Configuration**:
```ini
[logging]
level = INFO  # DEBUG for detailed logs
```

**Common Log Patterns**:
- `ERROR`: Critical issues requiring attention
- `WARNING`: Potential problems, may affect functionality
- `INFO`: Normal operation information
- `DEBUG`: Detailed execution information

#### Performance Monitoring

**System Requirements Check**:
```python
# Memory usage
import psutil
print(f"Memory: {psutil.virtual_memory().percent}%")

# Database connections
# Check active connections in PostgreSQL
SELECT count(*) FROM pg_stat_activity;
```

**Performance Metrics**:
- Search response time: < 5 seconds typical
- Data collection: 30-60 seconds per property
- Memory usage: < 500MB normal operation
- Database connections: < 10 typical

---

## Advanced Configuration

### Configuration Files

#### Main Configuration: `config/config.ini`

```ini
[database]
host = localhost
port = 5433
database = maricopa_properties
user = property_user
password = your_password_here
pool_size = 20
max_overflow = 40

[api]
base_url = https://mcassessor.maricopa.gov
token = your_api_token_here
timeout = 30
max_retries = 3
rate_limit = 10

[scraping]
browser = chrome
headless = true
timeout = 30
max_workers = 5
parallel_browsers = 3

[application]
auto_start_collection = true
max_results = 20
cache_size = 1000
status_update_frequency = 2
```

#### Environment Variables: `.env`

```bash
# Project paths
PROJECT_ROOT=C:\Users\YourName\Development\MaricopaPropertySearch
PYTHONPATH=C:\Users\YourName\Development\MaricopaPropertySearch\src

# Database connection
DB_HOST=localhost
DB_PORT=5433
DB_NAME=maricopa_properties
DB_USER=property_user
DB_PASSWORD=your_password_here

# API configuration
API_TOKEN=your_api_token_here

# Logging
LOG_LEVEL=INFO
```

### Performance Tuning

#### Database Optimization

```sql
-- Increase connection limits
ALTER SYSTEM SET max_connections = 200;

-- Optimize for read-heavy workload
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';

-- Restart PostgreSQL after changes
```

#### Application Tuning

```ini
[application]
# Reduce for slower systems
max_concurrent_jobs = 2

# Increase for better performance
db_pool_size = 10

# Adjust cache size based on available memory
cache_size = 2000

# Faster updates for responsive UI
status_update_frequency = 1
```

#### System Optimization

**Windows**:
```batch
# Increase virtual memory
# System Properties → Advanced → Performance → Settings → Advanced → Virtual Memory

# Disable unnecessary services
# services.msc → Disable unused services
```

**Linux**:
```bash
# Increase file handle limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize PostgreSQL shared memory
echo "kernel.shmmax = 268435456" >> /etc/sysctl.conf
```

### API Integration

#### Maricopa County API Setup

1. **Obtain API Token**
   - Visit Maricopa County Assessor website
   - Request developer access
   - Follow authentication setup instructions

2. **Configure Authentication**
   ```ini
   [api]
   token = your_api_token_here
   base_url = https://mcassessor.maricopa.gov
   ```

3. **Test API Connection**
   ```python
   python scripts/test_real_endpoints.py
   ```

#### Custom API Endpoints

To add custom endpoints:

1. **Modify API Client**
   ```python
   # src/api_client.py
   class MaricopaAPIClient:
       def custom_endpoint(self, params):
           # Add your custom endpoint logic
           pass
   ```

2. **Update Configuration**
   ```ini
   [api]
   custom_endpoint = https://your-api.com/endpoint
   ```

### Data Source Priority

Configure data source priority in settings:

```python
# Priority order (1 = highest priority)
data_sources = {
    'api': 1,        # Fastest, requires token
    'scraping': 2,   # Reliable, moderate speed
    'cache': 3       # Fastest for repeat queries
}
```

---

## Developer Notes

### Architecture Overview

#### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RUN_APPLICATION.py                      │
│              (Primary Application Launcher)                │
├─────────────────────────────────────────────────────────────┤
│  Environment Check → Database Setup → GUI Launch          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│                Enhanced Main Window                         │
├─────────────────────┼───────────────────────────────────────┤
│  Search Interface → Results Table → Background Status      │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│  Background Data Collection Manager                         │
├─────────────────────┼───────────────────────────────────────┤
│  • Job Prioritization • Cache Management                   │
│  • Progress Tracking • Signal Coordination                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│  Thread-Safe Database Manager                              │
├─────────────────────┼───────────────────────────────────────┤
│  • Connection Pooling • Concurrent Operations              │
│  • Performance Monitoring • Data Validation                │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│  Web Scraping & API Integration                            │
├─────────────────────┼───────────────────────────────────────┤
│  • Playwright Automation • Tax Data Collection             │
│  • Sales History • Property Details                        │
└─────────────────────────────────────────────────────────────┘
```

#### Project Structure

```
MaricopaPropertySearch/
├── RUN_APPLICATION.py          # Primary launcher
├── src/                        # Core application modules
│   ├── api_client.py           # API integration layer
│   ├── database_manager.py     # Database operations
│   ├── config_manager.py       # Configuration management
│   ├── background_data_collector.py # Background processing
│   ├── gui/                    # GUI components
│   │   ├── enhanced_main_window.py # Main interface
│   │   └── gui_enhancements_dialogs.py # Dialog windows
│   └── web_scraper.py          # Web automation
├── config/                     # Configuration files
│   ├── config.ini              # Main configuration
│   └── app_settings.json       # User settings
├── scripts/                    # Utility scripts
│   ├── setup_database_tables.py # Database setup
│   ├── test_installation.py    # Installation testing
│   └── diagnostics/            # Diagnostic tools
├── docs/                       # Documentation
├── logs/                       # Application logs
└── requirements.txt            # Python dependencies
```

### Key Technologies

#### Frontend Framework
- **PyQt5**: Cross-platform GUI framework
- **Custom Widgets**: Professional interface components
- **Threading**: Non-blocking background operations
- **Signals/Slots**: Event-driven communication

#### Backend Systems
- **PostgreSQL**: Primary data storage with connection pooling
- **SQLAlchemy**: Database ORM for complex queries
- **Threading**: Concurrent data collection and processing
- **Caching**: Multi-level caching for performance

#### Web Integration
- **Playwright**: Modern web automation framework
- **Requests**: HTTP client for API integration
- **BeautifulSoup**: HTML parsing fallback
- **Selenium**: Legacy browser automation support

#### Data Processing
- **Pandas**: Data analysis and manipulation
- **JSON**: Configuration and data serialization
- **CSV/Excel**: Export functionality
- **Logging**: Comprehensive operation tracking

### Development Workflow

#### Setting Up Development Environment

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd MaricopaPropertySearch
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv dev-env
   # Windows
   dev-env\Scripts\activate
   # Linux/macOS
   source dev-env/bin/activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-qt mypy black flake8
   ```

4. **Setup Pre-commit Hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

#### Code Standards

**Python Style**:
- Follow PEP 8 guidelines
- Use Black for code formatting
- Maximum line length: 88 characters
- Use type hints for all functions

**Documentation**:
- Docstrings for all public methods
- Inline comments for complex logic
- README updates for new features
- API documentation for public interfaces

**Testing**:
- Unit tests for all core functionality
- Integration tests for data collection
- GUI tests using pytest-qt
- Performance tests for optimization

#### Testing Framework

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/test_gui.py
pytest tests/test_database.py
pytest tests/test_api_client.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run performance tests
pytest tests/test_performance.py --benchmark
```

### API Documentation

#### Core Classes

**ConfigManager**:
```python
class ConfigManager:
    """Manages application configuration from multiple sources"""

    def get_database_config(self) -> dict:
        """Returns database connection parameters"""

    def get_api_config(self) -> dict:
        """Returns API configuration"""

    def get_source_priority(self) -> list:
        """Returns data source priority order"""
```

**DatabaseManager**:
```python
class DatabaseManager:
    """Thread-safe database operations manager"""

    def search_properties(self, search_term: str, search_type: str) -> list:
        """Search for properties in database"""

    def store_property_data(self, property_data: dict) -> bool:
        """Store comprehensive property data"""

    def get_property_details(self, apn: str) -> dict:
        """Get detailed property information"""
```

**BackgroundDataCollectionManager**:
```python
class BackgroundDataCollectionManager:
    """Manages background data collection operations"""

    def queue_property_collection(self, apn: str, priority: int = 5):
        """Add property to collection queue"""

    def start_collection(self):
        """Start background collection processing"""

    def get_collection_status(self) -> dict:
        """Get current collection status"""
```

#### Event System

**Signal Definitions**:
```python
# Main window signals
property_selected = Signal(str)  # APN selected
search_completed = Signal(list)  # Search results ready
collection_progress = Signal(str, int)  # Progress updates

# Background collection signals
collection_started = Signal(str)  # Collection began for APN
collection_completed = Signal(str, dict)  # Collection finished
collection_failed = Signal(str, str)  # Collection failed with error
```

#### Database Schema

**Properties Table**:
```sql
CREATE TABLE properties (
    apn VARCHAR(20) PRIMARY KEY,
    address TEXT NOT NULL,
    owner_name TEXT,
    property_type VARCHAR(50),
    market_value DECIMAL(12,2),
    assessed_value DECIMAL(12,2),
    square_feet INTEGER,
    lot_size DECIMAL(10,2),
    year_built INTEGER,
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Tax History Table**:
```sql
CREATE TABLE tax_history (
    id SERIAL PRIMARY KEY,
    apn VARCHAR(20) REFERENCES properties(apn),
    tax_year INTEGER NOT NULL,
    assessed_value DECIMAL(12,2),
    tax_amount DECIMAL(10,2),
    payment_status VARCHAR(20),
    due_date DATE,
    paid_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Customization Guide

#### Adding New Data Sources

1. **Create Data Source Class**:
```python
class CustomDataSource:
    def __init__(self, config):
        self.config = config

    def search_properties(self, search_term):
        # Implement search logic
        pass

    def get_property_details(self, apn):
        # Implement detail collection
        pass
```

2. **Register Data Source**:
```python
# In config_manager.py
def get_data_sources(self):
    sources = {
        'api': MaricopaAPIClient,
        'scraping': WebScraper,
        'custom': CustomDataSource  # Add new source
    }
    return sources
```

#### Custom GUI Components

```python
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Signal

class CustomPropertyWidget(QWidget):
    """Custom widget for property display"""

    property_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Custom widget layout
        pass
```

#### Plugin Architecture

```python
class PluginInterface:
    """Interface for application plugins"""

    def get_name(self) -> str:
        """Return plugin name"""
        pass

    def get_version(self) -> str:
        """Return plugin version"""
        pass

    def initialize(self, app_context):
        """Initialize plugin with application context"""
        pass

    def get_menu_items(self) -> list:
        """Return menu items to add to application"""
        pass
```

---

## Recent Updates and Fixes

### September 2024 Major Updates

#### Critical Bug Fixes
- ✅ **Fixed**: clear_apn_cache AttributeError
- ✅ **Fixed**: show_message AttributeError in BackgroundCollectionStatusWidget
- ✅ **Enhanced**: Data collection with progress dialog and better error handling
- ✅ **Fixed**: Settings persistence mechanism
- ✅ **Configured**: Source priority (API → Scraping → Cache)
- ✅ **Fixed**: Test All Sources functionality

#### Performance Improvements
- **Background Collection**: Non-blocking architecture with priority queuing
- **Concurrent Processing**: Configurable concurrent job execution (default: 3)
- **Smart Caching**: 24-hour data freshness with intelligent cache management
- **User Experience**: Professional messaging with actionable guidance

#### User Interface Enhancements
- **Progress Tracking**: Real-time progress dialogs for data collection
- **Status Transparency**: Clear indication of data completeness
- **Error Recovery**: User-friendly error messages with retry options
- **Settings Persistence**: Configuration saved across application restarts

### Testing and Validation
- **Missouri Avenue Testing**: Comprehensive validation with real property data
- **Auto-Collection Verification**: Background system validated
- **Database Integration**: Proper data storage and retrieval confirmed
- **Performance Metrics**: Response times and success rates monitored

---

## Support and Contact

### Getting Help

1. **Documentation**: Start with this guide and the troubleshooting section
2. **Built-in Diagnostics**: Use Tools → Test All Sources for system status
3. **Log Analysis**: Check `logs/application.log` for detailed error information
4. **Test Scripts**: Run diagnostic scripts in the `scripts/` directory

### Reporting Issues

When reporting issues, please include:
- Operating system and version
- Python version: `python --version`
- Error messages from logs
- Steps to reproduce the issue
- Screenshots if applicable

### Contributing

We welcome contributions! Please see the [Contributing Guide](../CONTRIBUTING.md) for:
- Code standards and style guide
- Testing requirements
- Pull request process
- Development workflow

---

**Last Updated**: January 2025
**Version**: 2.0 (Enhanced with Background Collection)
**Status**: Production Ready

This comprehensive guide covers all aspects of the Maricopa Property Search application. For additional support or questions, please refer to the troubleshooting section or contact the development team.