#!/usr/bin/env python3
"""
Fix absolute imports to relative imports in the src directory
"""

import os
import re
import glob

def fix_imports_in_file(file_path):
    """Fix absolute src.* imports to relative imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Replace absolute imports with relative imports
        # Pattern: from src.module_name import ...
        content = re.sub(r'from src\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*) import',
                        r'from \1 import', content)

        if content != original_content:
            print(f"Fixing imports in: {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Fix imports in all Python files in the src directory"""
    src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')

    # Find all Python files in src directory and subdirectories
    python_files = []
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    print(f"Found {len(python_files)} Python files to process...")

    fixed_count = 0
    for file_path in python_files:
        if fix_imports_in_file(file_path):
            fixed_count += 1

    print(f"\nFixed imports in {fixed_count} files")

if __name__ == "__main__":
    main()