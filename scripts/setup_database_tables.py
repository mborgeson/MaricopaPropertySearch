#!/usr/bin/env python
"""
Setup database tables using SQL scripts
"""

import psycopg2
from psycopg2 import OperationalError
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")

try:
    # Connect to maricopa_properties as property_user
    connection = psycopg2.connect(
        host='localhost',
        port=5433,
        database='maricopa_properties',
        user='property_user',
        password='Wildcats777!!'
    )
    
    connection.autocommit = True
    cursor = connection.cursor()
    
    print("Connected to maricopa_properties as property_user")
    
    # Read and execute create_tables.sql
    sql_file = PROJECT_ROOT / "database" / "create_tables.sql"
    
    if sql_file.exists():
        print("Executing create_tables.sql...")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Execute SQL
        cursor.execute(sql_content)
        print("SUCCESS: Tables created")
        
        # Verify tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print("Database tables:")
        for table in tables:
            print(f"  - {table[0]}")
    else:
        print("ERROR: create_tables.sql not found")
    
    connection.close()
    
except Exception as e:
    print(f"ERROR: {e}")