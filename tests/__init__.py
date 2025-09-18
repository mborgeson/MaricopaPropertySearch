"""
Test Suite for MaricopaPropertySearch - Phase 5 Quality Infrastructure

This test suite provides comprehensive testing for the unified architecture
that consolidated 16 components into 4 unified implementations with 75% file reduction.

Test Categories:
- Unit Tests: Individual component testing
- Integration Tests: Component interaction testing
- Performance Tests: Benchmark validation
- System Tests: End-to-end workflow testing
"""

# Test configuration
TEST_CONFIG = {
    'api_timeout': 5.0,
    'db_timeout': 2.0,
    'gui_timeout': 10.0,
    'performance_baseline': {
        'basic_search': 0.1,  # seconds
        'detailed_search': 0.5,
        'background_collection': 2.0,
    }
}

# Test data configuration
TEST_DATA_CONFIG = {
    'missouri_ave_apn': '10215009',
    'missouri_ave_address': '10000 W Missouri Ave',
    'sample_properties': [
        {'apn': '10215009', 'address': '10000 W Missouri Ave'},
        {'apn': '10215010', 'address': '10010 W Missouri Ave'},
        {'apn': '10215011', 'address': '10020 W Missouri Ave'},
    ]
}

__version__ = "5.0.0"
__author__ = "MaricopaPropertySearch Development Team"