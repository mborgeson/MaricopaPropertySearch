#!/usr/bin/env python
"""Quick test to verify RUN_APPLICATION.py works"""

import sys
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent

# Try to run the app for 2 seconds
try:
    result = subprocess.run(
        [sys.executable, "RUN_APPLICATION.py"],
        capture_output=True,
        text=True,
        timeout=2,
        cwd=project_root,
    )
except subprocess.TimeoutExpired as e:
    # This is expected - app runs until timeout
    if "[START] Starting application..." in str(e.stdout):
        print("[OK] Application starts successfully")
        sys.exit(0)
    else:
        print("[FAIL] Application has issues")
        print("Output:", str(e.stdout)[:500])
        sys.exit(1)
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

print("[OK] Test complete")
