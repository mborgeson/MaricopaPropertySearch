# Maricopa Property Search Application

A comprehensive property research application for Maricopa County, Arizona, featuring advanced property search capabilities, automated data collection, and professional user experience.

![Application Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python Version](https://img.shields.io/badge/Python-3.7%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

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

### Recent Enhancements (September 2024)

#### Script Consolidation (September 2024)
- **Consolidated Structure**: Reduced 68+ scripts to 12 authoritative scripts
- **Single Application Launcher**: RUN_APPLICATION.py serves as the primary entry point
- **Organized Script Directory**: Scripts organized by purpose (setup, testing, maintenance, development)
- **Archive System**: Deprecated scripts moved to archive/ directory for reference
- **Clear Workflow**: Simplified development and deployment processes

#### Background Data Collection System
- **Non-Blocking Architecture**: All data collection happens in background threads
- **Intelligent Prioritization**: High priority for user-viewed properties
- **Concurrent Processing**: Configurable concurrent job execution (default: 3 simultaneous)
- **Smart Queue Management**: Priority-based job queue with retry logic

#### User Experience Improvements
- **Professional Messaging**: Replaced all "Not Available" messages with actionable alternatives
- **Contextual Tooltips**: Helpful guidance throughout the interface
- **Status Transparency**: Clear indication of data completeness for each property
- **Enhanced Error Handling**: User-friendly error messages with recovery instructions

#### Missouri Avenue Testing
- **Comprehensive Validation**: Extensive testing with "10000 W Missouri Ave" property
- **Auto-Collection Verification**: Validated background data collection system
- **Progress Indicator Testing**: Confirmed visual feedback accuracy
- **Database Integration**: Verified proper data storage and caching

## Installation

### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: 3.7 or higher
- **Database**: PostgreSQL 12+ (recommended) or PostgreSQL 10+
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 1GB free space for application and data

### Quick Start

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd MaricopaPropertySearch
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Configure Environment**
   ```bash
   # Copy and customize environment file
   cp .env.example .env
   # Edit .env with your database credentials and settings
   ```

4. **Setup Database**
   ```bash
   # Create PostgreSQL database
   createdb maricopa_property_search
   
   # Run initial schema setup
   python scripts/setup_database_tables.py
   ```

5. **Launch Application**
   ```bash
   python RUN_APPLICATION.py
   ```

## How to Run

### Primary Method (Recommended)
```bash
python RUN_APPLICATION.py
```

### Windows Users (Easiest)
Simply double-click:
```
RUN_APPLICATION.bat
```

The application launcher will automatically:
- ✅ Check all dependencies and environment setup
- ✅ Verify database connection
- ✅ Initialize comprehensive logging system
- ✅ Launch the full-featured GUI application

**Note**: Deprecated launch scripts (launch_app_fixed.py, launch_enhanced_app.py, etc.) have been consolidated into the single RUN_APPLICATION.py launcher as part of the September 2025 consolidation.

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

## API Configuration

### Maricopa County API
The application integrates with official Maricopa County APIs:

```bash
# Required API configuration in .env file
API_TOKEN=your_api_token_here
```

To obtain an API token:
1. Visit the Maricopa County Assessor's Office website
2. Request developer access to property data APIs
3. Follow their documentation for authentication setup

### Database Configuration

PostgreSQL connection settings in `.env`:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=maricopa_property_search
DB_USER=your_username
DB_PASSWORD=your_password
```

### Application Settings

Customize application behavior:

```bash
# Project paths
PROJECT_ROOT=C:\Users\YourName\Development\MaricopaPropertySearch
PYTHONPATH=C:\Users\YourName\Development\MaricopaPropertySearch\src

# Logging
LOG_LEVEL=INFO

# Performance tuning
MAX_CONCURRENT_JOBS=3
CACHE_EXPIRY_HOURS=24
```

## Troubleshooting

### Common Issues

#### Database Connection Problems
```bash
# Test database connectivity
python src/database_manager.py

# Common solutions:
# 1. Verify PostgreSQL is running
# 2. Check credentials in .env file
# 3. Ensure database exists
# 4. Verify network connectivity
```

#### Search Not Returning Results
- **Check Search Terms**: Ensure correct spelling and format
- **Try Partial Matches**: Use wildcards (*) for broader searches
- **Verify Data Sources**: Confirm Maricopa County websites are accessible
- **Check API Token**: Ensure valid API token in configuration

#### Background Collection Not Working
- **Check Browser Drivers**: Ensure Playwright browsers are installed
- **Verify Internet Connection**: Background collection requires internet access
- **Review Logs**: Check `logs/` directory for error details
- **Monitor Resources**: Ensure sufficient system memory

#### Performance Issues
- **Reduce Concurrent Jobs**: Lower `MAX_CONCURRENT_JOBS` in configuration
- **Check Database Performance**: Monitor PostgreSQL resource usage
- **Clear Cache**: Delete cached data if experiencing memory issues
- **Update Dependencies**: Ensure all packages are up to date

### Error Messages

#### "Connection timeout while searching"
- Check internet connectivity
- Verify Maricopa County websites are accessible
- Consider increasing timeout values in configuration

#### "Database connection failed"
- Verify PostgreSQL service is running
- Check database credentials in `.env` file
- Ensure database exists and user has proper permissions

#### "Collection failed - click to retry"
- Network connectivity issue during data collection
- Target website may be temporarily unavailable
- Try manual collection or retry later

### Getting Help

1. **Check Logs**: Review `logs/application.log` for detailed error information
2. **Test Components**: Use built-in diagnostic tools in the Help menu
3. **Configuration Review**: Verify all settings in `.env` and configuration files
4. **Database Status**: Check database connectivity and performance
5. **System Resources**: Monitor CPU and memory usage during operation

## Contributing

### Development Setup

1. **Fork the Repository**
   ```bash
   git fork <repository-url>
   cd MaricopaPropertySearch
   ```

2. **Create Development Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate environment
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   
   # Install development dependencies
   pip install -r requirements.txt
   pip install pytest pytest-qt mypy black
   ```

3. **Run Tests**
   ```bash
   # Run all tests
   pytest
   
   # Run specific test suites
   pytest tests/test_missouri_avenue_address.py
   
   # Run with coverage
   pytest --cov=src
   ```

### Code Standards

- **Python Style**: Follow PEP 8 guidelines
- **Type Hints**: Use type hints for all functions and methods
- **Documentation**: Document all public APIs with docstrings
- **Testing**: Write tests for new functionality
- **Logging**: Use the centralized logging system for all output

### Submitting Changes

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow existing code patterns
   - Add comprehensive tests
   - Update documentation as needed

3. **Test Thoroughly**
   ```bash
   # Run test suite
   pytest
   
   # Run type checking
   mypy src/
   
   # Format code
   black src/
   ```

4. **Submit Pull Request**
   - Provide clear description of changes
   - Include test results and screenshots if applicable
   - Reference any related issues

## Architecture

### Project Structure

```
MaricopaPropertySearch/
├── src/                    # Core application modules
│   ├── api_client.py       # API integration layer
│   ├── database_manager.py # Database operations
│   ├── property_gui.py     # Main GUI interface
│   └── web_scraper.py      # Web automation
├── scripts/                # Authoritative utility scripts
│   ├── setup/              # Installation and setup scripts
│   ├── testing/            # Integration and system tests
│   ├── maintenance/        # Database and system maintenance
│   └── development/        # Development utilities
├── archive/                # Consolidated deprecated scripts
├── config/                 # Configuration files
├── logs/                   # Application logs
└── RUN_APPLICATION.py      # Primary application launcher
```

### High-Level Components

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

### Key Technologies

- **Frontend**: PyQt5 for cross-platform GUI
- **Database**: PostgreSQL with connection pooling
- **Web Scraping**: Playwright for modern web automation
- **Background Processing**: QThread for non-blocking operations
- **Configuration**: JSON configuration with environment variable support
- **Logging**: Centralized logging system with performance monitoring

## License

This project is proprietary software developed for internal use. All rights reserved.

## Support

For technical support or questions:

1. **Documentation**: Check INSTALLATION.md for detailed setup instructions
2. **Troubleshooting**: Review the troubleshooting section above
3. **Logs**: Examine application logs in the `logs/` directory
4. **Testing**: Use the built-in diagnostic tools and test suites

---

**Last Updated**: December 2024  
**Version**: 2.0 (Enhanced with Background Collection)  
**Status**: Production Ready