# Quick Start Guide - Consolidated
**Maricopa Property Search Application**  
**Updated:** September 2025 (Post-Consolidation)

Get the Maricopa Property Search application running in 3 simple steps. This guide reflects the new consolidated structure with streamlined processes.

---

## 🚀 3-Step Quick Start

### Step 1: Environment Setup
```bash
# Clone the repository
git clone <repository-url>
cd MaricopaPropertySearch

# Install Python dependencies
pip install -r requirements.txt

# Install browser for web scraping
playwright install chromium
```

### Step 2: Database Configuration
```bash
# Create PostgreSQL database
createdb maricopa_property_search

# Copy environment template and configure
cp .env.example .env

# Edit .env with your database credentials:
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=maricopa_property_search
# DB_USER=your_username
# DB_PASSWORD=your_password

# Initialize database tables
python scripts/setup/setup_database_tables.py
```

### Step 3: Run the Application
```bash
# Launch the application
python RUN_APPLICATION.py
```

**Windows Users**: Simply double-click `RUN_APPLICATION.bat`

---

## 🎯 What You Get

After following these 3 steps, you'll have:
- ✅ Full property search capabilities (Address, Owner, APN)
- ✅ Automated background data collection
- ✅ Export functionality (CSV, Excel, JSON)
- ✅ Professional GUI interface
- ✅ Comprehensive logging and error handling

---

## 🔧 Detailed Setup (If Needed)

### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: 3.7 or higher
- **Database**: PostgreSQL 12+ (recommended) or PostgreSQL 10+
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 1GB free space for application and data

### Environment Variables (.env file)
```bash
# Database Configuration (Required)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=maricopa_property_search
DB_USER=your_username
DB_PASSWORD=your_password

# Application Settings (Optional)
PROJECT_ROOT=C:\Users\YourName\Development\MaricopaPropertySearch
PYTHONPATH=C:\Users\YourName\Development\MaricopaPropertySearch\src
LOG_LEVEL=INFO
MAX_CONCURRENT_JOBS=3
CACHE_EXPIRY_HOURS=24

# API Configuration (Optional - for enhanced features)
API_TOKEN=your_api_token_here
```

### Dependency Installation Options

#### Standard Installation
```bash
pip install -r requirements.txt
playwright install chromium
```

#### Conda Environment (Recommended for Development)
```bash
# Create and activate conda environment
conda env create -f environment.yml
conda activate maricopa_property

# Or manually create environment
conda create -n maricopa_property python=3.9
conda activate maricopa_property
pip install -r requirements.txt
playwright install chromium
```

### Database Setup Details

#### Using PostgreSQL (Recommended)
```bash
# Install PostgreSQL (if not already installed)
# Windows: Download from postgresql.org
# macOS: brew install postgresql
# Ubuntu: sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE maricopa_property_search;
CREATE USER your_username WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE maricopa_property_search TO your_username;
\q

# Initialize tables
python scripts/setup/setup_database_tables.py
```

#### Alternative: SQLite (Basic Setup)
```bash
# For testing or development without PostgreSQL
# The application will automatically create SQLite database
# No additional setup required
```

---

## ✅ Validation and Testing

### Verify Installation
```bash
# Check all dependencies and environment
python scripts/setup/verify_dependencies.py

# Test database connection
python scripts/development/test_db_connection.py

# Check environment configuration
python scripts/development/check_environment.py
```

### Run System Tests
```bash
# Comprehensive system validation
python scripts/testing/COMPLETE_SYSTEM_DEMONSTRATION.py

# Test with real property data
python scripts/testing/run_missouri_tests.py
```

---

## 🛠️ Troubleshooting Quick Fixes

### Common Issues and Solutions

#### "ModuleNotFoundError" when running application
```bash
# Solution: Install missing dependencies
pip install -r requirements.txt
playwright install chromium
```

#### "Database connection failed"
```bash
# Solution 1: Check PostgreSQL is running
# Windows: Check Services
# macOS/Linux: sudo systemctl status postgresql

# Solution 2: Verify credentials in .env file
cat .env  # Check DB_* variables match your PostgreSQL setup

# Solution 3: Test connection manually
python scripts/development/test_db_connection.py
```

#### "Permission denied" or access errors
```bash
# Solution: Check file permissions and paths
ls -la RUN_APPLICATION.py  # Should be executable
python --version           # Should be 3.7+
pwd                       # Should be in MaricopaPropertySearch directory
```

#### Application starts but searches don't work
```bash
# Solution: Check internet connection and browser setup
playwright install chromium  # Reinstall browser
ping google.com              # Test internet connectivity
```

### Quick Diagnostic Commands
```bash
# Check system health
python scripts/maintenance/DIAGNOSE_AND_FIX_ALL_ISSUES.py

# View application logs
tail -f logs/application.log

# Check environment status
python scripts/development/check_environment.py
```

---

## 📱 Using the Application

### Basic Workflow
1. **Launch**: Double-click `RUN_APPLICATION.bat` (Windows) or run `python RUN_APPLICATION.py`
2. **Search**: Select search type (Address/Owner/APN) and enter search terms
3. **Review**: View search results in the main table
4. **Details**: Double-click any property for detailed information
5. **Export**: Use "Export to CSV" to save results

### Search Tips
- **Address Search**: Use partial addresses ("Missouri Ave" finds all Missouri Avenue properties)
- **Owner Search**: Works with partial names ("Smith" finds all Smith properties)
- **APN Search**: Use full APN format (123-45-678) or partial (123-45)
- **Wildcards**: Use asterisk (*) for broader searches

---

## 📋 Next Steps

After successful setup:

1. **Explore Features**: Try different search types and export options
2. **Set Up API Access**: Configure API tokens for enhanced data collection
3. **Review Documentation**: Check README.md for comprehensive feature guide
4. **Join Development**: See CONTRIBUTING section in README.md for development setup

---

## 📞 Getting Help

If you encounter issues:

1. **Check Logs**: Review `logs/application.log` for error details
2. **Run Diagnostics**: Use `python scripts/maintenance/DIAGNOSE_AND_FIX_ALL_ISSUES.py`
3. **Validate Setup**: Run `python scripts/setup/verify_dependencies.py`
4. **Review Configuration**: Check your `.env` file settings

For additional support, provide:
- Operating system and Python version
- Complete error messages from logs
- Output from diagnostic scripts
- Steps to reproduce the issue

---

**Success Indicator**: When you can launch the application and perform a property search, you're ready to go! 🎉

**Last Updated:** September 12, 2025  
**Version**: Post-Consolidation (Streamlined Setup)