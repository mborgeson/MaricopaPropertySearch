#!/usr/bin/env python
"""
Test PostgreSQL database connection
"""
import sys
from pathlib import Path

import psycopg2
from psycopg2 import OperationalError

# Add project root to path
PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    # MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
from src.enhanced_config_manager import EnhancedConfigManager

    config = EnhancedConfigManager()
    db_config = config.get_db_config()
        print("Testing PostgreSQL connection...")
        print(f"Host: {db_config['host']}")
        print(f"Port: {db_config['port']}")
        print(f"Database: {db_config['database']}")
        print(f"User: {db_config['user']}")
    
    # Test connection
    connection = psycopg2.connect(
        host=db_config['host'],
        port=db_config['port'],
        database='postgres',  # Connect to default database first
        user='postgres',
        password=db_config['password']
    )
    
    cursor = connection.cursor()
    
    # Check if our database exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_config['database'],))
    db_exists = cursor.fetchone()
    
    if db_exists:
        print(f"SUCCESS: Database '{db_config['database']}' exists")
        
        # Connect to our database
        connection.close()
        connection = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = connection.cursor()
        
        # Check tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        if tables:
        print("SUCCESS: Database tables found:")
            for table in tables:
        print(f"  - {table[0]}")
        else:
        print("WARNING: No tables found in database")
            
    else:
        print(f"ERROR: Database '{db_config['database']}' does not exist")
    
    connection.close()
        print("SUCCESS: Connection test successful")
    
except OperationalError as e:
        print(f"ERROR: Connection failed: {e}")
        print("Attempting to connect as postgres user...")
    
try:
        connection = psycopg2.connect(
            host='localhost',
            port=5433,
            database='postgres',
            user='postgres',
            password='Wildcats777!!'
        )
        print("SUCCESS: Connected as postgres user")
        connection.close()
        
except OperationalError as e2:
        print(f"ERROR: Even postgres connection failed: {e2}")
        
except Exception as e:
        print(f"ERROR: Unexpected error: {e}")