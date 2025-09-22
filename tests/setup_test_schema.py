#!/usr/bin/env python3
"""
Test Schema Setup Script
Creates a separate test schema within the existing database for testing isolation
"""

import psycopg2
import sys
from pathlib import Path

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Database configuration - use existing database with test schema
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "user": "property_user",
    "password": "Wildcats777!!",
    "database": "maricopa_properties",  # Use existing database
    "test_schema": "test_data",  # Separate schema for test data
}


def create_test_schema():
    """Create test schema for isolated testing"""
    print("Creating test schema...")

    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
        )
        cursor = conn.cursor()

        # Create test schema
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {DB_CONFIG['test_schema']}")
        print(f"Created test schema: {DB_CONFIG['test_schema']}")

        # Set search path for test schema
        cursor.execute(f"SET search_path TO {DB_CONFIG['test_schema']}, public")

        conn.commit()
        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        print(f"Error creating test schema: {e}")
        return False


def setup_test_tables():
    """Create test tables in test schema"""
    print("Setting up test tables...")

    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
        )
        cursor = conn.cursor()

        # Set search path to test schema
        cursor.execute(f"SET search_path TO {DB_CONFIG['test_schema']}, public")

        # Create test properties table
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {DB_CONFIG['test_schema']}.properties (
                id SERIAL PRIMARY KEY,
                apn VARCHAR(20) UNIQUE NOT NULL,
                owner_name VARCHAR(255),
                property_address VARCHAR(255),
                city VARCHAR(100),
                zip_code VARCHAR(10),
                property_type VARCHAR(50),
                assessed_value INTEGER,
                market_value INTEGER,
                square_feet INTEGER,
                year_built INTEGER,
                bedrooms INTEGER,
                bathrooms DECIMAL(3,1),
                lot_size DECIMAL(8,3),
                legal_description TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_source VARCHAR(50) DEFAULT 'database',
                enhanced BOOLEAN DEFAULT FALSE,
                enhancement_timestamp TIMESTAMP
            )
        """
        )

        # Create test search history table
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {DB_CONFIG['test_schema']}.search_history (
                id SERIAL PRIMARY KEY,
                search_type VARCHAR(20) NOT NULL,
                search_term VARCHAR(255) NOT NULL,
                results_count INTEGER,
                search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_time_ms INTEGER
            )
        """
        )

        # Create test tax history table
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {DB_CONFIG['test_schema']}.tax_history (
                id SERIAL PRIMARY KEY,
                apn VARCHAR(20),
                tax_year INTEGER NOT NULL,
                assessed_value INTEGER,
                tax_amount DECIMAL(10,2),
                tax_status VARCHAR(50),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (apn) REFERENCES {DB_CONFIG['test_schema']}.properties(apn)
            )
        """
        )

        # Create test sales history table
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {DB_CONFIG['test_schema']}.sales_history (
                id SERIAL PRIMARY KEY,
                apn VARCHAR(20),
                sale_date DATE,
                sale_price INTEGER,
                deed_type VARCHAR(100),
                buyer_name VARCHAR(255),
                seller_name VARCHAR(255),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (apn) REFERENCES {DB_CONFIG['test_schema']}.properties(apn)
            )
        """
        )

        # Create test documents table
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {DB_CONFIG['test_schema']}.documents (
                id SERIAL PRIMARY KEY,
                apn VARCHAR(20),
                document_type VARCHAR(50),
                document_number VARCHAR(100),
                document_date DATE,
                document_url VARCHAR(500),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (apn) REFERENCES {DB_CONFIG['test_schema']}.properties(apn)
            )
        """
        )

        # Create indexes for performance
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_test_properties_apn ON {DB_CONFIG['test_schema']}.properties(apn)"
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_test_properties_owner ON {DB_CONFIG['test_schema']}.properties(owner_name)"
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_test_properties_address ON {DB_CONFIG['test_schema']}.properties(property_address)"
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_test_properties_city ON {DB_CONFIG['test_schema']}.properties(city)"
        )

        conn.commit()
        print("Test tables created successfully")

        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        print(f"Error setting up test tables: {e}")
        return False


def load_test_data():
    """Load test data including 10000 W Missouri Ave"""
    print("Loading test data...")

    test_properties = [
        {
            "apn": "101-01-001A",
            "owner_name": "SMITH, JOHN & JANE",
            "property_address": "123 MAIN ST",
            "city": "PHOENIX",
            "zip_code": "85001",
            "property_type": "RESIDENTIAL",
            "assessed_value": 250000,
            "market_value": 275000,
            "square_feet": 1800,
            "year_built": 1995,
        },
        {
            "apn": "301-07-042",  # 10000 W Missouri Ave - Critical test property
            "owner_name": "MISSOURI AVENUE LLC",
            "property_address": "10000 W MISSOURI AVE",
            "city": "PHOENIX",
            "zip_code": "85037",
            "property_type": "COMMERCIAL",
            "assessed_value": 850000,
            "market_value": 920000,
            "square_feet": 12500,
            "year_built": 1998,
        },
        {
            "apn": "102-02-001B",
            "owner_name": "JONES, ROBERT M",
            "property_address": "456 OAK AVE",
            "city": "TEMPE",
            "zip_code": "85281",
            "property_type": "RESIDENTIAL",
            "assessed_value": 320000,
            "market_value": 350000,
            "square_feet": 2100,
            "year_built": 2005,
        },
    ]

    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
        )
        cursor = conn.cursor()

        # Set search path to test schema
        cursor.execute(f"SET search_path TO {DB_CONFIG['test_schema']}, public")

        # Clear existing test data
        cursor.execute(f"TRUNCATE TABLE {DB_CONFIG['test_schema']}.tax_history CASCADE")
        cursor.execute(
            f"TRUNCATE TABLE {DB_CONFIG['test_schema']}.sales_history CASCADE"
        )
        cursor.execute(f"TRUNCATE TABLE {DB_CONFIG['test_schema']}.documents CASCADE")
        cursor.execute(
            f"TRUNCATE TABLE {DB_CONFIG['test_schema']}.search_history CASCADE"
        )
        cursor.execute(
            f"TRUNCATE TABLE {DB_CONFIG['test_schema']}.properties RESTART IDENTITY CASCADE"
        )

        # Insert test properties (simplified field list)
        for prop in test_properties:
            cursor.execute(
                f"""
                INSERT INTO {DB_CONFIG['test_schema']}.properties (
                    apn, owner_name, property_address, city, zip_code,
                    property_type, assessed_value, market_value, 
                    square_feet, year_built
                ) VALUES (
                    %(apn)s, %(owner_name)s, %(property_address)s, %(city)s, %(zip_code)s,
                    %(property_type)s, %(assessed_value)s, %(market_value)s,
                    %(square_feet)s, %(year_built)s
                )
            """,
                prop,
            )

        # Add tax history for 10000 W Missouri Ave
        cursor.execute(
            f"""
            INSERT INTO {DB_CONFIG['test_schema']}.tax_history (apn, tax_year, assessed_value, tax_amount, tax_status)
            VALUES 
                ('301-07-042', 2023, 850000, 12750.00, 'PAID'),
                ('301-07-042', 2022, 825000, 12375.00, 'PAID'),
                ('301-07-042', 2021, 800000, 12000.00, 'PAID')
        """
        )

        # Add sample sale for 10000 W Missouri Ave
        cursor.execute(
            f"""
            INSERT INTO {DB_CONFIG['test_schema']}.sales_history (apn, sale_date, sale_price, deed_type, buyer_name, seller_name)
            VALUES ('301-07-042', '2020-03-15', 750000, 'WARRANTY DEED', 'MISSOURI AVENUE LLC', 'PREVIOUS OWNER CORP')
        """
        )

        conn.commit()
        print(f"Loaded {len(test_properties)} test properties")
        print("Added tax and sales history for 10000 W Missouri Ave")

        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        print(f"Error loading test data: {e}")
        return False


def validate_test_setup():
    """Validate the test schema setup"""
    print("Validating test schema setup...")

    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
        )
        cursor = conn.cursor()

        # Set search path to test schema
        cursor.execute(f"SET search_path TO {DB_CONFIG['test_schema']}, public")

        # Check properties table
        cursor.execute(f"SELECT COUNT(*) FROM {DB_CONFIG['test_schema']}.properties")
        property_count = cursor.fetchone()[0]
        print(f"Properties table: {property_count} records")

        # Check 10000 W Missouri Ave specifically
        cursor.execute(
            f"SELECT apn, owner_name, property_address FROM {DB_CONFIG['test_schema']}.properties WHERE apn = '301-07-042'"
        )
        missouri_property = cursor.fetchone()
        if missouri_property:
            print(f"✓ Test property 10000 W Missouri Ave found: {missouri_property}")
        else:
            print("✗ Test property 10000 W Missouri Ave NOT found")

        # Check tax history
        cursor.execute(f"SELECT COUNT(*) FROM {DB_CONFIG['test_schema']}.tax_history")
        tax_count = cursor.fetchone()[0]
        print(f"Tax history records: {tax_count}")

        # Check sales history
        cursor.execute(f"SELECT COUNT(*) FROM {DB_CONFIG['test_schema']}.sales_history")
        sales_count = cursor.fetchone()[0]
        print(f"Sales history records: {sales_count}")

        cursor.close()
        conn.close()

        print("✓ Test schema validation complete")
        return True

    except psycopg2.Error as e:
        print(f"✗ Error validating test setup: {e}")
        return False


def get_test_config_info():
    """Print test configuration information for conftest.py"""
    print("\n" + "=" * 60)
    print("TEST CONFIGURATION FOR conftest.py")
    print("=" * 60)
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Test Schema: {DB_CONFIG['test_schema']}")
    print(
        f"Connection String: postgresql://{DB_CONFIG['user']}:***@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    print("\nUpdate your test configuration to use:")
    print(f"- Schema: {DB_CONFIG['test_schema']}")
    print("- Search Path: test_data, public")
    print("- Table References: test_data.properties, test_data.tax_history, etc.")
    print("\nExample conftest.py update:")
    print("config.config.set('database', 'database', 'maricopa_properties')")
    print("config.config.set('database', 'schema', 'test_data')")


def main():
    """Main setup function"""
    print("Maricopa Property Search - Test Schema Setup")
    print("=" * 50)

    # Step 1: Create test schema
    if not create_test_schema():
        print("Failed to create test schema")
        return False

    # Step 2: Setup test tables
    if not setup_test_tables():
        print("Failed to setup test tables")
        return False

    # Step 3: Load test data
    if not load_test_data():
        print("Failed to load test data")
        return False

    # Step 4: Validate setup
    if not validate_test_setup():
        print("Failed to validate test setup")
        return False

    # Step 5: Provide configuration info
    get_test_config_info()

    print("\n✓ Test schema setup completed successfully!")
    print(
        f"✓ Test schema: {DB_CONFIG['test_schema']} in database {DB_CONFIG['database']}"
    )
    print("✓ Schema created with all required tables")
    print("✓ Test data loaded including 10000 W Missouri Ave")
    print("✓ Ready for automated testing")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
