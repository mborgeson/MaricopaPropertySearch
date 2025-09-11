#!/usr/bin/env python3
"""
Test Database Setup Script
Creates and configures the test database for the Maricopa Property Search application
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
from pathlib import Path

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'property_user',
    'password': 'Wildcats777!!',
    'production_db': 'maricopa_properties',
    'test_db': 'maricopa_test'
}

def create_test_database():
    """Create the test database if it doesn't exist"""
    print("Creating test database...")
    
    try:
        # Connect to PostgreSQL server (not specific database)
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database='postgres'  # Connect to default database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if test database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", 
                      (DB_CONFIG['test_db'],))
        exists = cursor.fetchone()
        
        if exists:
            print(f"Test database '{DB_CONFIG['test_db']}' already exists")
            # Drop and recreate for clean state
            cursor.execute(f"DROP DATABASE {DB_CONFIG['test_db']}")
            print(f"Dropped existing test database")
        
        # Create test database
        cursor.execute(f"CREATE DATABASE {DB_CONFIG['test_db']}")
        print(f"Created test database: {DB_CONFIG['test_db']}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"Error creating test database: {e}")
        return False

def setup_test_schema():
    """Create tables and schema in test database"""
    print("Setting up test database schema...")
    
    try:
        # Connect to test database
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['test_db']
        )
        cursor = conn.cursor()
        
        # Create properties table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
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
        """)
        
        # Create search history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id SERIAL PRIMARY KEY,
                search_type VARCHAR(20) NOT NULL,
                search_term VARCHAR(255) NOT NULL,
                results_count INTEGER,
                search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_time_ms INTEGER
            )
        """)
        
        # Create tax history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tax_history (
                id SERIAL PRIMARY KEY,
                apn VARCHAR(20) REFERENCES properties(apn),
                tax_year INTEGER NOT NULL,
                assessed_value INTEGER,
                tax_amount DECIMAL(10,2),
                tax_status VARCHAR(50),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create sales history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales_history (
                id SERIAL PRIMARY KEY,
                apn VARCHAR(20) REFERENCES properties(apn),
                sale_date DATE,
                sale_price INTEGER,
                deed_type VARCHAR(100),
                buyer_name VARCHAR(255),
                seller_name VARCHAR(255),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                apn VARCHAR(20) REFERENCES properties(apn),
                document_type VARCHAR(50),
                document_number VARCHAR(100),
                document_date DATE,
                document_url VARCHAR(500),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_properties_apn ON properties(apn)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_properties_owner ON properties(owner_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_properties_address ON properties(property_address)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_properties_city ON properties(city)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_history_timestamp ON search_history(search_timestamp)")
        
        conn.commit()
        print("Database schema created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"Error setting up test schema: {e}")
        return False

def load_test_data():
    """Load test data including 10000 W Missouri Ave"""
    print("Loading test data...")
    
    test_properties = [
        {
            'apn': '101-01-001A',
            'owner_name': 'SMITH, JOHN & JANE',
            'property_address': '123 MAIN ST',
            'city': 'PHOENIX',
            'zip_code': '85001',
            'property_type': 'RESIDENTIAL',
            'assessed_value': 250000,
            'market_value': 275000,
            'square_feet': 1800,
            'year_built': 1995,
            'bedrooms': 3,
            'bathrooms': 2.0,
            'lot_size': 0.25
        },
        {
            'apn': '301-07-042',  # 10000 W Missouri Ave - Critical test property
            'owner_name': 'MISSOURI AVENUE LLC',
            'property_address': '10000 W MISSOURI AVE',
            'city': 'PHOENIX',
            'zip_code': '85037',
            'property_type': 'COMMERCIAL',
            'assessed_value': 850000,
            'market_value': 920000,
            'square_feet': 12500,
            'year_built': 1998,
            'lot_size': 2.15
        },
        {
            'apn': '102-02-001B',
            'owner_name': 'JONES, ROBERT M',
            'property_address': '456 OAK AVE',
            'city': 'TEMPE',
            'zip_code': '85281',
            'property_type': 'RESIDENTIAL',
            'assessed_value': 320000,
            'market_value': 350000,
            'square_feet': 2100,
            'year_built': 2005,
            'bedrooms': 4,
            'bathrooms': 2.5,
            'lot_size': 0.30
        },
        {
            'apn': '103-03-001C',
            'owner_name': 'WILLIAMS, MARY E',
            'property_address': '789 PINE ST',
            'city': 'SCOTTSDALE',
            'zip_code': '85251',
            'property_type': 'RESIDENTIAL',
            'assessed_value': 480000,
            'market_value': 525000,
            'square_feet': 2800,
            'year_built': 2010,
            'bedrooms': 4,
            'bathrooms': 3.0,
            'lot_size': 0.40
        },
        {
            'apn': '104-04-001D',
            'owner_name': 'BROWN ENTERPRISES LLC',
            'property_address': '1000 BUSINESS BLVD',
            'city': 'PHOENIX',
            'zip_code': '85004',
            'property_type': 'COMMERCIAL',
            'assessed_value': 1200000,
            'market_value': 1350000,
            'square_feet': 8500,
            'year_built': 1985
        },
        {
            'apn': '105-05-001E',
            'owner_name': 'VACANT LAND TRUST',
            'property_address': 'DESERT VISTA RD',
            'city': 'PHOENIX',
            'zip_code': '85048',
            'property_type': 'VACANT LAND',
            'assessed_value': 75000,
            'market_value': 85000,
            'lot_size': 1.50
        }
    ]
    
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['test_db']
        )
        cursor = conn.cursor()
        
        for prop in test_properties:
            cursor.execute("""
                INSERT INTO properties (
                    apn, owner_name, property_address, city, zip_code,
                    property_type, assessed_value, market_value, 
                    square_feet, year_built, bedrooms, bathrooms, lot_size
                ) VALUES (
                    %(apn)s, %(owner_name)s, %(property_address)s, %(city)s, %(zip_code)s,
                    %(property_type)s, %(assessed_value)s, %(market_value)s,
                    %(square_feet)s, %(year_built)s, %(bedrooms)s, %(bathrooms)s, %(lot_size)s
                )
            """, prop)
        
        # Add some tax history for 10000 W Missouri Ave
        cursor.execute("""
            INSERT INTO tax_history (apn, tax_year, assessed_value, tax_amount, tax_status)
            VALUES 
                ('301-07-042', 2023, 850000, 12750.00, 'PAID'),
                ('301-07-042', 2022, 825000, 12375.00, 'PAID'),
                ('301-07-042', 2021, 800000, 12000.00, 'PAID')
        """)
        
        # Add a sample sale for 10000 W Missouri Ave
        cursor.execute("""
            INSERT INTO sales_history (apn, sale_date, sale_price, deed_type, buyer_name, seller_name)
            VALUES ('301-07-042', '2020-03-15', 750000, 'WARRANTY DEED', 'MISSOURI AVENUE LLC', 'PREVIOUS OWNER CORP')
        """)
        
        conn.commit()
        print(f"Loaded {len(test_properties)} test properties")
        print("Added tax and sales history for test property")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"Error loading test data: {e}")
        return False

def validate_test_setup():
    """Validate the test database setup"""
    print("Validating test database setup...")
    
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['test_db']
        )
        cursor = conn.cursor()
        
        # Check properties table
        cursor.execute("SELECT COUNT(*) FROM properties")
        property_count = cursor.fetchone()[0]
        print(f"Properties table: {property_count} records")
        
        # Check 10000 W Missouri Ave specifically
        cursor.execute("SELECT apn, owner_name, property_address FROM properties WHERE apn = '301-07-042'")
        missouri_property = cursor.fetchone()
        if missouri_property:
            print(f"✓ Test property 10000 W Missouri Ave found: {missouri_property}")
        else:
            print("✗ Test property 10000 W Missouri Ave NOT found")
        
        # Check tax history
        cursor.execute("SELECT COUNT(*) FROM tax_history")
        tax_count = cursor.fetchone()[0]
        print(f"Tax history records: {tax_count}")
        
        # Check sales history
        cursor.execute("SELECT COUNT(*) FROM sales_history")
        sales_count = cursor.fetchone()[0]
        print(f"Sales history records: {sales_count}")
        
        cursor.close()
        conn.close()
        
        print("✓ Test database validation complete")
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error validating test setup: {e}")
        return False

def main():
    """Main setup function"""
    print("Maricopa Property Search - Test Database Setup")
    print("=" * 50)
    
    # Step 1: Create test database
    if not create_test_database():
        print("Failed to create test database")
        return False
    
    # Step 2: Setup schema
    if not setup_test_schema():
        print("Failed to setup test schema")
        return False
    
    # Step 3: Load test data
    if not load_test_data():
        print("Failed to load test data")
        return False
    
    # Step 4: Validate setup
    if not validate_test_setup():
        print("Failed to validate test setup")
        return False
    
    print("\n✓ Test database setup completed successfully!")
    print(f"✓ Test database: {DB_CONFIG['test_db']}")
    print("✓ Schema created with all required tables")
    print("✓ Test data loaded including 10000 W Missouri Ave")
    print("✓ Ready for automated testing")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)