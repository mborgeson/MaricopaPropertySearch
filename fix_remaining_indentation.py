#!/usr/bin/env python3
"""
Fix remaining indentation issues in files that Black cannot parse
"""
import os
import re


def fix_indentation_in_file(file_path):
    """Fix common indentation issues in a Python file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        fixed_lines = []
        in_class = False
        in_function = False
        indent_level = 0

        for i, line in enumerate(lines):
            stripped = line.lstrip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                fixed_lines.append(line)
                continue

            # Check for improperly indented function definitions
            if stripped.startswith("def "):
                # Check if this is at module level (after imports or at start)
                if i == 0 or (
                    i > 0
                    and (
                        lines[i - 1].strip() == ""
                        or lines[i - 1].strip().startswith("import ")
                        or lines[i - 1].strip().startswith("from ")
                        or lines[i - 1].strip().startswith("#")
                    )
                ):
                    # Module level function
                    fixed_lines.append(stripped)
                    in_function = True
                    indent_level = 0
                elif in_class:
                    # Method in class - should be indented
                    fixed_lines.append("    " + stripped)
                    in_function = True
                    indent_level = 4
                else:
                    # Keep existing indentation
                    fixed_lines.append(line)
                continue

            # Check for class definitions
            if stripped.startswith("class "):
                in_class = True
                in_function = False
                indent_level = 0
                fixed_lines.append(stripped)
                continue

            # Fix lines that should be indented but aren't
            if (
                in_function
                and not line[0].isspace()
                and not stripped.startswith("def ")
                and not stripped.startswith("class ")
            ):
                # This line should be indented
                fixed_lines.append("    " * ((indent_level // 4) + 1) + stripped)
            else:
                fixed_lines.append(line)

        # Write back
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)

        return True
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


# Files that Black cannot parse
files_to_fix = [
    "apply_refresh_fixes_simple.py",
    "apply_gui_integration.py",
    "apply_refresh_fixes.py",
    "add_setup_calls.py",
    "RUN_APPLICATION.py",
    # Archive files that might affect the pipeline
    "archive/api_clients_consolidated_2025_09_18/api_client_performance_patch.py",
    "archive/database_managers_consolidated_2025_09_18/database_manager.py",
]

# Also check for .history files that might be included
history_files = [
    ".history/scripts/test_installation_20250910085244.py",
    ".history/scripts/test_installation_20250910070232.py",
    ".history/scripts/test_installation_20250910085331.py",
]

print("Fixing remaining indentation issues...")
fixed_count = 0
for file_path in files_to_fix:
    if os.path.exists(file_path):
        print(f"Fixing: {file_path}")
        if fix_indentation_in_file(file_path):
            fixed_count += 1

# Remove or exclude .history files from git
if os.path.exists(".history"):
    print("\nRemoving .history directory from git tracking...")
    os.system("git rm -r --cached .history/ 2>/dev/null")

print(f"\n✅ Fixed {fixed_count} files")
