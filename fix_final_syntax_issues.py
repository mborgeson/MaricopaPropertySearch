#!/usr/bin/env python3
"""
Final Syntax Fix Script for Black Parse Errors
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
    """Fix import statements in wrong positions (like after try without proper except)"""
    lines = content.split("\n")
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for pattern: try: ... import ... except ImportError:
        if line.strip().startswith("try:") and i < len(lines) - 2:
            # Look ahead for import without proper except structure
            j = i + 1
            imports_found = []
            except_found = False

            while j < len(lines) and j < i + 10:  # Look ahead max 10 lines
                if lines[j].strip().startswith("from ") or lines[j].strip().startswith(
                    "import "
                ):
                    imports_found.append(j)
                elif lines[j].strip().startswith("except "):
                    except_found = True
                    break
                elif (
                    lines[j].strip()
                    and not lines[j].startswith(" ")
                    and not lines[j].startswith("\t")
                ):
                    # Hit non-indented code, stop looking
                    break
                j += 1

            if imports_found and except_found:
                # This is a proper try/except import block, keep as is
                fixed_lines.append(line)
                i += 1
                continue
            elif imports_found and not except_found:
                # Import without proper except, fix it
                log_message(f"  Fixed import structure in {filename}:{i+1}")
                fixed_lines.append("try:")
                for import_idx in imports_found:
                    fixed_lines.append(f"    {lines[import_idx].strip()}")
                fixed_lines.append("except ImportError:")
                fixed_lines.append("    pass")

                # Skip the original lines we just fixed
                i = max(imports_found) + 1
                continue

        fixed_lines.append(line)
        i += 1

    return "\n".join(fixed_lines)


def fix_except_indentation(content: str, filename: str) -> str:
    """Fix missing indentation after except: statements"""
    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
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
                indented_next = "    " + next_line.strip()
                log_message(
                    f"  Fixed except indentation in {filename}:{i+2}: {next_line.strip()}"
                )
                # We'll handle this when we get to that line

        # Handle the case where we're on a line that should be indented after except:
        elif i > 0 and lines[i - 1].strip() == "except:":
            if (
                line.strip()
                and not line.startswith("    ")
                and not line.startswith("\t")
            ):
                # This line should be indented
                fixed_lines[-1] = "    " + line.strip()

    return "\n".join(fixed_lines)


def fix_dedent_errors(content: str, filename: str) -> str:
    """Fix DedentDoesNotMatchAnyOuterIndent errors"""
    lines = content.split("\n")
    fixed_lines = []
    indent_stack = [0]  # Stack to track indentation levels

    for i, line in enumerate(lines):
        if not line.strip():
            # Empty lines don't affect indentation
            fixed_lines.append(line)
            continue

        # Calculate current indentation
        current_indent = len(line) - len(line.lstrip())

        # If this is a dedent, make sure it matches a previous level
        if current_indent < indent_stack[-1]:
            # Find the closest matching indentation level
            matching_level = 0
            for level in reversed(indent_stack[:-1]):
                if level <= current_indent:
                    matching_level = level
                    break

            if matching_level != current_indent:
                # Adjust indentation to match
                adjusted_line = " " * matching_level + line.lstrip()
                if adjusted_line != line:
                    log_message(
                        f"  Fixed dedent in {filename}:{i+1}: adjusted to {matching_level} spaces"
                    )
                fixed_lines.append(adjusted_line)
                # Update indent stack
                while indent_stack and indent_stack[-1] > matching_level:
                    indent_stack.pop()
            else:
                fixed_lines.append(line)
                # Update indent stack
                while indent_stack and indent_stack[-1] > current_indent:
                    indent_stack.pop()
        else:
            # Regular line or indent
            fixed_lines.append(line)
            if current_indent > indent_stack[-1]:
                indent_stack.append(current_indent)

    return "\n".join(fixed_lines)


def process_file(file_path: Path) -> bool:
    """Process a single file to fix syntax issues"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        original_content = content
        filename = str(file_path.relative_to(Path.cwd()))

        # Apply all fixes
        content = fix_except_indentation(content, filename)
        content = fix_function_indentation(content, filename)
        content = fix_import_structure(content, filename)
        content = fix_dedent_errors(content, filename)

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

    # Get all Python files
    python_files = []
    for root, dirs, files in os.walk("."):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]

        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)

    log_message(f"Found {len(python_files)} Python files to process")

    # Process files
    modified_count = 0
    for file_path in python_files:
        if process_file(file_path):
            modified_count += 1

    log_message(f"Fixed syntax issues in {modified_count} files")

    # Run Black check to see current status
    log_message("Running Black check to verify fixes...")
    result = os.system("python -m black --check --diff . 2>&1")

    if result == 0:
        log_message("✅ All files now pass Black formatting!")
    else:
        log_message("⚠️  Some files still have issues - may need manual review")


if __name__ == "__main__":
    main()
