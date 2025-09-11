#!/usr/bin/env python
"""
Dependency Verification Script
Comprehensive testing of all dependencies and environment setup
"""

import sys
import os
import platform
from pathlib import Path
import subprocess

# Add project to path
PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))

def print_header(title):
    """Print formatted header"""
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_section(title):
    """Print section header"""
    print(f"\n{title}")
    print("-" * len(title))

def test_environment():
    """Test conda environment"""
    print_section("Environment Information")
    
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")
    
    # Check conda environment
    try:
        conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'Not set')
        print(f"Conda environment: {conda_env}")
        
        if conda_env != 'maricopa_property':
            print("WARNING: Not in the correct conda environment!")
            print("Please run: conda activate maricopa_property")
            return False
        else:
            print("OK: Correct environment active")
            return True
    except Exception as e:
        print(f"ERROR: Could not check environment: {e}")
        return False

def test_core_imports():
    """Test all core package imports"""
    print_section("Core Package Imports")
    
    packages = [
        ('pandas', 'Data manipulation library'),
        ('numpy', 'Numerical computing'),
        ('matplotlib', 'Plotting library'),
        ('PyQt5', 'GUI framework'),
        ('PyQt5.QtWidgets', 'PyQt5 widgets'),
        ('PyQt5.QtCore', 'PyQt5 core'),
        ('sqlalchemy', 'Database ORM'),
        ('psycopg2', 'PostgreSQL adapter'),
        ('selenium', 'Web scraping/automation'),
        ('requests', 'HTTP requests'),
        ('bs4', 'BeautifulSoup HTML parsing'),
        ('dotenv', 'Environment variables'),
        ('lxml', 'XML/HTML processing'),
        ('openpyxl', 'Excel file processing'),
    ]
    
    failed = []
    for package, description in packages:
        try:
            __import__(package)
            print(f"OK:   {package:<20} - {description}")
        except ImportError as e:
            print(f"FAIL: {package:<20} - {e}")
            failed.append(package)
    
    if failed:
        print(f"\nFailed imports: {', '.join(failed)}")
        return False
    else:
        print("\nAll core packages imported successfully!")
        return True

def test_psycopg2_detailed():
    """Detailed psycopg2 testing"""
    print_section("PostgreSQL Driver (psycopg2) Details")
    
    try:
        import psycopg2
        print(f"psycopg2 version: {psycopg2.__version__}")
        
        # Test both psycopg2 and psycopg2-binary
        try:
            import psycopg2.extensions
            print("psycopg2 extensions available")
        except ImportError:
            print("WARNING: psycopg2 extensions not available")
        
        return True
    except ImportError as e:
        print(f"FAIL: psycopg2 not available: {e}")
        
        # Check for psycopg2-binary
        try:
            import psycopg2
            print("psycopg2-binary available as fallback")
            return True
        except ImportError:
            print("FAIL: Neither psycopg2 nor psycopg2-binary available")
            return False

def test_pyqt5_detailed():
    """Detailed PyQt5 testing"""
    print_section("PyQt5 GUI Framework Details")
    
    try:
        from PyQt5 import QtCore, QtWidgets, QtGui
        from PyQt5.QtWidgets import QApplication
        
        print(f"PyQt5 version: {QtCore.PYQT_VERSION_STR}")
        print(f"Qt version: {QtCore.QT_VERSION_STR}")
        
        # Test application creation (without display)
        import os
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # Headless mode
        
        app = QApplication([])
        print("QApplication created successfully")
        app.quit()
        
        return True
    except ImportError as e:
        print(f"FAIL: PyQt5 import error: {e}")
        return False
    except Exception as e:
        print(f"FAIL: PyQt5 runtime error: {e}")
        return False

def test_project_structure():
    """Test project directory structure"""
    print_section("Project Structure")
    
    required_dirs = [
        'src', 'scripts', 'config', 'logs', 
        'exports', 'cache', 'drivers', 'database'
    ]
    
    required_files = [
        'environment.yml',
        'requirements.txt',
        '.env',
        'launch_app.bat',
        'src/maricopa_property_search.py'
    ]
    
    missing_dirs = []
    missing_files = []
    
    # Check directories
    for dir_name in required_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
            print(f"OK:   Directory '{dir_name}' exists")
        else:
            print(f"FAIL: Directory '{dir_name}' missing")
            missing_dirs.append(dir_name)
    
    # Check files
    for file_name in required_files:
        file_path = PROJECT_ROOT / file_name
        if file_path.exists():
            print(f"OK:   File '{file_name}' exists")
        else:
            print(f"FAIL: File '{file_name}' missing")
            missing_files.append(file_name)
    
    success = len(missing_dirs) == 0 and len(missing_files) == 0
    
    if not success:
        if missing_dirs:
            print(f"\nMissing directories: {', '.join(missing_dirs)}")
        if missing_files:
            print(f"Missing files: {', '.join(missing_files)}")
    
    return success

def test_database_connection():
    """Test database connection"""
    print_section("Database Connection Test")
    
    try:
        import psycopg2
        from dotenv import load_dotenv
        
        # Load environment variables
        env_path = PROJECT_ROOT / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            print("Environment variables loaded from .env file")
        else:
            print("WARNING: .env file not found")
        
        # Try connection with default values
        conn_params = {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'port': int(os.environ.get('DB_PORT', '5433')),
            'database': os.environ.get('DB_NAME', 'maricopa_properties'),
            'user': os.environ.get('DB_USER', 'property_user'),
            'password': os.environ.get('DB_PASSWORD', 'Wildcats777!!')
        }
        
        print(f"Attempting connection to: {conn_params['host']}:{conn_params['port']}")
        print(f"Database: {conn_params['database']}")
        print(f"User: {conn_params['user']}")
        
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"OK: PostgreSQL connected - {version}")
        
        # Check for tables
        cursor.execute("""
            SELECT count(*) FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cursor.fetchone()[0]
        print(f"OK: Found {table_count} tables in database")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"FAIL: Database connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Ensure PostgreSQL is running")
        print("2. Check connection parameters in .env file")
        print("3. Verify user permissions")
        return False

def provide_solutions(failed_tests):
    """Provide solutions for failed tests"""
    print_section("Solutions for Failed Tests")
    
    solutions = {
        'environment': [
            "Run: conda activate maricopa_property",
            "If environment doesn't exist, run: conda env create -f environment.yml"
        ],
        'imports': [
            "Install missing packages with: conda install -c conda-forge <package_name>",
            "Or reinstall environment: conda env remove -n maricopa_property && conda env create -f environment.yml"
        ],
        'psycopg2': [
            "Install with: conda install -c conda-forge psycopg2",
            "Or: pip install psycopg2-binary"
        ],
        'pyqt5': [
            "Install with: conda install -c conda-forge pyqt",
            "For display issues: pip install PyQt5"
        ],
        'structure': [
            "Create missing directories manually",
            "Check project setup documentation"
        ],
        'database': [
            "Start PostgreSQL service: net start postgresql-x64-14",
            "Check database configuration in .env file",
            "Run database setup script: scripts\\setup_database.bat"
        ]
    }
    
    for test_type in failed_tests:
        if test_type in solutions:
            print(f"\n{test_type.upper()} Issues:")
            for solution in solutions[test_type]:
                print(f"  - {solution}")

def main():
    """Run all verification tests"""
    print_header("Maricopa Property Search - Dependency Verification")
    
    # Track test results
    test_results = {}
    
    # Run tests
    test_results['environment'] = test_environment()
    test_results['imports'] = test_core_imports()
    test_results['psycopg2'] = test_psycopg2_detailed()
    test_results['pyqt5'] = test_pyqt5_detailed()
    test_results['structure'] = test_project_structure()
    test_results['database'] = test_database_connection()
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    passed = []
    failed = []
    
    test_names = {
        'environment': 'Conda Environment',
        'imports': 'Core Package Imports',
        'psycopg2': 'PostgreSQL Driver',
        'pyqt5': 'PyQt5 GUI Framework',
        'structure': 'Project Structure',
        'database': 'Database Connection'
    }
    
    for test_key, result in test_results.items():
        test_name = test_names[test_key]
        if result:
            print(f"PASS: {test_name}")
            passed.append(test_key)
        else:
            print(f"FAIL: {test_name}")
            failed.append(test_key)
    
    print(f"\nTotal: {len(passed)} passed, {len(failed)} failed")
    
    if failed:
        provide_solutions(failed)
        print("\nPlease resolve the failed tests before running the application.")
        return 1
    else:
        print("\nAll tests passed! Your environment is ready.")
        print("You can now run: launch_app.bat")
        return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        input("\nPress Enter to close...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error during verification: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to close...")
        sys.exit(1)