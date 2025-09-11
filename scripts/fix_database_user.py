#!/usr/bin/env python
"""
Fix PostgreSQL database user permissions
"""

import psycopg2
from psycopg2 import OperationalError
import sys

try:
    # Connect as postgres user
    connection = psycopg2.connect(
        host='localhost',
        port=5433,
        database='postgres',
        user='postgres',
        password='Wildcats777!!'
    )
    
    connection.autocommit = True
    cursor = connection.cursor()
    
    print("Connected as postgres user")
    
    # Check if property_user exists
    cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'property_user'")
    user_exists = cursor.fetchone()
    
    if user_exists:
        print("property_user exists, updating password...")
        cursor.execute("ALTER USER property_user WITH PASSWORD 'Wildcats777!!'")
    else:
        print("Creating property_user...")
        cursor.execute("CREATE USER property_user WITH PASSWORD 'Wildcats777!!'")
    
    # Grant privileges
    cursor.execute("GRANT ALL PRIVILEGES ON DATABASE maricopa_properties TO property_user")
    
    # Connect to maricopa_properties database
    connection.close()
    
    connection = psycopg2.connect(
        host='localhost',
        port=5433,
        database='maricopa_properties',
        user='postgres',
        password='Wildcats777!!'
    )
    
    connection.autocommit = True
    cursor = connection.cursor()
    
    # Grant schema privileges
    cursor.execute("GRANT ALL ON SCHEMA public TO property_user")
    cursor.execute("GRANT ALL ON ALL TABLES IN SCHEMA public TO property_user")
    cursor.execute("GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO property_user")
    
    print("SUCCESS: property_user setup complete")
    
    # Test connection as property_user
    connection.close()
    
    test_connection = psycopg2.connect(
        host='localhost',
        port=5433,
        database='maricopa_properties',
        user='property_user',
        password='Wildcats777!!'
    )
    
    test_cursor = test_connection.cursor()
    test_cursor.execute("SELECT current_user")
    current_user = test_cursor.fetchone()[0]
    print(f"SUCCESS: Connected as {current_user}")
    
    test_connection.close()
    
except Exception as e:
    print(f"ERROR: {e}")