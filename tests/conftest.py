"""
Pytest configuration and fixtures for MaricopaPropertySearch testing

This file provides shared fixtures and configuration for all test modules.
Supports testing of the 4 unified components with comprehensive mock data.
"""

import pytest
import asyncio
import json
import tempfile
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, MagicMock, patch
import logging

# Add src directory to path for imports
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(project_root))

# Import test configuration
from tests import TEST_CONFIG, TEST_DATA_CONFIG

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    # Ensure test directories exist
    test_dirs = ['htmlcov', 'test-reports', 'test-data']
    for directory in test_dirs:
        (project_root / directory).mkdir(exist_ok=True)

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Auto-mark based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "system" in str(item.fspath):
            item.add_marker(pytest.mark.system)

        # Auto-mark slow tests
        if "slow" in item.name or "performance" in item.name:
            item.add_marker(pytest.mark.slow)

# ============================================================================
# CORE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def test_config():
    """Provide test configuration dictionary."""
    return TEST_CONFIG.copy()

@pytest.fixture
def test_data_config():
    """Provide test data configuration."""
    return TEST_DATA_CONFIG.copy()

# ============================================================================
# MOCK DATA FIXTURES
# ============================================================================

@pytest.fixture
def mock_property_data():
    """Generate realistic mock property data."""
    return {
        'apn': '10215009',
        'address': '10000 W Missouri Ave',
        'owner': 'SAMPLE PROPERTY OWNER',
        'property_type': 'Residential',
        'year_built': 1995,
        'square_feet': 2100,
        'lot_size': 0.25,
        'bedrooms': 4,
        'bathrooms': 2.5,
        'assessed_value': 285000,
        'market_value': 320000,
        'tax_amount': 3420.50,
        'legal_description': 'LOT 1 MISSOURI AVENUE SUBDIVISION',
        'zone': 'R1-6',
        'school_district': 'PEORIA UNIFIED SCHOOL DISTRICT',
        'coordinates': {
            'latitude': 33.5806,
            'longitude': -112.2839
        },
        'last_sale': {
            'date': '2020-05-15',
            'price': 275000,
            'document_number': 'DOC2020051500123'
        }
    }

@pytest.fixture
def mock_tax_history():
    """Generate realistic tax history data."""
    return [
        {
            'year': 2023,
            'assessed_value': 285000,
            'tax_amount': 3420.50,
            'paid_date': '2023-11-15',
            'status': 'PAID'
        },
        {
            'year': 2022,
            'assessed_value': 275000,
            'tax_amount': 3300.25,
            'paid_date': '2022-12-01',
            'status': 'PAID'
        },
        {
            'year': 2021,
            'assessed_value': 265000,
            'tax_amount': 3180.75,
            'paid_date': '2021-11-30',
            'status': 'PAID'
        }
    ]

@pytest.fixture
def mock_api_responses():
    """Mock API response data for different scenarios."""
    return {
        'success': {
            'status_code': 200,
            'json': {
                'success': True,
                'data': {
                    'property_info': {'apn': '10215009'},
                    'tax_info': {'current_amount': 3420.50}
                }
            }
        },
        'partial_success': {
            'status_code': 200,
            'json': {
                'success': True,
                'data': {'property_info': {'apn': '10215009'}},
                'warnings': ['Tax data unavailable']
            }
        },
        'api_error': {
            'status_code': 500,
            'json': {'error': 'Internal server error'}
        },
        'rate_limited': {
            'status_code': 429,
            'json': {'error': 'Rate limit exceeded'}
        },
        'not_found': {
            'status_code': 404,
            'json': {'error': 'Property not found'}
        }
    }

# ============================================================================
# COMPONENT FIXTURES
# ============================================================================

@pytest.fixture
def mock_api_client():
    """Mock UnifiedMaricopaAPIClient for testing."""
    client = Mock()
    client.session = Mock()
    client.cache = {}
    client.rate_limiter = Mock()
    client.connection_pool = Mock()
    client.logger = Mock()
    return client

@pytest.fixture
def mock_data_collector():
    """Mock UnifiedDataCollector for testing."""
    collector = Mock()
    collector.api_client = Mock()
    collector.job_queue = Mock()
    collector.background_thread = Mock()
    collector.progress_callback = Mock()
    collector.logger = Mock()
    return collector

@pytest.fixture
def mock_database_manager():
    """Mock ThreadSafeDatabaseManager for testing."""
    db_manager = Mock()
    db_manager.connection_pool = Mock()
    db_manager.mock_mode = True
    db_manager.cache = {}
    db_manager.logger = Mock()
    return db_manager

@pytest.fixture
def mock_gui_launcher():
    """Mock UnifiedGUILauncher for testing."""
    launcher = Mock()
    launcher.platform_detector = Mock()
    launcher.platform_detector.detect_platform.return_value = {
        'os_type': 'Linux',
        'is_wsl': False,
        'gui_backend': 'XCB',
        'display_available': True
    }
    launcher.logger = Mock()
    return launcher

# ============================================================================
# ENVIRONMENT FIXTURES
# ============================================================================

@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    env_vars = {
        'DISPLAY': ':0',
        'WAYLAND_DISPLAY': 'wayland-0',
        'QT_QPA_PLATFORM': 'xcb',
        'PGHOST': 'localhost',
        'PGPORT': '5432',
        'PGDATABASE': 'test_db',
        'PGUSER': 'test_user',
        'PGPASSWORD': 'test_password'
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars

@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.perf_counter()

        def stop(self):
            self.end_time = time.perf_counter()
            return self.elapsed

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()

@pytest.fixture
def benchmark_baseline():
    """Provide performance benchmark baselines."""
    return {
        'api_response_time': 0.1,  # seconds
        'database_query_time': 0.05,
        'gui_startup_time': 2.0,
        'search_completion_time': 0.5,
        'memory_usage_mb': 100
    }

# Test data for parameterized tests
PROPERTY_TEST_CASES = [
    ('10215009', '10000 W Missouri Ave', True),
    ('10215010', '10010 W Missouri Ave', True),
    ('invalid_apn', 'Invalid Address', False),
    ('', '', False),
]

API_ERROR_TEST_CASES = [
    (500, 'Internal Server Error'),
    (404, 'Not Found'),
    (429, 'Rate Limited'),
    (403, 'Forbidden'),
    (400, 'Bad Request'),
]