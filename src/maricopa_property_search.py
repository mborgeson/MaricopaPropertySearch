#!/usr/bin/env python
"""
Maricopa County Property Search Application
Main application file
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Windows-specific fixes
import platform
if platform.system() == 'Windows':
    import multiprocessing
    multiprocessing.freeze_support()
    
    # Fix for high DPI
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# Import configuration and logging
from src.config_manager import ConfigManager
from src.logging_config import setup_logging, get_logger, log_exception
from src.database_manager import DatabaseManager
from src.api_client import MaricopaAPIClient
from src.web_scraper import WebScraperManager
from gui.main_window import PropertySearchApp

# [Rest of the application code from earlier...]

def main():
    """Main entry point"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Maricopa Property Search")
        
        # Load configuration
        config = ConfigManager()
        
        # Setup logging
        logging_config = setup_logging(config)
        logger = get_logger(__name__)
        
        # Log application startup
        logging_config.log_application_start("Maricopa Property Search", "1.0")
        
        logger.info("Initializing application components...")
        
        # Create main window
        window = PropertySearchApp(config)
        window.show()
        
        logger.info("Application window displayed successfully")
        logger.info("Application ready for user interaction")
        
        # Start event loop
        exit_code = app.exec_()
        
        logger.info(f"Application exiting with code: {exit_code}")
        logging_config.log_application_shutdown("Maricopa Property Search")
        
        sys.exit(exit_code)
        
    except Exception as e:
        # Fallback logging if main logging system isn't working
        try:
            logger = get_logger(__name__)
            log_exception(logger, e, "main application startup")
        except:
            print(f"CRITICAL ERROR in main(): {e}")
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()