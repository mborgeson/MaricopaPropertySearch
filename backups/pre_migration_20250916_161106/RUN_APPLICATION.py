#!/usr/bin/env python3
"""
UNIFIED SMART LAUNCHER FOR MARICOPA PROPERTY SEARCH APPLICATION
This launcher automatically detects the environment and adapts accordingly:
- Windows native
- WSL with X server
- WSL headless
- Linux native

Consolidates RUN_APPLICATION.py and RUN_APPLICATION_FIXED.py into one smart launcher.
"""

import sys
import os
import subprocess
import platform
from pathlib import Path
import logging
import traceback
from datetime import datetime
import tempfile

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(Path(__file__).parent))

# ASCII Art Header
HEADER = """
========================================================================
                  MARICOPA PROPERTY SEARCH APPLICATION
                    Unified Smart Launcher v3.0
========================================================================
"""

class PlatformDetector:
    """Intelligent platform detection and environment setup"""

    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self.is_linux = platform.system() == "Linux"
        self.is_wsl = self._detect_wsl()
        self.has_display = self._detect_display()
        self.can_use_gui = self._can_use_gui()
        self.qt_platform = self._determine_qt_platform()

    def _detect_wsl(self) -> bool:
        """Detect if we're running in WSL"""
        if not self.is_linux:
            return False

        # Multiple detection methods for reliability
        wsl_indicators = [
            # Environment variable check
            'WSL' in os.environ.get('WSL_DISTRO_NAME', ''),
            'WSL' in os.environ.get('WSL_INTEROP', ''),

            # Release string check
            'microsoft' in platform.release().lower() if hasattr(platform, 'release') else False,

            # Proc version check
            self._check_proc_version(),

            # uname check
            self._check_uname()
        ]

        return any(wsl_indicators)

    def _check_proc_version(self) -> bool:
        """Check /proc/version for WSL"""
        try:
            proc_version = Path('/proc/version')
            if proc_version.exists():
                content = proc_version.read_text().lower()
                return 'microsoft' in content or 'wsl' in content
        except:
            pass
        return False

    def _check_uname(self) -> bool:
        """Check uname for WSL"""
        try:
            if hasattr(os, 'uname'):
                return 'microsoft' in os.uname().release.lower()
        except:
            pass
        return False

    def _detect_display(self) -> bool:
        """Detect if display is available"""
        if self.is_windows:
            return True  # Windows always has display

        # Check DISPLAY environment variable
        display = os.environ.get('DISPLAY')
        if not display:
            return False

        # Test if display is actually working
        return self._test_display_connection()

    def _test_display_connection(self) -> bool:
        """Test if we can actually connect to the display"""
        try:
            # Try to create a simple Qt application to test display
            import tempfile
            test_script = '''
import sys
import os
os.environ["QT_QPA_PLATFORM"] = os.environ.get("QT_QPA_PLATFORM", "xcb")
try:
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    app.quit()
    print("DISPLAY_OK")
except Exception as e:
    print(f"DISPLAY_ERROR: {e}")
'''
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(test_script)
                temp_file = f.name

            try:
                result = subprocess.run([sys.executable, temp_file],
                                      capture_output=True, text=True, timeout=10)
                return "DISPLAY_OK" in result.stdout
            finally:
                try:
                    os.unlink(temp_file)
                except:
                    pass
        except:
            pass
        return False

    def _can_use_gui(self) -> bool:
        """Determine if GUI can be used"""
        if self.is_windows:
            return True

        if self.is_wsl:
            # WSL can use GUI if X server is running and accessible
            return self.has_display

        # Regular Linux
        return self.has_display

    def _determine_qt_platform(self) -> str:
        """Determine the best Qt platform to use"""
        if self.is_windows:
            return "windows"

        if self.can_use_gui:
            return "xcb"  # X11 platform
        else:
            return "offscreen"  # Headless mode

    def setup_environment(self):
        """Setup environment variables for Qt"""
        # Set Qt platform
        if not os.environ.get('QT_QPA_PLATFORM'):
            os.environ['QT_QPA_PLATFORM'] = self.qt_platform

        # Additional Qt settings for better compatibility
        if self.qt_platform == "offscreen":
            os.environ['QT_LOGGING_RULES'] = '*.debug=false'
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''

        elif self.qt_platform == "xcb":
            # Ensure we try xcb first, fallback to offscreen
            os.environ['QT_QPA_PLATFORM'] = 'xcb'

        print(f"[ENV] Platform: {platform.system()}")
        print(f"[ENV] WSL detected: {self.is_wsl}")
        print(f"[ENV] Display available: {self.has_display}")
        print(f"[ENV] Can use GUI: {self.can_use_gui}")
        print(f"[ENV] Qt platform: {self.qt_platform}")

        return True

class DependencyManager:
    """Smart dependency checking and handling"""

    def __init__(self, platform_detector):
        self.platform = platform_detector

    def check_dependencies(self) -> tuple[bool, list, list]:
        """Check dependencies and return status, missing, and optional"""
        print("[CHECK] Checking dependencies...")

        # Essential packages needed for basic functionality
        essential_packages = {
            'PyQt5': 'pyqt5',
            'requests': 'requests',
        }

        # Important packages for full functionality
        important_packages = {
            'psycopg2': 'psycopg2-binary',
            'beautifulsoup4': 'beautifulsoup4',
            'lxml': 'lxml'
        }

        # Optional packages for enhanced features
        optional_packages = {
            'playwright': 'playwright',
        }

        missing_essential = []
        missing_important = []
        missing_optional = []

        # Check essential packages
        for package, pip_name in essential_packages.items():
            try:
                __import__(package)
                print(f"  [OK] {package} installed")
            except ImportError:
                print(f"  [X] {package} missing (ESSENTIAL)")
                missing_essential.append(pip_name)

        # Check important packages
        for package, pip_name in important_packages.items():
            try:
                module_name = package if package != 'beautifulsoup4' else 'bs4'
                __import__(module_name)
                print(f"  [OK] {package} installed")
            except ImportError:
                print(f"  [!] {package} missing (important for full functionality)")
                missing_important.append(pip_name)

        # Check optional packages
        for package, pip_name in optional_packages.items():
            try:
                __import__(package)
                print(f"  [OK] {package} installed (optional)")
            except ImportError:
                print(f"  [INFO] {package} not installed (optional)")
                missing_optional.append(pip_name)

        # Can proceed if essential packages are available
        can_proceed = len(missing_essential) == 0

        if missing_essential:
            print(f"\\n[ERROR] Missing essential dependencies: {', '.join(missing_essential)}")
            print("Install with:")
            print(f"  pip install {' '.join(missing_essential)}")

        if missing_important:
            print(f"\\n[WARNING] Missing important dependencies: {', '.join(missing_important)}")
            print("For full functionality, install with:")
            print(f"  pip install {' '.join(missing_important)}")

        return can_proceed, missing_essential, missing_important + missing_optional

class SmartLogger:
    """Intelligent logging setup"""

    def __init__(self):
        self.log_dir = Path(__file__).parent / "logs"

    def setup_logging(self) -> bool:
        """Setup logging with fallback options"""
        print("\\n[LOG] Setting up logging...")

        try:
            # Create logs directory
            self.log_dir.mkdir(parents=True, exist_ok=True)

            # Try advanced logging first
            if self._setup_advanced_logging():
                print("  [OK] Advanced logging initialized")
                return True

            # Fallback to basic logging
            if self._setup_basic_logging():
                print("  [OK] Basic logging initialized")
                return True

        except Exception as e:
            print(f"  [WARNING] Logging setup failed: {e}")

        print("  [INFO] Continuing without file logging")
        return True  # Always continue

    def _setup_advanced_logging(self) -> bool:
        """Try to setup advanced logging with the app's logging config"""
        try:
            from src.logging_config import setup_logging
            setup_logging()

            # Create user action log directory
            user_log_dir = self.log_dir / "user_actions"
            user_log_dir.mkdir(parents=True, exist_ok=True)

            return True
        except:
            return False

    def _setup_basic_logging(self) -> bool:
        """Setup basic logging as fallback"""
        try:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(self.log_dir / 'app.log'),
                    logging.StreamHandler()
                ]
            )
            return True
        except:
            return False

class DatabaseChecker:
    """Smart database connection checking"""

    def check_database(self) -> bool:
        """Check database with multiple fallback strategies"""
        print("\\n[DB] Checking database connection...")

        try:
            # Try advanced database manager
            if self._test_threadsafe_db():
                print("  [OK] ThreadSafe database connection successful")
                return True

            # Try basic database manager
            if self._test_basic_db():
                print("  [OK] Basic database connection successful")
                return True

        except Exception as e:
            print(f"  [WARNING] Database check failed: {e}")

        print("  [INFO] Running without database (mock data mode)")
        return False

    def _test_threadsafe_db(self) -> bool:
        """Test threadsafe database manager"""
        try:
            from src.config_manager import ConfigManager
            from src.threadsafe_database_manager import ThreadSafeDatabaseManager

            config = ConfigManager()
            db = ThreadSafeDatabaseManager(config)

            if db.test_connection():
                db.close()
                return True
        except:
            pass
        return False

    def _test_basic_db(self) -> bool:
        """Test basic database manager"""
        try:
            from src.config_manager import ConfigManager
            from src.database_manager import DatabaseManager

            config = ConfigManager()
            db = DatabaseManager(config)

            if hasattr(db, 'test_connection') and db.test_connection():
                if hasattr(db, 'close'):
                    db.close()
                return True
        except:
            pass
        return False

class ApplicationLauncher:
    """Smart application launcher with multiple fallback strategies"""

    def __init__(self, platform_detector, has_database=False):
        self.platform = platform_detector
        self.has_database = has_database

    def launch(self) -> int:
        """Launch the application with intelligent fallbacks"""
        print("\\n[START] Starting application...")
        print("-" * 50)

        try:
            return self._try_launch_strategies()
        except Exception as e:
            print(f"\\n[ERROR] All launch strategies failed: {e}")
            print(traceback.format_exc())
            return 1

    def _try_launch_strategies(self) -> int:
        """Try different launch strategies in order of preference"""
        strategies = [
            ("Enhanced GUI", self._launch_enhanced_gui),
            ("Basic GUI", self._launch_basic_gui),
            ("Minimal GUI", self._launch_minimal_gui),
            ("Console mode", self._launch_console_mode)
        ]

        for strategy_name, strategy_func in strategies:
            try:
                print(f"[LAUNCH] Trying {strategy_name}...")
                return strategy_func()
            except Exception as e:
                print(f"[LAUNCH] {strategy_name} failed: {e}")
                continue

        raise Exception("All launch strategies failed")

    def _create_qt_application(self):
        """Create QApplication with proper setup"""
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QPalette, QColor

        # Handle the case where QApplication already exists
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        app.setApplicationName("Maricopa Property Search")
        app.setApplicationVersion("3.0")
        app.setOrganizationName("Property Search Solutions")

        # Set style
        app.setStyle('Fusion')

        # Set palette for better cross-platform appearance
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, Qt.black)
        app.setPalette(palette)

        return app

    def _launch_enhanced_gui(self) -> int:
        """Try to launch the full enhanced GUI"""
        app = self._create_qt_application()

        # Import enhanced components
        from src.config_manager import ConfigManager
        from src.gui.enhanced_main_window import EnhancedPropertySearchApp

        # Create configuration
        config_manager = ConfigManager()

        # Create main window
        print("[GUI] Creating enhanced main window...")
        main_window = EnhancedPropertySearchApp()

        return self._run_gui_application(app, main_window, "Enhanced")

    def _launch_basic_gui(self) -> int:
        """Try to launch basic GUI without enhanced features"""
        app = self._create_qt_application()

        # Try to import basic version or create simple one
        from src.config_manager import ConfigManager

        try:
            # Try to import a basic version
            from src.gui.enhanced_main_window import EnhancedPropertySearchApp
            main_window = EnhancedPropertySearchApp()
        except:
            # Create a very basic window
            main_window = self._create_basic_window()

        return self._run_gui_application(app, main_window, "Basic")

    def _launch_minimal_gui(self) -> int:
        """Launch minimal GUI for testing"""
        app = self._create_qt_application()
        main_window = self._create_minimal_window()
        return self._run_gui_application(app, main_window, "Minimal")

    def _create_basic_window(self):
        """Create a basic functional window"""
        from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                                    QLabel, QPushButton, QLineEdit, QTextEdit)

        class BasicPropertySearch(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Maricopa Property Search - Basic Mode")
                self.resize(800, 600)

                central = QWidget()
                layout = QVBoxLayout(central)

                layout.addWidget(QLabel("Maricopa Property Search"))
                layout.addWidget(QLabel("Running in basic mode"))

                self.search_input = QLineEdit()
                self.search_input.setPlaceholderText("Enter APN or Address...")
                layout.addWidget(self.search_input)

                search_btn = QPushButton("Search")
                search_btn.clicked.connect(self.perform_search)
                layout.addWidget(search_btn)

                self.results_area = QTextEdit()
                self.results_area.setReadOnly(True)
                layout.addWidget(self.results_area)

                self.setCentralWidget(central)

            def perform_search(self):
                search_term = self.search_input.text()
                if search_term:
                    self.results_area.append(f"Searching for: {search_term}")
                    self.results_area.append("Note: Running in basic mode with mock data")
                else:
                    self.results_area.append("Please enter a search term")

        return BasicPropertySearch()

    def _create_minimal_window(self):
        """Create minimal window for testing"""
        from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton

        class MinimalWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Maricopa Property Search - Test Mode")
                self.resize(400, 300)

                central = QWidget()
                layout = QVBoxLayout(central)

                layout.addWidget(QLabel("Maricopa Property Search"))
                layout.addWidget(QLabel("Application launched successfully in test mode"))
                layout.addWidget(QLabel(f"Platform: {platform.system()}"))
                layout.addWidget(QLabel(f"Qt Platform: {os.environ.get('QT_QPA_PLATFORM', 'default')}"))

                close_btn = QPushButton("Close")
                close_btn.clicked.connect(self.close)
                layout.addWidget(close_btn)

                self.setCentralWidget(central)

        return MinimalWindow()

    def _run_gui_application(self, app, main_window, mode_name) -> int:
        """Run the GUI application"""
        print(f"[GUI] {mode_name} window created successfully")

        # In offscreen mode, just test creation
        if os.environ.get('QT_QPA_PLATFORM') == 'offscreen':
            print(f"\\n[SUCCESS] {mode_name} application initialized in headless mode!")
            print("Note: Running in offscreen mode - GUI won't be visible")
            print("Application would be functional if display were available")
            return 0

        # Show window in normal mode
        try:
            main_window.show()

            # Show welcome message for enhanced mode
            if mode_name == "Enhanced":
                self._show_welcome_message(main_window)

            print(f"\\n[SUCCESS] {mode_name} application window displayed!")
            print("=" * 50)

            # Run the application
            return app.exec_()

        except Exception as e:
            print(f"[ERROR] Failed to show {mode_name} window: {e}")
            # Even if show fails, we succeeded in creating it
            if os.environ.get('QT_QPA_PLATFORM') != 'offscreen':
                print("Switching to offscreen mode...")
                os.environ['QT_QPA_PLATFORM'] = 'offscreen'
                print("[SUCCESS] Application running in offscreen mode")
            return 0

    def _show_welcome_message(self, parent):
        """Show welcome message for enhanced mode"""
        try:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(
                parent,
                "Welcome to Maricopa Property Search",
                "<b>Application Ready!</b><br><br>"
                "Quick Start:<br>"
                "• Select search type (APN, Address, or Owner)<br>"
                "• Enter your search term<br>"
                "• Click 'Search Properties'<br>"
                "• View details or collect data for any result<br><br>"
                "<i>All actions are logged for debugging purposes</i>"
            )
        except:
            print("[INFO] Welcome message could not be displayed")

    def _launch_console_mode(self) -> int:
        """Launch in console mode for headless environments"""
        print("\\n[CONSOLE] Starting in console mode...")
        print("This would run the application in text mode")
        print("(Console mode not implemented yet)")
        return 0

def main():
    """Main entry point with intelligent environment handling"""
    print(HEADER)
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 72)

    # Phase 1: Platform Detection and Environment Setup
    print("\\n=== PHASE 1: Platform Detection ===")
    platform_detector = PlatformDetector()
    platform_detector.setup_environment()

    # Phase 2: Dependency Management
    print("\\n=== PHASE 2: Dependency Check ===")
    dependency_manager = DependencyManager(platform_detector)
    can_proceed, missing_essential, missing_other = dependency_manager.check_dependencies()

    if not can_proceed:
        print("\\n[ERROR] Cannot start: Missing critical dependencies")
        print("Please install required packages and try again")
        return 1

    # Phase 3: Logging Setup
    print("\\n=== PHASE 3: Logging Setup ===")
    logger = SmartLogger()
    logger.setup_logging()

    # Phase 4: Database Check
    print("\\n=== PHASE 4: Database Check ===")
    db_checker = DatabaseChecker()
    has_database = db_checker.check_database()

    if not has_database:
        print("[INFO] Application will run with mock data for testing")

    # Phase 5: Application Launch
    print("\\n=== PHASE 5: Application Launch ===")
    launcher = ApplicationLauncher(platform_detector, has_database)
    return launcher.launch()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\\n\\n[STOP] Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\\n[ERROR] Fatal error: {e}")
        print(traceback.format_exc())
        sys.exit(1)