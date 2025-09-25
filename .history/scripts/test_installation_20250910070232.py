#!/usr/bin/env python
"""
Test Installation Script
Verifies all components are properly installed
"""
import os
import sys
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))
    def test_imports():
    """Test all required imports"""
        print("Testing Python package imports...")

    packages = [
        ("pandas", "Data manipulation"),
        ("numpy", "Numerical computing"),
        ("matplotlib", "Plotting"),
        ("PyQt5", "GUI framework"),
        ("sqlalchemy", "Database ORM"),
        ("psycopg2", "PostgreSQL adapter"),
        ("selenium", "Web scraping"),
        ("requests", "HTTP requests"),
        ("bs4", "BeautifulSoup"),
        ("dotenv", "Environment variables"),
    ]

    failed = []
    for package, description in packages:
        try:
            __import__(package)
        print(f"  ✓ {package:<15} - {description}")
        except ImportError as e:
        print(f"  ✗ {package:<15} - FAILED: {e}")
            failed.append(package)

    return len(failed) == 0
    def test_database():
    """Test database connection"""
        print("\nTesting database connection...")

    try:
import psycopg2

        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="maricopa_properties",
            user="property_user",
            password="Maricopa2024!",
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"  ✓ PostgreSQL connected: {version}")

        # Check tables
        cursor.execute(
            """
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """
        )
        tables = cursor.fetchall()
        print(f"  ✓ Found {len(tables)} tables")

        conn.close()
        return True
    except Exception as e:
        print(f"  ✗ Database connection FAILED: {e}")
        return False
    def test_chromedriver():
    """Test ChromeDriver installation"""
        print("\nTesting ChromeDriver...")

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service

        driver_path = PROJECT_ROOT / "drivers" / "chromedriver.exe"

        if not driver_path.exists():
        print(f"  ✗ ChromeDriver not found at {driver_path}")
            return False

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        service = Service(str(driver_path))

        driver = webdriver.Chrome(service=service, options=options)
        driver.quit()
        print(f"  ✓ ChromeDriver working")
        return True
    except Exception as e:
        print(f"  ✗ ChromeDriver test FAILED: {e}")
        return False
    def test_api():
    """Test API connection"""
        print("\nTesting API connection...")

    try:
import requests

        headers = {
            "AUTHORIZATION": "ca1a11a6-adc4-4e0c-a584-36cbb6eb35e5",
            "user-agent": "null",
        }

        response = requests.get(
            "https://mcassessor.maricopa.gov/search/property/?q=test&page=1",
            headers=headers,
            timeout=10,
        )

        if response.status_code == 200:
        print(f"  ✓ API connection successful")
            return True
        else:
        print(f"  ✗ API returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ API connection FAILED: {e}")
        return False
    def test_directories():
    """Test directory structure"""
        print("\nChecking directory structure...")

    dirs = [
        "config",
        "scripts",
        "src",
        "logs",
        "exports",
        "cache",
        "drivers",
        "database",
    ]

    all_exist = True
    for dir_name in dirs:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
        print(f"  ✓ {dir_name}")
        else:
        print(f"  ✗ {dir_name} - MISSING")
            all_exist = False

    return all_exist
    def main():
        print("=" * 50)
        print("Maricopa Property Search - Installation Test")
        print("=" * 50)
        print()

    results = []

    # Run tests
    results.append(("Directory Structure", test_directories()))
    results.append(("Python Packages", test_imports()))
    results.append(("Database Connection", test_database()))
    results.append(("ChromeDriver", test_chromedriver()))
    results.append(("API Connection", test_api()))

    # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)

    all_passed = True
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {test_name:<25} {status}")
        if not passed:
            all_passed = False
        print()
    if all_passed:
        print("✓ All tests passed! Installation is complete.")
        print("You can now run: launch_app.bat")
    else:
        print("✗ Some tests failed. Please fix the issues above.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
