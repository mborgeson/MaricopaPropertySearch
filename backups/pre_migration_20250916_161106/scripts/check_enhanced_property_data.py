#!/usr/bin/env python
"""
Check enhanced property data to see what fields are filled
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from config_manager import ConfigManager
from database_manager import DatabaseManager

def check_enhanced_property_data():
    """Check what enhanced data is now available"""
    print("Enhanced Property Data Check")
    print("=" * 40)
    
    config = ConfigManager()
    db_manager = DatabaseManager(config)
    
    test_apn = '13304014A'
    
    try:
        # Get the property record
        property_record = db_manager.get_property_by_apn(test_apn)
        
        if property_record:
            print(f"Property Record for APN: {test_apn}")
            print("-" * 30)
            
            # Show all fields and their values
            for field, value in property_record.items():
                if field == 'raw_data':
                    print(f"  {field}: [JSON data - {len(str(value))} chars]")
                elif value is not None and value != '':
                    print(f"  {field}: {value}")
                else:
                    print(f"  {field}: None/Empty")
            
            print(f"\nFields with data: {sum(1 for v in property_record.values() if v is not None and v != '')}")
            print(f"Total fields: {len(property_record)}")
            
        else:
            print(f"No property record found for APN: {test_apn}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db_manager.close()

if __name__ == "__main__":
    check_enhanced_property_data()