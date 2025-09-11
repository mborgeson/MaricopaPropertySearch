# Maricopa Property Search - Installation Guide

This comprehensive guide will walk you through setting up the Maricopa Property Search application on your system.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Pre-Installation Checklist](#pre-installation-checklist)
3. [Database Setup](#database-setup)
4. [Python Environment Setup](#python-environment-setup)
5. [Application Installation](#application-installation)
6. [Configuration](#configuration)
7. [Browser Driver Setup](#browser-driver-setup)
8. [Initial Testing](#initial-testing)
9. [Troubleshooting](#troubleshooting)
10. [Performance Optimization](#performance-optimization)

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10, macOS 10.14, or Linux (Ubuntu 18.04+)
- **Python**: 3.7 or higher
- **Memory**: 4GB RAM
- **Storage**: 2GB free disk space
- **Network**: Broadband internet connection
- **Database**: PostgreSQL 10+

### Recommended Requirements
- **Operating System**: Windows 11, macOS 12+, or Linux (Ubuntu 20.04+)
- **Python**: 3.9 or higher
- **Memory**: 8GB RAM or more
- **Storage**: 5GB free disk space (for data caching)
- **Network**: High-speed internet connection
- **Database**: PostgreSQL 14+
- **CPU**: 4+ cores for optimal background processing

### Hardware Considerations
- **SSD Storage**: Recommended for better database performance
- **Multiple CPU Cores**: Background data collection benefits from multiple cores
- **Stable Internet**: Required for real-time property data collection

## Pre-Installation Checklist

Before beginning installation, ensure you have:

- [ ] Administrator/sudo access on your system
- [ ] Python 3.7+ installed and accessible from command line
- [ ] PostgreSQL 10+ installed and running
- [ ] Git installed (if cloning from repository)
- [ ] Reliable internet connection
- [ ] Basic familiarity with command line operations

### Verify Python Installation
```bash
# Check Python version
python --version
# or
python3 --version

# Should show Python 3.7 or higher
```

### Verify PostgreSQL Installation
```bash
# Check PostgreSQL version
psql --version

# Should show PostgreSQL 10 or higher
```

## Database Setup

### 1. PostgreSQL Installation

#### Windows
1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Run the installer as Administrator
3. Choose installation directory (default: `C:\Program Files\PostgreSQL\15`)
4. Set password for postgres user (remember this password!)
5. Set port (default: 5432)
6. Select locale (default: English, United States)
7. Complete installation

#### macOS
```bash
# Using Homebrew (recommended)
brew install postgresql
brew services start postgresql

# Or download from https://www.postgresql.org/download/macosx/
```

#### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Database Creation

#### Create Database User
```bash
# Connect to PostgreSQL as postgres user
sudo -u postgres psql

# Create application user
CREATE USER maricopa_user WITH PASSWORD 'your_secure_password';

# Grant privileges
ALTER USER maricopa_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE postgres TO maricopa_user;

# Exit PostgreSQL
\q
```

#### Create Application Database
```bash
# Connect as the new user
psql -U maricopa_user -h localhost

# Create database
CREATE DATABASE maricopa_property_search;

# Connect to the new database
\c maricopa_property_search

# Verify connection
SELECT current_database();

# Exit
\q
```

### 3. Database Schema Setup

The application will automatically create required tables on first run, but you can verify the setup:

```sql
-- Core tables that will be created:
-- properties: Main property information
-- tax_records: Tax assessment and payment data
-- sales_records: Property transaction history
-- search_cache: Cached search results
-- data_collection_status: Background collection tracking
```

## Python Environment Setup

### 1. Create Virtual Environment (Recommended)

#### Windows
```cmd
# Navigate to your desired installation directory
cd C:\Development

# Clone or download the application
git clone <repository-url> MaricopaPropertySearch
cd MaricopaPropertySearch

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Verify activation (should show venv in prompt)
where python
```

#### macOS/Linux
```bash
# Navigate to your desired installation directory
cd ~/Development

# Clone or download the application
git clone <repository-url> MaricopaPropertySearch
cd MaricopaPropertySearch

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation (should show venv in prompt)
which python
```

### 2. Upgrade pip and Install Dependencies

```bash
# Upgrade pip to latest version
python -m pip install --upgrade pip

# Install application dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

## Application Installation

### 1. Download Application Files

#### From Git Repository
```bash
git clone <repository-url> MaricopaPropertySearch
cd MaricopaPropertySearch
```

#### From Archive
1. Extract the application archive to your desired location
2. Navigate to the extracted directory

### 2. Install Python Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Dependencies include:
# - PyQt5: GUI framework
# - psycopg2-binary: PostgreSQL adapter
# - selenium: Web automation
# - requests: HTTP library
# - python-dotenv: Environment configuration
# - pathlib2: Path utilities
# - pytest: Testing framework (development)
```

### 3. Install Browser Dependencies

```bash
# Install Playwright browsers
playwright install chromium

# Verify browser installation
playwright --version
```

## Configuration

### 1. Environment File Setup

```bash
# Copy example environment file
cp .env.example .env

# Edit the environment file with your settings
# Windows: notepad .env
# macOS: open .env
# Linux: nano .env
```

### 2. Database Configuration

Edit the `.env` file with your database settings:

```bash
# Database settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=maricopa_property_search
DB_USER=maricopa_user
DB_PASSWORD=your_secure_password
```

### 3. Application Paths

Update paths in `.env` to match your installation:

```bash
# Windows example
PROJECT_ROOT=C:\Development\MaricopaPropertySearch
PYTHONPATH=C:\Development\MaricopaPropertySearch\src

# macOS/Linux example
PROJECT_ROOT=/home/username/Development/MaricopaPropertySearch
PYTHONPATH=/home/username/Development/MaricopaPropertySearch/src
```

### 4. API Configuration (Optional)

If you have a Maricopa County API token:

```bash
API_TOKEN=your_api_token_here
```

To obtain an API token:
1. Contact Maricopa County Assessor's Office
2. Request developer access to property data APIs
3. Follow their documentation for authentication

### 5. Performance Settings

Adjust based on your system resources:

```bash
# Conservative settings (4GB RAM systems)
MAX_CONCURRENT_JOBS=1
LOG_LEVEL=WARNING

# Standard settings (8GB RAM systems)
MAX_CONCURRENT_JOBS=3
LOG_LEVEL=INFO

# High performance settings (16GB+ RAM systems)
MAX_CONCURRENT_JOBS=5
LOG_LEVEL=INFO
```

## Browser Driver Setup

### 1. Playwright Installation

```bash
# Install Playwright browsers
playwright install

# Install specific browser (if needed)
playwright install chromium

# Verify installation
playwright --help
```

### 2. Browser Configuration

The application uses Playwright for web automation. Configuration options:

```bash
# In .env file
BROWSER_TYPE=chromium  # or firefox, webkit
BROWSER_HEADLESS=true  # false for visible browser (debugging)
PAGE_TIMEOUT=30000     # Page load timeout in milliseconds
```

### 3. Troubleshooting Browser Issues

If browser installation fails:

```bash
# Clear Playwright cache
playwright uninstall

# Reinstall browsers
playwright install

# On Linux, install system dependencies
sudo apt install libnss3 libatk-bridge2.0-0 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libgtk-3-0
```

## Initial Testing

### 1. Database Connection Test

```bash
# Test database connectivity
python src/database_manager.py

# Should output: "Database connection successful"
```

### 2. Configuration Validation

```bash
# Validate configuration
python src/config_manager.py

# Should output configuration summary without errors
```

### 3. Browser Automation Test

```bash
# Test browser automation
python src/web_scraper.py

# Should open browser and perform basic navigation test
```

### 4. Application Launch Test

```bash
# Launch application in test mode
python launch_enhanced_app.py

# Application should start without errors
# Check background status panel shows "Collection Available"
```

### 5. Basic Search Test

1. Launch the application
2. Select "Property Address" search type
3. Enter "10000 W Missouri Ave" (test property)
4. Click "Find Properties"
5. Verify search results appear
6. Double-click a result to view property details

## Troubleshooting

### Common Installation Issues

#### Python Import Errors
```bash
# Error: ModuleNotFoundError
# Solution: Verify virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

#### Database Connection Failed
```bash
# Error: psycopg2.OperationalError
# Solutions:
1. Verify PostgreSQL is running:
   sudo systemctl status postgresql  # Linux
   brew services list postgresql     # macOS
   
2. Check database exists:
   psql -U maricopa_user -l
   
3. Verify credentials in .env file
4. Test connection manually:
   psql -U maricopa_user -h localhost -d maricopa_property_search
```

#### PyQt5 Installation Issues
```bash
# Error: Failed building wheel for PyQt5
# Windows solution:
pip install --only-binary=PyQt5 PyQt5

# macOS solution:
brew install pyqt5
pip install PyQt5

# Linux solution:
sudo apt install python3-pyqt5
pip install PyQt5
```

#### Playwright Browser Download Failed
```bash
# Error: Browser download failed
# Solutions:
1. Check internet connection
2. Clear cache and retry:
   playwright uninstall
   playwright install chromium
   
3. Use system browser (if available):
   pip install selenium
   # Update configuration to use selenium
```

### Performance Issues

#### High Memory Usage
```bash
# Reduce concurrent jobs
MAX_CONCURRENT_JOBS=1

# Enable conservative mode
LOG_LEVEL=WARNING
CACHE_EXPIRY_HOURS=6
```

#### Slow Database Operations
```bash
# Check PostgreSQL configuration
# Edit postgresql.conf:
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### Browser Timeout Errors
```bash
# Increase timeouts
PAGE_TIMEOUT=60000
JOB_TIMEOUT_SECONDS=600

# Use faster browser
BROWSER_TYPE=chromium
```

## Performance Optimization

### 1. Database Optimization

#### PostgreSQL Configuration
```sql
-- Optimize for property search workload
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;

-- Reload configuration
SELECT pg_reload_conf();
```

#### Index Creation
```sql
-- Create indexes for better search performance
CREATE INDEX idx_properties_address ON properties(address);
CREATE INDEX idx_properties_owner ON properties(owner_name);
CREATE INDEX idx_properties_apn ON properties(apn);
CREATE INDEX idx_tax_records_apn ON tax_records(apn);
CREATE INDEX idx_sales_records_apn ON sales_records(apn);
```

### 2. Application Optimization

#### High-Performance Configuration
```bash
# .env settings for high-performance systems
MAX_CONCURRENT_JOBS=5
DB_POOL_MAX_CONNECTIONS=20
CACHE_EXPIRY_HOURS=24
PERFORMANCE_MONITORING=true
```

#### Memory Optimization
```bash
# .env settings for memory-constrained systems
MAX_CONCURRENT_JOBS=1
DB_POOL_MAX_CONNECTIONS=5
CACHE_EXPIRY_HOURS=6
PERFORMANCE_MONITORING=false
```

### 3. System-Level Optimization

#### Windows
```cmd
# Increase virtual memory
# Control Panel → System → Advanced → Performance Settings → Advanced → Virtual Memory
```

#### Linux
```bash
# Increase swap if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### macOS
```bash
# Monitor memory usage
top -o MEM

# Consider increasing PostgreSQL shared_buffers
```

## Post-Installation Verification

### 1. Functionality Checklist

- [ ] Application launches without errors
- [ ] Database connection successful
- [ ] Search functionality works (all three types)
- [ ] Property details display correctly
- [ ] Background data collection starts automatically
- [ ] Export functionality works
- [ ] Logging system operational

### 2. Performance Verification

- [ ] Search results appear within 3 seconds
- [ ] Background collection processes without UI freezing
- [ ] Memory usage stable during operation
- [ ] Database queries complete in reasonable time
- [ ] Browser automation works reliably

### 3. Data Validation

- [ ] Test with known property (10000 W Missouri Ave)
- [ ] Verify tax records collection
- [ ] Confirm sales history retrieval
- [ ] Check data persistence across sessions
- [ ] Validate export file formats

## Getting Help

### 1. Log Analysis
```bash
# Check application logs
tail -f logs/application.log

# Check error logs
grep ERROR logs/application.log

# Check performance logs
grep PERFORMANCE logs/application.log
```

### 2. Diagnostic Tools
```bash
# Run built-in diagnostics
python scripts/system_diagnostics.py

# Test individual components
python src/database_manager.py
python src/web_scraper.py
python src/config_manager.py
```

### 3. Support Resources

1. **Documentation**: Check README.md for usage instructions
2. **Troubleshooting**: Review troubleshooting section above
3. **Logs**: Examine logs directory for detailed error information
4. **Configuration**: Verify .env settings match your system
5. **Dependencies**: Ensure all required packages are installed

## Advanced Installation Options

### 1. Docker Installation (Optional)

```dockerfile
# Dockerfile for containerized deployment
FROM python:3.9

RUN apt-get update && apt-get install -y postgresql-client
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium

COPY . /app
WORKDIR /app
CMD ["python", "launch_enhanced_app.py"]
```

### 2. Service Installation (Linux)

```bash
# Create systemd service file
sudo nano /etc/systemd/system/maricopa-search.service

# Service content:
[Unit]
Description=Maricopa Property Search
After=network.target postgresql.service

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/MaricopaPropertySearch
ExecStart=/path/to/venv/bin/python launch_enhanced_app.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl enable maricopa-search
sudo systemctl start maricopa-search
```

### 3. Development Installation

```bash
# Additional development dependencies
pip install pytest pytest-qt mypy black flake8

# Pre-commit hooks
pip install pre-commit
pre-commit install

# Run tests
pytest

# Code formatting
black src/
```

---

## Installation Summary

After completing this installation guide, you should have:

1. ✅ **PostgreSQL database** configured and running
2. ✅ **Python environment** with all dependencies installed
3. ✅ **Application configured** with proper .env settings
4. ✅ **Browser automation** working with Playwright
5. ✅ **Initial testing** completed successfully
6. ✅ **Performance optimization** applied for your system

The application is now ready for production use with comprehensive property search and background data collection capabilities.

**Next Steps:**
1. Launch the application: `python launch_enhanced_app.py`
2. Perform test searches to verify functionality
3. Review the README.md for usage instructions
4. Check logs directory for any startup issues

**Remember:** Keep your .env file secure and never commit it to version control. Regularly update your API tokens and database passwords for security.

---

**Support**: If you encounter issues during installation, check the troubleshooting section above or examine the application logs for detailed error information.