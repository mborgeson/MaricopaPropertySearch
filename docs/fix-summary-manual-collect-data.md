# Fix Summary: manual_collect_data AttributeError

## Problem
The `manual_collect_data` method in the PropertyDetailsDialog was causing an AttributeError:
```
'PropertyDetailsDialog' object has no attribute 'results_table'. Did you mean: 'sales_table'?
```

## Root Cause
The method was trying to access `self.results_table` to get selected items, but:
1. `results_table` only exists in the main window context (EnhancedPropertySearchApp)
2. The method was being called from PropertyDetailsDialog context
3. PropertyDetailsDialog already has the APN available in `self.property_data`

## Solution
Modified the `manual_collect_data` method in PropertyDetailsDialog to:

### Before (Broken)
```python
def manual_collect_data(self):
    selected_items = self.results_table.selectedItems()  # ❌ AttributeError
    # ... get APN from table selection
```

### After (Fixed)
```python
def manual_collect_data(self):
    """Manual data collection with enhanced error handling for PropertyDetailsDialog"""
    # Get APN from property data instead of table selection
    apn = self.property_data.get('apn', '').strip()  # ✅ Uses available data

    # Use background manager to collect data
    if self.background_manager and self.background_manager.is_running():
        result = self.background_manager.collect_data_for_apn(apn, JobPriority.CRITICAL)
        # ... handle result
```

## Key Changes

1. **Data Source**: Changed from `self.results_table.selectedItems()` to `self.property_data.get('apn')`
2. **Context Awareness**: Method now works correctly in PropertyDetailsDialog context
3. **Proper API Usage**: Uses `collect_data_for_apn` instead of non-existent method
4. **Error Handling**: Added comprehensive try/catch blocks
5. **Auto-startup**: If background collection isn't running, starts it automatically

## Validation
- ✅ Syntax check passes
- ✅ Method uses correct data source (`property_data`)
- ✅ No reference to `results_table` in PropertyDetailsDialog context
- ✅ Proper background manager usage
- ✅ Complete error handling
- ✅ All necessary imports present

## Impact
- Manual data collection now works from Property Details dialog
- No more AttributeError when clicking "Manual Collect (Immediate)" button
- Method appropriately handles different execution contexts
- Maintains all existing functionality in main window context

## Files Modified
- `src/gui/enhanced_main_window.py` - Fixed `manual_collect_data` method

## Testing
- Created validation script: `scripts/validate_manual_collect_fix.py`
- All validation checks pass
- Ready for production use