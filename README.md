# Maricopa Property Search Application

A modern, cross-platform property research application for Maricopa County, Arizona, featuring unified architecture, WSL GUI support, and comprehensive property search capabilities.

![Application Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue)
![Platform](https://img.shields.io/badge/Platform-WSL%20%7C%20Linux%20%7C%20Windows-lightgrey)
![Architecture](https://img.shields.io/badge/Architecture-Unified%20Components-blue)

## 🚨 **IMPORTANT: GitHub CI/CD Requirements**

**Before pushing any code to GitHub, ALL changes must pass automated quality gates.**

This repository uses strict code formatting and quality enforcement through GitHub Actions. **Your push will FAIL if code is not properly formatted.**

### Quick Setup for Contributors

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install formatting tools
pip install black isort flake8 pylint mypy bandit

# 3. Format code before commit (REQUIRED)
python -m black src/
python -m isort src/

# 4. Install pre-commit hooks (RECOMMENDED)
pip install pre-commit
pre-commit install
```

### Most Common Error: Black Formatting
**Error**: `"Code Formatting Check: Black" with exit code 123`

**Fix**:
```bash
source venv/bin/activate
python -m black src/
git add .
git commit -m "Fix Black formatting"
git push
```

📋 **For complete setup instructions, quality standards, and troubleshooting**, see **[CONTRIBUTING.md](CONTRIBUTING.md)**

---

## Features

### Core Search Capabilities
- **Multi-Search Types**: Search by property address, owner name, or APN (Assessor's Parcel Number)
- **Real-Time Results**: Instant search results with progressive data enhancement
- **Database Caching**: Smart caching system with 24-hour data freshness validation
- **Export Functionality**: Export search results to CSV, Excel, and JSON formats

### Advanced Data Collection
- **Automatic Background Collection**: Non-blocking data enhancement system
- **Tax Record Integration**: Comprehensive tax assessment and payment history
- **Sales History**: Property transfer records and transaction details
- **Real-Time Progress Indicators**: Visual feedback for all data collection operations

### Professional User Experience
- **Modern Interface**: Clean, professional PyQt5-based GUI
- **Actionable Messaging**: Eliminated "Not Available" messages with user-friendly guidance
- **Progress Visualization**: Real-time status updates and collection progress
- **Error Recovery**: Intelligent retry mechanisms with clear user instructions

### Major Enhancements (September 2025)

#### Unified Architecture (Phase 2 Complete)
- **75% File Reduction**: Consolidated 16 duplicate implementations into 4 unified components
- **Unified API Client**: Single client with progressive loading (0.04s basic → 0.33s comprehensive)
- **Unified Data Collector**: Background processing with priority queues and parallel collection
- **Thread-Safe Database**: Unified manager with PostgreSQL, SQLite, and Mock mode support
- **Unified GUI Launcher**: Intelligent platform detection with Enhanced + Basic GUI fallback

#### WSL GUI Support (Phase 3 Complete)
- **Native Wayland Support**: WSLg integration with automatic platform detection
- **Cross-Platform Compatibility**: Native support for WSL, Linux, and Windows environments
- **Enhanced Platform Detection**: Intelligent Wayland/X11/Windows backend selection
- **Import System Resolution**: Fixed relative import errors for reliable Enhanced GUI loading

#### Performance Optimization
- **Sub-Second Search**: 0.04s basic search, 0.33s comprehensive data collection
- **Progressive Data Loading**: Three-stage loading with immediate basic results
- **Background Processing**: Non-blocking data collection with real-time progress tracking
- **Smart Caching**: 24-hour data freshness with intelligent cache management

#### Developer Experience
- **Simplified Architecture**: Clear module hierarchy with absolute imports
- **Backward Compatibility**: All original entry points maintained through delegation
- **Comprehensive Documentation**: Updated guides, migration paths, and troubleshooting
- **Validated Workflows**: Complete Missouri Avenue testing with performance metrics

## Installation

### System Requirements
- **Operating System**: WSL Ubuntu 22.04+, Linux (Ubuntu 20.04+), or Windows 10+
- **Python**: 3.12+ (tested on Python 3.12.3)
- **Database**: PostgreSQL 12+ (production), SQLite (development), Mock mode (testing)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 1GB free space for application and data
- **Display**: WSLg, X11, or native Windows GUI support

### Quick Start

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd MaricopaPropertySearch
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   # Optional: Enhanced web scraping (recommended)
   pip install playwright
   playwright install chromium
   ```

3. **Launch Application (Multiple Options)**
   ```bash
   # Recommended: Unified launcher with automatic platform detection
   python src/gui_launcher_unified.py

   # Alternative: Basic GUI launcher
   python src/basic_gui_launcher.py

   # Legacy compatibility (delegated to unified launcher)
   python maricopa_property_search.py
   ```

### WSL GUI Setup (Windows Users)

For WSL users to enable GUI functionality:

4. **Verify WSLg Installation** (pre-configured on Ubuntu 22.04+)
   ```bash
   echo $WAYLAND_DISPLAY  # Should show: wayland-0
   echo $DISPLAY          # Should show: :0
   ```

5. **Test GUI Capability**
   ```bash
   python src/gui_launcher_unified.py --test-gui
   ```

   Expected output:
   ```
   [ENV] Platform: Linux
   [ENV] WSL detected: True
   [ENV] Display available: True
   [ENV] Can use GUI: True
   [ENV] Qt platform: wayland
   ```

6. **Install GUI Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pyqt5 python3-pyqt5.qtwebkit
   ```

## How to Run

### Unified Launcher (Recommended)
```bash
python src/gui_launcher_unified.py
```

**Features**:
- ✅ Automatic platform detection (WSL/Linux/Windows)
- ✅ Enhanced GUI with PyQt5 + Basic GUI fallback
- ✅ Native Wayland support for WSL environments
- ✅ Intelligent Qt backend selection
- ✅ Graceful degradation across platforms

### Alternative Launch Methods

**Basic GUI** (lightweight option):
```bash
python src/basic_gui_launcher.py
```

**Legacy Compatibility** (delegated to unified launcher):
```bash
python maricopa_property_search.py
```

### Platform-Specific Notes

**WSL Users**:
- WSLg provides native GUI support with Wayland backend
- No manual X11 server configuration required
- Enhanced GUI loads automatically with full features

**Linux Users**:
- X11 and Wayland both supported
- Automatic platform detection and optimization
- Install PyQt5 via package manager for best performance

**Windows Users**:
- Native Windows GUI integration
- Enhanced GUI provides full feature set
- Basic GUI available as lightweight alternative

## Usage

### Basic Property Search

1. **Select Search Type**
   - Property Address: Search by street address or partial address
   - Owner Name: Search by property owner name (full or partial)
   - APN: Search by Assessor's Parcel Number

2. **Enter Search Criteria**
   - Type your search terms in the search box
   - Use wildcards (*) for broader searches
   - Partial matches are supported for most search types

3. **Review Results**
   - Search results appear instantly with basic property information
   - Background data collection automatically enhances results
   - Double-click any property to view detailed information

### Background Data Collection

The application automatically collects comprehensive property data in the background:

- **Automatic Enhancement**: Top search results are queued for data collection
- **Progress Monitoring**: Watch the background status panel for real-time progress
- **Manual Override**: Force immediate data collection for specific properties
- **Smart Caching**: Avoids duplicate collection with intelligent cache management

### Property Details

Property detail views include:
- **Basic Information**: Address, APN, owner details, property characteristics
- **Tax Records**: Assessment history, tax payments, exemptions
- **Sales History**: Transaction records, sale prices, transfer dates
- **Property Characteristics**: Square footage, lot size, year built, bedrooms/bathrooms

### Export and Reporting

- **Multiple Formats**: Export to CSV, Excel, or JSON
- **Customizable Fields**: Select specific data fields for export
- **Bulk Operations**: Export all search results or selected properties
- **Report Generation**: Generate formatted reports for property research

## Configuration

### Unified Configuration Manager

The application uses a centralized configuration system (`src/enhanced_config_manager.py`):

```python
from src.enhanced_config_manager import EnhancedConfigManager

# Single configuration instance for entire application
config = EnhancedConfigManager()
```

### Database Configuration

**Production** (PostgreSQL):
```bash
config.set('database', 'engine', 'postgresql')
config.set('database', 'host', 'localhost')
config.set('database', 'port', 5432)
config.set('database', 'name', 'maricopa_property_search')
```

**Development** (SQLite):
```bash
config.set('database', 'engine', 'sqlite')
config.set('database', 'path', 'data/maricopa.db')
```

**Testing** (Mock mode):
```bash
config.set('database', 'use_mock', True)
```

### API Integration

**Multi-Source Fallback System**:
1. **Primary**: Maricopa County Assessor API
2. **Secondary**: Web scraping with BeautifulSoup/Playwright
3. **Fallback**: Mock data for testing

```python
# API client automatically handles fallback chain
from src.api_client_unified import UnifiedMaricopaAPIClient
api_client = UnifiedMaricopaAPIClient(config)
```

### Performance Settings

**Progressive Data Loading**:
- **Basic Search**: 0.04s average response time
- **Comprehensive Data**: 0.33s average with background enhancement
- **Background Processing**: Non-blocking with priority queues

## Troubleshooting

### WSL GUI Issues

#### GUI Not Loading
**Symptoms**: "Display not available" or Qt platform errors

**Solutions**:
1. **Verify Display Environment**:
   ```bash
   echo $WAYLAND_DISPLAY $DISPLAY
   # Should show values for WSL/Linux
   ```

2. **Check Qt Installation**:
   ```bash
   python -c "import PyQt5; print('PyQt5 available')"
   ```

3. **Test Platform Detection**:
   ```bash
   python src/gui_launcher_unified.py --debug-platform
   ```

#### Import Errors
**Symptoms**: "ModuleNotFoundError" or relative import errors

**Solutions**:
1. **Verify Working Directory**:
   ```bash
   pwd  # Should be in MaricopaPropertySearch root
   ```

2. **Check Python Path**:
   ```bash
   python -c "import sys; print('\n'.join(sys.path))"
   ```

3. **Use Absolute Imports** (for development):
   ```python
   # Correct
   from src.api_client_unified import UnifiedMaricopaAPIClient

   # Avoid
   from api_client_unified import UnifiedMaricopaAPIClient
   ```

### Performance Issues

#### Slow Searches or Timeouts
**Solutions**:
1. **Check Data Source Status**:
   ```bash
   python claudedocs/missouri_ave_test.py
   ```

2. **Verify Network Connectivity**:
   ```bash
   curl -I https://mcassessor.maricopa.gov
   ```

3. **Enable Mock Mode** (for development):
   ```python
   config = EnhancedConfigManager()
   config.set('database', 'use_mock', True)
   ```

### Database Connection Issues

#### Database Connection Errors or Timeouts
**Solutions**:
1. **Check PostgreSQL Status** (production):
   ```bash
   systemctl status postgresql
   ```

2. **Use SQLite Fallback** (development):
   ```python
   config.set('database', 'engine', 'sqlite')
   ```

3. **Enable Mock Mode** (testing):
   ```python
   config.set('database', 'use_mock', True)
   ```

### Getting Help

1. **Check Phase Completion Documents**: Detailed technical information and troubleshooting
2. **Run Validation Tests**: Use provided test scripts to verify functionality
3. **Review Documentation**:
   - `CLAUDE.md` - Updated development guide with consolidated architecture
   - `MIGRATION_GUIDE.md` - Comprehensive migration documentation
   - `checkpoints/PHASE_*_COMPLETE_*.md` - Detailed phase completion records
4. **Test Missouri Avenue Workflow**: `python claudedocs/missouri_ave_test.py`
5. **Platform Detection**: `python src/gui_launcher_unified.py --test-gui`

## Contributing

⚠️ **CRITICAL**: Before contributing, read **[CONTRIBUTING.md](CONTRIBUTING.md)** for complete GitHub CI/CD requirements and quality standards.

### Quick Start for Contributors

**⚡ Fast Track Setup**:
```bash
# 1. Setup environment
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install black isort flake8 pylint mypy bandit pre-commit

# 2. Install pre-commit hooks (prevents CI failures)
pre-commit install

# 3. Before EVERY commit (REQUIRED)
python -m black src/
python -m isort src/
```

### Development Workflow

1. **Fork and Setup**
   ```bash
   git fork <repository-url>
   cd MaricopaPropertySearch
   ```

2. **Follow Quality Standards** (See [CONTRIBUTING.md](CONTRIBUTING.md))
   - ✅ **Black formatting**: 100% compliance (enforced by CI/CD)
   - ✅ **Type hints**: Required for all public functions
   - ✅ **Test coverage**: 80%+ minimum
   - ✅ **Security scanning**: Zero high-severity issues

3. **Submit Changes**
   - Format code with Black (REQUIRED)
   - Run tests and quality checks
   - Create pull request

### GitHub Actions Pipeline

Every push triggers a **9-stage quality pipeline**:
1. **Code Formatting Check (Black)** ⚠️ **WILL FAIL IF NOT FORMATTED**
2. Import Organization (isort)
3. Code Linting (Flake8, Pylint)
4. Type Checking (mypy)
5. Security Scanning (Bandit, Safety)
6. Unit Tests (80%+ coverage required)
7. Integration Tests
8. Performance Benchmarks
9. System Workflow Validation

**📋 For complete details, troubleshooting, and quality standards**: **[CONTRIBUTING.md](CONTRIBUTING.md)**

## Architecture

### Unified Component Structure (Post-Phase 2)

```
MaricopaPropertySearch/
├── src/
│   ├── gui_launcher_unified.py       # Unified GUI launcher (consolidates 4)
│   ├── api_client_unified.py         # Unified API client (consolidates 6)
│   ├── unified_data_collector.py     # Unified data collector (consolidates 4)
│   ├── threadsafe_database_manager.py # Unified database manager (consolidates 2)
│   ├── enhanced_config_manager.py    # Centralized configuration
│   └── gui/
│       ├── enhanced_main_window.py   # Enhanced GUI (PyQt5)
│       └── gui_enhancements_dialogs.py # GUI components
├── claudedocs/
│   └── missouri_ave_test.py          # Workflow validation
├── checkpoints/                      # Phase completion records
├── CLAUDE.md                         # Development guide
├── MIGRATION_GUIDE.md                # Migration documentation
└── maricopa_property_search.py       # Legacy entry point (delegates)
```

### Unified Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│              UnifiedGUILauncher                             │
│    (Intelligent Platform Detection & GUI Selection)        │
├─────────────────────────────────────────────────────────────┤
│  WSL/Wayland → Enhanced GUI │ Linux/X11 → Enhanced GUI     │
│  Windows → Enhanced GUI     │ Fallback → Basic GUI        │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│            Enhanced Main Window (PyQt5)                    │
├─────────────────────┼───────────────────────────────────────┤
│  • Progressive Search Interface • Real-time Results       │
│  • Background Status Panel • Export Capabilities          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│         UnifiedMaricopaAPIClient                           │
├─────────────────────┼───────────────────────────────────────┤
│  API → Web Scraping → Mock (Multi-source fallback)       │
│  • 0.04s Basic Search • 0.33s Comprehensive Data          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│        UnifiedDataCollector                                │
├─────────────────────┼───────────────────────────────────────┤
│  • Background Processing • Priority Queues                │
│  • Parallel Collection • Real-time Progress               │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│      ThreadSafeDatabaseManager                             │
├─────────────────────┼───────────────────────────────────────┤
│  PostgreSQL → SQLite → Mock (Environment-based selection) │
│  • Connection Pooling • Thread-safe Operations            │
└─────────────────────────────────────────────────────────────┘
```

### Key Technologies

**Frontend**:
- **PyQt5**: Enhanced GUI with native Wayland/X11/Windows support
- **tkinter**: Basic GUI fallback for lightweight environments
- **Platform Detection**: Intelligent Qt backend selection

**Backend**:
- **PostgreSQL**: Production database with connection pooling
- **SQLite**: Development database for local testing
- **Mock Mode**: Testing environment with realistic data generation

**Web Automation**:
- **BeautifulSoup4 + lxml**: Primary web scraping engine
- **Playwright**: Optional enhanced browser automation
- **Multi-source Fallback**: API → Web scraping → Mock data

**Architecture**:
- **Unified Components**: 75% file reduction through consolidation
- **Thread-safe Operations**: Background processing with QThread
- **Progressive Loading**: Three-stage data enhancement
- **Configuration Management**: Centralized EnhancedConfigManager

## License

This project is proprietary software developed for internal use. All rights reserved.

## Support

For technical support or questions:

1. **Migration Guide**: Check `MIGRATION_GUIDE.md` for comprehensive Phase 2 & 3 documentation
2. **Development Guide**: Review `CLAUDE.md` for updated architecture details
3. **Troubleshooting**: WSL GUI setup and common issues covered above
4. **Testing**: Missouri Avenue workflow validation with `claudedocs/missouri_ave_test.py`
5. **Checkpoints**: Phase completion records in `checkpoints/` directory

## Migration Status

- ✅ **Phase 1 Complete**: Windows → Linux path migration
- ✅ **Phase 2 Complete**: Component consolidation (75% file reduction)
- ✅ **Phase 3 Complete**: WSL GUI configuration with native Wayland support
- 🔄 **Phase 4 In Progress**: Documentation updates and unified interface documentation

---

**Last Updated**: September 2025
**Version**: 3.0 (Unified Architecture with WSL GUI Support)
**Status**: Production Ready
**Platform Support**: WSL (Wayland), Linux (X11/Wayland), Windows (Native)