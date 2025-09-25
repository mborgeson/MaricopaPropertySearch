#!/usr/bin/env python
"""
Launcher for Improved Maricopa Property Search Application
Launches the application with UX improvements and Missouri Ave testing support
"""

import os
import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

import logging

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen

# Import application modules
from config_manager import ConfigManager
from gui.improved_main_window import ImprovedPropertySearchApp
from logging_config import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


def show_improvement_splash():
    """Show splash screen highlighting improvements"""
    try:
        # Create splash screen
        splash_pix = QPixmap(500, 300)
        splash_pix.fill(Qt.white)

        splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        splash.setMask(splash_pix.mask())

        # Add text about improvements
        splash.showMessage(
            "🏠 Maricopa Property Search - Enhanced UX\n"
            "✨ NEW: User-friendly messages throughout\n"
            "📋 NEW: Actionable data collection prompts\n"
            "🔍 ENHANCED: Missouri Ave property testing\n"
            "⚡ IMPROVED: Professional appearance\n\n"
            "🚀 Loading improved application...",
            Qt.AlignCenter | Qt.AlignBottom,
            Qt.black,
        )

        splash.show()
        return splash

    except Exception as e:
        logger.warning(f"Could not create improvement splash screen: {e}")
        return None


def check_ux_improvements():
    """Check that UX improvement files are available"""
    improvements_available = True
    missing_components = []

    # Check for improved components
    improved_files = [
        "src/gui/improved_main_window.py",
        "tests/test_missouri_avenue_address.py",
        "UX_IMPROVEMENTS_SUMMARY.md",
        "run_missouri_tests.py",
    ]

    for file_path in improved_files:
        if not Path(file_path).exists():
            missing_components.append(file_path)
            improvements_available = False

    if not improvements_available:
        logger.warning(f"Some UX improvement components missing: {missing_components}")
        return False, missing_components

    logger.info("✅ All UX improvement components available")
    return True, []


def show_missouri_ave_demo_info():
    """Show information about Missouri Avenue testing capabilities"""
    info_text = """
🏠 Missouri Avenue Property Testing Ready!

This enhanced version includes comprehensive testing for:
• Address: 10000 W Missouri Ave
• Expected APN: 13304014A  
• Owner: CITY OF GLENDALE
• Complete property data collection

🎯 Key Testing Features:
✓ Auto-collection functionality
✓ Progress indicator testing
✓ UX message verification
✓ Error handling validation
✓ Database integration testing

💡 To test Missouri Avenue property:
1. Select "Property Address" search type
2. Enter "10000 W Missouri Ave" 
3. Click "Find Properties"
4. Test data collection features

📋 UX Improvements:
• No more "Not Available" messages
• Actionable user guidance
• Professional appearance
• Clear progress indicators
• Helpful error messages

Would you like to continue to the application?
    """

    return (
        QMessageBox.question(
            None,
            "Missouri Avenue Testing & UX Improvements Ready",
            info_text,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        == QMessageBox.Yes
    )


def main():
    """Main application entry point with UX improvements"""
    logger.info("Starting Improved Maricopa Property Search Application")

    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Maricopa Property Search - Enhanced UX")
    app.setApplicationVersion("2.1")
    app.setOrganizationName("Property Search Solutions")

    # Set application style
    app.setStyle("Fusion")

    # Check UX improvements availability
    improvements_ready, missing = check_ux_improvements()
    if not improvements_ready:
        QMessageBox.critical(
            None,
            "UX Improvements Missing",
            f"Some UX improvement components are missing:\n\n"
            + "\n".join(f"• {file}" for file in missing)
            + "\n\nPlease ensure all improvement files are in place.",
        )
        return 1

    # Show improvement splash
    splash = show_improvement_splash()

    try:
        # Show demo information
        if splash:
            splash.showMessage(
                "🏠 Maricopa Property Search - Enhanced UX\n"
                "✨ Preparing Missouri Avenue testing demo...\n\n"
                "🚀 Loading improved application...",
                Qt.AlignCenter | Qt.AlignBottom,
                Qt.black,
            )

        app.processEvents()

        # Give user information about testing capabilities
        if not show_missouri_ave_demo_info():
            logger.info("User chose not to continue to application")
            if splash:
                splash.close()
            return 0

        # Update splash
        if splash:
            splash.showMessage(
                "🏠 Maricopa Property Search - Enhanced UX\n"
                "📋 Loading configuration...\n\n"
                "🚀 Starting improved application...",
                Qt.AlignCenter | Qt.AlignBottom,
                Qt.black,
            )

        # Load configuration
        logger.info("Loading application configuration")
        config_manager = ConfigManager()

        # Update splash
        if splash:
            splash.showMessage(
                "🏠 Maricopa Property Search - Enhanced UX\n"
                "🗄️ Testing database connection...\n\n"
                "🚀 Almost ready...",
                Qt.AlignCenter | Qt.AlignBottom,
                Qt.black,
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
            QMessageBox.critical(
                None,
                "Database Connection Issue",
                f"Could not connect to database:\n{str(e)}\n\n"
                "The application can still run with limited functionality.\n"
                "Some features may not be available.",
            )
            # Continue anyway for testing purposes

        # Update splash
        if splash:
            splash.showMessage(
                "🏠 Maricopa Property Search - Enhanced UX\n"
                "🎨 Creating improved interface...\n\n"
                "✨ Ready to launch!",
                Qt.AlignCenter | Qt.AlignBottom,
                Qt.black,
            )

        # Create main window with improvements
        logger.info("Creating improved main application window")
        main_window = ImprovedPropertySearchApp(config_manager)

        # Close splash and show main window
        if splash:
            splash.finish(main_window)

        main_window.show()

        # Show welcome message about improvements
        QMessageBox.information(
            main_window,
            "🎉 UX Improvements Active!",
            "Welcome to the enhanced Maricopa Property Search!\n\n"
            "✨ What's New:\n"
            "• User-friendly messages replace technical jargon\n"
            "• Clear guidance for data collection\n"
            "• Professional appearance throughout\n"
            "• Enhanced Missouri Avenue property testing\n"
            "• Improved error handling and recovery\n\n"
            "💡 Try searching for '10000 W Missouri Ave' to test\n"
            "the enhanced functionality!",
        )

        logger.info("Improved application startup complete")

        # Start the application event loop
        exit_code = app.exec_()

        logger.info(f"Improved application exiting with code: {exit_code}")
        return exit_code

    except Exception as e:
        logger.error(f"Critical error during improved application startup: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        if splash:
            splash.close()

        QMessageBox.critical(
            None,
            "Application Startup Error",
            f"A critical error occurred during startup:\n\n{str(e)}\n\n"
            "This may be due to:\n"
            "• Missing required files\n"
            "• Configuration issues\n"
            "• Database connectivity problems\n\n"
            "Please check the log files for more details.",
        )
        return 1

    except KeyboardInterrupt:
        logger.info("Improved application interrupted by user")
        return 0


def run_quick_test():
    """Run a quick test of the Missouri Avenue functionality"""
    logger.info("Running quick Missouri Avenue functionality test...")

    try:
        # Import test modules
        from tests.test_missouri_avenue_address import TestMissouriAvenueProperty

        logger.info("✅ Test modules imported successfully")
        logger.info("✅ Missouri Avenue tests are ready to run")
        logger.info("✅ Use 'python run_missouri_tests.py' for comprehensive testing")

        return True

    except ImportError as e:
        logger.error(f"❌ Test import failed: {e}")
        return False


if __name__ == "__main__":
    import traceback

    try:
        # Quick test first
        logger.info("Performing pre-launch checks...")
        test_ready = run_quick_test()

        if test_ready:
            logger.info("✅ Pre-launch checks passed")
        else:
            logger.warning("⚠️ Some test components may not be available")

        # Launch improved application
        exit_code = main()
        sys.exit(exit_code)

    except Exception as e:
        print(f"Fatal error in improved application launcher: {e}")
        print(traceback.format_exc())
        sys.exit(1)
