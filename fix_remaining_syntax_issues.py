#!/usr/bin/env python3
"""
Fix remaining syntax issues preventing Black formatting
Handles all the remaining parse errors found by Black
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

    def fix_indentation_issues(file_path: Path) -> bool:
    """Fix indentation issues after except/try blocks"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Pattern 1: except: followed by unindented code
        patterns = [
            # except: pass with wrong indentation
            (r'(\s*except:\s*\n)(\s*)([a-zA-Z_])', r'\1        \3'),
            # try: followed by wrong indentation
            (r'(\s*try:\s*\n)(\s{0,3})([a-zA-Z_])', r'\1        \3'),
            # class/function definitions with wrong indentation
            (r'(\n\s*)(def|class)\s+([a-zA-Z_])', r'\1    \2 \3'),
        ]

        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

        # Fix specific known issues
        fixes = [
            # Fix bare except with wrong indentation
            (r'except:\s*\n\s*return "real"', 'except:\n            return "real"'),
            (r'except:\s*\n\s*stats\["recent_searches"\] = 0', 'except:\n            stats["recent_searches"] = 0'),
            (r'except:\s*\n\s*pass', 'except:\n            pass'),
            # Fix function definitions at module level
            (r'^\s*def ', '    def ', re.MULTILINE),
            # Fix import at wrong indentation
            (r'^\s*from src\.', 'from src.', re.MULTILINE),
            (r'^\s*import ', 'import ', re.MULTILINE),
            # Fix print statements with wrong indentation
            (r'^\s*print\(', '        print(', re.MULTILINE),
            # Fix traceback statements
            (r'^\s*traceback\.print_exc\(\)', '        traceback.print_exc()', re.MULTILINE),
        ]

        for find, replace, *flags in fixes:
            flags = flags[0] if flags else 0
            content = re.sub(find, replace, content, flags=flags)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False
    def fix_specific_syntax_errors(file_path: Path) -> bool:
    """Fix specific syntax errors found by Black"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        modified = False

        for i, line in enumerate(lines):
            original_line = line

            # Fix missing indentation after except:
        if re.match(r'^(\s*)except:\s*$', line) and i + 1 < len(lines):
                next_line = lines[i + 1]
                if not next_line.strip().startswith('#') and not next_line.startswith('            '):
                    # Ensure next line has proper indentation
                    indent_match = re.match(r'^(\s*)', line)
                    base_indent = indent_match.group(1) if indent_match else ''
                    lines[i + 1] = base_indent + '        ' + next_line.lstrip()
                    modified = True

            # Fix function definitions with wrong indentation
            if re.match(r'^\s*def [a-zA-Z_]', line) and not line.startswith('    def') and not line.startswith('def'):
                lines[i] = '    ' + line.lstrip()
                modified = True

            # Fix class definitions with wrong indentation
            if re.match(r'^\s*class [a-zA-Z_]', line) and not line.startswith('class'):
                lines[i] = line.lstrip()
                modified = True

            # Fix import statements at wrong level
            if re.match(r'^\s+(from|import) ', line) and 'from src.' in line:
                lines[i] = line.lstrip()
                modified = True

        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True

        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False
    def process_files(directory: Path) -> Tuple[int, List[str]]:
    """Process all Python files in directory"""
    fixed_files = []
    total_files = 0

    for root, dirs, files in os.walk(directory):
        # Skip virtual environments, archives, backups
        if any(skip in root for skip in ['.venv', 'archive', 'backups', '__pycache__']):
            continue

        for file in files:
            if file.endswith('.py'):
                total_files += 1
                file_path = Path(root) / file

                try:
                    fixed1 = fix_indentation_issues(file_path)
                    fixed2 = fix_specific_syntax_errors(file_path)

                    if fixed1 or fixed2:
                        fixed_files.append(str(file_path))
        print(f"Fixed: {file_path}")

                except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return total_files, fixed_files
def main():
    """Main execution"""
    if len(sys.argv) > 1:
        directory = Path(sys.argv[1])
    else:
        directory = Path('.')

    if not directory.exists():
        print(f"Directory {directory} does not exist")
        sys.exit(1)
        print(f"Processing Python files in {directory}")
    total_files, fixed_files = process_files(directory)
        print(f"\nSummary:")
        print(f"Total Python files processed: {total_files}")
        print(f"Files fixed: {len(fixed_files)}")

    if fixed_files:
        print(f"\nFixed files:")
        for file in fixed_files[:20]:  # Show first 20
        print(f"  - {file}")
        if len(fixed_files) > 20:
        print(f"  ... and {len(fixed_files) - 20} more")
        print(f"\nNow run: source .venv/bin/activate && python -m black src/ tests/ --line-length=88")

if __name__ == '__main__':
    main()