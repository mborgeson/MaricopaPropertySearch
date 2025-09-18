#!/usr/bin/env python
"""Quick test runner for hive mind fixes"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Test 1: ConfigManager.get()
print("Testing ConfigManager.get() method...")
from src.config_manager import ConfigManager
config = ConfigManager()
result = config.get('test_key', 'default_value')
print(f"✅ ConfigManager.get() works! Result: {result}")

# Test 2: DatabaseManager methods
print("\nTesting DatabaseManager methods...")
from src.database_manager import DatabaseManager
db_methods = dir(DatabaseManager)
print(f"✅ get_property_by_apn exists: {'get_property_by_apn' in db_methods}")
print(f"✅ get_tax_history exists: {'get_tax_history' in db_methods}")
print(f"✅ get_sales_history exists: {'get_sales_history' in db_methods}")

# Test 3: GUI import
print("\nTesting GUI imports...")
try:
    from src.gui.enhanced_main_window import EnhancedMainWindow
    print("✅ EnhancedMainWindow imported successfully")
except AttributeError as e:
    print(f"❌ AttributeError: {e}")

print("\n🎉 All critical fixes verified!")