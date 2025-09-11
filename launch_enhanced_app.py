#!/usr/bin/env python
"""
Enhanced Property Search Application Launcher
Launches the property search app with background data collection
"""

import sys
import os
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

import logging
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont

# Import application modules
from config_manager import ConfigManager
from gui.enhanced_main_window import EnhancedPropertySearchApp
from logging_config import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


def show_splash_screen():
    """Show splash screen during startup"""
    try:
        # Create a simple splash screen
        splash_pix = QPixmap(400, 200)
        splash_pix.fill(Qt.white)
        
        splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        splash.setMask(splash_pix.mask())
        
        # Add text to splash screen
        splash.showMessage(
            "Maricopa Property Search\n"
            "Enhanced with Background Data Collection\n\n"
            "Initializing application...",
            Qt.AlignCenter | Qt.AlignBottom,
            Qt.black
        )
        
        splash.show()
        return splash
        
    except Exception as e:
        logger.warning(f"Could not create splash screen: {e}")
        return None


def check_system_requirements():
    """Check system requirements and dependencies"""
    requirements_met = True
    missing_deps = []
    
    # Check Python version
    if sys.version_info < (3, 7):
        logger.error("Python 3.7 or higher is required")
        requirements_met = False
    
    # Check required packages
    required_packages = [
        'PyQt5',
        'psycopg2',
        'playwright',
        'asyncio',
        'json',
        'csv',
        'pathlib'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_deps.append(package)
            requirements_met = False
    
    if missing_deps:
        logger.error(f"Missing required packages: {', '.join(missing_deps)}")
    
    return requirements_met, missing_deps


def main():
    """Main application entry point"""
    logger.info("Starting Enhanced Maricopa Property Search Application")
    
    # Check system requirements
    requirements_met, missing_deps = check_system_requirements()
    if not requirements_met:
        error_msg = "System requirements not met.\n\n"
        if missing_deps:
            error_msg += f"Missing packages: {', '.join(missing_deps)}\n"
            error_msg += "Please install missing packages using pip."
        
        if 'QApplication' in globals():
            app = QApplication(sys.argv)
            QMessageBox.critical(None, "System Requirements", error_msg)
            sys.exit(1)
        else:
            print(error_msg)
            sys.exit(1)
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Maricopa Property Search - Enhanced")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Property Search Solutions")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Show splash screen
    splash = show_splash_screen()
    
    try:
        # Update splash message
        if splash:
            splash.showMessage(
                "Maricopa Property Search\n"
                "Enhanced with Background Data Collection\n\n"
                "Loading configuration...",
                Qt.AlignCenter | Qt.AlignBottom,
                Qt.black
            )
        
        # Load configuration
        logger.info("Loading application configuration")
        config_manager = ConfigManager()
        
        # Update splash message
        if splash:
            splash.showMessage(
                "Maricopa Property Search\n"
                "Enhanced with Background Data Collection\n\n"
                "Initializing database connection...",
                Qt.AlignCenter | Qt.AlignBottom,
                Qt.black
            )
        
        # Test database connection early
        from threadsafe_database_manager import ThreadSafeDatabaseManager
        try:
            db_test = ThreadSafeDatabaseManager(config_manager)
            if not db_test.test_connection():
                raise Exception("Database connection test failed")
            db_test.close()
            logger.info("Database connection verified")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            if splash:
                splash.close()
            QMessageBox.critical(None, "Database Error", 
                               f"Could not connect to database:\n{str(e)}\n\n"
                               "Please check your database configuration.")
            sys.exit(1)
        
        # Update splash message
        if splash:
            splash.showMessage(
                "Maricopa Property Search\n"
                "Enhanced with Background Data Collection\n\n"
                "Starting main application...",
                Qt.AlignCenter | Qt.AlignBottom,
                Qt.black
            )
        
        # Create main window
        logger.info("Creating main application window")
        main_window = EnhancedPropertySearchApp(config_manager)
        
        # Close splash screen and show main window
        if splash:
            splash.finish(main_window)
        
        main_window.show()
        
        logger.info("Application startup complete")
        
        # Log system information
        logger.info(f"Python version: {sys.version}")
        logger.info(f"PyQt5 version: {getattr(__import__('PyQt5.QtCore'), 'QT_VERSION_STR', 'Unknown')}")
        logger.info(f"Application PID: {os.getpid()}")
        
        # Start the application event loop
        exit_code = app.exec_()
        
        logger.info(f"Application exiting with code: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.error(f"Critical error during application startup: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        if splash:
            splash.close()
        
        QMessageBox.critical(None, "Application Error", 
                           f"A critical error occurred during startup:\n\n{str(e)}\n\n"
                           "Please check the log files for more details.")
        return 1
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0


if __name__ == "__main__":
    import traceback
    
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {e}")
        print(traceback.format_exc())
        sys.exit(1)