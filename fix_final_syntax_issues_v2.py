#!/usr/bin/env python3
"""
Final Syntax Fix Script for Black Parse Errors - Version 2
Handles the remaining 79 files with specific parse error patterns
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set


def log_message(message: str):
    """Log a message with timestamp"""
    import datetime

    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def fix_function_indentation(content: str, filename: str) -> str:
    """Fix function definitions at wrong indentation level"""
    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        # Look for function definitions that should be at module level (0 indentation)
        if re.match(r"^    def [a-zA-Z_][a-zA-Z0-9_]*\(.*\):.*$", line):
            # Check if this is actually supposed to be a module-level function
            # Look at context: if previous lines don't suggest it's inside a class
            context_suggests_module_level = True

            # Look backwards for class definition
            for j in range(max(0, i - 10), i):
                if lines[j].strip().startswith("class "):
                    context_suggests_module_level = False
                    break
                # If we see another def at module level, this should probably be too
                if re.match(r"^def [a-zA-Z_]", lines[j]):
                    context_suggests_module_level = True
                    break

            if context_suggests_module_level:
                # Move function to module level
                fixed_line = line[4:]  # Remove 4 spaces of indentation
                log_message(
                    f"  Fixed function indentation in {filename}:{i+1}: {line.strip()[:50]}"
                )
                fixed_lines.append(fixed_line)
                continue

        fixed_lines.append(line)

    return "\n".join(fixed_lines)


def fix_import_structure(content: str, filename: str) -> str:
    """Fix import statements in wrong positions"""
    lines = content.split("\n")
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for orphaned import after try without except
        if line.strip().startswith("from ") or line.strip().startswith("import "):
            # Check if previous line was try: or similar
            prev_line = lines[i - 1] if i > 0 else ""

            # Look for pattern where import comes after comment or other statement
            if i > 0 and ("MIGRATED:" in prev_line or "# MIGRATED:" in prev_line):
                # This is a migrated import, make sure it's properly structured
                if i + 1 < len(lines):
                    next_line = lines[i + 1] if i + 1 < len(lines) else ""
                    if next_line.strip() == "" and i + 2 < len(lines):
                        after_next = lines[i + 2] if i + 2 < len(lines) else ""
                        if after_next.strip().startswith("except "):
                            # This looks like an incomplete try/except block
                            log_message(f"  Fixed import structure in {filename}:{i+1}")
                            fixed_lines.append("try:")
                            fixed_lines.append(f"    {line.strip()}")
                            fixed_lines.append("except ImportError:")
                            fixed_lines.append("    pass")
                            i += 1
                            continue

        fixed_lines.append(line)
        i += 1

    return "\n".join(fixed_lines)


def fix_except_indentation(content: str, filename: str) -> str:
    """Fix missing indentation after except: statements"""
    lines = content.split("\n")
    fixed_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)

        # Look for except: followed by improperly indented code
        if line.strip() == "except:" and i < len(lines) - 1:
            next_line = lines[i + 1] if i + 1 < len(lines) else ""

            # If next line exists and is not properly indented
            if (
                next_line.strip()
                and not next_line.startswith("    ")
                and not next_line.startswith("\t")
            ):
                # The next line should be indented
                log_message(
                    f"  Fixed except indentation in {filename}:{i+2}: {next_line.strip()}"
                )
                i += 1  # Move to next line
                fixed_lines.append("    " + lines[i].strip())
                i += 1
                continue

        i += 1

    return "\n".join(fixed_lines)


def fix_specific_known_issues(content: str, filename: str) -> str:
    """Fix specific known issues from Black error output"""

    # Fix specific issues we know about
    if "batch_search_demo.py" in filename:
        # Fix the function definition at wrong level
        content = re.sub(
            r"^    def demonstrate_batch_search\(\):",
            "def demonstrate_batch_search():",
            content,
            flags=re.MULTILINE,
        )
        if "    def demonstrate_batch_search():" in content:
            log_message(
                f"  Fixed demonstrate_batch_search function indentation in {filename}"
            )

    if "enhanced_main_window.py" in filename:
        # Fix the import structure issue
        lines = content.split("\n")
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if "from src.api_client_unified import UnifiedMaricopaAPIClient" in line:
                # Check if this is after a try without proper structure
                if i > 0 and not any(
                    lines[j].strip().startswith("try:") for j in range(max(0, i - 5), i)
                ):
                    # Add proper try/except structure
                    fixed_lines.append("try:")
                    fixed_lines.append("    " + line.strip())
                    fixed_lines.append("except ImportError:")
                    fixed_lines.append("    UnifiedMaricopaAPIClient = None")
                    log_message(f"  Fixed import structure in {filename}:{i+1}")
                    i += 1
                    continue
            fixed_lines.append(line)
            i += 1
        content = "\n".join(fixed_lines)

    return content


def process_file(file_path: Path) -> bool:
    """Process a single file to fix syntax issues"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        original_content = content
        filename = str(file_path)

        # Apply all fixes
        content = fix_specific_known_issues(content, filename)
        content = fix_except_indentation(content, filename)
        content = fix_function_indentation(content, filename)
        content = fix_import_structure(content, filename)

        # Only write if content changed
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        log_message(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to fix remaining syntax issues"""
    log_message("Starting final syntax issue fixes...")

    # Get all Python files in src directory and root
    python_files = []

    # Look in src directory
    src_dir = Path("./src")
    if src_dir.exists():
        for file_path in src_dir.rglob("*.py"):
            python_files.append(file_path)

    # Look in root directory for specific files
    for pattern in ["*.py"]:
        for file_path in Path(".").glob(pattern):
            if file_path.is_file():
                python_files.append(file_path)

    # Filter out venv and other unwanted directories
    python_files = [
        f for f in python_files if "venv" not in str(f) and "__pycache__" not in str(f)
    ]

    log_message(f"Found {len(python_files)} Python files to process")

    # Process files
    modified_count = 0
    for file_path in python_files:
        if process_file(file_path):
            modified_count += 1

    log_message(f"Fixed syntax issues in {modified_count} files")

    # Run Black check to see current status
    log_message("Running Black check to verify fixes...")
    result = os.system("python3 -m black --check --diff . 2>&1 | head -20")


if __name__ == "__main__":
    main()
