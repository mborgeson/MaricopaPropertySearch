#!/usr/bin/env python
"""
Quick Environment Check Script
Non-interactive verification of core dependencies
"""

import sys
import os
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")
sys.path.insert(0, str(PROJECT_ROOT))


def check_environment():
    """Quick environment check"""
    issues = []

    # Check conda environment
    conda_env = os.environ.get("CONDA_DEFAULT_ENV", "Not set")
    if conda_env != "maricopa_property":
        issues.append(
            f"Wrong conda environment: {conda_env} (expected: maricopa_property)"
        )

    # Check core imports
    critical_packages = ["pandas", "PyQt5", "psycopg2", "requests", "selenium"]

    for package in critical_packages:
        try:
            __import__(package)
        except ImportError as e:
            issues.append(f"Missing package: {package} - {e}")

    # Check database connection
    try:
        import psycopg2
        from dotenv import load_dotenv

        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        conn_params = {
            "host": os.environ.get("DB_HOST", "localhost"),
            "port": int(os.environ.get("DB_PORT", "5433")),
            "database": os.environ.get("DB_NAME", "maricopa_properties"),
            "user": os.environ.get("DB_USER", "property_user"),
            "password": os.environ.get("DB_PASSWORD", "Wildcats777!!"),
        }

        conn = psycopg2.connect(**conn_params)
        conn.close()
    except Exception as e:
        issues.append(f"Database connection failed: {e}")

    return issues


def main():
    """Main check function"""
    print("Checking environment...")

    issues = check_environment()

    if not issues:
        print("OK: Environment check passed - all dependencies available")
        return 0
    else:
        print("FAIL: Environment issues detected:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nRun 'python scripts\\verify_dependencies.py' for detailed diagnostics")
        return 1


if __name__ == "__main__":
    sys.exit(main())
