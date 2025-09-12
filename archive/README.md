# Archive Directory

This directory contains deprecated scripts and historical versions that have been consolidated as part of the script cleanup initiative.

## Directory Structure

- **deprecated_scripts/launch_variants/**: Multiple application launcher versions that were superseded by `RUN_APPLICATION.py`
- **deprecated_scripts/test_variants/**: Redundant test scripts consolidated into `COMPLETE_SYSTEM_DEMONSTRATION.py` and `run_missouri_tests.py`
- **deprecated_scripts/utility_variants/**: Utility scripts merged into `DIAGNOSE_AND_FIX_ALL_ISSUES.py` and `fix_data_collection.py`
- **deprecated_scripts/historical/**: Historical versions and backup files from `.history/` directory

## Restoration Instructions

If you need to restore any deprecated script:

```bash
# Copy specific script back to main project
cp archive/deprecated_scripts/[category]/[script_name].py ./

# Or restore entire category
cp archive/deprecated_scripts/[category]/* scripts/
```

## Archival Date
Scripts archived: 2025-09-12

## Consolidation Reference
See `consolidation_report.md` for complete details on what was archived and why.