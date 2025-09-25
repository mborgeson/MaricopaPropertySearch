#!/usr/bin/env python3
"""
Validation script for the manual_collect_data AttributeError fix

This script validates that:
1. PropertyDetailsDialog has the correct manual_collect_data method that uses property_data
2. The method accesses the APN from self.property_data instead of table selection
3. All necessary imports and method calls are correct
4. No reference to self.results_table exists in PropertyDetailsDialog context
"""
import ast
import os
import sys

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
    def validate_fix():
    """Validate that the manual_collect_data fix is correct"""
    enhanced_main_window_path = os.path.join(
        project_root, "src", "gui", "enhanced_main_window.py"
    )

    if not os.path.exists(enhanced_main_window_path):
        print(f"ERROR: File not found: {enhanced_main_window_path}")
        return False
        print("Validating manual_collect_data fix...")

    with open(enhanced_main_window_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse the AST to find the manual_collect_data method
try:
        tree = ast.parse(content)
except SyntaxError as e:
        print(f"ERROR: Syntax error in file: {e}")
        return False

    # Find PropertyDetailsDialog class and its manual_collect_data method
    property_dialog_class = None
    manual_collect_method = None

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "PropertyDetailsDialog":
            property_dialog_class = node

            # Look for manual_collect_data method
            for class_node in node.body:
                if (
                    isinstance(class_node, ast.FunctionDef)
                    and class_node.name == "manual_collect_data"
                ):
                    manual_collect_method = class_node
                    break

    if not property_dialog_class:
        print("ERROR: PropertyDetailsDialog class not found")
        return False

    if not manual_collect_method:
        print("ERROR: manual_collect_data method not found in PropertyDetailsDialog")
        return False
        print("OK: PropertyDetailsDialog class found")
        print("OK: manual_collect_data method found")

    # Check method content for correct implementation
    method_source = ast.get_source_segment(content, manual_collect_method)
    if method_source:
        # Check that it uses property_data instead of results_table
        if "self.property_data.get('apn'," in method_source:
        print("OK: Method correctly uses self.property_data.get('apn')")
        else:
        print("ERROR: Method does not use self.property_data.get('apn')")
            return False

        # Check that it doesn't use results_table
        if "self.results_table" in method_source:
        print("ERROR: Method still references self.results_table")
            return False
        else:
        print("OK: Method does not reference self.results_table")

        # Check that it uses background_manager properly
        if "self.background_manager" in method_source:
        print("OK: Method uses self.background_manager")
        else:
        print("ERROR: Method does not use self.background_manager")
            return False

        # Check for proper error handling
        if "try:" in method_source and "except Exception" in method_source:
        print("OK: Method has proper error handling")
        else:
        print("ERROR: Method lacks proper error handling")
            return False

    # Check imports
    if (
        "from src.background_data_collector import" in content
        and "JobPriority" in content
    ):
        print("OK: JobPriority is properly imported")
    else:
        print("ERROR: JobPriority import not found")
        return False

    if "from PyQt5.QtCore import" in content and "QTimer" in content:
        print("OK: QTimer is properly imported")
    else:
        print("ERROR: QTimer import not found")
        return False
        print("\nSUCCESS: All validation checks passed!")
        print("The manual_collect_data AttributeError fix appears to be correct.")
    return True


if __name__ == "__main__":
    success = validate_fix()
    sys.exit(0 if success else 1)
