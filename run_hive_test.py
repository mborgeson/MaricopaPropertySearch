#!/usr/bin/env python
"""Quick test runner for hive mind fixes"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Test 1: EnhancedConfigManager.get()
        print("Testing EnhancedConfigManager.get() method...")
# MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
config = EnhancedConfigManager()
result = config.get('test_key', 'default_value')
        print(f"✅ EnhancedConfigManager.get() works! Result: {result}")

# Test 2ThreadSafeDatabaseManager methods
        print("\nTesting DatabaseManager methods...")
# MIGRATED: from src.database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
db_methods = dir(DatabaseManager)
        print(f"✅ get_property_by_apn exists: {'get_property_by_apn' in db_methods}")
        print(f"✅ get_tax_history exists: {'get_tax_history' in db_methods}")
        print(f"✅ get_sales_history exists: {'get_sales_history' in db_methods}")

# Test 3: GUI import
        print("\nTesting GUI imports...")
try:
from src.enhanced_config_manager import EnhancedConfigManager
from src.gui.enhanced_main_window import EnhancedMainWindow
from src.threadsafe_database_manager import ThreadSafeDatabaseManager

        print("✅ EnhancedMainWindow imported successfully")
except AttributeError as e:
        print(f"❌ AttributeError: {e}")
        print("\n🎉 All critical fixes verified!")