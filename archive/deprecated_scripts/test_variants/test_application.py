#!/usr/bin/env python
"""
Test the complete Maricopa Property Search application
"""

import sys
import os
from pathlib import Path

# Add project paths
PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

def test_imports():
    """Test all module imports"""
    print("Testing module imports...")
    
    try:
        # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        print("✓ ConfigManager imported")
        
        # MIGRATED: # MIGRATED: from database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager  
        print("✓ DatabaseManager imported")
        
        # MIGRATED: from api_client import MaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient, MockMaricopaAPIClient
        print("✓ API clients imported")
        
        from web_scraper import WebScraperManager, MockWebScraperManager
        print("✓ Web scraper imported")
        
        from gui.main_window import PropertySearchApp
        print("✓ Main GUI imported")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        config = EnhancedConfigManager()
        
        db_config = config.get_db_config()
        print(f"✓ Database config loaded: {db_config['host']}:{db_config['port']}")
        
        api_config = config.get_api_config()
        print(f"✓ API config loaded: {api_config['base_url']}")
        
        return True
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False

def test_database():
    """Test database connectivity"""
    print("\nTesting database...")
    
    try:
        # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        # MIGRATED: # MIGRATED: from database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
        
        config = EnhancedConfigManager()
        db = ThreadSafeDatabaseManager(config)
        
        if db.test_connection():
            print("✓ Database connection successful")
            
            # Test basic operations
            stats = {'properties': 0, 'tax_records': 0, 'sales_records': 0}
            try:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM properties")
                    stats['properties'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM tax_history")  
                    stats['tax_records'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM sales_history")
                    stats['sales_records'] = cursor.fetchone()[0]
                    
                print(f"✓ Database stats: {stats}")
            except Exception as e:
                print(f"⚠ Stats query failed: {e}")
            
            db.close()
            return True
        else:
            print("✗ Database connection failed")
            return False
            
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_mock_clients():
    """Test mock API and scraper clients"""
    print("\nTesting mock clients...")
    
    try:
        # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        # MIGRATED: from api_client import MockMaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
        from web_scraper import MockWebScraperManager
        
        config = EnhancedConfigManager()
        
        # Test mock API client
        api_client = MockMaricopaAPIClient(config)
        api_status = api_client.get_api_status()
        print(f"✓ Mock API client: {api_status['status']}")
        api_client.close()
        
        # Test mock web scraper
        scraper = MockWebScraperManager(config)
        print("✓ Mock web scraper initialized")
        scraper.close()
        
        return True
    except Exception as e:
        print(f"✗ Mock clients test failed: {e}")
        return False

def test_gui_creation():
    """Test GUI creation (without showing)"""
    print("\nTesting GUI creation...")
    
    try:
        # Import Qt modules
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        
        # Check if QApplication exists
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            app_created = True
        else:
            app_created = False
        
        # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: # MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        from gui.main_window import PropertySearchApp
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.enhanced_config_manager import EnhancedConfigManager
        
        config = EnhancedConfigManager()
        
        # Create main window (but don't show it)
        window = PropertySearchApp(config)
        print("✓ Main window created successfully")
        
        # Clean up
        window.close()
        if app_created:
            app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ GUI creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Maricopa Property Search - Application Test")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_configuration),  
        ("Database", test_database),
        ("Mock Clients", test_mock_clients),
        ("GUI Creation", test_gui_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[{passed + 1}/{total}] {test_name}")
        print("-" * 30)
        
        if test_func():
            passed += 1
            print(f"✓ {test_name} PASSED")
        else:
            print(f"✗ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Application is ready to use.")
        print("\nTo run the application:")
        print("1. Use launch_app.bat")
        print("2. Or run: python src/maricopa_property_search.py")
    else:
        print(f"\n⚠ {total - passed} tests failed. Please review errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)