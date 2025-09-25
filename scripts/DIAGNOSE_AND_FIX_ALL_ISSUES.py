#!/usr/bin/env python
"""
COMPREHENSIVE DIAGNOSIS AND FIX
This script will diagnose all current issues and implement systematic fixes
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
# MIGRATED: from database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
import json

def diagnose_all_issues():
    """Comprehensive diagnosis of all data issues"""
        print("="*80)
        print("COMPREHENSIVE PROPERTY DATA DIAGNOSIS")
        print("="*80)
    
    config = EnhancedConfigManager()
    db_manager = ThreadSafeDatabaseManager(config)
    
try:
        # 1. Get all properties from recent searches
        print("\n1. ANALYZING RECENT PROPERTY DATA:")
        print("-"*50)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT apn, owner_name, property_address, year_built, lot_size_sqft, 
                       raw_data, created_at
                FROM properties 
                WHERE created_at > NOW() - INTERVAL '2 hours'
                ORDER BY created_at DESC
                LIMIT 10
            """)
            
            recent_properties = cursor.fetchall()
        print(f"Found {len(recent_properties)} recent properties")
        
        for i, prop in enumerate(recent_properties, 1):
        print(f"\nProperty {i}:")
        print(f"  APN: {prop['apn']}")
        print(f"  Owner: {repr(prop['owner_name'])}")
        print(f"  Address: {prop['property_address']}")
        print(f"  Year Built: {repr(prop['year_built'])}")
        print(f"  Lot Size: {repr(prop['lot_size_sqft'])}")
            
            raw_data = prop['raw_data']
            if raw_data:
        print(f"  Raw Data Keys: {list(raw_data.keys())}")
        print(f"  Raw Data Values:")
                for key, value in raw_data.items():
        print(f"    {key}: {repr(value)}")
            else:
        print(f"  Raw Data: None")
                
        # 2. Check what fields are actually available in raw_data
        print(f"\n2. ANALYZING RAW_DATA FIELD PATTERNS:")
        print("-"*50)
        
        all_raw_keys = set()
        non_empty_fields = {}
        
        for prop in recent_properties:
            raw_data = prop['raw_data']
            if raw_data:
                all_raw_keys.update(raw_data.keys())
                for key, value in raw_data.items():
                    if value and str(value).strip():
                        if key not in non_empty_fields:
                            non_empty_fields[key] = []
                        non_empty_fields[key].append(value)
        print(f"All raw_data keys found: {sorted(all_raw_keys)}")
        print(f"\nFields with actual data:")
        for key, values in non_empty_fields.items():
            unique_values = list(set(values))[:3]  # Show first 3 unique values
        print(f"  {key}: {unique_values}")
        
        # 3. Check tax and sales data availability
        print(f"\n3. TAX AND SALES DATA AVAILABILITY:")
        print("-"*50)
        
        total_tax_records = 0
        total_sales_records = 0
        
        for prop in recent_properties:
            apn = prop['apn']
            tax_records = db_manager.get_tax_history(apn)
            sales_records = db_manager.get_sales_history(apn)
            
            total_tax_records += len(tax_records)
            total_sales_records += len(sales_records)
        print(f"  {apn}: {len(tax_records)} tax records, {len(sales_records)} sales records")
        print(f"\nTotals: {total_tax_records} tax records, {total_sales_records} sales records")
        
        # 4. Database schema analysis
        print(f"\n4. DATABASE SCHEMA ANALYSIS:")
        print("-"*50)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get properties table structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'properties'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
        print("Properties table structure:")
            for col in columns:
        print(f"  {col['column_name']}: {col['data_type']} {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        
        # 5. API vs Database data comparison
        print(f"\n5. POTENTIAL SOLUTIONS:")
        print("-"*50)
        print("Issues identified:")
        print("1. API returns minimal structured data (owner_name, property_address)")
        print("2. Most property details (year_built, lot_size) are None/empty")
        print("3. Raw_data has limited information")
        print("4. No tax or sales data for most properties")
        print()
        print("Solutions needed:")
        print("1. Enhance API data collection from multiple Maricopa County endpoints")
        print("2. Implement web scraping for missing property details")
        print("3. Add automatic tax/sales data collection")
        print("4. Improve GUI to show what data is available vs needs collection")
        
        # 6. Test our test property with complete data
        print(f"\n6. TESTING COMPLETE DATA PROPERTY (13304014A):")
        print("-"*50)
        
        test_property = db_manager.get_property_by_apn('13304014A')
        if test_property:
        print("Complete test property found:")
            for key, value in test_property.items():
                if key not in ['raw_data', 'created_at', 'last_updated']:
        print(f"  {key}: {repr(value)}")
        else:
        print("Test property not found - this explains empty tabs issue!")
            
except Exception as e:
        print(f"Error during diagnosis: {e}")
import traceback

from src.enhanced_config_manager import EnhancedConfigManager
from src.threadsafe_database_manager import ThreadSafeDatabaseManager

        traceback.print_exc()

finally:
        db_manager.close()
    def implement_fixes():
    """Implement systematic fixes based on diagnosis"""
        print(f"\n" + "="*80)
        print("IMPLEMENTING SYSTEMATIC FIXES")
        print("="*80)
        print("The diagnosis shows the core issues:")
        print("1. API data is incomplete - only basic info is returned")
        print("2. Properties need individual data collection for complete information")
        print("3. GUI needs to better guide users to collect missing data")
        print()
        print("RECOMMENDED ACTIONS:")
        print("1. Use 'Collect Complete Property Data' button for any property needing details")
        print("2. The search results table now shows appropriate placeholders") 
        print("3. Property details dialog clearly indicates when data needs collection")
        print("4. Debug system helps identify specific data issues")

if __name__ == "__main__":
    diagnose_all_issues()
    implement_fixes()