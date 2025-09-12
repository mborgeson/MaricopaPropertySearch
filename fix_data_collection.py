#!/usr/bin/env python
"""
Fix for tax and sales data collection issues
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config_manager import ConfigManager
from api_client import MaricopaAPIClient
from database_manager import DatabaseManager
from logging_config import setup_logging

def fix_data_collection_issues():
    """Fix data collection issues"""
    
    # Setup logging
    setup_logging()
    
    print("Fixing Data Collection Issues...")
    print("=" * 50)
    
    try:
        # Initialize components
        config_manager = ConfigManager()
        api_client = MaricopaAPIClient(config_manager)
        db_manager = DatabaseManager(config_manager)
        
        # Test APN from logs
        test_apn = "13304017"
        
        print(f"\n1. Testing database methods for APN: {test_apn}")
        
        # Test database methods to see what they return
        try:
            tax_records = db_manager.get_tax_history(test_apn)
            sales_records = db_manager.get_sales_history(test_apn)
            
            print(f"   Tax records type: {type(tax_records)}")
            print(f"   Tax records value: {tax_records}")
            print(f"   Sales records type: {type(sales_records)}")
            print(f"   Sales records value: {sales_records}")
            
            # If they return integers or other non-list values, that's the issue
            if not isinstance(tax_records, list):
                print(f"   [ISSUE] Tax records should be list, got {type(tax_records)}")
            if not isinstance(sales_records, list):
                print(f"   [ISSUE] Sales records should be list, got {type(sales_records)}")
                
        except Exception as e:
            print(f"   [ERROR] Database method error: {e}")
        
        print(f"\n2. Testing API tax history collection for APN: {test_apn}")
        
        try:
            # Test the real API tax history endpoint
            api_tax_history = api_client.get_tax_history(test_apn)
            print(f"   API tax history type: {type(api_tax_history)}")
            print(f"   API tax history count: {len(api_tax_history) if isinstance(api_tax_history, list) else 'N/A'}")
            
            if api_tax_history and isinstance(api_tax_history, list):
                print(f"   [SUCCESS] API returned {len(api_tax_history)} tax records")
                
                # Try to save to database
                for i, tax_record in enumerate(api_tax_history):
                    tax_data = {
                        'apn': test_apn,
                        'tax_year': tax_record.get('TaxYear'),
                        'assessed_value': int(tax_record.get('FullCashValue', 0)) if tax_record.get('FullCashValue') else None,
                        'limited_value': int(tax_record.get('LimitedPropertyValue', '').strip()) if tax_record.get('LimitedPropertyValue', '').strip() else None,
                        'tax_amount': None,  # Not in API
                        'payment_status': None,  # Not in API
                        'last_payment_date': None,  # Not in API
                        'raw_data': tax_record
                    }
                    
                    success = db_manager.insert_tax_history(tax_data)
                    if success:
                        print(f"   [OK] Saved tax record {i+1}/{len(api_tax_history)} to database")
                    else:
                        print(f"   [ERROR] Failed to save tax record {i+1}")
            else:
                print(f"   [ERROR] API did not return valid tax history")
                
        except Exception as e:
            print(f"   [ERROR] API tax collection error: {e}")
        
        print(f"\n3. Testing comprehensive property data for APN: {test_apn}")
        
        try:
            # Test comprehensive data which should include valuations
            comprehensive_data = api_client.get_comprehensive_property_info(test_apn)
            if comprehensive_data:
                print(f"   [OK] Got comprehensive property data")
                
                # Check if it has valuation history
                if 'valuation_history' in comprehensive_data:
                    val_count = len(comprehensive_data['valuation_history'])
                    print(f"   [OK] Found {val_count} valuation records")
                else:
                    print(f"   [WARNING] No valuation history in comprehensive data")
                
                # Try to save comprehensive data to database
                success = db_manager.save_comprehensive_property_data(comprehensive_data)
                if success:
                    print(f"   [OK] Saved comprehensive property data to database")
                else:
                    print(f"   [ERROR] Failed to save comprehensive data")
                    
            else:
                print(f"   [ERROR] No comprehensive property data found")
                
        except Exception as e:
            print(f"   [ERROR] Comprehensive data collection error: {e}")
        
        print(f"\n4. Verifying database after data collection...")
        
        try:
            # Check what's in database now
            updated_tax_records = db_manager.get_tax_history(test_apn)
            updated_sales_records = db_manager.get_sales_history(test_apn)
            
            print(f"   Updated tax records: {len(updated_tax_records) if isinstance(updated_tax_records, list) else updated_tax_records}")
            print(f"   Updated sales records: {len(updated_sales_records) if isinstance(updated_sales_records, list) else updated_sales_records}")
            
        except Exception as e:
            print(f"   [ERROR] Database verification error: {e}")
        
        print("\n" + "=" * 50)
        print("[COMPLETE] Data collection fix test completed!")
        print("Check the application to see if tax data now populates.")
        
        # Clean up
        api_client.close()
        db_manager.close()
        
    except Exception as e:
        print(f"\n[ERROR] Fix test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = fix_data_collection_issues()
    sys.exit(0 if success else 1)