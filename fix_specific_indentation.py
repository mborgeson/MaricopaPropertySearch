#!/usr/bin/env python3
"""
Fix specific indentation issues in problematic files
"""
import os

# Dictionary of files and their specific fixes
fixes = {
    "apply_refresh_fixes_simple.py": [
        (
            17,
            '        print("Applying crash-safe refresh button fixes...")',
            '    print("Applying crash-safe refresh button fixes...")',
        ),
    ],
    "apply_refresh_fixes.py": [
        (
            17,
            '        print("🔧 Applying crash-safe refresh button fixes...")',
            '    print("🔧 Applying crash-safe refresh button fixes...")',
        ),
    ],
    "add_setup_calls.py": [
        (
            12,
            "    with open(main_window_path, 'r', encoding='utf-8') as f:",
            "with open(main_window_path, 'r', encoding='utf-8') as f:",
        ),
    ],
    "RUN_APPLICATION.py": [
        (
            47,
            "        print(traceback.format_exc())",
            "    print(traceback.format_exc())",
        ),
    ],
    "cleanup_duplicates.py": [
        (
            15,
            "    with open(main_window_path, 'r', encoding='utf-8') as f:",
            "with open(main_window_path, 'r', encoding='utf-8') as f:",
        ),
    ],
    "final_settings_fix.py": [
        (
            16,
            '        print(f"Created backup: {backup_path}")',
            '    print(f"Created backup: {backup_path}")',
        ),
    ],
}


def fix_file(filepath, line_fixes):
    """Fix specific lines in a file"""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line_num, old_content, new_content in line_fixes:
            # Line numbers are 1-based, convert to 0-based
            idx = line_num - 1
            if idx < len(lines):
                # Replace the line
                lines[idx] = new_content + "\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"✅ Fixed {filepath}")
        return True
    except Exception as e:
        print(f"❌ Error fixing {filepath}: {e}")
        return False


# Apply fixes
print("Fixing specific indentation issues...")
for filepath, line_fixes in fixes.items():
    fix_file(filepath, line_fixes)

# Fix the claudedocs files with a different approach
claudedocs_files = [
    "claudedocs/simple_api_test.py",
    "claudedocs/test_background_collection.py",
    "claudedocs/test_property_search.py",
]

for filepath in claudedocs_files:
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()

            fixed_lines = []
            for i, line in enumerate(lines):
                stripped = line.lstrip()
                # Fix improperly indented function definitions
                if stripped.startswith("def ") and i > 0:
                    # Check if previous line suggests this should be at module level
                    prev_stripped = lines[i - 1].strip()
                    if (
                        prev_stripped == ""
                        or prev_stripped.startswith("#")
                        or prev_stripped.startswith("import ")
                        or prev_stripped.startswith("from ")
                    ):
                        # Module level function - no indentation
                        fixed_lines.append(stripped)
                    else:
                        # Keep original
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)

            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(fixed_lines)

            print(f"✅ Fixed {filepath}")
        except Exception as e:
            print(f"❌ Error fixing {filepath}: {e}")

print("\nDone fixing indentation issues!")
