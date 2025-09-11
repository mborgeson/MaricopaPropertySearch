# Maricopa Property Search - Environment Setup Guide

## Quick Fix for "ModuleNotFoundError: No module named 'psycopg2'"

### Problem
The error occurs when you're not in the correct conda environment or dependencies are missing.

### Solution

#### Option 1: Quick Fix (Recommended)
1. **Open Command Prompt as Administrator**
2. **Navigate to project directory:**
   ```cmd
   cd C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch
   ```
3. **Activate the environment:**
   ```cmd
   conda activate maricopa_property
   ```
4. **Verify dependencies (optional):**
   ```cmd
   python scripts\verify_dependencies.py
   ```
5. **Launch the application:**
   ```cmd
   launch_app.bat
   ```

#### Option 2: Complete Environment Reset
If you continue to have issues:

1. **Remove existing environment:**
   ```cmd
   conda deactivate
   conda env remove -n maricopa_property -y
   ```

2. **Recreate environment:**
   ```cmd
   conda env create -f environment.yml
   ```

3. **Activate and verify:**
   ```cmd
   conda activate maricopa_property
   python scripts\verify_dependencies.py
   ```

## Environment Status

### ✅ Current Status (All Working)
Based on our verification, your environment is properly configured with:

- **Conda Environment**: `maricopa_property` ✅
- **Python**: 3.10.18 ✅
- **PostgreSQL Driver**: psycopg2 v2.9.10 ✅
- **GUI Framework**: PyQt5 v5.15.9 ✅
- **Database**: PostgreSQL 14.19 connected ✅
- **All Dependencies**: Installed and working ✅

## Troubleshooting Scripts

### 1. Environment Activation Script
```cmd
scripts\activate_environment.bat
```
- Interactive environment activation
- Creates environment if missing
- Keeps window open for development

### 2. Dependency Verification Script
```cmd
python scripts\verify_dependencies.py
```
- Comprehensive dependency testing
- Detailed diagnostics
- Solution recommendations

### 3. Dependency Fix Script
```cmd
scripts\fix_dependencies.bat
```
- Automatically installs missing dependencies
- Handles both conda and pip packages
- Includes verification at the end

### 4. Enhanced Launch Script
```cmd
launch_app.bat
```
- Improved environment activation
- Quick dependency check
- Automatic environment creation if missing
- Better error handling

## Common Issues and Solutions

### Issue: "Conda not found"
**Solution:**
```cmd
conda init cmd.exe
# Restart command prompt, then try again
```

### Issue: "Environment activation failed"
**Solutions:**
1. Use the activation script: `scripts\activate_environment.bat`
2. Try alternative activation: `activate maricopa_property`
3. Restart command prompt and try again

### Issue: "PostgreSQL connection failed"
**Solutions:**
1. Start PostgreSQL service: `net start postgresql-x64-14`
2. Check connection parameters in `.env` file
3. Run database setup: `scripts\setup_database.bat`

### Issue: "PyQt5 display errors"
**Solutions:**
1. Install PyQt5: `pip install PyQt5`
2. Set display environment: `set QT_QPA_PLATFORM=windows`
3. Check for high DPI issues in Windows display settings

## Environment Files

### Core Configuration Files
- **environment.yml**: Conda environment specification
- **requirements.txt**: Alternative pip requirements
- **.env**: Database and API configuration
- **launch_app.bat**: Main application launcher

### Verification Files
- **scripts\verify_dependencies.py**: Comprehensive testing
- **scripts\activate_environment.bat**: Interactive activation
- **scripts\fix_dependencies.bat**: Automatic dependency installation

## Next Steps

1. **Test the fix:**
   ```cmd
   launch_app.bat
   ```

2. **If issues persist:**
   ```cmd
   python scripts\verify_dependencies.py
   ```

3. **For development:**
   ```cmd
   scripts\activate_environment.bat
   ```

## Manual Dependency Installation

If automated scripts fail, install dependencies manually:

```cmd
conda activate maricopa_property

# Core packages
conda install -c conda-forge psycopg2 pyqt pandas numpy matplotlib requests selenium beautifulsoup4 lxml openpyxl python-dotenv sqlalchemy -y

# Pip-only packages
pip install psycopg2-binary webdriver-manager pytest-qt pyqtgraph --upgrade
```

## Success Indicators

When everything is working correctly, you should see:
- ✅ All dependency tests pass
- ✅ Database connection successful
- ✅ Application launches without errors
- ✅ GUI interface displays properly

## Support

If you continue to experience issues:
1. Run the comprehensive diagnostic: `python scripts\verify_dependencies.py`
2. Check the application logs in `logs\maricopa_property.log`
3. Verify PostgreSQL service is running
4. Ensure you're in the correct conda environment

The environment is currently working correctly with all dependencies installed and verified.