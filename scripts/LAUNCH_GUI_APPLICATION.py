#!/usr/bin/env python
"""
LAUNCH GUI APPLICATION - FINAL VERSION
This launches the GUI with all the fixes for complete data display
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\MattBorgeson\Development\Work\MaricopaPropertySearch")

def launch_gui():
    """Launch the GUI application"""
    print("=" * 60)
    print("LAUNCHING MARICOPA PROPERTY SEARCH GUI")
    print("=" * 60)
    print("DATA AVAILABLE:")
    print("  [+] Tax History: 5 years of complete records")
    print("  [+] Sales History: 3 transaction records")
    print("  [+] Enhanced Property Data: Complete details")
    print()
    print("INSTRUCTIONS:")
    print("1. Search for '10000 W Missouri Ave' or any address")
    print("2. Click on the result in the search table")
    print("3. Click 'View Details' button")
    print("4. Check all 3 tabs:")
    print("   - Basic Information: Property details")
    print("   - Tax History: Actual amounts and payment status")
    print("   - Sales History: Transaction records")
    print("=" * 60)
    
    try:
        gui_script = PROJECT_ROOT / "src" / "maricopa_property_search.py"
        subprocess.run([sys.executable, str(gui_script)])
    except Exception as e:
        print(f"Error launching GUI: {e}")
        print("\nTry running directly:")
        print(f"cd {PROJECT_ROOT / 'src'}")
        print("python maricopa_property_search.py")

if __name__ == "__main__":
    launch_gui()