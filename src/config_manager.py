"""
Configuration Manager
Handles all configuration loading and management
"""

import os
import configparser
from pathlib import Path
from dotenv import load_dotenv

class ConfigManager:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.resolve()
        self.config_file = self.project_root / "config" / "config.ini"
        self.env_file = self.project_root / ".env"
        
        # Load environment variables
        load_dotenv(self.env_file)
        
        # Load configuration
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)
        
    def get_db_config(self):
        """Get database configuration"""
        return {
            'host': self.config.get('database', 'host'),
            'port': self.config.getint('database', 'port'),
            'database': self.config.get('database', 'database'),
            'user': self.config.get('database', 'user'),
            'password': os.getenv('DB_PASSWORD', self.config.get('database', 'password'))
        }
    
    def get_database_config(self):
        """Get database configuration - alias for compatibility with ThreadSafeDatabaseManager"""
        return self.get_db_config()
    
    def get_api_config(self):
        """Get API configuration"""
        return {
            'base_url': self.config.get('api', 'base_url'),
            'token': os.getenv('API_TOKEN', self.config.get('api', 'token')),
            'timeout': self.config.getint('api', 'timeout'),
            'max_retries': self.config.getint('api', 'max_retries')
        }
    
    def get_scraping_config(self):
        """Get web scraping configuration"""
        return {
            'browser': self.config.get('scraping', 'browser'),
            'headless': self.config.getboolean('scraping', 'headless'),
            'timeout': self.config.getint('scraping', 'timeout'),
            'max_workers': self.config.getint('scraping', 'max_workers')
        }
    
    def get_path(self, path_type):
        """Get configured paths"""
        return Path(self.config.get('paths', f'{path_type}_dir'))

    def get_database_enabled(self):
        """Check if database is enabled in configuration"""
        try:
            return self.config.getboolean('database', 'enabled')
        except:
            return True  # Default to enabled if not specified

    def get_api_client_type(self):
        """Get the API client type from configuration"""
        try:
            return self.config.get('api', 'client_type')
        except:
            return 'real'  # Default to real client

    def get_web_scraper_type(self):
        """Get the web scraper type from configuration"""
        try:
            return self.config.get('scraping', 'type')
        except:
            return 'real'  # Default to real scraper

    def get_logging_enabled(self):
        """Check if logging is enabled in configuration"""
        try:
            return self.config.getboolean('logging', 'enabled')
        except:
            return True  # Default to enabled if not specified