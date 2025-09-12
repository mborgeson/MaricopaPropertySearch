# Authoritative Script List
**Maricopa Property Search Project**  
**Updated:** 2025-09-12

## Primary Application Launcher

### RUN_APPLICATION.py
- **Absolute Path:** `/c/Users/MattBorgeson/Development/Work/MaricopaPropertySearch/RUN_APPLICATION.py`
- **Purpose:** Primary application launcher with comprehensive error handling
- **Usage:** `python RUN_APPLICATION.py`
- **Status:** AUTHORITATIVE - Use this for all application launches
- **Features:** Environment validation, database connectivity check, GUI launch
- **Replaces:** launch_app_fixed.py, launch_enhanced_app.py, launch_improved_app.py

## Setup and Installation Scripts

### 1. verify_dependencies.py
- **Absolute Path:** `/c/Users/MattBorgeson/Development/Work/MaricopaPropertySearch/scripts/verify_dependencies.py`
- **Purpose:** Comprehensive dependency validation and environment setup verification
- **Usage:** `python scripts/setup/verify_dependencies.py` (after reorganization)
- **Status:** AUTHORITATIVE - Use for all environment validation
- **Features:** Package verification, environment checks, installation guidance
- **Replaces:** scripts/test_installation.py

### 2. setup_database_tables.py
- **Absolute Path:** `/c/Users/MattBorgeson/Development/Work/MaricopaPropertySearch/scripts/setup_database_tables.py`
- **Purpose:** Database initialization and table creation
- **Usage:** `python scripts/setup/setup_database_tables.py` (after reorganization)
- **Status:** AUTHORITATIVE - Use for all database setup
- **Features:** Clean database initialization, table schema creation

### 3. install_chromedriver.py
- **Absolute Path:** `/c/Users/MattBorgeson/Development/Work/MaricopaPropertySearch/scripts/install_chromedriver.py`
- **Purpose:** Browser driver installation for web scraping functionality
- **Usage:** `python scripts/setup/install_chromedriver.py` (after reorganization)
- **Status:** AUTHORITATIVE - Use for browser setup
- **Features:** ChromeDriver installation and configuration

## System Testing Scripts

### 4. COMPLETE_SYSTEM_DEMONSTRATION.py
- **Absolute Path:** `/c/Users/MattBorgeson/Development/Work/MaricopaPropertySearch/scripts/COMPLETE_SYSTEM_DEMONSTRATION.py`
- **Purpose:** Comprehensive system validation and end-to-end testing
- **Usage:** `python scripts/testing/COMPLETE_SYSTEM_DEMONSTRATION.py` (after reorganization)
- **Status:** AUTHORITATIVE - Use for all integration testing
- **Features:** Full system test suite, API validation, database testing
- **Replaces:** test_application.py, test_api_integration.py, test_final_integration.py, test_comprehensive_api.py, test_comprehensive_database_integration.py, test_detailed_endpoints.py, test_real_api_endpoints.py, test_real_endpoints.py, scripts/test_api_with_token.py

### 5. run_missouri_tests.py
- **Absolute Path:** `/c/Users/MattBorgeson/Development/Work/MaricopaPropertySearch/run_missouri_tests.py`
- **Purpose:** Real property data validation with specific test cases
- **Usage:** `python scripts/testing/run_missouri_tests.py` (after reorganization)
- **Status:** AUTHORITATIVE - Use for property-specific testing
- **Features:** Missouri Ave property testing, real data validation
- **Replaces:** test_real_implementation.py, scripts/test_complete_property_with_tax_scraping.py

## Maintenance and Diagnostic Scripts

### 6. DIAGNOSE_AND_FIX_ALL_ISSUES.py
- **Absolute Path:** `/c/Users/MattBorgeson/Development/Work/MaricopaPropertySearch/scripts/DIAGNOSE_AND_FIX_ALL_ISSUES.py`
- **Purpose:** Comprehensive system diagnostics and automated issue resolution
- **Usage:** `python scripts/maintenance/DIAGNOSE_AND_FIX_ALL_ISSUES.py` (after reorganization)
- **Status:** AUTHORITATIVE - Use for all system diagnostics
- **Features:** System health checks, automated fixes, comprehensive reporting
- **Replaces:** test_complete_fix.py, scripts/check_enhanced_property_data.py, scripts/check_tax_history_records.py, scripts/fix_database_user.py, scripts/verify_and_fix_all_data.py

### 7. fix_data_collection.py
- **Absolute Path:** `/c/Users/MattBorgeson/Development/Work/MaricopaPropertySearch/fix_data_collection.py`
- **Purpose:** Critical data collection fixes and corrections
- **Usage:** `python scripts/maintenance/fix_data_collection.py` (after reorganization)
- **Status:** AUTHORITATIVE - Use for data repair operations
- **Features:** Data collection fixes, error correction, data integrity
- **Replaces:** scripts/fix_tax_data_discrepancy.py

### 8. populate_sample_data.py
- **Absolute Path:** `/c/Users/MattBorgeson/Development/Work/MaricopaPropertySearch/scripts/populate_sample_data.py`
- **Purpose:** Sample data generation and database population for development
- **Usage:** `python scripts/maintenance/populate_sample_data.py` (after reorganization)
- **Status:** AUTHORITATIVE - Use for test data generation
- **Features:** Sample data creation, development database seeding

## Development Utility Scripts

### 9. check_environment.py
- **Absolute Path:** `/c/Users/MattBorgeson/Development/Work/MaricopaPropertySearch/scripts/check_environment.py`
- **Purpose:** Environment configuration validation and status reporting
- **Usage:** `python scripts/development/check_environment.py` (after reorganization)
- **Status:** AUTHORITATIVE - Use for environment checks
- **Features:** Configuration validation, environment status, quick health check

### 10. test_db_connection.py
- **Absolute Path:** `/c/Users/MattBorgeson/Development/Work/MaricopaPropertySearch/scripts/test_db_connection.py`
- **Purpose:** Database connectivity validation and connection testing
- **Usage:** `python scripts/development/test_db_connection.py` (after reorganization)
- **Status:** AUTHORITATIVE - Use for database connection validation
- **Features:** Database connectivity test, connection troubleshooting

### 11. LAUNCH_GUI_APPLICATION.py
- **Absolute Path:** `/c/Users/MattBorgeson/Development/Work/MaricopaPropertySearch/scripts/LAUNCH_GUI_APPLICATION.py`
- **Purpose:** Dedicated GUI application launcher for development
- **Usage:** `python scripts/development/LAUNCH_GUI_APPLICATION.py` (after reorganization)
- **Status:** AUTHORITATIVE - Use for GUI-specific launches
- **Features:** GUI application startup, development interface

## Command Quick Reference

```bash
# Application Launch
python RUN_APPLICATION.py

# Initial Setup (run once)
python scripts/setup/verify_dependencies.py
python scripts/setup/setup_database_tables.py
python scripts/setup/install_chromedriver.py

# Regular Testing
python scripts/testing/COMPLETE_SYSTEM_DEMONSTRATION.py
python scripts/testing/run_missouri_tests.py

# Maintenance Tasks
python scripts/maintenance/DIAGNOSE_AND_FIX_ALL_ISSUES.py
python scripts/maintenance/fix_data_collection.py
python scripts/maintenance/populate_sample_data.py

# Development Tasks
python scripts/development/check_environment.py
python scripts/development/test_db_connection.py
python scripts/development/LAUNCH_GUI_APPLICATION.py
```

## Deprecated Scripts Reference

**DO NOT USE** - These scripts are archived and superseded:

### Launch Scripts (use RUN_APPLICATION.py instead)
- launch_app_fixed.py
- launch_enhanced_app.py  
- launch_improved_app.py

### Test Scripts (use COMPLETE_SYSTEM_DEMONSTRATION.py or run_missouri_tests.py instead)
- test_application.py
- test_api_integration.py
- test_complete_fix.py
- test_final_integration.py
- test_real_implementation.py
- scripts/test_api_with_token.py
- scripts/test_complete_property_with_tax_scraping.py
- scripts/test_comprehensive_api.py
- scripts/test_comprehensive_database_integration.py
- scripts/test_detailed_endpoints.py
- scripts/test_installation.py
- scripts/test_real_api_endpoints.py
- scripts/test_real_endpoints.py

### Utility Scripts (use DIAGNOSE_AND_FIX_ALL_ISSUES.py or fix_data_collection.py instead)
- scripts/check_enhanced_property_data.py
- scripts/check_tax_history_records.py
- scripts/fix_database_user.py
- scripts/fix_tax_data_discrepancy.py
- scripts/investigate_real_endpoints.py
- scripts/verify_and_fix_all_data.py

## Script Status Definitions

- **AUTHORITATIVE**: Official script for this functionality - always use this version
- **DEPRECATED**: Functionality moved to authoritative script - do not use
- **ARCHIVED**: Historical version stored in archive/ directory
- **SUPERSEDED**: Replaced by newer authoritative version

## Maintenance Notes

- All authoritative scripts include comprehensive error handling
- Logging is standardized across all scripts
- Command-line arguments follow consistent patterns
- Documentation is embedded in each script
- Each script validates its prerequisites before execution

## Updates and Changes

When modifying functionality:
1. Update only the AUTHORITATIVE script for that function
2. Never modify archived/deprecated scripts
3. Update this list if new authoritative scripts are created
4. Test all changes against the authoritative script list
5. Update documentation to reflect any changes

**Last Updated:** 2025-09-12  
**Next Review:** 2025-12-12 (quarterly review recommended)