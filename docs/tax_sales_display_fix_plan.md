# Tax and Sales History Display Fix Plan

## Problem Analysis ✅

**Root Cause Identified**: BackgroundDataWorker initializes ImprovedMaricopaDataCollector with `api_client=None`, causing data collection to fail silently.

### Current Flow:
1. PropertyDetailsDialog opens → calls `_start_automatic_data_collection()`
2. BackgroundDataCollectionManager starts worker → `BackgroundDataWorker(db_manager, max_concurrent_jobs)`
3. BackgroundDataWorker initializes → `ImprovedMaricopaDataCollector(db_manager, api_client=None)`
4. Collection fails because API client is None → No data collected
5. UI shows "No records found" despite collection "completing"

### Infrastructure Status:
- ✅ Database connection works
- ✅ API client (MaricopaAPIClient) exists and functional
- ✅ Data collection logic (ImprovedMaricopaDataCollector) works
- ✅ UI refresh mechanism works (job_completed signal)
- ❌ API client not properly injected into data collector

## Solution Plan

### Fix 1: Proper API Client Initialization in BackgroundDataWorker
**File**: `src/background_data_collector.py`
**Method**: `BackgroundDataWorker.__init__()`
**Change**: Initialize API client properly instead of None

```python
# BEFORE (line 197):
self.data_collector = ImprovedMaricopaDataCollector(db_manager, api_client=None)

# AFTER:
from src.config_manager import ConfigManager
from src.api_client import MaricopaAPIClient

config_manager = ConfigManager()
api_client = MaricopaAPIClient(config_manager)
self.data_collector = ImprovedMaricopaDataCollector(db_manager, api_client)
```

### Fix 2: Enhanced Error Handling and Logging
**Purpose**: Better visibility into collection failures
**Changes**:
- Add error logging when API client is missing
- Improve collection status reporting
- Add validation in collect_data_for_apn_sync

### Fix 3: UI Status Updates
**Purpose**: Show meaningful status during collection
**Changes**:
- Update status messages to reflect actual collection state
- Show errors when collection fails
- Clear status when no data is needed

## Implementation Tasks

1. **Fix BackgroundDataWorker API client initialization**
2. **Add error handling and validation**
3. **Enhance logging for debugging**
4. **Test the complete data collection flow**
5. **Verify UI updates properly after collection**

## Expected Results

After fixes:
- PropertyDetailsDialog opens → automatic data collection starts
- Data collector has working API client → successful data collection
- Database gets populated with tax and sales records
- UI refreshes and shows collected data
- Users see tax/sales history immediately without manual intervention

## Testing Plan

1. **Unit test**: Verify BackgroundDataWorker initializes API client
2. **Integration test**: Test complete collection flow for sample APN
3. **UI test**: Open PropertyDetailsDialog and verify data appears
4. **Error test**: Verify graceful handling when collection fails