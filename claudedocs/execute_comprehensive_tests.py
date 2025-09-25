#!/usr/bin/env python
"""
Comprehensive Test Execution Script
Orchestrates complete testing workflow with reporting and analysis
"""
import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_execution.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveTestRunner:
    """Orchestrates comprehensive testing with reporting and analysis"""
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_results = {}
        self.start_time = time.time()
        self.reports_dir = project_root / "tests" / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    def run_test_suite(self, suite_name: str, command: List[str], timeout: int = 300) -> Dict[str, Any]:
        """Execute a test suite and capture results"""
        logger.info(f"🧪 Running {suite_name} tests...")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            test_result = {
                'suite': suite_name,
                'command': ' '.join(command),
                'duration': duration,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'passed': result.returncode == 0,
                'timestamp': datetime.now().isoformat()
            }
            
            if result.returncode == 0:
                logger.info(f"✅ {suite_name} tests PASSED in {duration:.2f}s")
            else:
                logger.error(f"❌ {suite_name} tests FAILED in {duration:.2f}s")
                logger.error(f"Error output: {result.stderr}")
                
            return test_result
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ {suite_name} tests TIMED OUT after {timeout}s")
            return {
                'suite': suite_name,
                'command': ' '.join(command),
                'duration': timeout,
                'return_code': -1,
                'stdout': '',
                'stderr': f'Test suite timed out after {timeout} seconds',
                'passed': False,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"💥 {suite_name} tests CRASHED: {e}")
            return {
                'suite': suite_name,
                'command': ' '.join(command),
                'duration': 0,
                'return_code': -2,
                'stdout': '',
                'stderr': str(e),
                'passed': False,
                'timestamp': datetime.now().isoformat()
            }
    def run_unit_tests(self) -> Dict[str, Any]:
        """Execute unit tests with coverage reporting"""
        command = [
            'pytest',
            'tests/unit/',
            '-v',
            '--cov=src',
            '--cov-report=html:tests/reports/coverage_html',
            '--cov-report=term-missing',
            '--cov-report=json:tests/reports/coverage.json',
            '--junitxml=tests/reports/unit_tests.xml',
            '--tb=short',
            '--durations=10'
        ]
        return self.run_test_suite('Unit Tests', command, timeout=300)
    def run_integration_tests(self) -> Dict[str, Any]:
        """Execute integration tests"""
        command = [
            'pytest',
            'tests/integration/',
            '-v',
            '--junitxml=tests/reports/integration_tests.xml',
            '--tb=short',
            '-m', 'integration'
        ]
        return self.run_test_suite('Integration Tests', command, timeout=600)
    def run_performance_tests(self) -> Dict[str, Any]:
        """Execute performance benchmarks"""
        command = [
            'pytest',
            'tests/performance/',
            '-v',
            '--benchmark-only',
            '--benchmark-json=tests/reports/benchmark.json',
            '--benchmark-sort=mean',
            '--junitxml=tests/reports/performance_tests.xml',
            '-m', 'performance'
        ]
        return self.run_test_suite('Performance Tests', command, timeout=900)
    def run_e2e_tests(self) -> Dict[str, Any]:
        """Execute end-to-end tests"""
        command = [
            'pytest',
            'tests/e2e/',
            '-v',
            '--junitxml=tests/reports/e2e_tests.xml',
            '--tb=long',
            '-m', 'e2e'
        ]
        return self.run_test_suite('E2E Tests', command, timeout=1200)
    def run_gui_tests(self) -> Dict[str, Any]:
        """Execute GUI tests"""
        # Set up virtual display for headless GUI testing
        env = os.environ.copy()
        env['QT_QPA_PLATFORM'] = 'offscreen'
        
        command = [
            'pytest',
            'tests/',
            '-v',
            '--junitxml=tests/reports/gui_tests.xml',
            '--tb=short',
            '-m', 'gui'
        ]
        return self.run_test_suite('GUI Tests', command, timeout=600)
    def run_security_tests(self) -> Dict[str, Any]:
        """Execute security vulnerability scanning"""
        command = [
            'bandit',
            '-r', 'src/',
            '-f', 'json',
            '-o', 'tests/reports/security_report.json'
        ]
        return self.run_test_suite('Security Scan', command, timeout=300)
    def run_code_quality_checks(self) -> Dict[str, Any]:
        """Execute code quality checks"""
        commands = [
            (['flake8', 'src/', '--output-file=tests/reports/flake8.txt'], 'Flake8'),
            (['mypy', 'src/', '--junit-xml=tests/reports/mypy.xml'], 'MyPy'),
            (['black', '--check', 'src/'], 'Black Formatting')
        ]
        
        results = []
        for command, name in commands:
            result = self.run_test_suite(f'Code Quality - {name}', command, timeout=120)
            results.append(result)
        
        # Aggregate results
        overall_passed = all(r['passed'] for r in results)
        total_duration = sum(r['duration'] for r in results)
        
        return {
            'suite': 'Code Quality Checks',
            'command': 'Multiple quality tools',
            'duration': total_duration,
            'return_code': 0 if overall_passed else 1,
            'stdout': '\n'.join(r['stdout'] for r in results),
            'stderr': '\n'.join(r['stderr'] for r in results),
            'passed': overall_passed,
            'timestamp': datetime.now().isoformat(),
            'detailed_results': results
        }
    def analyze_coverage_report(self) -> Dict[str, Any]:
        """Analyze code coverage and identify gaps"""
        coverage_file = self.reports_dir / "coverage.json"
        
        if not coverage_file.exists():
            return {'error': 'Coverage report not found'}
        
        try:
            with open(coverage_file) as f:
                coverage_data = json.load(f)
            
            total_coverage = coverage_data['totals']['percent_covered']
            
            # Identify low-coverage files
            low_coverage_files = []
            for filename, file_data in coverage_data['files'].items():
                if file_data['summary']['percent_covered'] < 80:
                    low_coverage_files.append({
                        'file': filename,
                        'coverage': file_data['summary']['percent_covered'],
                        'missing_lines': file_data['summary']['num_statements'] - file_data['summary']['covered_lines']
                    })
            
            return {
                'total_coverage': total_coverage,
                'coverage_target': 80.0,
                'meets_target': total_coverage >= 80.0,
                'low_coverage_files': low_coverage_files,
                'files_analyzed': len(coverage_data['files'])
            }
            
        except Exception as e:
            return {'error': f'Failed to analyze coverage: {e}'}
    def generate_comprehensive_report(self) -> str:
        """Generate a comprehensive test execution report"""
        total_duration = time.time() - self.start_time
        
        # Count test results
        passed_suites = sum(1 for result in self.test_results.values() if result['passed'])
        total_suites = len(self.test_results)
        
        # Analyze coverage
        coverage_analysis = self.analyze_coverage_report()
        
        # Generate report
        report = f"""
# Comprehensive Test Execution Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Execution Time: {total_duration:.2f} seconds

## Summary
- Test Suites Executed: {total_suites}
- Passed: {passed_suites}
- Failed: {total_suites - passed_suites}
- Success Rate: {(passed_suites/total_suites)*100:.1f}%

## Coverage Analysis
"""
        
        if 'error' not in coverage_analysis:
            report += f"""
- Overall Coverage: {coverage_analysis['total_coverage']:.1f}%
- Target Coverage: {coverage_analysis['coverage_target']:.1f}%
- Meets Target: {'✅ YES' if coverage_analysis['meets_target'] else '❌ NO'}
- Files Analyzed: {coverage_analysis['files_analyzed']}
"""
            
            if coverage_analysis['low_coverage_files']:
                report += "\n### Low Coverage Files (< 80%):\n"
                for file_info in coverage_analysis['low_coverage_files'][:5]:  # Top 5
                    report += f"- {file_info['file']}: {file_info['coverage']:.1f}% ({file_info['missing_lines']} lines uncovered)\n"
        else:
            report += f"\n- Coverage Analysis: {coverage_analysis['error']}\n"
        
        report += "\n## Test Suite Results\n"
        
        for suite_name, result in self.test_results.items():
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            report += f"\n### {suite_name} - {status}\n"
            report += f"- Duration: {result['duration']:.2f} seconds\n"
            report += f"- Command: `{result['command']}`\n"
            
            if not result['passed']:
                report += f"- Error: {result['stderr'][:200]}...\n"
        
        # Performance benchmarks
        if 'Performance Tests' in self.test_results:
            benchmark_file = self.reports_dir / "benchmark.json"
            if benchmark_file.exists():
                try:
                    with open(benchmark_file) as f:
                        benchmark_data = json.load(f)
                    
                    report += "\n## Performance Benchmarks\n"
                    for benchmark in benchmark_data['benchmarks'][:5]:  # Top 5
                        report += f"- {benchmark['name']}: {benchmark['stats']['mean']:.4f}s (mean)\n"
                except:
                        report += "\n## Performance Benchmarks\nError parsing benchmark data\n"
        
        # Quality Gates Assessment
        report += "\n## Quality Gates Assessment\n"
        
        quality_gates = [
            ("Unit Tests", self.test_results.get('Unit Tests', {}).get('passed', False)),
            ("Integration Tests", self.test_results.get('Integration Tests', {}).get('passed', False)),
            ("Code Coverage >80%", coverage_analysis.get('meets_target', False)),
            ("Security Scan", self.test_results.get('Security Scan', {}).get('passed', False)),
            ("Code Quality", self.test_results.get('Code Quality Checks', {}).get('passed', False))
        ]
        
        all_gates_passed = all(passed for _, passed in quality_gates)
        
        for gate_name, passed in quality_gates:
            status = "✅ PASS" if passed else "❌ FAIL"
            report += f"- {gate_name}: {status}\n"
        
        report += f"\n**Overall Quality Assessment: {'✅ READY FOR RELEASE' if all_gates_passed else '❌ NOT READY - ISSUES NEED RESOLUTION'}**\n"
        
        return report
    def save_report(self, report: str) -> Path:
        """Save the comprehensive report to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.reports_dir / f"comprehensive_report_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"📊 Comprehensive report saved to: {report_file}")
        return report_file
    def main():
    """Main test execution workflow"""
    parser = argparse.ArgumentParser(description='Comprehensive Test Runner')
    parser.add_argument('--suite', choices=['unit', 'integration', 'performance', 'e2e', 'gui', 'security', 'quality', 'all'],
                       default='all', help='Test suite to run')
    parser.add_argument('--fast', action='store_true', help='Run only fast tests (unit + integration)')
    parser.add_argument('--critical', action='store_true', help='Run only critical path tests')
    parser.add_argument('--report-only', action='store_true', help='Generate report from existing test results')
    
    args = parser.parse_args()
    
    # Determine project root
    project_root = Path(__file__).parent.parent
    
    runner = ComprehensiveTestRunner(project_root)
    
    logger.info("🚀 Starting Comprehensive Test Execution")
    logger.info(f"Project Root: {project_root}")
    
    if not args.report_only:
        # Execute test suites based on arguments
        if args.fast:
            runner.test_results['Unit Tests'] = runner.run_unit_tests()
            runner.test_results['Integration Tests'] = runner.run_integration_tests()
        elif args.critical:
            runner.test_results['Unit Tests'] = runner.run_unit_tests()
            runner.test_results['Integration Tests'] = runner.run_integration_tests()
            runner.test_results['Code Quality Checks'] = runner.run_code_quality_checks()
        elif args.suite == 'all':
            runner.test_results['Code Quality Checks'] = runner.run_code_quality_checks()
            runner.test_results['Security Scan'] = runner.run_security_tests()
            runner.test_results['Unit Tests'] = runner.run_unit_tests()
            runner.test_results['Integration Tests'] = runner.run_integration_tests()
            runner.test_results['Performance Tests'] = runner.run_performance_tests()
            runner.test_results['GUI Tests'] = runner.run_gui_tests()
            runner.test_results['E2E Tests'] = runner.run_e2e_tests()
        else:
            # Run specific suite
            suite_methods = {
                'unit': runner.run_unit_tests,
                'integration': runner.run_integration_tests,
                'performance': runner.run_performance_tests,
                'e2e': runner.run_e2e_tests,
                'gui': runner.run_gui_tests,
                'security': runner.run_security_tests,
                'quality': runner.run_code_quality_checks
            }
            
            if args.suite in suite_methods:
                runner.test_results[args.suite.title() + ' Tests'] = suite_methods[args.suite]()
    
    # Generate and save comprehensive report
    report = runner.generate_comprehensive_report()
    report_file = runner.save_report(report)
    
    # Display summary
        print("\n" + "="*80)
        print("📊 TEST EXECUTION SUMMARY")
        print("="*80)
        print(report)
    
    # Exit with appropriate code
    failed_suites = [name for name, result in runner.test_results.items() if not result['passed']]
    
    if failed_suites:
        logger.error(f"❌ Test execution completed with failures: {', '.join(failed_suites)}")
        sys.exit(1)
    else:
        logger.info("✅ All test suites passed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()


# Example usage commands:
"""
# Run all tests (full comprehensive suite)
python claudedocs/execute_comprehensive_tests.py --suite all

# Run only fast tests (unit + integration)
python claudedocs/execute_comprehensive_tests.py --fast

# Run only critical path tests
python claudedocs/execute_comprehensive_tests.py --critical

# Run specific test suite
python claudedocs/execute_comprehensive_tests.py --suite unit
python claudedocs/execute_comprehensive_tests.py --suite integration
python claudedocs/execute_comprehensive_tests.py --suite performance

# Generate report from existing results
python claudedocs/execute_comprehensive_tests.py --report-only

# Integration with CI/CD:
# - For commits: --fast (2-3 minutes)
# - For daily builds: --critical (5-10 minutes)  
# - For releases: --suite all (30-60 minutes)
"""