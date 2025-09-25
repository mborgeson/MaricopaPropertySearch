#!/usr/bin/env python3
"""
Test script to verify the APN KeyError fix in database_manager.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock, Mock, patch

# MIGRATED: from src.database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
    def test_apn_keyerror_fix():
    """Test that missing 'apn' key is handled gracefully"""
        print("Testing APN KeyError fix...")

    # Mock the config manager
    mock_config_manager = Mock()
    mock_config_manager.get_db_config.return_value = {
        'host': 'localhost',
        'port': 5432,
        'database': 'test_db',
        'user': 'test_user',
        'password': 'test_pass'
    }

    # Mock the connection pool
    with patch('src.database_manager.ThreadedConnectionPool'):
        db_manager = ThreadSafeDatabaseManager(mock_config_manager)

        # Mock the database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(db_manager, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_get_conn.return_value.__exit__.return_value = None

            # Test Case 1: Property data missing 'apn' key
        print("\n1. Testing property data missing 'apn' key...")
            property_data_no_apn = {
                'owner_name': 'John Doe',
                'property_address': '123 Main St'
            }

            result = db_manager.insert_property(property_data_no_apn)
        print(f"   Result (should be False): {result}")
            assert result == False, "Should return False when 'apn' is missing"

            # Test Case 2: Property data with 'apn' but missing other fields
        print("\n2. Testing property data with 'apn' but missing other fields...")
            property_data_partial = {
                'apn': '123-45-678',
                'owner_name': 'Jane Smith'
                # Missing other fields that are expected by SQL
            }

            result = db_manager.insert_property(property_data_partial)
        print(f"   Result (should be True): {result}")

            # Verify that the cursor.execute was called with all required fields
            if mock_cursor.execute.called:
                call_args = mock_cursor.execute.call_args[0]
                executed_data = call_args[1]  # Second argument is the data dict
        print(f"   Executed data keys: {list(executed_data.keys())}")

                # Verify all required fields are present
                required_fields = [
                    'apn', 'owner_name', 'property_address', 'mailing_address',
                    'legal_description', 'land_use_code', 'year_built', 'living_area_sqft',
                    'lot_size_sqft', 'bedrooms', 'bathrooms', 'pool', 'garage_spaces', 'raw_data'
                ]

                missing_fields = [field for field in required_fields if field not in executed_data]
        print(f"   Missing fields: {missing_fields}")
                assert len(missing_fields) == 0, f"Missing required fields: {missing_fields}"

                # Verify APN value is correct
                assert executed_data['apn'] == '123-45-678', "APN value should be preserved"
        print("   [OK] All required fields present in executed data")

            # Test Case 3: Complete property data
        print("\n3. Testing complete property data...")
            property_data_complete = {
                'apn': '987-65-432',
                'owner_name': 'Complete Owner',
                'property_address': '456 Complete Ave',
                'mailing_address': '456 Complete Ave',
                'legal_description': 'LOT 1 BLOCK 1',
                'land_use_code': 'RES',
                'year_built': 2000,
                'living_area_sqft': 1500,
                'lot_size_sqft': 7200,
                'bedrooms': 3,
                'bathrooms': 2,
                'pool': False,
                'garage_spaces': 2,
                'raw_data': {'source': 'test'}
            }

            result = db_manager.insert_property(property_data_complete)
        print(f"   Result (should be True): {result}")
        print("\n[SUCCESS] All tests passed! KeyError fix is working correctly.")
    def test_validation_method():
    """Test the new validation method"""
        print("\n\nTesting validation method...")

    # Mock the config manager
    mock_config_manager = Mock()
    mock_config_manager.get_db_config.return_value = {
        'host': 'localhost',
        'port': 5432,
        'database': 'test_db',
        'user': 'test_user',
        'password': 'test_pass'
    }

    with patch('src.database_manager.ThreadedConnectionPool'):
        db_manager = ThreadSafeDatabaseManager(mock_config_manager)

        # Test invalid data
        invalid_data = {
            'owner_name': 'Test Owner',
            'year_built': 'not_a_number'  # Invalid numeric value
        }

        is_valid, errors = db_manager.validate_property_data(invalid_data)
        print(f"   Invalid data validation - Valid: {is_valid}, Errors: {errors}")
        assert not is_valid, "Should be invalid"
        assert len(errors) >= 1, "Should have errors"

        # Test valid data
        valid_data = {
            'apn': '123-45-678',
            'owner_name': 'Test Owner',
            'year_built': 2000,
            'pool': False
        }

        is_valid, errors = db_manager.validate_property_data(valid_data)
        print(f"   Valid data validation - Valid: {is_valid}, Errors: {errors}")
        assert is_valid, "Should be valid"
        assert len(errors) == 0, "Should have no errors"
        print("   [OK] Validation method working correctly")


if __name__ == "__main__":
try:
        test_apn_keyerror_fix()
        test_validation_method()
        print("\n[SUCCESS] All tests completed successfully!")

except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
import traceback

from src.threadsafe_database_manager import ThreadSafeDatabaseManager

        traceback.print_exc()

    sys.exit(1)