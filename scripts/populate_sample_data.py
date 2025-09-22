#!/usr/bin/env python
"""
Populate database with real Maricopa County property samples for testing
This uses real property data format but sample records for demonstration
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
# MIGRATED: from database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.enhanced_config_manager import EnhancedConfigManager


def populate_sample_properties():
    """Add real-format sample properties for testing"""

    config = EnhancedConfigManager()
    db = ThreadSafeDatabaseManager(config)

    # Real-format sample properties (based on typical Maricopa County data)
    sample_properties = [
        {
            "apn": "117-01-001A",
            "owner_name": "SMITH JOHN & MARY",
            "property_address": "1811 E APACHE BLVD, TEMPE, AZ 85281",
            "mailing_address": "1811 E APACHE BLVD, TEMPE, AZ 85281",
            "legal_description": "LOT 1 APACHE ESTATES SUBDIVISION",
            "land_use_code": "R1",
            "year_built": 2005,
            "living_area_sqft": 2450,
            "lot_size_sqft": 8500,
            "bedrooms": 4,
            "bathrooms": 2.5,
            "pool": True,
            "garage_spaces": 2,
            "raw_data": {"source": "sample_data", "populated_for_testing": True},
        },
        {
            "apn": "117-02-001B",
            "owner_name": "APACHE BOULEVARD PROPERTY LLC",
            "property_address": "1815 E APACHE BLVD, TEMPE, AZ 85281",
            "mailing_address": "PO BOX 12345, PHOENIX, AZ 85001",
            "legal_description": "LOT 2 APACHE ESTATES SUBDIVISION",
            "land_use_code": "R1",
            "year_built": 2008,
            "living_area_sqft": 2850,
            "lot_size_sqft": 9200,
            "bedrooms": 5,
            "bathrooms": 3.0,
            "pool": True,
            "garage_spaces": 3,
            "raw_data": {"source": "sample_data", "populated_for_testing": True},
        },
        {
            "apn": "117-03-001C",
            "owner_name": "TEMPE HOLDINGS INC",
            "property_address": "1821 E APACHE BLVD, TEMPE, AZ 85281",
            "mailing_address": "1821 E APACHE BLVD, TEMPE, AZ 85281",
            "legal_description": "LOT 3 APACHE ESTATES SUBDIVISION",
            "land_use_code": "R1",
            "year_built": 2003,
            "living_area_sqft": 2200,
            "lot_size_sqft": 7800,
            "bedrooms": 3,
            "bathrooms": 2.0,
            "pool": False,
            "garage_spaces": 2,
            "raw_data": {"source": "sample_data", "populated_for_testing": True},
        },
        {
            "apn": "118-01-001A",
            "owner_name": "JOHNSON FAMILY TRUST",
            "property_address": "2001 E UNIVERSITY DR, TEMPE, AZ 85281",
            "mailing_address": "2001 E UNIVERSITY DR, TEMPE, AZ 85281",
            "legal_description": "LOT 1 UNIVERSITY HEIGHTS SUBDIVISION",
            "land_use_code": "R1",
            "year_built": 2010,
            "living_area_sqft": 3200,
            "lot_size_sqft": 10500,
            "bedrooms": 5,
            "bathrooms": 4.0,
            "pool": True,
            "garage_spaces": 3,
            "raw_data": {"source": "sample_data", "populated_for_testing": True},
        },
        {
            "apn": "119-01-001A",
            "owner_name": "MILLER ROBERT L",
            "property_address": "3456 E MAIN ST, PHOENIX, AZ 85008",
            "mailing_address": "3456 E MAIN ST, PHOENIX, AZ 85008",
            "legal_description": "LOT 15 PHOENIX MEADOWS SUBDIVISION",
            "land_use_code": "R1",
            "year_built": 1998,
            "living_area_sqft": 1850,
            "lot_size_sqft": 6500,
            "bedrooms": 3,
            "bathrooms": 2.0,
            "pool": False,
            "garage_spaces": 2,
            "raw_data": {"source": "sample_data", "populated_for_testing": True},
        },
    ]

    # Sample tax history
    sample_tax_history = [
        {
            "apn": "117-01-001A",
            "tax_year": 2024,
            "assessed_value": 485000.00,
            "limited_value": 465000.00,
            "tax_amount": 4850.25,
            "payment_status": "PAID",
            "last_payment_date": "2024-10-15",
            "raw_data": {"source": "sample_data"},
        },
        {
            "apn": "117-01-001A",
            "tax_year": 2023,
            "assessed_value": 465000.00,
            "limited_value": 445000.00,
            "tax_amount": 4650.75,
            "payment_status": "PAID",
            "last_payment_date": "2023-11-20",
            "raw_data": {"source": "sample_data"},
        },
        {
            "apn": "117-02-001B",
            "tax_year": 2024,
            "assessed_value": 525000.00,
            "limited_value": 505000.00,
            "tax_amount": 5250.00,
            "payment_status": "PAID",
            "last_payment_date": "2024-12-01",
            "raw_data": {"source": "sample_data"},
        },
    ]

    # Sample sales history
    sample_sales_history = [
        {
            "apn": "117-01-001A",
            "sale_date": "2020-03-15",
            "sale_price": 425000.00,
            "seller_name": "PREVIOUS OWNER LLC",
            "buyer_name": "SMITH JOHN & MARY",
            "deed_type": "WARRANTY DEED",
            "recording_number": "DOC-2020-0315001",
        },
        {
            "apn": "117-02-001B",
            "sale_date": "2019-07-22",
            "sale_price": 475000.00,
            "seller_name": "BUILDER HOMES INC",
            "buyer_name": "APACHE BOULEVARD PROPERTY LLC",
            "deed_type": "WARRANTY DEED",
            "recording_number": "DOC-2019-0722001",
        },
    ]

    print("Populating database with sample property data...")

    # Insert properties
    success_count = 0
    for property_data in sample_properties:
        if db.insert_property(property_data):
            success_count += 1
            print(
                f"✓ Inserted property: {property_data['apn']} - {property_data['property_address']}"
            )
        else:
            print(f"✗ Failed to insert property: {property_data['apn']}")

    print(f"\nProperties inserted: {success_count}/{len(sample_properties)}")

    # Insert tax history
    tax_success = 0
    for tax_data in sample_tax_history:
        if db.insert_tax_history(tax_data):
            tax_success += 1

    print(f"Tax records inserted: {tax_success}/{len(sample_tax_history)}")

    # Insert sales history
    sales_success = 0
    for sales_data in sample_sales_history:
        if db.insert_sales_history(sales_data):
            sales_success += 1

    print(f"Sales records inserted: {sales_success}/{len(sample_sales_history)}")

    db.close()

    print(f"\n🎉 Sample data population complete!")
    print(f"✓ {success_count} properties available for search testing")
    print(f"✓ Database now has real-format property data")
    print(f"\nTest searches:")
    print(f"- Owner: 'SMITH' or 'APACHE' or 'JOHNSON'")
    print(f"- Address: '1811 E APACHE' or 'UNIVERSITY DR' or 'MAIN ST'")
    print(f"- APN: '117-01-001A' or '118-01-001A'")


if __name__ == "__main__":
    populate_sample_properties()
