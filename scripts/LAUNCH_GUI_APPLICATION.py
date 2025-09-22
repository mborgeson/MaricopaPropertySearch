#!/usr/bin/env python3
"""
LAUNCH GUI APPLICATION - FINAL VERSION
CONSOLIDATED - Now imports from gui_launcher_unified.py

This file maintains backward compatibility while delegating all functionality
to the unified GUI launcher that consolidates features from:
- RUN_APPLICATION.py (smart platform detection and environment setup)
- launch_gui_fixed.py (minimal testing functionality)
- scripts/LAUNCH_GUI_APPLICATION.py (Windows path handling)
- launch_enhanced_app.py (splash screen and requirement checking)
- launch_improved_app.py (UX improvements and Missouri Ave testing)
"""

import sys
import subprocess
from pathlib import Path

# Handle both Windows and Linux paths
if sys.platform.startswith("win"):
    PROJECT_ROOT = Path(
        r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch"
    )
else:
    PROJECT_ROOT = Path("/home/mattb/MaricopaPropertySearch")

# Add src directory to path
src_dir = PROJECT_ROOT / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(PROJECT_ROOT))

# Import unified launcher functionality
from src.gui_launcher_unified import main as unified_main

import logging
from src.logging_config import get_logger

logger = get_logger(__name__)

# Backward compatibility message
logger.info(
    "LAUNCH_GUI_APPLICATION: Using unified GUI launcher with consolidated features"
)


def launch_gui():
    """Launch the GUI application - delegates to unified launcher"""
    print("=" * 60)
    print("LAUNCHING MARICOPA PROPERTY SEARCH GUI")
    print("=" * 60)
    print("UNIFIED LAUNCHER FEATURES:")
    print("  [+] Smart platform detection (Windows/WSL/Linux)")
    print("  [+] Intelligent Qt platform configuration")
    print("  [+] Dependency checking with graceful fallbacks")
    print("  [+] Multiple GUI launch strategies")
    print("  [+] Database connection testing with fallback")
    print("  [+] Enhanced logging setup")
    print()
    print("INSTRUCTIONS:")
    print("1. Search for '10000 W Missouri Ave' or any address")
    print("2. Click on the result in the search table")
    print("3. Click 'View Details' button")
    print("4. Check all tabs for complete information")
    print("=" * 60)

    logger.info("Starting application via LAUNCH_GUI_APPLICATION (unified launcher)")
    return unified_main()


def main():
    """Main entry point"""
    return launch_gui()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error launching GUI: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
