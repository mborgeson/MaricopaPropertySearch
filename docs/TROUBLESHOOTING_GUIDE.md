# MaricopaPropertySearch Troubleshooting Guide

## Tax and Sales History Not Displaying

**Issue Date:** 2025-01-16
**Resolution Status:** RESOLVED
**Resolution Method:** Hive-Mind Tactical Swarm Analysis

### Problem Description
Tax history and sales history tabs in PropertyDetailsDialog were showing "No records found" despite the infrastructure being fully functional.

### Root Cause Analysis
The investigation by the hive-mind swarm revealed:
- ✅ Database connection was working
- ✅ API client methods existed and functioned
- ✅ Data pipeline (API → Database → UI) was intact
- ❌ Data collection workflows were NOT being triggered
- ❌ BackgroundDataWorker was initializing with `api_client=None`

### Applied Fixes

#### 1. ConfigManager 'get' Method Error
**Error:** `'ConfigManager' object has no attribute 'get'`
**Fix:**
- Added generic `get(key, default=None, section='application')` method to ConfigManager
- Added missing `[application]` section to config.ini with default values
- Files: `src/config_manager.py`, `config/config.ini`

#### 2. DatabaseManager Missing Method
**Error:** `'DatabaseManager' object has no attribute 'get_property_details'`
**Fix:**
- Added `get_property_details(apn)` method to DatabaseManager
- Added same method to ThreadSafeDatabaseManager
- Methods delegate to existing `get_property_by_apn()` for compatibility
- Files: `src/database_manager.py`, `src/threadsafe_database_manager.py`

#### 3. PropertyDetailsDialog AttributeError
**Error:** `'PropertyDetailsDialog' object has no attribute 'results_table'`
**Fix:**
- Fixed `manual_collect_data` method context handling
- Changed from table selection to property data access
- Added comprehensive error handling
- File: `src/gui/enhanced_main_window.py` (line ~877)

#### 4. Background Data Collection API Client
**Critical Fix:** BackgroundDataWorker was initializing with `api_client=None`
**Solution:**
```python
# BEFORE (BROKEN):
self.data_collector = ImprovedMaricopaDataCollector(db_manager, api_client=None)

# AFTER (FIXED):
config_manager = ConfigManager()
api_client = MaricopaAPIClient(config_manager)
self.data_collector = ImprovedMaricopaDataCollector(db_manager, api_client)
```
- File: `src/background_data_collector.py`

#### 5. Data Collection Triggers
**Fix:**
- Enabled automatic data collection when PropertyDetailsDialog opens
- Connected manual collection buttons properly
- Added UI refresh mechanisms after data collection
- File: `src/gui/enhanced_main_window.py`

### Verification Commands

```bash
# Quick verification of all fixes
python -c "
import sys
sys.path.insert(0, 'src')
from src.config_manager import ConfigManager
from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.api_client import MaricopaAPIClient

config = ConfigManager()
print('[OK] ConfigManager.get() works:', config.get('auto_start_collection'))

db = ThreadSafeDatabaseManager(config)
print('[OK] DatabaseManager.get_property_details exists:', hasattr(db, 'get_property_details'))
db.close()

api = MaricopaAPIClient(config)
print('[OK] API client methods exist:', hasattr(api, 'get_tax_history'))
"

# Run application and test
python RUN_APPLICATION.py
```

### Testing Tax/Sales Display

1. Launch application: `python RUN_APPLICATION.py`
2. Search for property (e.g., APN: 13304019)
3. Click "View Details" to open PropertyDetailsDialog
4. Navigate to "Tax History" and "Sales History" tabs
5. Data should automatically collect and display

### Solution Pattern for Similar Issues

When UI components show "No data" despite working infrastructure:

1. **Check data collection triggers**
   - Are background workers starting?
   - Are manual collection buttons connected?
   - Is auto-collection enabled for missing data?

2. **Verify dependency initialization**
   - Are workers getting proper API clients?
   - Are config managers being passed correctly?
   - Are database connections initialized?

3. **Trace the data pipeline**
   - API fetch → Database storage → UI query → Display
   - Check logs at each step
   - Verify data format conversions

4. **Test individual components**
   ```python
   # Test API client
   api_client.get_tax_history(apn)

   # Test database storage
   db_manager.insert_tax_history(apn, tax_data)

   # Test database retrieval
   db_manager.get_tax_history(apn)

   # Test UI refresh
   dialog.refresh_tax_data()
   ```

### Common Error Patterns

| Error | Likely Cause | Solution |
|-------|-------------|----------|
| `AttributeError: object has no attribute 'X'` | Missing method or wrong context | Add method or fix context handling |
| `TypeError: __init__() missing argument` | Dependency not passed | Pass required config/manager objects |
| Silent failures (no errors, no data) | Workers initialized with None | Check worker initialization chain |
| "No records found" with working DB | Collection not triggered | Enable auto-collection triggers |

### Files Modified Summary

- `src/config_manager.py` - Added get() method
- `src/database_manager.py` - Added get_property_details()
- `src/threadsafe_database_manager.py` - Added get_property_details()
- `src/gui/enhanced_main_window.py` - Fixed manual_collect_data, triggers
- `src/background_data_collector.py` - Fixed API client initialization
- `config/config.ini` - Added [application] section
- `config/app_settings.json` - Created for settings persistence

### Hive-Mind Command Used

```bash
npx claude-flow hive-mind spawn "Fix tax and sales history display issues" --claude --queen-type tactical
```

### Prevention Measures

1. Always initialize workers with required dependencies
2. Add validation to detect None API clients early
3. Implement health checks for data collection pipeline
4. Add logging at each data flow step
5. Create integration tests for full data pipeline

---

## Other Known Issues

### Syntax Errors
- **Line 3020 incomplete try/except**: Fixed by completing closeEvent method

### Settings Persistence
- **Settings not saving**: Fixed by creating app_settings.json

### Unicode Encoding
- **Test scripts with Unicode symbols**: Use ASCII equivalents in Windows console

---

## Memory Storage

Troubleshooting information is stored in Claude-Flow memory:
```bash
# Store memory
npx claude-flow memory store "KEY" "value"

# Recall memory
npx claude-flow memory query "KEY"

# Export all memory
npx claude-flow memory export backup.json
```

Key stored memories:
- `MCA_TAX_SALES_FIX` - Complete tax/sales history fix details

---

*Document maintained by: Hive-Mind Tactical Swarm*
*Last updated: 2025-01-16*