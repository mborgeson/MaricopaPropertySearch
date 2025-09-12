# Migration Guide: Script Consolidation

**Project:** Maricopa Property Search  
**Migration Date:** 2025-09-12  
**Purpose:** Consolidate 68 Python files into 12 authoritative scripts

## Quick Reference: Before → After

### Application Launch
```bash
# OLD (multiple options causing confusion)
python launch_app_fixed.py
python launch_enhanced_app.py
python launch_improved_app.py

# NEW (single authoritative launcher)
python RUN_APPLICATION.py
```

### System Testing
```bash
# OLD (multiple redundant test scripts)
python test_application.py
python test_api_integration.py
python test_final_integration.py
python scripts/test_comprehensive_api.py

# NEW (consolidated testing)
python scripts/testing/COMPLETE_SYSTEM_DEMONSTRATION.py
python scripts/testing/run_missouri_tests.py
```

### System Diagnostics
```bash
# OLD (scattered diagnostic tools)
python scripts/check_enhanced_property_data.py
python scripts/fix_database_user.py
python scripts/verify_and_fix_all_data.py

# NEW (unified diagnostic system)
python scripts/maintenance/DIAGNOSE_AND_FIX_ALL_ISSUES.py
```

### Environment Setup
```bash
# OLD (unclear setup process)
python scripts/test_installation.py
python scripts/verify_dependencies.py

# NEW (clear setup workflow)
python scripts/setup/verify_dependencies.py
python scripts/setup/setup_database_tables.py
python scripts/setup/install_chromedriver.py
```

## New Project Structure

```
MaricopaPropertySearch/
├── RUN_APPLICATION.py              # PRIMARY APPLICATION LAUNCHER
├── scripts/
│   ├── setup/                      # Installation & Setup
│   │   ├── verify_dependencies.py
│   │   ├── setup_database_tables.py
│   │   └── install_chromedriver.py
│   ├── testing/                    # System Testing
│   │   ├── COMPLETE_SYSTEM_DEMONSTRATION.py
│   │   └── run_missouri_tests.py
│   ├── maintenance/                # System Maintenance
│   │   ├── DIAGNOSE_AND_FIX_ALL_ISSUES.py
│   │   ├── fix_data_collection.py
│   │   └── populate_sample_data.py
│   └── development/                # Development Utilities
│       ├── check_environment.py
│       ├── test_db_connection.py
│       └── LAUNCH_GUI_APPLICATION.py
└── archive/                        # Deprecated Scripts
    └── deprecated_scripts/
        ├── launch_variants/
        ├── test_variants/
        ├── utility_variants/
        └── historical/
```

## Developer Workflow Changes

### New Developer Onboarding
```bash
# 1. Verify environment and dependencies
python scripts/setup/verify_dependencies.py

# 2. Setup database
python scripts/setup/setup_database_tables.py

# 3. Install required browser driver
python scripts/setup/install_chromedriver.py

# 4. Launch application
python RUN_APPLICATION.py

# 5. Run system tests
python scripts/testing/COMPLETE_SYSTEM_DEMONSTRATION.py
```

### Daily Development Workflow
```bash
# Check environment
python scripts/development/check_environment.py

# Test database connection
python scripts/development/test_db_connection.py

# Launch application
python RUN_APPLICATION.py

# For GUI development
python scripts/development/LAUNCH_GUI_APPLICATION.py
```

### Maintenance Tasks
```bash
# Comprehensive system diagnosis
python scripts/maintenance/DIAGNOSE_AND_FIX_ALL_ISSUES.py

# Fix data collection issues
python scripts/maintenance/fix_data_collection.py

# Populate test data
python scripts/maintenance/populate_sample_data.py
```

### Testing Workflow
```bash
# Full system integration test
python scripts/testing/COMPLETE_SYSTEM_DEMONSTRATION.py

# Property-specific testing
python scripts/testing/run_missouri_tests.py
```

## Migration Steps (DO NOT EXECUTE - REFERENCE ONLY)

The actual migration should be performed by following the consolidation report. These steps are for reference:

### Step 1: Create Archive Structure
```bash
mkdir -p archive/deprecated_scripts/{launch_variants,test_variants,utility_variants,historical}
```

### Step 2: Archive Deprecated Scripts
```bash
# Archive launch variants
mv launch_app_fixed.py archive/deprecated_scripts/launch_variants/
mv launch_enhanced_app.py archive/deprecated_scripts/launch_variants/
mv launch_improved_app.py archive/deprecated_scripts/launch_variants/

# Archive test variants
mv test_*.py archive/deprecated_scripts/test_variants/
mv scripts/test_*.py archive/deprecated_scripts/test_variants/

# Archive utility variants
mv scripts/check_enhanced_property_data.py archive/deprecated_scripts/utility_variants/
mv scripts/fix_database_user.py archive/deprecated_scripts/utility_variants/
mv scripts/verify_and_fix_all_data.py archive/deprecated_scripts/utility_variants/
```

### Step 3: Reorganize Authoritative Scripts
```bash
# Create new directory structure
mkdir -p scripts/{setup,testing,maintenance,development}

# Move setup scripts
mv scripts/verify_dependencies.py scripts/setup/
mv scripts/setup_database_tables.py scripts/setup/
mv scripts/install_chromedriver.py scripts/setup/

# Move testing scripts
mv scripts/COMPLETE_SYSTEM_DEMONSTRATION.py scripts/testing/
mv run_missouri_tests.py scripts/testing/

# Move maintenance scripts
mv scripts/DIAGNOSE_AND_FIX_ALL_ISSUES.py scripts/maintenance/
mv fix_data_collection.py scripts/maintenance/
mv scripts/populate_sample_data.py scripts/maintenance/

# Move development scripts
mv scripts/check_environment.py scripts/development/
mv scripts/test_db_connection.py scripts/development/
mv scripts/LAUNCH_GUI_APPLICATION.py scripts/development/
```

## Rollback Instructions

If issues occur during migration, restore from archive:

```bash
# Restore specific category
cp -r archive/deprecated_scripts/launch_variants/* ./
cp -r archive/deprecated_scripts/test_variants/* ./
cp -r archive/deprecated_scripts/utility_variants/* scripts/

# Or restore from full backup (if created)
cp -r archive/scripts_backup_YYYYMMDD/ scripts/
```

## Updated Commands Reference

### Most Common Operations

| Task | Old Command | New Command |
|------|-------------|-------------|
| Launch App | `python launch_enhanced_app.py` | `python RUN_APPLICATION.py` |
| Test System | `python test_final_integration.py` | `python scripts/testing/COMPLETE_SYSTEM_DEMONSTRATION.py` |
| Test Properties | `python test_real_implementation.py` | `python scripts/testing/run_missouri_tests.py` |
| Diagnose Issues | `python scripts/verify_and_fix_all_data.py` | `python scripts/maintenance/DIAGNOSE_AND_FIX_ALL_ISSUES.py` |
| Check Environment | `python scripts/check_environment.py` | `python scripts/development/check_environment.py` |
| Setup Database | `python scripts/setup_database_tables.py` | `python scripts/setup/setup_database_tables.py` |

## Batch File Updates Needed

Update any `.bat` files that reference moved scripts:

### RUN_APPLICATION.bat
```batch
@echo off
echo Starting Maricopa Property Search Application...
python RUN_APPLICATION.py
pause
```

### setup_environment.bat  
```batch
@echo off
echo Verifying dependencies...
python scripts/setup/verify_dependencies.py

echo Setting up database...
python scripts/setup/setup_database_tables.py

echo Installing Chrome driver...
python scripts/setup/install_chromedriver.py

echo Setup complete!
pause
```

## Benefits Achieved

- **Reduced Complexity**: 68 → 12 active scripts (65% reduction)
- **Clear Ownership**: Each function has one authoritative script
- **Organized Structure**: Logical grouping by purpose
- **Simplified Workflow**: Clear paths for common tasks
- **Easier Maintenance**: Fewer scripts to update and test
- **Better Documentation**: Each script has clear purpose

## Support

If you encounter issues after migration:
1. Check the consolidation report for script mappings
2. Refer to archived scripts if functionality seems missing
3. Use the rollback instructions if necessary
4. Update team documentation as needed