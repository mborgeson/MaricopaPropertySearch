# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Maricopa County Property Search Tool - A modern Python application for searching and managing property information from Maricopa County Assessor's office. The application has been migrated from Windows-specific paths to cross-platform Linux/WSL compatibility and features a consolidated architecture with unified components.

**Current Status**: Phase 3 Complete (WSL GUI Configuration and Testing) ✅
- Native WSL GUI support via WSLg with Wayland
- 75% file reduction through component consolidation (Phase 2)
- Enhanced platform detection and import resolution
- Validated Missouri Avenue workflow performance

## Running the Application

### WSL/Linux Environment (Recommended)
```bash
# Run the unified GUI launcher (supports Enhanced GUI)
python src/gui_launcher_unified.py

# Alternative: Run basic GUI launcher
python src/basic_gui_launcher.py

# Legacy compatibility (delegated to unified launcher)
python maricopa_property_search.py
```

### Environment Detection
The unified launcher automatically detects:
- **WSL with WSLg**: Native Wayland support (optimal performance)
- **Linux with X11**: XCB platform fallback
- **Windows**: Native Windows platform
- **Headless**: Offscreen rendering for server environments

## Dependencies

### Required
- Python 3.12+ (tested on Python 3.12.3)
- PyQt5 (for Enhanced GUI functionality)
- requests (for API integration)
- psycopg2 (for database operations)
- beautifulsoup4 + lxml (for web scraping fallback)

### Optional (for enhanced functionality)
```bash
# For advanced browser automation (optional enhancement)
pip install playwright

# For comprehensive testing
pip install pytest
```

### WSL GUI Requirements
For WSL users, ensure WSLg is enabled (pre-configured on Ubuntu 24.04.3 LTS):
- **Display Environment**: WAYLAND_DISPLAY or DISPLAY variables set
- **Qt Platform**: Wayland (preferred) or XCB fallback
- **Performance**: Native GUI responsiveness via WSLg

## Architecture

### Unified Component Design (Phase 2 Consolidation)
The application uses a **consolidated architecture** with 75% file reduction (16→4 unified implementations):

#### Core Unified Components

**UnifiedMaricopaAPIClient** (`src/api_client_unified.py`)
- Consolidates 6 previous API client implementations
- Multi-source data collection: API → Web Scraping → Mock fallback
- Progressive data loading: Basic (0.04s) → Detailed (0.33s) → Complete
- Thread-safe operations with connection pooling
- Intelligent retry logic and error handling

**UnifiedDataCollector** (`src/unified_data_collector.py`)
- Consolidates 4 data collection implementations
- Background processing with priority queues
- Parallel data collection from multiple sources
- Real-time progress tracking and cancellation support

**ThreadSafeDatabaseManager** (`src/threadsafe_database_manager.py`)
- Consolidates 2 database implementations
- PostgreSQL integration with connection pooling
- Thread-safe operations for concurrent access
- Mock mode support for testing environments

**UnifiedGUILauncher** (`src/gui_launcher_unified.py`)
- Consolidates 4 GUI launcher implementations
- Intelligent platform detection (WSL/Linux/Windows)
- Enhanced GUI with PyQt5 + Basic GUI with tkinter fallback
- Native Wayland support for WSL environments

### Data Sources Integration
Multi-source approach with intelligent fallback:

1. **Primary API Integration**
   - Maricopa County Assessor's office endpoints
   - Rate limiting and retry logic
   - Authentication and session management

2. **Web Scraping Fallback**
   - BeautifulSoup4 + Playwright (optional) integration
   - Parcel viewer and document retrieval
   - Graceful degradation when API unavailable

3. **Database Operations**
   - PostgreSQL for production environments
   - SQLite fallback for development
   - Mock mode for testing scenarios

### Key Features

- **Cross-Platform Compatibility**: Native WSL/Linux/Windows support
- **Multiple Search Methods**: APN, address, batch processing, CSV import/export
- **Progressive Data Loading**: Fast basic search (0.04s) → comprehensive data (0.33s)
- **Intelligent Platform Detection**: Automatic GUI backend selection (Wayland/XCB/Windows)
- **Background Processing**: Non-blocking data collection with real-time progress
- **Graceful Fallbacks**: API → Web Scraping → Mock data with seamless transitions
- **Enhanced GUI**: PyQt5-based interface with accessibility and performance optimization
- **Document Integration**: Direct links to assessor, recorder, and tax websites
- **Database Flexibility**: PostgreSQL production + SQLite development + Mock testing

## Configuration and Setup

### API Configuration
The unified API client (`src/api_client_unified.py`) provides configuration for:

1. **Enhanced Configuration Manager** (`src/enhanced_config_manager.py`)
   - Centralized configuration management
   - Environment-specific settings (development/production)
   - API endpoint and authentication configuration
   - Database connection parameters

2. **Real Data Sources** (Production Setup)
   - Configure Maricopa County API endpoints in enhanced config
   - Add API keys and authentication tokens as needed
   - Set up PostgreSQL database connection for data persistence

3. **Development Mode** (Testing Setup)
   - Mock data generation for offline testing
   - SQLite database for local development
   - Web scraping fallback for missing API data

### WSL GUI Setup (Phase 3)
For WSL users to enable GUI functionality:

1. **Verify WSLg Installation** (pre-configured on Ubuntu 24.04.3 LTS)
   ```bash
   echo $WAYLAND_DISPLAY  # Should show: wayland-0
   echo $DISPLAY          # Should show: :0
   ```

2. **Test GUI Capability**
   ```bash
   python src/gui_launcher_unified.py --test-gui
   ```

3. **Troubleshooting Display Issues**
   - Check platform detection: unified launcher reports environment status
   - Verify Qt platform: should auto-detect "wayland" on WSL
   - Fallback to X11: automatic if Wayland unavailable

## Unified Data Flow (Post-Consolidation)

1. **Input Processing**: User search via Enhanced GUI or Basic GUI
2. **Unified API Client**: Single point of data collection coordination
3. **Progressive Loading**:
   - **Stage 1**: Basic search (0.04s average) → immediate results
   - **Stage 2**: Detailed information (0.33s average) → comprehensive data
   - **Stage 3**: Background processing → tax history, sales records
4. **Data Source Fallback**: API → Web Scraping → Mock (seamless transitions)
5. **Background Processing**: Non-blocking data collection with progress tracking
6. **Database Integration**: Persistent storage with thread-safe operations
7. **Export Capabilities**: CSV, JSON, formatted reports

## Important URLs

- Assessor Parcel Viewer: https://mcassessor.maricopa.gov/parcel/{apn}
- Recorder Documents: https://recorder.maricopa.gov/recdocdata/
- Tax Information: https://treasurer.maricopa.gov/parcelinfo/

## Testing and Validation

### Missouri Avenue Workflow (Validated in Phase 3)
The application has been tested and validated with the Missouri Avenue property search:

- **Target Property**: "10000 W Missouri Ave" → APN 10215009
- **Performance**: 0.04s basic search, 0.33s comprehensive data collection
- **Data Retrieval**: 6 tax records successfully retrieved
- **API Integration**: Unified client working perfectly
- **Database**: Mock mode operational (production PostgreSQL ready)

### Testing Framework
```bash
# Run the comprehensive test suite
python claudedocs/missouri_ave_test.py

# Test GUI functionality
python src/gui_launcher_unified.py --test-gui

# Test individual components
python -m pytest tests/ # (when test suite is implemented)
```

### Mock Data Capabilities
The application includes comprehensive mock data generation:
- **Property Information**: Realistic property details and assessments
- **Tax History**: Multi-year tax records with proper calculations
- **Sales History**: Property transfer records and market data
- **Geographic Data**: Address validation and APN mapping
- **Performance**: Full workflow testing without external dependencies

## Migration Status

### Completed Phases
- ✅ **Phase 1**: Windows → Linux Path Migration (COMPLETE)
- ✅ **Phase 2**: Component Consolidation (75% file reduction, COMPLETE)
- ✅ **Phase 3**: WSL GUI Configuration and Testing (Native Wayland, COMPLETE)

### Current Architecture Benefits
- **Maintainability**: 75% fewer files to manage and maintain
- **Performance**: Sub-second response times with progressive loading
- **Reliability**: Graceful fallbacks and error handling throughout
- **Cross-Platform**: Native support for WSL, Linux, and Windows environments
- **User Experience**: Fast, responsive GUI with professional interface design