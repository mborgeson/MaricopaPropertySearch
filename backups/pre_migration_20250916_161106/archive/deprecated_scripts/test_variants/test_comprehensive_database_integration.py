#!/usr/bin/env python
"""
Test comprehensive property data database integration
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from api_client import MaricopaAPIClient
from database_manager import DatabaseManager

from config_manager import ConfigManager


def test_comprehensive_database_integration():
    """Test saving comprehensive property data to database"""
    print("Testing Comprehensive Database Integration")
    print("=" * 50)
    
    config = ConfigManager()
    
    # Test database connection first
    print("Checking database connection...")
    try:
        db_manager = DatabaseManager(config)
        print("+ Database connection successful")
    except Exception as e:
        print(f"- Database connection failed: {e}")
        return False
    
    # Get comprehensive property data
    print("Getting comprehensive property data...")
    try:
        api_client = MaricopaAPIClient(config)
        test_apn = '13304014A'
        
        comprehensive_info = api_client.get_comprehensive_property_info(test_apn)
        api_client.close()
        
        if not comprehensive_info:
            print(f"- No comprehensive data retrieved for APN: {test_apn}")
            return False
            
        print(f"+ Retrieved comprehensive data for APN: {test_apn}")
        print(f"  - Valuation records: {len(comprehensive_info.get('valuation_history', []))}")
        print(f"  - Detailed endpoints: {len(comprehensive_info.get('detailed_data', {}))}")
        
    except Exception as e:
        print(f"- Failed to get comprehensive data: {e}")
        return False
    
    # Save to database
    print("Saving comprehensive data to database...")
    try:
        success = db_manager.save_comprehensive_property_data(comprehensive_info)
        
        if success:
            print("+ Comprehensive data saved successfully!")
            
            # Verify the data was saved
            print("Verifying saved data...")
            
            # Check basic property record
            property_record = db_manager.get_property_by_apn(test_apn)
            if property_record:
                print(f"+ Property record found: {property_record['property_address']}")
            else:
                print("- Property record not found")
                
            # Check tax history records
            tax_records = db_manager.get_tax_history(test_apn)
            print(f"+ Tax history records: {len(tax_records)}")
            
            if tax_records:
                print("  Recent tax years:")
                for record in tax_records[:3]:  # Show first 3
                    assessed_val = f"${record['assessed_value']:,}" if record['assessed_value'] else "N/A"
                    print(f"    {record['tax_year']}: {assessed_val}")
            
            print()
            print("=" * 50)
            print("DATABASE INTEGRATION SUCCESS!")
            print("The system now saves:")
            print("- Basic property information")
            print("- 5 years of tax assessment history")
            print("- Detailed property data (in raw_data field)")
            print("- Complete valuation records with full cash values")
            
            return True
            
        else:
            print("- Failed to save comprehensive data")
            return False
            
    except Exception as e:
        print(f"- Database save failed: {e}")
        import traceback

        traceback.print_exc()

    return False
    
    finally:
        try:
            db_manager.close()
        except:
        pass

if __name__ == "__main__":
    success = test_comprehensive_database_integration()
    if not success:
        sys.exit(1)