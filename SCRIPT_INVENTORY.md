# MaricopaPropertySearch Script Inventory

## Summary
- **Total Python Files**: 180
- **Categories**: 12 major categories identified
- **Duplicate Candidates**: Multiple versions of similar functionality found

## Categorized Script Inventory

### 1. Main Entry Points & Launchers (6 files)
- `RUN_APPLICATION.py` - Main application launcher
- `maricopa_property_search.py` - Core application
- `maricopa_property_search_fixed.py` - Fixed version
- `maricopa_property_search_stable.py` - Stable version
- `maricopa_property_search_ORIGINAL_WORKING.py` - Original backup
- `maricopa_property_search_advanced.py` - Advanced features

### 2. Core API Clients (8 files - DUPLICATES DETECTED)
- `src/api_client_original.py` - Original API client
- `src/api_client_backup.py` - Backup version
- `src/parallel_api_client.py` - Parallel processing API
- `src/api_client.py` - Current API client
- `src/threadsafe_api_client.py` - Thread-safe version
- `api_client_fixed.py` - Fixed version
- `api_client.py` - Root version
- `optimized_api_client.py` - Optimized version

### 3. Web Scrapers (7 files - DUPLICATES DETECTED)
- `src/web_scraper.py` - Basic scraper
- `src/optimized_web_scraper.py` - Optimized version
- `src/parallel_web_scraper.py` - Parallel processing
- `src/tax_scraper.py` - Tax-specific scraping
- `web_scraper_maricopa.py` - Maricopa-specific
- `web_scraper_original.py` - Original backup
- `web_scraper_fixed.py` - Fixed version

### 4. GUI Components (15 files - MAJOR DUPLICATES)
- `src/gui/enhanced_main_window.py` - Enhanced window
- `src/gui/enhanced_main_window_fixed.py` - Fixed enhanced
- `src/gui/main_window_improved.py` - Improved version
- `src/gui/main_window_stable.py` - Stable version
- `src/gui/main_window.py` - Basic window
- `enhanced_gui.py` - Enhanced GUI module
- `enhanced_gui_integrated.py` - Integrated version
- `gui_improvements.py` - Improvements module
- `gui_integration_enhancements.py` - Integration enhancements
- `apply_gui_integration.py` - Integration application
- `simple_integration.py` - Simple integration
- `integration_fix.py` - Integration fixes
- `fix_refresh_button.py` - Specific fix
- `enhanced_property_search_integrated.py` - Enhanced search UI
- `enhanced_property_gui_updated.py` - Updated GUI

### 5. Batch Search Components (8 files)
- `src/enhanced_batch_search_dialog.py` - Enhanced dialog
- `src/batch_search_integration.py` - Integration module
- `src/batch_search_demo.py` - Demo application
- `src/batch_search_engine.py` - Core engine
- `batch_search_interface.py` - Interface module
- `batch_search_integration.py` - Root integration
- `batch_search_test.py` - Test module
- `test_batch_search.py` - Another test module

### 6. Database Management (5 files - DUPLICATES)
- `src/threadsafe_database_manager.py` - Thread-safe version
- `src/database_manager.py` - Basic manager
- `database_manager.py` - Root version
- `database_manager_fixed.py` - Fixed version
- `database_manager_original.py` - Original backup

### 7. Configuration Management (5 files - DUPLICATES)
- `src/config_manager.py` - Basic config
- `src/enhanced_config_manager.py` - Enhanced version
- `config_manager.py` - Root version
- `settings.py` - Settings module
- `fix_default_settings_simple.py` - Settings fix

### 8. Data Collectors (9 files)
- `src/background_data_collector.py` - Background collection
- `src/automatic_data_collector.py` - Automatic collection
- `src/performance_optimized_data_collector.py` - Optimized
- `src/data_collector.py` - Basic collector
- `data_collector.py` - Root version
- `data_collector_fixed.py` - Fixed version
- `fresh_data_collector.py` - Fresh data version
- `optimized_data_collector.py` - Optimized root
- `raw_data_collector.py` - Raw data collection

### 9. Testing Scripts (45+ files)
#### Unit Tests
- `tests/test_database_manager_fixes.py`
- `tests/test_runtime_issues.py`
- `tests/test_tax_sales_fix.py`
- `tests/test_background_fix.py`
- `tests/test_missouri_avenue_address.py`
- `tests/test_gui_database_integration.py`

#### Integration Tests
- `tests/integration/test_error_handling.py`
- `tests/integration/test_api_with_token.py`
- `tests/integration/test_real_implementation.py`
- `tests/integration/test_api_integration.py`
- `tests/integration/test_user_experience.py`

#### E2E Tests
- `tests/e2e/test_complete_workflows.py`
- `tests/e2e/run_missouri_tests.py`

#### Performance Tests
- `tests/performance/test_load_testing.py`
- `src/performance_test.py`

#### Ad-hoc Test Scripts
- `comprehensive_data_test.py`
- `quick_method_test.py`
- `test_settings.py`
- `run_hive_mind_tests.py`
- `test_*.py` (20+ files in root)

### 10. Hook System (8 files)
- `src/hook_manager.py` - Main manager
- `src/hooks/error_hooks.py`
- `src/hooks/hook_integration.py`
- `src/hooks/database_hooks.py`
- `src/hooks/search_hooks.py`
- `src/hooks/user_action_hooks.py`
- `src/hooks/api_hooks.py`
- `src/hooks/lifecycle_hooks.py`
- `src/hooks/performance_hooks.py`

### 11. Utilities & Helpers (10+ files)
- `src/search_cache.py` - Search caching
- `src/logging_config.py` - Logging setup
- `src/test_logging_system.py` - Logging test
- `scripts/validate_manual_collect_fix.py`
- `scripts/install_chromedriver.py`
- `scripts/test_api_endpoints.py`
- `scripts/test_data_source_status.py`
- `scripts/run_comprehensive_tests.py`
- `simple_error_handler.py`
- `simple_cache_manager.py`

### 12. Documentation Scripts (10+ files in claudedocs/)
- `claudedocs/simple_api_test.py`
- `claudedocs/execute_comprehensive_tests.py`
- `claudedocs/test_background_collection.py`
- `claudedocs/missouri_ave_test.py`
- `claudedocs/test_implementation_examples.py`
- `claudedocs/test_property_search.py`
- `claudedocs/performance_analysis.py`

## Duplicate Analysis Summary

### Critical Duplicates to Consolidate:

1. **API Client** (8 versions) → Consolidate to 1
   - Keep: Thread-safe version with parallel capabilities
   - Remove: Original, backup, fixed, optimized duplicates

2. **Web Scraper** (7 versions) → Consolidate to 2
   - Keep: Optimized parallel scraper + Tax-specific scraper
   - Remove: Original, fixed, basic duplicates

3. **GUI Main Window** (15 versions) → Consolidate to 1
   - Keep: Enhanced stable version with all fixes
   - Remove: All intermediate fixes and improvements

4. **Database Manager** (5 versions) → Consolidate to 1
   - Keep: Thread-safe version
   - Remove: Original, basic, fixed duplicates

5. **Configuration Manager** (5 versions) → Consolidate to 1
   - Keep: Enhanced version
   - Remove: Basic and duplicate versions

6. **Data Collector** (9 versions) → Consolidate to 2
   - Keep: Performance optimized + Background collector
   - Remove: All other duplicates

## Estimated Cleanup Impact
- **Current Files**: 180
- **After Consolidation**: ~95-100 files
- **Reduction**: 45-50% fewer files
- **Benefit**: Clearer codebase, easier maintenance, reduced confusion