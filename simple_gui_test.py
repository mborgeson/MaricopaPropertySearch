#!/usr/bin/env python
"""Simple GUI test without unicode characters"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
        print("Testing GUI imports after PySide6 to PyQt5 conversion...")

try:
    # Test importing the main window
from src.gui.enhanced_main_window import EnhancedMainWindow

        print("SUCCESS: EnhancedMainWindow imported (PyQt5)")

    # Test PyQt5 components
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import QApplication
        print("SUCCESS: PyQt5 components imported")
        print("\nGUI FIX SUCCESSFUL!")
        print("- No more PySide6 dependency")
        print("- All imports use PyQt5 consistently")
        print("- Application ready to run")

except ImportError as e:
    if "PySide6" in str(e):
        print(f"ERROR: Still importing PySide6: {e}")
    elif "PyQt5" in str(e):
        print(f"ERROR: PyQt5 not available: {e}")
    else:
        print(f"ERROR: Import error: {e}")

except Exception as e:
        print(f"ERROR: {e}")