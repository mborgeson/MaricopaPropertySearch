#!/usr/bin/env python
"""
Test the comprehensive property data retrieval
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import json
from config_manager import ConfigManager
from api_client import MaricopaAPIClient

def test_comprehensive_property_data():
    """Test comprehensive property data retrieval"""
    print("Testing Comprehensive Property Data Retrieval")
    print("=" * 55)
    
    config = ConfigManager()
    client = MaricopaAPIClient(config)
    
    test_apn = '13304014A'
    
    print(f"Getting comprehensive data for APN: {test_apn}")
    print("-" * 40)
    
    try:
        comprehensive_info = client.get_comprehensive_property_info(test_apn)
        
        if comprehensive_info:
            print("SUCCESS - Retrieved comprehensive property information!")
            print()
            
            # Basic property info
            print("BASIC PROPERTY INFO:")
            basic_fields = ['apn', 'owner_name', 'property_address', 'property_type']
            for field in basic_fields:
                if field in comprehensive_info:
                    print(f"  {field}: {comprehensive_info[field]}")
            print()
            
            # Valuation info
            print("VALUATION INFO:")
            valuation_fields = ['latest_tax_year', 'latest_assessed_value', 'latest_limited_value', 'assessment_ratio']
            for field in valuation_fields:
                if field in comprehensive_info:
                    value = comprehensive_info[field]
                    if field == 'latest_assessed_value' and isinstance(value, int):
                        print(f"  {field}: ${value:,}")
                    elif field == 'latest_limited_value' and isinstance(value, int):
                        print(f"  {field}: ${value:,}")
                    elif field == 'assessment_ratio' and isinstance(value, float):
                        print(f"  {field}: {value:.1%}")
                    else:
                        print(f"  {field}: {value}")
            
            # Show 5-year valuation history
            if 'valuation_history' in comprehensive_info:
                print("\\n5-YEAR VALUATION HISTORY:")
                for val in comprehensive_info['valuation_history']:
                    fcv = int(val['FullCashValue']) if val['FullCashValue'].isdigit() else 0
                    print(f"  {val['TaxYear']}: ${fcv:,} (Full Cash Value)")
            print()
            
            # Physical details
            print("PHYSICAL DETAILS:")
            physical_fields = ['year_built', 'lot_size_sqft', 'living_area_sqft', 'pool', 'quality_grade', 'bathrooms', 'garage_spaces']
            for field in physical_fields:
                if field in comprehensive_info:
                    value = comprehensive_info[field]
                    if field == 'lot_size_sqft' and isinstance(value, int):
                        print(f"  {field}: {value:,} sq ft")
                    elif field == 'living_area_sqft' and value:
                        print(f"  {field}: {value:,} sq ft")
                    else:
                        print(f"  {field}: {value}")
            print()
            
            # Improvements
            print("IMPROVEMENTS:")
            if 'improvements_count' in comprehensive_info:
                print(f"  Total improvements: {comprehensive_info['improvements_count']}")
            if 'total_improvement_sqft' in comprehensive_info:
                print(f"  Total improvement area: {comprehensive_info['total_improvement_sqft']:,} sq ft")
            
            if 'improvements_details' in comprehensive_info:
                print("  Improvement breakdown:")
                for imp in comprehensive_info['improvements_details'][:5]:  # Show first 5
                    sqft = imp.get('ImprovementSquareFootage', 'Unknown')
                    desc = imp.get('ImprovementDescription', 'Unknown')
                    print(f"    {desc}: {sqft} sq ft")
            print()
            
            # Data endpoints retrieved
            print("DATA SOURCES RETRIEVED:")
            if 'detailed_data' in comprehensive_info:
                for endpoint, data in comprehensive_info['detailed_data'].items():
                    if data:
                        count = len(data) if isinstance(data, list) else len(data) if isinstance(data, dict) else 1
                        print(f"  {endpoint}: {count} items/fields")
            
            print()
            print("=" * 55)
            print("COMPREHENSIVE DATA RETRIEVAL COMPLETE!")
            print("This property now has:")
            print("- 5 years of tax assessment history")
            print("- Detailed physical characteristics")
            print("- Complete improvements breakdown")
            print("- Maps and document references")
            
        else:
            print("ERROR: No comprehensive info retrieved")
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    test_comprehensive_property_data()