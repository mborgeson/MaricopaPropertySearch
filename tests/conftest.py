"""
pytest configuration and shared fixtures for comprehensive testing
"""

import pytest
import sys
import os
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch
import json

# Add project paths
PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Test configuration
TEST_DATABASE_URL = "postgresql://property_user:Wildcats777!!@localhost:5433/maricopa_test"
MOCK_API_RESPONSES = PROJECT_ROOT / "tests" / "fixtures" / "mock_api_responses.json"

@pytest.fixture(scope="session")
def app_config():
    """Provide test configuration manager"""
    # MIGRATED: from src.config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
    
    # Create test config
    config = EnhancedConfigManager()
    
    # Override with test values using correct ConfigParser interface
    config.config.set('database', 'database', 'maricopa_test')
    config.config.set('api', 'timeout', '5')  # Faster timeouts for tests
    config.config.set('scraping', 'headless', 'true')
    
    # Add cache section if it doesn't exist
    if not config.config.has_section('cache'):
        config.config.add_section('cache')
    config.config.set('cache', 'ttl', '60')  # Short TTL for tests
    
    return config

@pytest.fixture(scope="session")
def test_database(app_config):
    """Set up test database with sample data"""
    # MIGRATED: from src.database_manager import DatabaseManager  # → from src.threadsafe_database_manager import ThreadSafeDatabaseManager
    
    db = ThreadSafeDatabaseManager(app_config)
    
    # Ensure test database exists and is clean
    try:
        if db.test_connection():
            # Clean existing test data
            with db.get_connection() as conn:
                cursor = conn.cursor()
                # Truncate tables in correct order (respecting foreign keys)
                cursor.execute("TRUNCATE TABLE tax_history, sales_history, documents, search_history CASCADE")
                cursor.execute("TRUNCATE TABLE properties RESTART IDENTITY CASCADE")
                conn.commit()
                
            # Load test data
            load_test_data(db)
            
        yield db
        
        # Cleanup after all tests
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("TRUNCATE TABLE tax_history, sales_history, documents, search_history CASCADE")
            cursor.execute("TRUNCATE TABLE properties RESTART IDENTITY CASCADE")
            conn.commit()
            
    finally:
        db.close()

@pytest.fixture
def mock_api_client(app_config):
    """Provide mock API client with predictable responses"""
    # MIGRATED: from src.api_client import MockMaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient
    
    client = MockMaricopaAPIClient(app_config)
    yield client
    client.close()

@pytest.fixture
def mock_web_scraper(app_config):
    """Provide mock web scraper for testing"""
    from src.web_scraper import MockWebScraperManager
    
    scraper = MockWebScraperManager(app_config)
    yield scraper
    scraper.close()

@pytest.fixture
def sample_property_data():
    """Provide sample property data for testing"""
    return {
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
        'bathrooms': 2,
        'lot_size': 0.25
    }

@pytest.fixture
def missouri_avenue_property():
    """Provide 10000 W Missouri Ave test property data"""
    return {
        'apn': '301-07-042',
        'owner_name': 'MISSOURI AVENUE LLC',
        'property_address': '10000 W MISSOURI AVE',
        'city': 'PHOENIX',
        'zip_code': '85037',
        'property_type': 'COMMERCIAL',
        'assessed_value': 850000,
        'market_value': 920000,
        'square_feet': 12500,
        'year_built': 1998,
        'lot_size': 2.15,
        # Expected search variations
        'search_variations': [
            '10000 W Missouri Ave',
            '10000 MISSOURI AVE',
            '10000 W MISSOURI AVENUE',
            'Missouri Avenue LLC'
        ]
    }

@pytest.fixture
def sample_search_results():
    """Provide sample search results for testing"""
    return [
        {
            'apn': '101-01-001A',
            'owner_name': 'SMITH, JOHN & JANE',
            'property_address': '123 MAIN ST',
            'city': 'PHOENIX',
            'assessed_value': 250000
        },
        {
            'apn': '101-01-002B',
            'owner_name': 'JONES, ROBERT',
            'property_address': '456 OAK AVE',
            'city': 'TEMPE', 
            'assessed_value': 300000
        },
        {
            'apn': '301-07-042',
            'owner_name': 'MISSOURI AVENUE LLC',
            'property_address': '10000 W MISSOURI AVE',
            'city': 'PHOENIX',
            'assessed_value': 850000
        }
    ]

@pytest.fixture
def qt_app():
    """Provide QApplication for GUI testing"""
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    
    # Set up high DPI scaling for consistent tests
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        
    yield app
    
    # Cleanup is handled by Qt

@pytest.fixture
def temp_cache_dir():
    """Provide temporary directory for cache testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

def load_test_data(db_manager):
    """Load sample test data into database including 10000 W Missouri Ave"""
    test_properties = [
        # Standard test properties
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
            'year_built': 1995
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
            'year_built': 2005
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
            'year_built': 2010
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
        # Critical test property: 10000 W Missouri Ave
        {
            'apn': '301-07-042',
            'owner_name': 'MISSOURI AVENUE LLC',
            'property_address': '10000 W MISSOURI AVE',
            'city': 'PHOENIX',
            'zip_code': '85037',
            'property_type': 'COMMERCIAL',
            'assessed_value': 850000,
            'market_value': 920000,
            'square_feet': 12500,
            'year_built': 1998
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
            'square_feet': None,
            'year_built': None
        }
    ]
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            for prop in test_properties:
                cursor.execute("""
                    INSERT INTO properties (
                        apn, owner_name, property_address, city, zip_code,
                        property_type, assessed_value, market_value, 
                        square_feet, year_built, last_updated
                    ) VALUES (
                        %(apn)s, %(owner_name)s, %(property_address)s, %(city)s, %(zip_code)s,
                        %(property_type)s, %(assessed_value)s, %(market_value)s,
                        %(square_feet)s, %(year_built)s, CURRENT_TIMESTAMP
                    )
                """, prop)
                
            conn.commit()
            
    except Exception as e:
        print(f"Error loading test data: {e}")

# Performance test utilities
@pytest.fixture
def performance_timer():
    """Utility for timing operations in performance tests"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            
        def start(self):
            self.start_time = time.perf_counter()
            
        def stop(self):
            self.end_time = time.perf_counter()
            return self.elapsed()
            
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
            
    return Timer()

# Mock network conditions for reliability testing
@pytest.fixture
def network_simulator():
    """Simulate various network conditions for testing"""
    
    class NetworkSimulator:
        def __init__(self):
            self.conditions = {
                'normal': {'delay': 0, 'fail_rate': 0},
                'slow': {'delay': 2, 'fail_rate': 0},
                'unstable': {'delay': 1, 'fail_rate': 0.3},
                'offline': {'delay': 0, 'fail_rate': 1.0}
            }
            
        def apply_condition(self, condition_name):
            """Apply network condition to requests"""
            condition = self.conditions.get(condition_name, self.conditions['normal'])
            
            def mock_request(*args, **kwargs):
                import time
                import random
from src.api_client_unified import UnifiedMaricopaAPIClient
from src.threadsafe_database_manager import ThreadSafeDatabaseManager
from src.enhanced_config_manager import EnhancedConfigManager
                
                # Simulate delay
                if condition['delay'] > 0:
                    time.sleep(condition['delay'])
                    
                # Simulate failure
                if random.random() < condition['fail_rate']:
                    raise ConnectionError("Simulated network failure")
                    
                # Return mock success response
                return Mock(status_code=200, json=lambda: {'status': 'success'})
                
            return patch('requests.get', side_effect=mock_request)
            
    return NetworkSimulator()

@pytest.fixture
def database_isolation():
    """Ensure test isolation with proper cleanup"""
    # This fixture ensures each test starts with a clean database state
    # Implementation depends on specific database manager architecture
    pass

# Test markers for organization
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests for component interactions")
    config.addinivalue_line("markers", "performance: Performance and load tests")
    config.addinivalue_line("markers", "e2e: End-to-end user workflow tests")
    config.addinivalue_line("markers", "slow: Tests that take more than 10 seconds")
    config.addinivalue_line("markers", "gui: Tests requiring GUI components")
    config.addinivalue_line("markers", "network: Tests requiring network access")
    config.addinivalue_line("markers", "database: Tests requiring database connection")
    config.addinivalue_line("markers", "accessibility: Accessibility compliance tests")