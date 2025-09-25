#!/usr/bin/env python3
"""
UNIFIED SMART LAUNCHER FOR MARICOPA PROPERTY SEARCH APPLICATION
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
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(Path(__file__).parent))

import logging

# Import unified launcher functionality
from src.gui_launcher_unified import main as unified_main
from src.logging_config import get_logger

logger = get_logger(__name__)

# Backward compatibility message
logger.info("RUN_APPLICATION: Using unified GUI launcher with consolidated features")
def main():
    """Main entry point - delegates to unified launcher"""
    logger.info("Starting application via RUN_APPLICATION (unified launcher)")
    return unified_main()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[STOP] Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
import traceback

    print(traceback.format_exc())
        sys.exit(1)