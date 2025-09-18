#!/usr/bin/env python
"""
Fixed launcher for Maricopa Property Search Application
Handles all import issues and launches the application correctly
"""

import sys
import os
from pathlib import Path

# Add src directory to path FIRST
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Ensure the parent directory is also in path for relative imports
sys.path.insert(0, str(Path(__file__).parent))

import logging
import traceback

# Set up logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    """Main application entry point with error handling"""
    logger.info("Starting Enhanced Maricopa Property Search Application")
    
    try:
        # Import PyQt5 components
        from PyQt5.QtWidgets import QApplication, QMessageBox
        from PyQt5.QtCore import Qt
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("Maricopa Property Search - Enhanced")
        app.setApplicationVersion("2.0")
        app.setOrganizationName("Property Search Solutions")
        app.setStyle('Fusion')
        
        # Import configuration
        # MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        logger.info("Loading application configuration")
        config_manager = EnhancedConfigManager()
        
        # Test database connection
        from threadsafe_database_manager import ThreadSafeDatabaseManager
        try:
            db_test = ThreadSafeDatabaseManager(config_manager)
            if not db_test.test_connection():
                raise Exception("Database connection test failed")
            db_test.close()
            logger.info("Database connection verified")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            QMessageBox.critical(None, "Database Error", 
                               f"Could not connect to database:\n{str(e)}\n\n"
                               "Please check your database configuration.")
            sys.exit(1)
        
        # Import and create main window
        logger.info("Creating main application window")
        from gui.enhanced_main_window import EnhancedPropertySearchApp
        main_window = EnhancedPropertySearchApp(config_manager)
        
        main_window.show()
        logger.info("Application startup complete")
        
        # Log system information
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Application PID: {os.getpid()}")
        
        # Start the application event loop
        exit_code = app.exec_()
        logger.info(f"Application exiting with code: {exit_code}")
        return exit_code
        
    except ImportError as e:
        logger.error(f"Import error during startup: {e}")
        logger.error(f"Python path: {sys.path}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        if 'PyQt5' in str(e):
            print("\nERROR: PyQt5 is not installed or not accessible.")
            print("Please install it with: pip install PyQt5")
        elif 'playwright' in str(e):
            print("\nERROR: Playwright is not installed.")
            print("Please install it with: pip install playwright")
            print("Then run: playwright install chromium")
        else:
            print(f"\nERROR: Missing module: {e}")
            print("Please check your dependencies are installed.")
        
        return 1
        
    except Exception as e:
        logger.error(f"Critical error during application startup: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        try:
            from PyQt5.QtWidgets import QMessageBox
from src.enhanced_config_manager import EnhancedConfigManager
            QMessageBox.critical(None, "Application Error", 
                               f"A critical error occurred during startup:\n\n{str(e)}\n\n"
                               "Please check the log files for more details.")
        except:
            print(f"\nCRITICAL ERROR: {e}")
            print("Please check the logs for more details.")
        
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        print(traceback.format_exc())
        sys.exit(1)