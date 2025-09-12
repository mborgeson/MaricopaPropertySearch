# Raw Data Display Error Fix

## Issue Fixed
Fixed AttributeError at line 1385 in `src/gui/enhanced_main_window.py` where `raw_data` was being treated as a dictionary but was actually a JSON string from the database.

## Root Cause
The `raw_data` field is stored as JSON text in the PostgreSQL database. When retrieved, it comes back as a string that needs to be parsed into a dictionary before accessing its properties with `.get()` method.

## Solution Implemented
Added JSON parsing logic at the beginning of the `display_results` method to handle `raw_data` properly:

```python
# Handle raw_data - it might be a JSON string that needs parsing
raw_data = result.get('raw_data', {})
if isinstance(raw_data, str):
    try:
        import json
        raw_data = json.loads(raw_data)
    except (json.JSONDecodeError, TypeError):
        raw_data = {}
elif not isinstance(raw_data, dict):
    raw_data = {}
```

## Files Modified
- `src/gui/enhanced_main_window.py` (lines 1370-1404)
  - Moved raw_data parsing to the beginning of the loop
  - Updated owner_name extraction to use parsed raw_data
  - Updated year_built extraction to use parsed raw_data
  - Updated lot_size extraction to use parsed raw_data

## Testing Status
✅ Application launches without errors
✅ No AttributeError when displaying search results
✅ Property data displays correctly with parsed raw_data fields

## Impact
- Search results now display without errors
- Year Built, Owner Name, and Lot Size fields properly extract data from raw_data
- Application is more robust when handling database results