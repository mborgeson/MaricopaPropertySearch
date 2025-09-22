#!/usr/bin/env python3
"""
Static GUI Analysis for Maricopa Property Search Application
Analyzes GUI code structure without requiring GUI initialization
"""

import sys
import os
import ast
import inspect
from pathlib import Path
from datetime import datetime

# Add the src directory to the path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
)


class StaticGUIAnalyzer:
    """Analyzes GUI code structure and identifies potential issues"""

    def __init__(self):
        self.issues = []
        self.components = {}
        self.methods = {}
        self.imports = {}
        self.gui_file_path = None

    def analyze_gui_file(self):
        """Analyze the main GUI file"""
        print("🔍 Starting Static GUI Analysis...")

        # Find the GUI file
        possible_paths = [
            "src/gui/enhanced_main_window.py",
            "../src/gui/enhanced_main_window.py",
            "./src/gui/enhanced_main_window.py",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                self.gui_file_path = path
                break

        if not self.gui_file_path:
            self.issues.append("❌ CRITICAL: Cannot find enhanced_main_window.py")
            return False

        print(f"📁 Found GUI file: {self.gui_file_path}")

        try:
            with open(self.gui_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse the AST
            tree = ast.parse(content)

            # Analyze the structure
            self.analyze_imports(tree)
            self.analyze_classes(tree)
            self.analyze_methods(tree)

            return True

        except Exception as e:
            self.issues.append(f"❌ CRITICAL: Failed to parse GUI file: {e}")
            return False

    def analyze_imports(self, tree):
        """Analyze import statements"""
        print("📦 Analyzing imports...")

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports[alias.name] = "import"
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    self.imports[f"{module}.{alias.name}"] = "from_import"

        # Check critical imports
        critical_imports = [
            "PyQt5.QtWidgets",
            "PyQt5.QtCore",
            "PyQt5.QtGui",
            "config_manager",
            "database_manager",
            "background_data_collector",
        ]

        for imp in critical_imports:
            found = any(imp in key for key in self.imports.keys())
            if found:
                self.components[f'import_{imp.replace(".", "_")}'] = "✅ FOUND"
            else:
                self.components[f'import_{imp.replace(".", "_")}'] = "❌ MISSING"
                self.issues.append(f"Missing critical import: {imp}")

    def analyze_classes(self, tree):
        """Analyze class definitions"""
        print("🏗️ Analyzing class definitions...")

        classes_found = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes_found.append(node.name)

                # Analyze class inheritance
                bases = [
                    base.id if hasattr(base, "id") else str(base) for base in node.bases
                ]
                self.components[f"class_{node.name}"] = (
                    f"✅ FOUND - inherits from: {bases}"
                )

                # Check for required GUI classes
                if node.name == "EnhancedMainWindow":
                    self.analyze_main_window_class(node)

        # Check for expected classes
        expected_classes = [
            "EnhancedMainWindow",
            "PropertyDetailsWidget",
            "NotificationArea",
            "StatusIndicator",
            "AdvancedFiltersWidget",
        ]

        for expected in expected_classes:
            if expected in classes_found:
                self.components[f"class_check_{expected}"] = "✅ FOUND"
            else:
                self.components[f"class_check_{expected}"] = "❌ MISSING"
                self.issues.append(f"Expected class not found: {expected}")

    def analyze_main_window_class(self, class_node):
        """Analyze the main window class specifically"""
        print("🏠 Analyzing EnhancedMainWindow class...")

        methods_found = []
        attributes_found = []

        for node in ast.walk(class_node):
            if isinstance(node, ast.FunctionDef):
                methods_found.append(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if hasattr(target, "attr"):
                        attributes_found.append(target.attr)

        # Check critical methods
        critical_methods = [
            "__init__",
            "setup_ui",
            "perform_search",
            "start_background_collection",
            "show_export_dialog",
            "connect_signals",
        ]

        for method in critical_methods:
            if method in methods_found:
                self.components[f"method_{method}"] = "✅ FOUND"
            else:
                self.components[f"method_{method}"] = "❌ MISSING"
                self.issues.append(f"Critical method missing: {method}")

    def analyze_methods(self, tree):
        """Analyze method definitions and their complexity"""
        print("⚙️ Analyzing method implementations...")

        method_stats = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count lines of code
                if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                    lines = node.end_lineno - node.lineno + 1
                    method_stats[node.name] = {
                        "lines": lines,
                        "args": len(node.args.args) if node.args else 0,
                    }

                    # Flag very long methods
                    if lines > 100:
                        self.issues.append(
                            f"⚠️ Long method detected: {node.name} ({lines} lines)"
                        )

        self.methods = method_stats

    def check_gui_patterns(self):
        """Check for common GUI patterns and potential issues"""
        print("🔍 Checking GUI patterns...")

        try:
            with open(self.gui_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for signal connections
            if "connect(" in content:
                self.components["signal_connections"] = (
                    "✅ FOUND - Signal connections present"
                )
            else:
                self.components["signal_connections"] = (
                    "❌ MISSING - No signal connections found"
                )
                self.issues.append("No PyQt signal connections found")

            # Check for error handling
            if "try:" in content and "except" in content:
                self.components["error_handling"] = "✅ FOUND - Error handling present"
            else:
                self.components["error_handling"] = "⚠️ LIMITED - Minimal error handling"
                self.issues.append("Limited error handling detected")

            # Check for threading
            if "QThread" in content or "QTimer" in content:
                self.components["threading"] = "✅ FOUND - Threading components present"
            else:
                self.components["threading"] = "⚠️ LIMITED - No threading detected"

            # Check for database integration
            if "db_manager" in content or "DatabaseManager" in content:
                self.components["database_integration"] = (
                    "✅ FOUND - Database integration present"
                )
            else:
                self.components["database_integration"] = (
                    "❌ MISSING - No database integration"
                )
                self.issues.append("No database integration found")

            # Check for progress indicators
            if "QProgressBar" in content or "progress" in content.lower():
                self.components["progress_indicators"] = (
                    "✅ FOUND - Progress indicators present"
                )
            else:
                self.components["progress_indicators"] = (
                    "⚠️ LIMITED - Limited progress feedback"
                )

        except Exception as e:
            self.issues.append(f"Pattern analysis failed: {e}")

    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("\n" + "=" * 80)
        print("📋 STATIC GUI ANALYSIS REPORT")
        print("=" * 80)

        # Component analysis
        print("\n🏗️ COMPONENT ANALYSIS:")
        for component, status in self.components.items():
            print(f"  {component:40} | {status}")

        # Method statistics
        if self.methods:
            print(f"\n⚙️ METHOD STATISTICS:")
            print(f"  Total methods found: {len(self.methods)}")

            # Top 5 longest methods
            sorted_methods = sorted(
                self.methods.items(), key=lambda x: x[1]["lines"], reverse=True
            )[:5]
            print("  Longest methods:")
            for name, stats in sorted_methods:
                print(
                    f"    {name:30} | {stats['lines']:3} lines | {stats['args']:2} args"
                )

        # Issues found
        if self.issues:
            print(f"\n🚨 ISSUES IDENTIFIED ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i:2}. {issue}")
        else:
            print("\n✅ No critical issues identified!")

        # Summary statistics
        total_components = len(self.components)
        passed_components = len(
            [c for c in self.components.values() if c.startswith("✅")]
        )
        warning_components = len(
            [c for c in self.components.values() if c.startswith("⚠️")]
        )
        failed_components = len(
            [c for c in self.components.values() if c.startswith("❌")]
        )

        print(f"\n📊 SUMMARY:")
        print(f"  Total components analyzed: {total_components}")
        print(f"  ✅ Passed: {passed_components}")
        print(f"  ⚠️ Warnings: {warning_components}")
        print(f"  ❌ Failed: {failed_components}")
        print(f"  🚨 Issues: {len(self.issues)}")

        if total_components > 0:
            success_rate = (passed_components / total_components) * 100
            print(f"  📈 Success rate: {success_rate:.1f}%")

        return {
            "timestamp": datetime.now().isoformat(),
            "components": self.components,
            "methods": self.methods,
            "issues": self.issues,
            "summary": {
                "total_components": total_components,
                "passed": passed_components,
                "warnings": warning_components,
                "failed": failed_components,
                "total_issues": len(self.issues),
                "success_rate": success_rate if total_components > 0 else 0,
            },
        }


def main():
    """Main analysis function"""
    analyzer = StaticGUIAnalyzer()

    # Run analysis
    if analyzer.analyze_gui_file():
        analyzer.check_gui_patterns()
        report = analyzer.generate_report()

        # Save report
        try:
            import json

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"static_gui_analysis_{timestamp}.json"

            with open(filename, "w") as f:
                json.dump(report, f, indent=2)

            print(f"\n💾 Analysis report saved to: {filename}")

        except Exception as e:
            print(f"⚠️ Could not save report: {e}")

        return report
    else:
        print("💥 Analysis failed to complete")
        return None


if __name__ == "__main__":
    main()
