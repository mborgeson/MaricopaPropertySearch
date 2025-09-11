# Troubleshooting Guide

## Common Issues and **Solution**s

### 1. Conda Environment Issues

**Problem**: "conda not recognized as command"
**Solution**:

- Install Anaconda/Miniconda
- Add to PATH: C:\Users\MattBorgeson\Anaconda3\Scripts

**Problem**: Package conflicts during environment creation
**Solution**:

```batch
conda clean --all
conda update conda
conda env create -f environment.yml --force


### 2. PostgreSQL Issues
**Problem**: "psql not recognized"
**Solution**: Add to PATH: C:\Program Files\PostgreSQL\14\bin

**Problem**: "Connection refused"
**Solution**:
# Start PostgreSQL service
net start postgresql-x64-14
# Check if running
sc query postgresql-x64-14

**Problem**: "Authentication failed"
**Solution**: Reset password in pgAdmin or:
ALTER USER property_user WITH PASSWORD 'new_password';


### 3. ChromeDriver Issues
**Problem**: "ChromeDriver version mismatch"
**Solution**: Run scripts\install_chromedriver.bat again

**Problem**: "Chrome not found"
**Solution**: Install Chrome from https://www.google.com/chrome/


### 4. Application Won't Start
**Problem**: ImportError
**Solution**:
conda activate maricopa_property
pip install [missing_package]

**Problem**: Database connection error
**Solution**: Check config\config.ini has correct password


### 5. Performance Issues
**Problem**: Slow searches
**Solution**:
Increase workers in config.ini
Check PostgreSQL indexes:
SELECT * FROM pg_indexes WHERE tablename = 'properties';


### 6. Web Scraping Issues
**Problem**: Timeout errors
**Solution**: Increase timeout in config.ini

**Problem**: "Element not found"
**Solution**: Websites may have changed - check src\web_scraper.py

### Log Files
Check these logs for detailed error messages:
Application: logs\maricopa_property.log
PostgreSQL: C:\Program Files\PostgreSQL\14\data\log\
ChromeDriver: Check console output

### Getting Help
Run test_installation.bat to diagnose issues
Check logs\maricopa_property.log
Verify all paths in config\config.ini
Ensure all services are running


## Master Installation Checklist

### Script 9.1: `INSTALLATION_CHECKLIST.md`
**Save Location**: `C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch\`

```markdown
# Installation Checklist

Follow these steps in order:

## Prerequisites
- [ ] Windows 10/11
- [ ] Anaconda/Miniconda installed
- [ ] Chrome browser installed
- [ ] Administrator access

## Installation Steps

### 1. Create Project Structure
- [ ] Run: create_project_structure.bat
- [ ] Verify all directories created

### 2. Setup Conda Environment  
- [ ] Copy environment.yml to project root
- [ ] Run: scripts\setup_conda_env.bat
- [ ] Verify: conda env list shows maricopa_property

### 3. Install PostgreSQL
- [ ] Download and install PostgreSQL 14
- [ ] Remember postgres password
- [ ] Add to PATH: C:\Program Files\PostgreSQL\14\bin
- [ ] Copy database scripts to database\
- [ ] Run: scripts\setup_database.bat
- [ ] Verify: Database created

### 4. Configure Application
- [ ] Copy config.ini to config\
- [ ] Copy .env to project root
- [ ] Update passwords if needed

### 5. Install ChromeDriver
- [ ] Run: scripts\install_chromedriver.bat
- [ ] Verify: ChromeDriver in drivers\

### 6. Copy Application Files
- [ ] Copy all .py files to src\
- [ ] Create subdirectories in src\ as needed

### 7. Test Installation
- [ ] Run: scripts\test_installation.bat
- [ ] All tests should pass

### 8. Launch Application
- [ ] Run: launch_app.bat
- [ ] Application should open

## Verification Commands

Open Anaconda Prompt and run:
```batch
# Check conda environment
conda env list

# Check PostgreSQL
psql -U property_user -d maricopa_properties -c "SELECT version();"

# Check Python packages
conda activate maricopa_property
python -c "import pandas, PyQt5, selenium; print('All packages OK')"


## Support Files Location
All scripts are in: C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch\scripts
All configs are in: C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch\config
All logs are in: C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch\logs\


## Quick Start Summary

1. **First Time Setup** (Run once in order):create_project_structure.bat
scripts\setup_conda_env.bat
Install PostgreSQL manually
scripts\setup_database.bat
scripts\install_chromedriver.bat
scripts\test_installation.bat

2. **Daily Use**:
Double-click: launch_app.bat

3. **If Something Goes Wrong**:
Check: scripts\test_installation.bat
Read: docs\troubleshooting.md
Check logs: logs\maricopa_property.log

This comprehensive setup ensures everything is properly configured for your Windows environment with full troubleshooting capabilities!
```
