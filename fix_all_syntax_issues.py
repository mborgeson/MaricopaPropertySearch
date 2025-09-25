#!/usr/bin/env python3
"""
Comprehensive script to fix ALL syntax issues preventing Black formatting
and other CI/CD pipeline failures.
"""
import os
import re
import subprocess
import sys
from pathlib import Path


def fix_traceback_issues(file_path: Path):
    """Fix missing newlines after traceback.print_exc()"""
    if not file_path.exists():
        return False

    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # Fix missing newlines after traceback.print_exc()

    patterns = [
            (r'traceback\.print_exc\(\)\s*def ', r'traceback.print_exc()\n\n    def '),
            (r'traceback\.print_exc\(\)\s*class ', r'traceback.print_exc()\n\n\nclass '),
            (r'traceback\.print_exc\(\)\s*([A-Za-z_])', r'traceback.print_exc()\n\n    \1'),
        ]

        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)

        # Fix dialog.exec_() followed immediately by def
        content = re.sub(r'dialog\.exec_\(\)\s*def ', r'dialog.exec_()\n\n    def ', content)

        # Fix except:
        blocks without proper newlines
        content = re.sub(r'except:\s*([a-zA-Z_])', r'except:\n        \1', content)

        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
        print(f"Fixed syntax issues in: {file_path}")
            return True

        return False

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False
def fix_import_issues(file_path: Path):
    """Fix import statement issues that break parsing"""
    if not file_path.exists():
        return False

    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # Fix imports without proper line breaks
        lines = content.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            # If line starts with 'from' or 'import' but is immediately followed by code
            if (line.strip().startswith(('from ', 'import ')) and
                i < len(lines) - 1 and
                lines[i + 1].strip() and
                not lines[i + 1].strip().startswith(('#', 'from ', 'import ', '"""', "''"))):

                # Add blank line after import if not already there
                fixed_lines.append(line)
                if not lines[i + 1].strip() == '':
                    fixed_lines.append('')
            else:
                fixed_lines.append(line)

        content = '\n'.join(fixed_lines)

        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
        print(f"Fixed import issues in: {file_path}")
            return True

        return False

    except Exception as e:
        print(f"Error fixing imports in {file_path}: {e}")
        return False
def fix_all_python_files(directory: Path):
    """Fix all Python files in directory recursively"""
    fixed_count = 0

    for file_path in directory.rglob("*.py"):
        # Skip certain problematic files
        if any(skip in str(file_path) for skip in ['.venv', '__pycache__', '.git']):
            continue
        print(f"Checking: {file_path}")

        if fix_traceback_issues(file_path):
            fixed_count += 1

        if fix_import_issues(file_path):
            fixed_count += 1

    return fixed_count
def run_black_formatting(directory: Path):
    """Run Black formatting on all Python files"""
        print("\n" + "="*60)
        print("Running Black formatting...")
        print("="*60)

    try:
        # Activate virtual environment and run Black
        result = subprocess.run([
            'bash', '-c',
            f'source .venv/bin/activate && black {directory}/src/ {directory}/tests/'
        ], cwd=directory, capture_output=True, text=True)
        print("STDOUT:", result.stdout)
        if result.stderr:
        print("STDERR:", result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"Error running Black: {e}")
        return False
def run_isort_formatting(directory: Path):
    """Run isort on all Python files"""
        print("\n" + "="*60)
        print("Running isort...")
        print("="*60)

    try:
        # Activate virtual environment and run isort
        result = subprocess.run([
            'bash', '-c',
            f'source .venv/bin/activate && isort {directory}/src/ {directory}/tests/'
        ], cwd=directory, capture_output=True, text=True)
        print("STDOUT:", result.stdout)
        if result.stderr:
        print("STDERR:", result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"Error running isort: {e}")
        return False
def main():
    """Main function to fix all issues"""
    project_dir = Path(__file__).parent.resolve()
        print("="*60)
        print("COMPREHENSIVE CI/CD PIPELINE FIX SCRIPT")
        print("="*60)
        print(f"Working directory: {project_dir}")

    # Step 1: Fix syntax issues
        print("\nStep 1: Fixing syntax issues...")
    fixed_count = fix_all_python_files(project_dir)
        print(f"Fixed syntax issues in {fixed_count} files")

    # Step 2: Apply Black formatting
        print("\nStep 2: Applying Black formatting...")
    black_success = run_black_formatting(project_dir)
        print(f"Black formatting: {'SUCCESS' if black_success else 'FAILED'}")

    # Step 3: Apply isort
        print("\nStep 3: Applying isort...")
    isort_success = run_isort_formatting(project_dir)
        print(f"isort formatting: {'SUCCESS' if isort_success else 'FAILED'}")

    # Final report
        print("\n" + "="*60)
        print("FINAL REPORT")
        print("="*60)
        print(f"Syntax fixes applied: {fixed_count} files")
        print(f"Black formatting: {'✓ PASS' if black_success else '✗ FAIL'}")
        print(f"isort formatting: {'✓ PASS' if isort_success else '✗ FAIL'}")

    if black_success and isort_success:
        print("\n🎉 ALL FORMATTING ISSUES FIXED!")
        return 0
    else:
        print("\n⚠️ Some issues remain - check output above")
        return 1

if __name__ == "__main__":
    sys.exit(main())