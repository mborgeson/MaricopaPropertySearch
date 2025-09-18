#!/usr/bin/env python3
"""
IMPORT MIGRATION SCRIPT - MaricopaPropertySearch DRY Consolidation

This script updates all import statements across the codebase to use the consolidated
components after the DRY principle consolidation.

CONSOLIDATION MAPPING:
- 8 API client variants → src/api_client_unified.py (UnifiedMaricopaAPIClient)
- 7 web scraper variants → optimized_web_scraper.py (general) + tax_scraper.py (specialized)
- 5 database manager variants → threadsafe_database_manager.py (thread-safe)
- 5 config manager variants → enhanced_config_manager.py (enhanced)
- 15 GUI variants → enhanced_main_window.py (with crash fixes)

Created as part of WAVE 2: DRY PRINCIPLE CONSOLIDATION EXECUTION
"""

import os
import re
import sys
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Set
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImportMigrator:
    """Handles migration of imports across the codebase"""

    def __init__(self, project_root: str, dry_run: bool = False):
        self.project_root = Path(project_root)
        self.dry_run = dry_run
        self.backup_dir = self.project_root / "backups" / f"pre_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.migration_stats = {
            'files_processed': 0,
            'files_modified': 0,
            'imports_updated': 0,
            'errors': 0
        }

        # Define import mapping rules
        self.import_mappings = {
            # API Client consolidation (8→1)
            'api_client': {
                'old_patterns': [
                    r'from\s+api_client\s+import\s+(\w+)',
                    r'from\s+src\.api_client\s+import\s+(\w+)',
                    r'from\s+parallel_api_client\s+import\s+(\w+)',
                    r'from\s+src\.parallel_api_client\s+import\s+(\w+)',
                    r'from\s+batch_api_client\s+import\s+(\w+)',
                    r'from\s+src\.batch_api_client\s+import\s+(\w+)',
                    r'from\s+threadsafe_api_client\s+import\s+(\w+)',
                    r'from\s+src\.threadsafe_api_client\s+import\s+(\w+)',
                    r'import\s+api_client',
                    r'import\s+src\.api_client',
                    r'import\s+parallel_api_client',
                    r'import\s+batch_api_client'
                ],
                'new_import': 'from src.api_client_unified import UnifiedMaricopaAPIClient',
                'class_mappings': {
                    'MaricopaAPIClient': 'UnifiedMaricopaAPIClient',
                    'HighPerformanceMaricopaAPIClient': 'UnifiedMaricopaAPIClient',
                    'BatchAPIClient': 'UnifiedMaricopaAPIClient',
                    'ThreadSafeAPIClient': 'UnifiedMaricopaAPIClient',
                    'MaricopaAssessorAPI': 'UnifiedMaricopaAPIClient'
                }
            },

            # Database Manager consolidation (5→1)
            'database': {
                'old_patterns': [
                    r'from\s+database_manager\s+import\s+(\w+)',
                    r'from\s+src\.database_manager\s+import\s+(\w+)',
                    r'import\s+database_manager',
                    r'import\s+src\.database_manager'
                ],
                'new_import': 'from src.threadsafe_database_manager import ThreadSafeDatabaseManager',
                'class_mappings': {
                    'DatabaseManager': 'ThreadSafeDatabaseManager'
                }
            },

            # Config Manager consolidation (5→1)
            'config': {
                'old_patterns': [
                    r'from\s+config_manager\s+import\s+(\w+)',
                    r'from\s+src\.config_manager\s+import\s+(\w+)',
                    r'import\s+config_manager',
                    r'import\s+src\.config_manager'
                ],
                'new_import': 'from src.enhanced_config_manager import EnhancedConfigManager',
                'class_mappings': {
                    'ConfigManager': 'EnhancedConfigManager'
                }
            }
        }

        # Files to exclude from migration
        self.exclude_patterns = [
            '*.pyc', '__pycache__', '.git', 'backups',
            'api_client_unified.py',  # Don't modify the new unified file
            'threadsafe_database_manager.py',
            'enhanced_config_manager.py',
            # Backup files
            '*backup*', '*_backup.py', '*.backup_*',
            # Test files that might be testing specific versions
            'test_api_client_comparison.py'
        ]

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from migration"""
        file_str = str(file_path)
        for pattern in self.exclude_patterns:
            if pattern in file_str or file_path.name.startswith('.'):
                return True
        return False

    def backup_file(self, file_path: Path) -> None:
        """Create backup of file before modification"""
        if self.dry_run:
            return

        # Create backup directory structure
        relative_path = file_path.relative_to(self.project_root)
        backup_file_path = self.backup_dir / relative_path
        backup_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file to backup location
        shutil.copy2(file_path, backup_file_path)
        logger.debug(f"Backed up: {file_path} → {backup_file_path}")

    def update_imports_in_content(self, content: str, file_path: Path) -> Tuple[str, int]:
        """Update import statements in file content"""
        updated_content = content
        updates_count = 0
        imports_added = set()

        for component, mapping in self.import_mappings.items():
            # Check each old pattern
            for pattern in mapping['old_patterns']:
                matches = list(re.finditer(pattern, updated_content, re.MULTILINE))

                for match in matches:
                    full_match = match.group(0)
                    logger.debug(f"Found import to update: {full_match} in {file_path}")

                    # Add new import if not already added
                    new_import = mapping['new_import']
                    if new_import not in imports_added and new_import not in updated_content:
                        # Find a good place to insert the new import
                        import_lines = []
                        lines = updated_content.split('\n')
                        insert_index = 0

                        # Find last import line
                        for i, line in enumerate(lines):
                            if line.strip().startswith(('import ', 'from ')) and not line.strip().startswith('#'):
                                insert_index = i + 1

                        # Insert new import
                        lines.insert(insert_index, new_import)
                        updated_content = '\n'.join(lines)
                        imports_added.add(new_import)
                        logger.info(f"Added import: {new_import}")

                    # Remove or comment out old import
                    old_import_line = full_match
                    if '# MIGRATED:' not in old_import_line:
                        updated_content = updated_content.replace(
                            old_import_line,
                            f"# MIGRATED: {old_import_line}  # → {new_import}"
                        )
                        updates_count += 1

        # Update class usage
        for component, mapping in self.import_mappings.items():
            for old_class, new_class in mapping['class_mappings'].items():
                # Update class instantiations and references
                class_patterns = [
                    rf'\b{old_class}\b(?=\s*\()',  # Class instantiation
                    rf'\b{old_class}\b(?=\s*\.)',  # Class method calls
                    rf':\s*{old_class}\b',         # Type annotations
                ]

                for pattern in class_patterns:
                    old_matches = len(re.findall(pattern, updated_content))
                    if old_matches > 0:
                        updated_content = re.sub(pattern, new_class, updated_content)
                        logger.info(f"Updated {old_matches} references: {old_class} → {new_class}")
                        updates_count += old_matches

        return updated_content, updates_count

    def migrate_file(self, file_path: Path) -> bool:
        """Migrate imports in a single file"""
        try:
            logger.debug(f"Processing file: {file_path}")

            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Update imports
            updated_content, updates_count = self.update_imports_in_content(original_content, file_path)

            if updates_count > 0:
                # Create backup
                self.backup_file(file_path)

                # Write updated content
                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)

                logger.info(f"Updated {updates_count} imports in: {file_path}")
                self.migration_stats['files_modified'] += 1
                self.migration_stats['imports_updated'] += updates_count
                return True

            return False

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            self.migration_stats['errors'] += 1
            return False

    def find_python_files(self) -> List[Path]:
        """Find all Python files to process"""
        python_files = []

        for file_path in self.project_root.rglob('*.py'):
            if not self.should_exclude_file(file_path):
                python_files.append(file_path)

        logger.info(f"Found {len(python_files)} Python files to process")
        return python_files

    def run_migration(self) -> Dict[str, int]:
        """Run the complete migration process"""
        logger.info("="*80)
        logger.info("STARTING IMPORT MIGRATION - DRY CONSOLIDATION")
        logger.info("="*80)

        if self.dry_run:
            logger.info("DRY RUN MODE - No files will be modified")

        # Create backup directory
        if not self.dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Backups will be stored in: {self.backup_dir}")

        # Find files to process
        python_files = self.find_python_files()

        # Process each file
        for file_path in python_files:
            self.migration_stats['files_processed'] += 1
            self.migrate_file(file_path)

        # Generate summary
        logger.info("="*80)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*80)
        logger.info(f"Files processed: {self.migration_stats['files_processed']}")
        logger.info(f"Files modified: {self.migration_stats['files_modified']}")
        logger.info(f"Imports updated: {self.migration_stats['imports_updated']}")
        logger.info(f"Errors: {self.migration_stats['errors']}")

        if not self.dry_run and self.migration_stats['files_modified'] > 0:
            logger.info(f"Backups stored in: {self.backup_dir}")
            logger.info("RECOMMENDATION: Test the application thoroughly before removing backup files")

        return self.migration_stats

def main():
    """Main migration script entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate imports for DRY consolidation')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without modifying files')
    parser.add_argument('--project-root', default=os.getcwd(),
                       help='Project root directory (default: current directory)')

    args = parser.parse_args()

    # Validate project root
    project_root = Path(args.project_root)
    if not project_root.exists():
        logger.error(f"Project root does not exist: {project_root}")
        sys.exit(1)

    # Check if this looks like the MaricopaPropertySearch project
    expected_files = ['src', 'src/api_client_unified.py']
    missing_files = [f for f in expected_files if not (project_root / f).exists()]
    if missing_files:
        logger.warning(f"Missing expected files: {missing_files}")
        logger.warning("This may not be the MaricopaPropertySearch project root")

        if sys.stdin.isatty():
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
        else:
            logger.info("Non-interactive mode: continuing with migration")

    # Run migration
    migrator = ImportMigrator(project_root, dry_run=args.dry_run)
    stats = migrator.run_migration()

    # Exit with appropriate code
    if stats['errors'] > 0:
        logger.error("Migration completed with errors")
        sys.exit(1)
    elif stats['files_modified'] > 0:
        logger.info("Migration completed successfully")
        sys.exit(0)
    else:
        logger.info("No files needed migration")
        sys.exit(0)

if __name__ == '__main__':
    main()