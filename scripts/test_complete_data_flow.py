#!/usr/bin/env python3
"""
Test complete data flow: API -> Database -> Retrieval
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))

# MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
# MIGRATED: from src.api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
# MIGRATED: from src.database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
import json
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.enhanced_config_manager import EnhancedConfigManager

def test_complete_data_flow(test_apn='13304019'):
    """Test complete data flow for an APN"""

    print(f'Testing complete data flow for APN: {test_apn}')
    print('=' * 50)

    config_manager = EnhancedConfigManager()
    api_client = UnifiedMaricopaAPIClient(config_manager)
    db_manager = ThreadSafeDatabaseManager(config_manager)

    print('1. Getting tax data from API...')
    tax_data = api_client.get_tax_history(test_apn, years=3)
    print(f'   Retrieved {len(tax_data) if tax_data else 0} tax records')

    if tax_data and len(tax_data) > 0:
        print('2. Converting and inserting tax data...')
        inserted_count = 0

        for record in tax_data:
            # Convert API format to database format
            db_record = {
                'apn': test_apn,
                'tax_year': int(record.get('TaxYear', 0)),
                'assessed_value': float(record.get('FullCashValue', 0)) if record.get('FullCashValue') != 'na' else None,
                'limited_value': None,  # Parse from LimitedPropertyValue if needed
                'tax_amount': None,     # Not available in this endpoint
                'payment_status': None, # Not available in this endpoint
                'last_payment_date': None,
                'raw_data': json.dumps(record)  # Convert to JSON string
            }

            if db_record['tax_year'] > 0:
                success = db_manager.insert_tax_history(db_record)
                if success:
                    inserted_count += 1
                    print(f'   ✓ Inserted tax record for year {db_record["tax_year"]}')
                else:
                    print(f'   ✗ Failed to insert tax record for year {db_record["tax_year"]}')

        print(f'3. Successfully inserted {inserted_count}/{len(tax_data)} tax records')

        # Verify retrieval
        print('4. Verifying data retrieval...')
        retrieved_data = db_manager.get_tax_history(test_apn)
        print(f'   Retrieved {len(retrieved_data)} tax records from database')

        if len(retrieved_data) > 0:
            print('')
            print('✅ COMPLETE DATA FLOW WORKING!')
            print('Sample retrieved record:')
            sample = retrieved_data[0]
            print(f'  Year: {sample.get("tax_year")}')
            print(f'  Assessed Value: ${sample.get("assessed_value", "N/A")}')
            print('')
            print('CONCLUSION: The system CAN collect and store data.')
            print('ISSUE: This process is not being triggered by the UI.')
            print('')
            print('NEXT STEPS:')
            print('1. Open the application UI')
            print('2. Search for a property')
            print('3. Open PropertyDetailsDialog')
            print('4. Check if tax/sales tabs now show data')
            print('5. If not, debug why auto-collection is not working')

            return True
        else:
            print('   ❌ Data insertion failed')
            return False
    else:
        print('   No tax data available to test with')
        return False

if __name__ == "__main__":
    test_apn = sys.argv[1] if len(sys.argv) > 1 else "13304019"
    success = test_complete_data_flow(test_apn)

    if success:
        print('\n🎉 SUCCESS: Data collection and storage pipeline is working!')
    else:
        print('\n❌ FAILURE: Data collection pipeline has issues')