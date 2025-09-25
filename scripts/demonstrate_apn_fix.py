#!/usr/bin/env python3
"""
Demonstration script showing the APN KeyError fix in action
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, patch

# MIGRATED: from src.database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
    def demonstrate_keyerror_fix():
    """Demonstrate how the KeyError fix handles various scenarios"""
        print("=== APN KeyError Fix Demonstration ===\n")

    # Mock the config manager
    mock_config_manager = Mock()
    mock_config_manager.get_db_config.return_value = {
        'host': 'localhost',
        'port': 5432,
        'database': 'test_db',
        'user': 'test_user',
        'password': 'test_pass'
    }
        print("Scenario 1: Property data missing 'apn' key (the original error)")
        print("-" * 60)

    # Mock the connection pool
    with patch('src.database_manager.ThreadedConnectionPool'):
        db_manager = ThreadSafeDatabaseManager(mock_config_manager)

        # Problematic data that would cause KeyError before fix
        problem_data = {
            'owner_name': 'John Doe',
            'property_address': '123 Main Street',
            'year_built': 1995
            # NOTE: No 'apn' field - this would cause KeyError: 'apn'
        }
        print(f"Input data: {problem_data}")
        print(f"Missing 'apn' field: {'apn' not in problem_data}")

        # This would throw KeyError before the fix
        result = db_manager.insert_property(problem_data)
        print(f"Result: {result} (gracefully handled - returns False instead of crashing)")
        print("\nScenario 2: Property data with 'apn' but other missing fields")
        print("-" * 60)

        # Mock the database connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(db_manager, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_get_conn.return_value.__exit__.return_value = None

            partial_data = {
                'apn': '123-45-678',
                'owner_name': 'Jane Smith',
                'property_address': '456 Oak Avenue'
                # Missing many other fields that SQL expects
            }
        print(f"Input data: {partial_data}")
            result = db_manager.insert_property(partial_data)
        print(f"Result: {result}")

            if mock_cursor.execute.called:
                executed_data = mock_cursor.execute.call_args[0][1]
        print(f"Data passed to SQL (shows all required fields): {list(executed_data.keys())}")
        print(f"APN value preserved: {executed_data.get('apn')}")
        print(f"Default values added for missing fields: {executed_data.get('bedrooms')} (bedrooms)")
        print("\nScenario 3: Using validation method")
        print("-" * 60)

        # Test validation
        invalid_data = {
            'owner_name': 'Test Owner'
            # Missing apn
        }

        is_valid, errors = db_manager.validate_property_data(invalid_data)
        print(f"Validation of data without APN: Valid={is_valid}, Errors={errors}")

        valid_data = {
            'apn': '789-12-345',
            'owner_name': 'Valid Owner',
            'year_built': 2000
        }

        is_valid, errors = db_manager.validate_property_data(valid_data)
        print(f"Validation of data with APN: Valid={is_valid}, Errors={errors}")
        print("\n=== Fix Summary ===")
        print("1. Before fix: KeyError: 'apn' would crash the application")
        print("2. After fix: Missing 'apn' is detected and handled gracefully")
        print("3. Missing other fields are filled with default values (None)")
        print("4. Validation method helps catch issues before database operations")
        print("5. Comprehensive logging helps with debugging")


if __name__ == "__main__":
try:
        demonstrate_keyerror_fix()
except Exception as e:
        print(f"[ERROR] Demonstration failed: {e}")
import traceback

from src.threadsafe_database_manager import ThreadSafeDatabaseManager

        traceback.print_exc()

    sys.exit(1)