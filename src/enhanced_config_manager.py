#!/usr/bin/env python
"""
Enhanced Configuration Manager
Extended configuration for background data collection system
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import os

from config_manager import ConfigManager

logger = logging.getLogger(__name__)


class EnhancedConfigManager(ConfigManager):
    """Enhanced configuration manager with background collection settings"""
    
    def __init__(self, config_file: Optional[str] = None):
        super().__init__()
        
        # Add default background collection settings
        self._add_background_collection_defaults()
    
    def _add_background_collection_defaults(self):
        """Add default configuration for background data collection"""
        
        # Background collection settings
        bg_defaults = {
            'max_concurrent_jobs': 3,
            'job_timeout_seconds': 300,  # 5 minutes
            'retry_attempts': 3,
            'retry_delay_seconds': 2,
            'cache_expiry_hours': 24,
            'auto_start_collection': True,
            'priority_queue_size': 1000,
            'collection_batch_size': 50
        }
        
        # Database pool settings
        db_pool_defaults = {
            'min_connections': 5,
            'max_connections': 20,
            'connection_timeout_seconds': 30,
            'pool_recycle_seconds': 3600  # 1 hour
        }
        
        # Performance monitoring
        performance_defaults = {
            'enable_performance_monitoring': True,
            'log_slow_operations': True,
            'slow_operation_threshold_seconds': 2.0,
            'stats_update_interval_seconds': 5
        }
        
        # UI update intervals
        ui_defaults = {
            'status_update_interval_ms': 2000,   # 2 seconds
            'progress_update_interval_ms': 1000, # 1 second
            'table_refresh_interval_ms': 5000    # 5 seconds
        }
        
        # Add to config if not present
        if 'background_collection' not in self.config:
            self.config['background_collection'] = bg_defaults
        
        if 'database_pool' not in self.config:
            self.config['database_pool'] = db_pool_defaults
            
        if 'performance' not in self.config:
            self.config['performance'] = performance_defaults
            
        if 'ui_updates' not in self.config:
            self.config['ui_updates'] = ui_defaults
    
    def get_background_collection_config(self) -> Dict[str, Any]:
        """Get background collection configuration"""
        return self.config.get('background_collection', {})
    
    def get_database_pool_config(self) -> Dict[str, Any]:
        """Get database connection pool configuration"""
        return self.config.get('database_pool', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance monitoring configuration"""
        return self.config.get('performance', {})
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI update configuration"""
        return self.config.get('ui_updates', {})
    
    def set_background_collection_setting(self, key: str, value: Any):
        """Set a specific background collection setting"""
        if 'background_collection' not in self.config:
            self.config['background_collection'] = {}
        
        self.config['background_collection'][key] = value
        self.save_config()
        logger.info(f"Updated background collection setting {key} = {value}")
    
    def enable_high_performance_mode(self):
        """Enable high performance mode for background collection"""
        logger.info("Enabling high performance mode")
        
        # Increase concurrent jobs
        self.config['background_collection']['max_concurrent_jobs'] = 5
        
        # Increase connection pool
        self.config['database_pool']['max_connections'] = 30
        
        # Reduce update intervals for more responsive UI
        self.config['ui_updates']['status_update_interval_ms'] = 1000
        self.config['ui_updates']['progress_update_interval_ms'] = 500
        
        # Enable all performance monitoring
        self.config['performance']['enable_performance_monitoring'] = True
        self.config['performance']['log_slow_operations'] = True
        
        self.save_config()
    
    def enable_conservative_mode(self):
        """Enable conservative mode for limited resources"""
        logger.info("Enabling conservative mode")
        
        # Reduce concurrent jobs
        self.config['background_collection']['max_concurrent_jobs'] = 2
        
        # Reduce connection pool
        self.config['database_pool']['max_connections'] = 10
        
        # Increase update intervals to reduce CPU usage
        self.config['ui_updates']['status_update_interval_ms'] = 5000
        self.config['ui_updates']['progress_update_interval_ms'] = 2000
        
        # Reduce monitoring to save resources
        self.config['performance']['log_slow_operations'] = False
        
        self.save_config()
    
    def get_optimized_config_for_system(self) -> Dict[str, Any]:
        """Get configuration optimized for the current system"""
        import psutil
        
        # Get system information
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        logger.info(f"System specs: {cpu_count} CPUs, {memory_gb:.1f}GB RAM")
        
        # Optimize based on system resources
        if cpu_count >= 8 and memory_gb >= 16:
            # High-end system
            max_concurrent = min(cpu_count - 2, 8)  # Leave some CPUs free
            max_connections = min(max_concurrent * 4, 40)
        elif cpu_count >= 4 and memory_gb >= 8:
            # Mid-range system
            max_concurrent = min(cpu_count - 1, 5)
            max_connections = min(max_concurrent * 3, 25)
        else:
            # Low-end system
            max_concurrent = max(cpu_count // 2, 2)
            max_connections = min(max_concurrent * 2, 15)
        
        optimized_config = self.config.copy()
        optimized_config['background_collection']['max_concurrent_jobs'] = max_concurrent
        optimized_config['database_pool']['max_connections'] = max_connections
        
        logger.info(f"Optimized config: {max_concurrent} concurrent jobs, {max_connections} DB connections")
        
        return optimized_config
    
    def create_example_config(self, output_path: Optional[str] = None) -> str:
        """Create an example configuration file with all enhanced settings"""
        
        example_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "maricopa_properties",
                "user": "your_username",
                "password": "your_password",
                "schema": "public"
            },
            "api": {
                "base_url": "https://api.maricopa.gov/property",
                "token": "your_api_token_here",
                "timeout": 30,
                "max_retries": 3,
                "rate_limit_requests_per_minute": 60
            },
            "web_scraping": {
                "enabled": True,
                "headless": True,
                "timeout": 30,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "max_concurrent_browsers": 2
            },
            "background_collection": {
                "max_concurrent_jobs": 3,
                "job_timeout_seconds": 300,
                "retry_attempts": 3,
                "retry_delay_seconds": 2,
                "cache_expiry_hours": 24,
                "auto_start_collection": True,
                "priority_queue_size": 1000,
                "collection_batch_size": 50
            },
            "database_pool": {
                "min_connections": 5,
                "max_connections": 20,
                "connection_timeout_seconds": 30,
                "pool_recycle_seconds": 3600
            },
            "performance": {
                "enable_performance_monitoring": True,
                "log_slow_operations": True,
                "slow_operation_threshold_seconds": 2.0,
                "stats_update_interval_seconds": 5
            },
            "ui_updates": {
                "status_update_interval_ms": 2000,
                "progress_update_interval_ms": 1000,
                "table_refresh_interval_ms": 5000
            },
            "logging": {
                "level": "INFO",
                "log_to_file": True,
                "log_directory": "./logs",
                "max_log_files": 10,
                "max_log_size_mb": 50
            }
        }
        
        if output_path is None:
            output_path = "config_enhanced_example.json"
        
        output_file = Path(output_path)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(example_config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Example enhanced configuration created: {output_file.absolute()}")
            return str(output_file.absolute())
            
        except Exception as e:
            logger.error(f"Error creating example config: {e}")
            raise
    
    def validate_enhanced_config(self) -> Dict[str, Any]:
        """Validate the enhanced configuration and return validation results"""
        
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Validate background collection settings
        bg_config = self.get_background_collection_config()
        
        max_concurrent = bg_config.get('max_concurrent_jobs', 3)
        if max_concurrent < 1:
            validation_results['errors'].append("max_concurrent_jobs must be at least 1")
            validation_results['valid'] = False
        elif max_concurrent > 10:
            validation_results['warnings'].append(f"max_concurrent_jobs ({max_concurrent}) is very high, may cause resource issues")
        
        # Validate database pool settings
        pool_config = self.get_database_pool_config()
        
        min_conn = pool_config.get('min_connections', 5)
        max_conn = pool_config.get('max_connections', 20)
        
        if min_conn > max_conn:
            validation_results['errors'].append("min_connections cannot be greater than max_connections")
            validation_results['valid'] = False
        
        if max_conn > 50:
            validation_results['warnings'].append(f"max_connections ({max_conn}) is very high, may exceed database limits")
        
        # Validate performance settings
        perf_config = self.get_performance_config()
        
        slow_threshold = perf_config.get('slow_operation_threshold_seconds', 2.0)
        if slow_threshold <= 0:
            validation_results['errors'].append("slow_operation_threshold_seconds must be positive")
            validation_results['valid'] = False
        
        # System-based recommendations
        try:
            import psutil
            cpu_count = psutil.cpu_count()
            
            if max_concurrent > cpu_count:
                validation_results['recommendations'].append(
                    f"Consider reducing max_concurrent_jobs to {cpu_count} or fewer (system has {cpu_count} CPUs)"
                )
            
            memory_gb = psutil.virtual_memory().total / (1024**3)
            if max_conn * 10 > memory_gb * 1024:  # Rough estimate: 10MB per connection
                validation_results['recommendations'].append(
                    f"Database connection pool may use significant memory (system has {memory_gb:.1f}GB)"
                )
                
        except ImportError:
            validation_results['warnings'].append("psutil not available for system resource validation")
        
        # Log validation results
        if validation_results['valid']:
            logger.info("Enhanced configuration validation passed")
        else:
            logger.error("Enhanced configuration validation failed")
            for error in validation_results['errors']:
                logger.error(f"Config error: {error}")
        
        for warning in validation_results['warnings']:
            logger.warning(f"Config warning: {warning}")
        
        for rec in validation_results['recommendations']:
            logger.info(f"Config recommendation: {rec}")
        
        return validation_results


def main():
    """Example usage of enhanced configuration manager"""
    logging.basicConfig(level=logging.INFO)
    
    # Create enhanced config manager
    config_manager = EnhancedConfigManager()
    
    # Validate configuration
    validation = config_manager.validate_enhanced_config()
    if not validation['valid']:
        print("Configuration validation failed!")
        for error in validation['errors']:
            print(f"ERROR: {error}")
        return 1
    
    # Create example config
    example_path = config_manager.create_example_config()
    print(f"Example configuration created: {example_path}")
    
    # Show current settings
    print("\nCurrent Background Collection Settings:")
    bg_config = config_manager.get_background_collection_config()
    for key, value in bg_config.items():
        print(f"  {key}: {value}")
    
    print("\nCurrent Database Pool Settings:")
    pool_config = config_manager.get_database_pool_config()
    for key, value in pool_config.items():
        print(f"  {key}: {value}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)