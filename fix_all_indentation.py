#!/usr/bin/env python3
"""
Comprehensive indentation fix script for all Python files with E999 errors
"""
import os
import re
import sys
from pathlib import Path


def fix_indentation_in_file(file_path):
    """Fix common indentation issues in a Python file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        fixed_lines = []
        in_class = False
        in_function = False
        indent_level = 0
        prev_line = ""

        for i, line in enumerate(lines):
            stripped = line.lstrip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                fixed_lines.append(line)
                prev_line = line
                continue

            # Check for class definitions
            if stripped.startswith("class "):
                in_class = True
                indent_level = len(line) - len(stripped)
                fixed_lines.append(line)
                prev_line = line
                continue

            # Check for function definitions at wrong level
            if stripped.startswith("def ") and i > 0:
                # Check if previous non-empty line suggests this should be at module level
                prev_stripped = prev_line.strip()

                # If after imports or module docstring, should be at module level
                if (
                    prev_stripped.startswith("import ")
                    or prev_stripped.startswith("from ")
                    or prev_stripped == '"""'
                    or prev_stripped == "'''"
                    or not prev_stripped
                ):
                    # Module level function
                    fixed_lines.append(stripped)
                    in_function = True
                    indent_level = 0
                elif in_class:
                    # Method in class
                    fixed_lines.append("    " + stripped)
                    in_function = True
                    indent_level = 4
                else:
                    fixed_lines.append(line)
                prev_line = line
                continue

            # Fix try/except blocks
            if stripped.startswith("try:"):
                fixed_lines.append(" " * indent_level + stripped)
                prev_line = line
                continue

            if stripped.startswith("except") or stripped.startswith("finally"):
                # Should be at same level as try
                fixed_lines.append(" " * indent_level + stripped)
                prev_line = line
                continue

            # Fix print statements that are incorrectly indented
            if stripped.startswith("print("):
                # Check context - if after function def, indent properly
                if in_function and len(line) - len(stripped) < indent_level + 4:
                    fixed_lines.append(" " * (indent_level + 4) + stripped)
                else:
                    fixed_lines.append(line)
                prev_line = line
                continue

            # Default - keep the line as is
            fixed_lines.append(line)
            prev_line = line

        # Write back
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)

        return True
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    """Fix indentation in all files with E999 errors"""

    # Files with indentation errors from flake8 output
    files_to_fix = [
        "scripts/COMPLETE_SYSTEM_DEMONSTRATION.py",
        "scripts/DIAGNOSE_AND_FIX_ALL_ISSUES.py",
        "scripts/apply_critical_fixes.py",
        "scripts/check_enhanced_property_data.py",
        "scripts/check_environment.py",
        "scripts/check_performance_regression.py",
        "scripts/check_specific_apn.py",
        "scripts/check_tax_history_records.py",
        "scripts/demonstrate_apn_fix.py",
        "scripts/diagnose_simple.py",
        "scripts/diagnose_tax_sales_data_flow.py",
        "scripts/fix_all_gui_issues.py",
        "scripts/fix_data_collection.py",
        "scripts/fix_database_user.py",
        "scripts/fix_gui_issues.py",
        "scripts/fix_imports.py",
        "scripts/fix_remaining_issues.py",
        "scripts/fix_tax_data_discrepancy.py",
        "scripts/install_chromedriver.py",
        "scripts/investigate_real_endpoints.py",
        "scripts/populate_sample_data.py",
        "scripts/setup_database_tables.py",
        "scripts/test_complete_data_flow.py",
        "scripts/test_db_connection.py",
        "scripts/test_installation.py",
        "scripts/test_real_endpoints.py",
        "scripts/validate_manual_collect_fix.py",
        "scripts/verify_and_fix_all_data.py",
        "scripts/verify_dependencies.py",
        "src/advanced_search_engine.py",
        "src/api_client_unified.py",
        "src/batch_processing_examples.py",
        "src/batch_processing_manager.py",
        "src/batch_search_demo.py",
        "src/batch_search_engine.py",
        "src/batch_search_integration.py",
        "src/database_manager_unified.py",
        "src/enhanced_api_client.py",
        "src/enhanced_batch_search_dialog.py",
        "src/enhanced_config_manager.py",
        "src/gui/enhanced_main_window.py",
        "src/gui/enhanced_main_window_backup.py",
        "src/gui/enhanced_main_window_before_fix.py",
        "src/gui/enhanced_main_window_pre_fix_backup.py",
        "src/gui/gui_enhancements_dialogs.py",
        "src/gui/refresh_crash_fix.py",
        "tests/application_diagnostic.py",
        "tests/comprehensive_application_test.py",
        "tests/comprehensive_gui_test.py",
        "tests/conftest.py",
        "tests/e2e/run_missouri_tests.py",
        "tests/e2e/test_complete_workflows.py",
        "tests/fix_missing_classes.py",
        "tests/fixtures/mock_responses.py",
        "tests/gui_framework_migration_test.py",
        "tests/gui_launcher_test.py",
        "tests/integration/test_api_integration.py",
        "tests/integration/test_api_with_token.py",
        "tests/integration/test_component_integration.py",
        "tests/integration/test_error_handling.py",
        "tests/integration/test_real_implementation.py",
        "tests/integration/test_user_experience.py",
        "tests/manual_verification_report.py",
        "tests/mock_client_fix.py",
        "tests/performance/test_load_testing.py",
        "tests/performance/test_performance_benchmarks.py",
        "tests/quick_run_test.py",
        "tests/run_comprehensive_tests.py",
        "tests/runtime_gui_test.py",
        "tests/setup_test_database.py",
        "tests/setup_test_schema.py",
        "tests/simple_database_test.py",
        "tests/static_gui_analysis.py",
        "tests/systematic_app_test.py",
        "tests/test_api_comprehensive.py",
        "tests/test_api_with_real_apns.py",
        "tests/test_apn_keyerror_fix.py",
        "tests/test_application_with_fixes.py",
        "tests/test_background_fix.py",
        "tests/test_batch_search_integration.py",
        "tests/test_database_manager_fixes.py",
        "tests/test_fixed_data_collection.py",
        "tests/test_gui_database_integration.py",
        "tests/test_hive_mind_fixes.py",
        "tests/test_runtime_issues.py",
        "tests/test_tax_sales_fix.py",
        "tests/unit/test_search_performance.py",
        "tests/unit/test_threadsafe_database_manager.py",
        "tests/unit/test_unified_data_collector.py",
        "tests/verify_fixes.py",
        "tests/verify_smart_agent_fixes.py",
    ]

    # More files from the full list (continuation)
    files_to_fix.extend(
        [
            "src/gui/refresh_patch.py",
            "src/improved_logging_setup.py",
            "src/logging_config.py",
            "src/maricopa_property_search.py",
            "src/optimized_web_scraper.py",
            "src/parallel_web_scraper.py",
            "src/performance_analysis.py",
            "src/performance_monitor.py",
            "src/performance_optimized_data_collector.py",
            "src/performance_test.py",
            "src/recorder_scraper.py",
            "src/tax_scraper.py",
            "src/test_enhanced_api_client.py",
            "src/test_logging_system.py",
            "src/threadsafe_database_manager.py",
            "src/unified_data_collector.py",
            "src/web_scraper.py",
        ]
    )

    fixed_count = 0
    failed_count = 0

    for file_path in files_to_fix:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue

        print(f"Fixing indentation in: {file_path}")
        if fix_indentation_in_file(file_path):
            fixed_count += 1
        else:
            failed_count += 1

    print(f"\n✅ Fixed {fixed_count} files")
    if failed_count > 0:
        print(f"❌ Failed to fix {failed_count} files")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
