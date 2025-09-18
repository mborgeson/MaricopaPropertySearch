#!/usr/bin/env python3
"""
Simple test runner for hive mind fixes
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))

# Change to project directory
os.chdir(project_root)

print("Current directory:", os.getcwd())
print("Project root:", project_root)
print("Python path includes:", [p for p in sys.path if 'MaricopaPropertySearch' in p])

try:
    # Import and run the test
    from tests.test_hive_mind_fixes import main
    exit_code = main()
    sys.exit(exit_code)
except Exception as e:
    print(f"Error running tests: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)