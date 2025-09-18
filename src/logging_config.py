"""
Centralized Logging Configuration
Provides comprehensive logging setup for the Maricopa Property Search application
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from datetime import datetime
import traceback
import functools
import time
from typing import Dict, Any, Optional, Callable
import json


class PerformanceLogger:
    """Performance logging utility for timing operations"""
    
    def __init__(self, logger_name: str = __name__):
        self.logger = logging.getLogger(logger_name)
    
    def log_performance(self, operation_name: str):
        """Decorator for logging operation performance"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                operation_id = f"{operation_name}_{int(start_time)}"
                
                self.logger.info(f"PERF_START: {operation_name} [ID: {operation_id}]")
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    self.logger.info(
                        f"PERF_SUCCESS: {operation_name} completed in {execution_time:.3f}s [ID: {operation_id}]"
                    )
                    
                    # Log detailed performance metrics for slow operations
                    if execution_time > 5.0:  # Operations taking more than 5 seconds
                        self.logger.warning(
                            f"PERF_SLOW: {operation_name} took {execution_time:.3f}s - consider optimization [ID: {operation_id}]"
                        )
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.logger.error(
                        f"PERF_ERROR: {operation_name} failed after {execution_time:.3f}s [ID: {operation_id}] - {str(e)}"
                    )
                    raise
                    
            return wrapper
        return decorator
    
    def log_database_operation(self, operation: str, table: str, record_count: int = None):
        """Log database operations with context"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                operation_id = f"db_{operation}_{table}_{int(start_time)}"
                
                context = {
                    "operation": operation,
                    "table": table,
                    "record_count": record_count,
                    "operation_id": operation_id
                }
                
                self.logger.info(f"DB_START: {operation} on {table} [ID: {operation_id}]")
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Try to get actual record count from result if not provided
                    actual_count = record_count
                    if result is not None:
                        if isinstance(result, list):
                            actual_count = len(result)
                        elif isinstance(result, bool) and result:
                            actual_count = 1
                    
                    self.logger.info(
                        f"DB_SUCCESS: {operation} on {table} completed in {execution_time:.3f}s, "
                        f"records: {actual_count} [ID: {operation_id}]"
                    )
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.logger.error(
                        f"DB_ERROR: {operation} on {table} failed after {execution_time:.3f}s [ID: {operation_id}] - {str(e)}"
                    )
                    raise
                    
            return wrapper
        return decorator


class APICallLogger:
    """Specialized logger for API operations"""
    
    def __init__(self, logger_name: str = __name__):
        self.logger = logging.getLogger(logger_name)
    
    def log_api_call(self, endpoint: str, method: str = "GET"):
        """Decorator for logging API calls"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                call_id = f"api_{method}_{endpoint.replace('/', '_')}_{int(start_time)}"
                
                self.logger.info(f"API_START: {method} {endpoint} [ID: {call_id}]")
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Determine result status
                    if result is None:
                        status = "NO_DATA"
                    elif isinstance(result, list):
                        status = f"SUCCESS_{len(result)}_records"
                    elif isinstance(result, dict):
                        status = "SUCCESS_single_record"
                    else:
                        status = "SUCCESS"
                    
                    self.logger.info(
                        f"API_SUCCESS: {method} {endpoint} - {status} in {execution_time:.3f}s [ID: {call_id}]"
                    )
                    
                    # Log slow API calls
                    if execution_time > 10.0:
                        self.logger.warning(
                            f"API_SLOW: {method} {endpoint} took {execution_time:.3f}s [ID: {call_id}]"
                        )
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.logger.error(
                        f"API_ERROR: {method} {endpoint} failed after {execution_time:.3f}s [ID: {call_id}] - {str(e)}"
                    )
                    raise
                    
            return wrapper
        return decorator


class SearchLogger:
    """Specialized logger for search operations"""
    
    def __init__(self, logger_name: str = __name__):
        self.logger = logging.getLogger(logger_name)
    
    def log_search_operation(self, search_type: str, search_term: str):
        """Decorator for logging search operations"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                search_id = f"search_{search_type}_{int(start_time)}"
                
                # Sanitize search term for logging (remove sensitive data if any)
                sanitized_term = search_term[:50] if len(search_term) > 50 else search_term
                
                self.logger.info(
                    f"SEARCH_START: {search_type} search for '{sanitized_term}' [ID: {search_id}]"
                )
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    result_count = 0
                    if isinstance(result, list):
                        result_count = len(result)
                    elif result is not None:
                        result_count = 1
                    
                    self.logger.info(
                        f"SEARCH_SUCCESS: {search_type} search completed in {execution_time:.3f}s, "
                        f"found {result_count} results [ID: {search_id}]"
                    )
                    
                    # Log search analytics
                    self.logger.info(
                        f"SEARCH_ANALYTICS: type={search_type}, term_length={len(search_term)}, "
                        f"results={result_count}, duration={execution_time:.3f}s [ID: {search_id}]"
                    )
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.logger.error(
                        f"SEARCH_ERROR: {search_type} search failed after {execution_time:.3f}s [ID: {search_id}] - {str(e)}"
                    )
                    raise
                    
            return wrapper
        return decorator


class LoggingConfig:
    """Centralized logging configuration manager"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.log_dir = None
        self.log_config = {}
        self.setup_complete = False
        
        # Load configuration
        self._load_config()
        self._setup_logging()
    
    def _load_config(self):
        """Load logging configuration from config manager or use defaults"""
        if self.config_manager:
            try:
                # Get log directory from config
                self.log_dir = self.config_manager.get_path('log')
                
                # Get logging configuration
                config = self.config_manager.config
                if 'logging' in config:
                    self.log_config = dict(config['logging'])
                else:
                    self._use_default_config()
            except Exception:
                self._use_default_config()
        else:
            self._use_default_config()
        
        # Ensure log directory exists
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _use_default_config(self):
        """Use default logging configuration"""
        # Default log directory - use Linux path for WSL environment
        project_root = Path("/home/mattb/MaricopaPropertySearch")
        self.log_dir = project_root / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Default logging configuration
        self.log_config = {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file_name': 'maricopa_property.log',
            'max_bytes': '10485760',  # 10MB
            'backup_count': '5'
        }
    
    def _setup_logging(self):
        """Setup comprehensive logging configuration"""
        try:
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(getattr(logging, self.log_config.get('level', 'INFO')))
            
            # Clear any existing handlers
            root_logger.handlers.clear()
            
            # Create formatter
            formatter = logging.Formatter(
                fmt=self.log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Setup file handlers
            self._setup_file_handlers(formatter)
            
            # Setup console handler for development
            self._setup_console_handler(formatter)
            
            # Setup specialized loggers
            self._setup_specialized_loggers(formatter)
            
            self.setup_complete = True
            
            # Log successful setup
            logger = logging.getLogger(__name__)
            logger.info("Logging system initialized successfully")
            logger.info(f"Log directory: {self.log_dir}")
            logger.info(f"Log level: {self.log_config.get('level', 'INFO')}")
            
        except Exception as e:
            print(f"ERROR: Failed to setup logging: {e}")
            traceback.print_exc()
            # Fallback to basic logging
            logging.basicConfig(level=logging.INFO)
    
    def _setup_file_handlers(self, formatter):
        """Setup file-based logging handlers"""
        # Main application log with rotation
        main_log_file = self.log_dir / self.log_config.get('file_name', 'maricopa_property.log')
        
        main_handler = logging.handlers.RotatingFileHandler(
            filename=main_log_file,
            maxBytes=int(self.log_config.get('max_bytes', 10485760)),  # 10MB default
            backupCount=int(self.log_config.get('backup_count', 5)),
            encoding='utf-8'
        )
        main_handler.setFormatter(formatter)
        main_handler.setLevel(logging.DEBUG)
        
        # Error-only log file
        error_log_file = self.log_dir / 'errors.log'
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_log_file,
            maxBytes=int(self.log_config.get('max_bytes', 10485760)),
            backupCount=int(self.log_config.get('backup_count', 5)),
            encoding='utf-8'
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Performance log file
        perf_log_file = self.log_dir / 'performance.log'
        perf_handler = logging.handlers.RotatingFileHandler(
            filename=perf_log_file,
            maxBytes=int(self.log_config.get('max_bytes', 10485760)),
            backupCount=int(self.log_config.get('backup_count', 5)),
            encoding='utf-8'
        )
        perf_handler.setFormatter(formatter)
        perf_handler.setLevel(logging.INFO)
        
        # Add performance filter
        perf_handler.addFilter(self._performance_filter)
        
        # Add handlers to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(main_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(perf_handler)
    
    def _setup_console_handler(self, formatter):
        """Setup console logging handler"""
        console_handler = logging.StreamHandler(sys.stdout)
        
        # More concise format for console
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Console shows INFO and above by default
        console_handler.setLevel(logging.INFO)
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(console_handler)
    
    def _setup_specialized_loggers(self, formatter):
        """Setup specialized loggers for different components"""
        # Database operations logger
        db_logger = logging.getLogger('database')
        db_log_file = self.log_dir / 'database.log'
        db_handler = logging.handlers.RotatingFileHandler(
            filename=db_log_file,
            maxBytes=int(self.log_config.get('max_bytes', 10485760)),
            backupCount=3,
            encoding='utf-8'
        )
        db_handler.setFormatter(formatter)
        db_logger.addHandler(db_handler)
        
        # API operations logger
        api_logger = logging.getLogger('api')
        api_log_file = self.log_dir / 'api.log'
        api_handler = logging.handlers.RotatingFileHandler(
            filename=api_log_file,
            maxBytes=int(self.log_config.get('max_bytes', 10485760)),
            backupCount=3,
            encoding='utf-8'
        )
        api_handler.setFormatter(formatter)
        api_logger.addHandler(api_handler)
        
        # Web scraping logger
        scraper_logger = logging.getLogger('scraper')
        scraper_log_file = self.log_dir / 'scraper.log'
        scraper_handler = logging.handlers.RotatingFileHandler(
            filename=scraper_log_file,
            maxBytes=int(self.log_config.get('max_bytes', 10485760)),
            backupCount=3,
            encoding='utf-8'
        )
        scraper_handler.setFormatter(formatter)
        scraper_logger.addHandler(scraper_handler)
        
        # Search operations logger
        search_logger = logging.getLogger('search')
        search_log_file = self.log_dir / 'search.log'
        search_handler = logging.handlers.RotatingFileHandler(
            filename=search_log_file,
            maxBytes=int(self.log_config.get('max_bytes', 10485760)),
            backupCount=3,
            encoding='utf-8'
        )
        search_handler.setFormatter(formatter)
        search_logger.addHandler(search_handler)
    
    def _performance_filter(self, record):
        """Filter for performance-related log records"""
        return any(keyword in record.getMessage() for keyword in [
            'PERF_', 'DB_', 'API_', 'SEARCH_'
        ])
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance with the specified name"""
        return logging.getLogger(name)
    
    def get_performance_logger(self, name: str) -> PerformanceLogger:
        """Get a performance logger instance"""
        return PerformanceLogger(name)
    
    def get_api_logger(self, name: str) -> APICallLogger:
        """Get an API call logger instance"""
        return APICallLogger(name)
    
    def get_search_logger(self, name: str) -> SearchLogger:
        """Get a search logger instance"""
        return SearchLogger(name)
    
    def log_system_info(self):
        """Log system information for debugging"""
        logger = logging.getLogger(__name__)
        
        logger.info("=== SYSTEM INFORMATION ===")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Platform: {sys.platform}")
        logger.info(f"Log directory: {self.log_dir}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Process ID: {os.getpid()}")
        logger.info("=== END SYSTEM INFORMATION ===")
    
    def log_application_start(self, app_name: str, version: str = "1.0"):
        """Log application startup"""
        logger = logging.getLogger(__name__)
        
        logger.info("=" * 60)
        logger.info(f"APPLICATION START: {app_name} v{version}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 60)
        
        self.log_system_info()
    
    def log_application_shutdown(self, app_name: str):
        """Log application shutdown"""
        logger = logging.getLogger(__name__)
        
        logger.info("=" * 60)
        logger.info(f"APPLICATION SHUTDOWN: {app_name}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 60)
    
    def create_context_logger(self, context: Dict[str, Any]) -> logging.LoggerAdapter:
        """Create a logger with additional context"""
        logger = logging.getLogger(__name__)
        return logging.LoggerAdapter(logger, context)


# Global logging instance
_logging_config = None


def setup_logging(config_manager=None) -> LoggingConfig:
    """Setup global logging configuration"""
    global _logging_config
    
    if _logging_config is None:
        _logging_config = LoggingConfig(config_manager)
    
    return _logging_config


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance"""
    if name is None:
        name = __name__
    
    # Ensure logging is setup
    if _logging_config is None:
        setup_logging()
    
    return logging.getLogger(name)


def get_performance_logger(name: str = None) -> PerformanceLogger:
    """Get a performance logger instance"""
    if name is None:
        name = __name__
    
    # Ensure logging is setup
    if _logging_config is None:
        setup_logging()
    
    return PerformanceLogger(name)


def get_api_logger(name: str = None) -> APICallLogger:
    """Get an API logger instance"""
    if name is None:
        name = __name__
    
    # Ensure logging is setup
    if _logging_config is None:
        setup_logging()
    
    return APICallLogger(name)


def get_search_logger(name: str = None) -> SearchLogger:
    """Get a search logger instance"""
    if name is None:
        name = __name__
    
    # Ensure logging is setup
    if _logging_config is None:
        setup_logging()
    
    return SearchLogger(name)


def log_exception(logger: logging.Logger, exception: Exception, context: str = ""):
    """Log exception with full traceback and context"""
    logger.error(f"Exception occurred{' in ' + context if context else ''}: {str(exception)}")
    logger.error(f"Exception type: {type(exception).__name__}")
    logger.error(f"Traceback:\n{traceback.format_exc()}")


def log_debug_variables(logger: logging.Logger, variables: Dict[str, Any], context: str = ""):
    """Log variable values for debugging"""
    logger.debug(f"Debug variables{' for ' + context if context else ''}:")
    for name, value in variables.items():
        try:
            # Safely convert to string, handling potentially problematic objects
            value_str = str(value)
            if len(value_str) > 500:  # Truncate very long values
                value_str = value_str[:500] + "... (truncated)"
            logger.debug(f"  {name}: {value_str}")
        except Exception as e:
            logger.debug(f"  {name}: <Could not convert to string: {e}>")


# Convenience function for common logging patterns
def log_function_call(logger: logging.Logger, func_name: str, args=None, kwargs=None):
    """Log function calls with parameters"""
    if args or kwargs:
        args_str = f"args={args}" if args else ""
        kwargs_str = f"kwargs={kwargs}" if kwargs else ""
        params = ", ".join(filter(None, [args_str, kwargs_str]))
        logger.debug(f"Calling {func_name}({params})")
    else:
        logger.debug(f"Calling {func_name}()")


# Export main components
__all__ = [
    'LoggingConfig',
    'PerformanceLogger', 
    'APICallLogger',
    'SearchLogger',
    'setup_logging',
    'get_logger',
    'get_performance_logger',
    'get_api_logger', 
    'get_search_logger',
    'log_exception',
    'log_debug_variables',
    'log_function_call'
]