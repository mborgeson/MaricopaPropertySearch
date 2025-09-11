"""
Test script to demonstrate the comprehensive logging system
Run this to verify all logging components are working correctly
"""

import sys
import time
from pathlib import Path

# Add src to path
project_root = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(project_root / "src"))

# Import modules
from config_manager import ConfigManager
from logging_config import (
    setup_logging, get_logger, get_performance_logger, 
    get_api_logger, get_search_logger, log_exception, 
    log_debug_variables
)


def test_basic_logging():
    """Test basic logging functionality"""
    logger = get_logger(__name__)
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")


def test_performance_logging():
    """Test performance logging decorators"""
    perf_logger = get_performance_logger(__name__)
    
    @perf_logger.log_performance('test_operation')
    def slow_operation():
        time.sleep(1.2)  # Simulate slow operation
        return "operation completed"
    
    @perf_logger.log_database_operation('select', 'test_table', 100)
    def database_operation():
        time.sleep(0.5)  # Simulate database query
        return [{"id": i, "name": f"record_{i}"} for i in range(100)]
    
    # Execute operations
    result1 = slow_operation()
    result2 = database_operation()
    
    return result1, result2


def test_api_logging():
    """Test API logging functionality"""
    api_logger = get_api_logger(__name__)
    
    @api_logger.log_api_call('/api/test/endpoint', 'GET')
    def api_call():
        time.sleep(0.3)  # Simulate API call
        return {"status": "success", "data": ["item1", "item2"]}
    
    result = api_call()
    return result


def test_search_logging():
    """Test search logging functionality"""
    search_logger = get_search_logger(__name__)
    
    @search_logger.log_search_operation('property', 'test search term')
    def search_operation():
        time.sleep(0.8)  # Simulate search
        return [{"apn": "123456789", "owner": "Test Owner"}]
    
    result = search_operation()
    return result


def test_exception_logging():
    """Test exception logging"""
    logger = get_logger(__name__)
    
    try:
        # Simulate an error
        result = 10 / 0
    except Exception as e:
        log_exception(logger, e, "division operation test")
    
    try:
        # Another type of error
        data = {"key": "value"}
        result = data["nonexistent_key"]
    except Exception as e:
        log_exception(logger, e, "dictionary access test")


def test_debug_variables():
    """Test debug variable logging"""
    logger = get_logger(__name__)
    
    variables = {
        "user_id": 12345,
        "search_term": "test property",
        "results_count": 42,
        "config": {"timeout": 30, "retries": 3},
        "large_data": "x" * 1000  # This should be truncated
    }
    
    log_debug_variables(logger, variables, "search operation")


def test_error_scenarios():
    """Test various error scenarios"""
    logger = get_logger(__name__)
    perf_logger = get_performance_logger(__name__)
    
    # Test failed operation with performance logging
    @perf_logger.log_performance('failing_operation')
    def failing_operation():
        time.sleep(0.2)
        raise ValueError("Simulated operation failure")
    
    try:
        failing_operation()
    except Exception as e:
        log_exception(logger, e, "performance logged operation")


def main():
    """Main test function"""
    print("=" * 60)
    print("MARICOPA PROPERTY SEARCH - LOGGING SYSTEM TEST")
    print("=" * 60)
    
    try:
        # Setup logging
        config = ConfigManager()
        logging_config = setup_logging(config)
        
        # Get main logger
        logger = get_logger(__name__)
        
        # Log application start
        logging_config.log_application_start("Logging System Test", "1.0")
        
        print("\n1. Testing basic logging...")
        test_basic_logging()
        
        print("\n2. Testing performance logging...")
        perf_results = test_performance_logging()
        logger.info(f"Performance test results: {perf_results}")
        
        print("\n3. Testing API logging...")
        api_result = test_api_logging()
        logger.info(f"API test result: {api_result}")
        
        print("\n4. Testing search logging...")
        search_result = test_search_logging()
        logger.info(f"Search test result: {search_result}")
        
        print("\n5. Testing exception logging...")
        test_exception_logging()
        
        print("\n6. Testing debug variable logging...")
        test_debug_variables()
        
        print("\n7. Testing error scenarios...")
        test_error_scenarios()
        
        # Log completion
        logger.info("All logging tests completed successfully")
        logging_config.log_application_shutdown("Logging System Test")
        
        print("\n" + "=" * 60)
        print("LOGGING SYSTEM TEST COMPLETED")
        print("Check the log files in the logs/ directory:")
        print(f"- Main log: {logging_config.log_dir}/maricopa_property.log")
        print(f"- Error log: {logging_config.log_dir}/errors.log")
        print(f"- Performance log: {logging_config.log_dir}/performance.log")
        print(f"- Database log: {logging_config.log_dir}/database.log")
        print(f"- API log: {logging_config.log_dir}/api.log")
        print(f"- Scraper log: {logging_config.log_dir}/scraper.log")
        print(f"- Search log: {logging_config.log_dir}/search.log")
        print("=" * 60)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())