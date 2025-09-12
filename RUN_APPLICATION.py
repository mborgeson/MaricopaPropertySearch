#!/usr/bin/env python
"""
MASTER LAUNCHER FOR MARICOPA PROPERTY SEARCH APPLICATION
This is the single script to run the entire application with all necessary checks and setup
"""

import sys
import os
import subprocess
from pathlib import Path
import logging
import traceback
from datetime import datetime

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Ensure parent directory is in path
sys.path.insert(0, str(Path(__file__).parent))

# ASCII Art Header
HEADER = """
========================================================================
                  MARICOPA PROPERTY SEARCH APPLICATION                 
                         Enhanced Version 2.0                          
========================================================================
"""

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("[CHECK] Checking dependencies...")
    
    required_packages = {
        'PyQt5': 'pyqt5',
        'psycopg2': 'psycopg2-binary',
        'requests': 'requests',
        'playwright': 'playwright',
        'beautifulsoup4': 'beautifulsoup4',
        'lxml': 'lxml'
    }
    
    missing = []
    for package, pip_name in required_packages.items():
        try:
            __import__(package if package != 'beautifulsoup4' else 'bs4')
            print(f"  [OK] {package} installed")
        except ImportError:
            print(f"  [X] {package} missing")
            missing.append(pip_name)
    
    if missing:
        print("\n[WARNING]  Missing dependencies detected!")
        print("Install them with:")
        print(f"  pip install {' '.join(missing)}")
        if 'playwright' in missing:
            print("  playwright install chromium")
        return False
    
    return True

def check_database():
    """Check database connection"""
    print("\n[DB]  Checking database connection...")
    
    try:
        from src.config_manager import ConfigManager
        from src.threadsafe_database_manager import ThreadSafeDatabaseManager
        
        config = ConfigManager()
        db = ThreadSafeDatabaseManager(config)
        
        if db.test_connection():
            print("  [OK] Database connection successful")
            db.close()
            return True
        else:
            print("  [WARNING]  Database connection failed")
            print("  The application will run with limited functionality")
            return False
            
    except Exception as e:
        print(f"  [WARNING]  Database check failed: {e}")
        print("  The application will run with limited functionality")
        return False

def check_environment():
    """Check environment configuration"""
    print("\n[CONFIG]  Checking environment configuration...")
    
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print("  [OK] .env file found")
    else:
        print("  [WARNING]  .env file not found (using defaults)")
    
    # Check conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'Not set')
    print(f"  [ENV] Conda environment: {conda_env}")
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"  [PYTHON] Python version: {python_version}")
    
    return True

def initialize_logging():
    """Initialize logging system"""
    print("\n[LOG] Initializing logging system...")
    
    try:
        from src.logging_config import setup_logging
        setup_logging()
        
        # Create user action log directory
        log_dir = Path(__file__).parent / "logs" / "user_actions"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        print("  [OK] Logging initialized")
        print(f"  [DIR] Log directory: {Path(__file__).parent / 'logs'}")
        return True
        
    except Exception as e:
        print(f"  [ERROR] Logging initialization failed: {e}")
        return False

def run_application():
    """Run the main application"""
    print("\n[START] Starting application...")
    print("-" * 50)
    
    try:
        # Import PyQt5
        from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
        from PyQt5.QtCore import Qt, QTimer
        from PyQt5.QtGui import QPixmap, QPalette, QColor
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("Maricopa Property Search - Master")
        app.setApplicationVersion("2.0")
        app.setOrganizationName("Property Search Solutions")
        app.setStyle('Fusion')
        
        # Set dark-friendly palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, Qt.black)
        app.setPalette(palette)
        
        # Create splash screen
        splash_pix = QPixmap(600, 400)
        splash_pix.fill(QColor(52, 73, 94))
        
        splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        splash.showMessage(
            "\n\n[HOME] MARICOPA PROPERTY SEARCH\n\n"
            "Enhanced Version with:\n"
            "* Auto-collection on search\n"
            "* Batch data collection\n"
            "* Comprehensive search options\n"
            "[LOG] User action logging\n"
            "[START] Performance optimizations\n\n"
            "Loading application...",
            Qt.AlignCenter,
            Qt.white
        )
        splash.show()
        app.processEvents()
        
        # Import main application
        from src.config_manager import ConfigManager
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp
        
        # Load configuration
        config_manager = ConfigManager()
        
        # Create main window
        main_window = EnhancedPropertySearchApp(config_manager)
        
        # Close splash and show main window
        splash.finish(main_window)
        main_window.show()
        
        # Show welcome message
        QMessageBox.information(
            main_window,
            "Welcome to Maricopa Property Search",
            "[HOME] <b>Application Ready!</b><br><br>"
            "Quick Start:<br>"
            "• Select search type (APN, Address, or Owner)<br>"
            "• Enter your search term<br>"
            "• Click 'Search Properties'<br>"
            "• View details or collect data for any result<br><br>"
            "<i>All actions are logged for debugging purposes</i>"
        )
        
        print("\n[SUCCESS] Application started successfully!")
        print("=" * 50)
        
        # Run the application
        return app.exec_()
        
    except ImportError as e:
        print(f"\n[ERROR] Import error: {e}")
        print("Please ensure all dependencies are installed")
        return 1
        
    except Exception as e:
        print(f"\n[ERROR] Error starting application: {e}")
        print(traceback.format_exc())
        return 1

def main():
    """Main entry point"""
    print(HEADER)
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 72)
    
    # Run checks
    deps_ok = check_dependencies()
    db_ok = check_database()
    env_ok = check_environment()
    log_ok = initialize_logging()
    
    if not deps_ok:
        print("\n[ERROR] Cannot start: Missing critical dependencies")
        print("Please install required packages and try again")
        return 1
    
    if not log_ok:
        print("\n[WARNING]  Warning: Logging system not fully initialized")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return 1
    
    if not db_ok:
        print("\n[WARNING]  Warning: Database not available")
        print("The application will run with limited functionality")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return 1
    
    # Run the application
    return run_application()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[STOP] Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        print(traceback.format_exc())
        sys.exit(1)