"""
Comprehensive test runner with reporting and analysis
"""

import pytest
import sys
import json
import time
from pathlib import Path
from datetime import datetime
import argparse
import subprocess

# Test suite configuration
TEST_SUITES = {
    'unit': {
        'path': 'tests/unit/',
        'markers': 'unit',
        'description': 'Unit tests for individual components',
        'timeout': 300  # 5 minutes
    },
    'integration': {
        'path': 'tests/integration/',
        'markers': 'integration',
        'description': 'Integration tests for component interactions',
        'timeout': 600  # 10 minutes
    },
    'performance': {
        'path': 'tests/performance/',
        'markers': 'performance',
        'description': 'Performance and load tests',
        'timeout': 1800  # 30 minutes
    },
    'e2e': {
        'path': 'tests/e2e/',
        'markers': 'e2e',
        'description': 'End-to-end workflow tests',
        'timeout': 900  # 15 minutes
    },
    'gui': {
        'path': 'tests/',
        'markers': 'gui',
        'description': 'GUI and user interface tests',
        'timeout': 600  # 10 minutes
    },
    'slow': {
        'path': 'tests/',
        'markers': 'slow',
        'description': 'Slow running tests (for comprehensive validation)',
        'timeout': 2400  # 40 minutes
    }
}

class TestRunner:
    """Comprehensive test runner with reporting"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_results = {}
        self.start_time = None
        self.reports_dir = project_root / "tests" / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
    def run_test_suite(self, suite_name: str, **pytest_args) -> dict:
        """Run a specific test suite and return results"""
        
        if suite_name not in TEST_SUITES:
            raise ValueError(f"Unknown test suite: {suite_name}")
            
        suite_config = TEST_SUITES[suite_name]
        
        print(f"\n{'='*60}")
        print(f"Running {suite_name.upper()} tests")
        print(f"Description: {suite_config['description']}")
        print(f"{'='*60}")
        
        # Prepare pytest arguments
        args = [
            str(self.project_root / suite_config['path']),
            '-v',
            '--tb=short',
            '--durations=10',
            f'--timeout={suite_config["timeout"]}',
            f'--junitxml={self.reports_dir / f"{suite_name}_results.xml"}',
            f'--html={self.reports_dir / f"{suite_name}_report.html"}',
            '--self-contained-html'
        ]
        
        # Add marker filter
        if suite_config.get('markers'):
            args.extend(['-m', suite_config['markers']])
            
        # Add custom pytest arguments
        for key, value in pytest_args.items():
            if key == 'verbose' and value:
                args.append('-vv')
            elif key == 'capture' and value == 'no':
                args.append('-s')
            elif key == 'pdb' and value:
                args.append('--pdb')
            elif key == 'maxfail' and value:
                args.extend(['--maxfail', str(value)])
                
        start_time = time.time()
        
        try:
            # Run pytest
            result = pytest.main(args)
            
            execution_time = time.time() - start_time
            
            suite_results = {
                'suite_name': suite_name,
                'exit_code': result,
                'execution_time': execution_time,
                'success': result == 0,
                'timestamp': datetime.now().isoformat(),
                'timeout': suite_config['timeout']
            }
            
            # Parse detailed results from XML if available
            xml_report = self.reports_dir / f"{suite_name}_results.xml"
            if xml_report.exists():
                suite_results.update(self._parse_junit_xml(xml_report))
                
            self.test_results[suite_name] = suite_results
            
            print(f"\n{suite_name.upper()} Tests Complete:")
            print(f"  Result: {'PASSED' if result == 0 else 'FAILED'}")
            print(f"  Time: {execution_time:.1f}s")
            
            return suite_results
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_results = {
                'suite_name': suite_name,
                'exit_code': -1,
                'execution_time': execution_time,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            self.test_results[suite_name] = error_results
            print(f"\n{suite_name.upper()} Tests FAILED with error: {e}")
            return error_results
            
    def run_comprehensive_tests(self, suites: list = None, **pytest_args) -> dict:
        """Run comprehensive test suite"""
        
        if suites is None:
            suites = ['unit', 'integration', 'performance', 'e2e']
            
        self.start_time = time.time()
        
        print("Maricopa Property Search - Comprehensive Test Suite")
        print(f"{'='*80}")
        print(f"Test suites: {', '.join(suites)}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        # Run each test suite
        for suite_name in suites:
            try:
                self.run_test_suite(suite_name, **pytest_args)
            except KeyboardInterrupt:
                print(f"\nTest execution interrupted during {suite_name} suite")
                break
            except Exception as e:
                print(f"\nUnexpected error in {suite_name} suite: {e}")
                continue
                
        # Generate comprehensive report
        return self._generate_final_report()
        
    def run_smoke_tests(self) -> dict:
        """Run quick smoke tests for basic functionality"""
        
        print("Running Smoke Tests (Quick Validation)")
        print("="*50)
        
        # Run essential tests only
        smoke_args = [
            'tests/',
            '-m', 'unit and not slow',
            '-v',
            '--tb=short',
            '--maxfail=5',
            f'--junitxml={self.reports_dir / "smoke_results.xml"}'
        ]
        
        start_time = time.time()
        result = pytest.main(smoke_args)
        execution_time = time.time() - start_time
        
        smoke_results = {
            'suite_name': 'smoke',
            'exit_code': result,
            'execution_time': execution_time,
            'success': result == 0,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\nSmoke Tests: {'PASSED' if result == 0 else 'FAILED'} ({execution_time:.1f}s)")
        
        return smoke_results
        
    def run_performance_baseline(self) -> dict:
        """Run performance tests to establish baseline metrics"""
        
        print("Establishing Performance Baseline")
        print("="*40)
        
        baseline_args = [
            'tests/performance/',
            '-m', 'performance and not slow',
            '-v',
            '--tb=short',
            '--benchmark-only',
            '--benchmark-save=baseline',
            f'--junitxml={self.reports_dir / "baseline_results.xml"}'
        ]
        
        start_time = time.time()
        result = pytest.main(baseline_args)
        execution_time = time.time() - start_time
        
        baseline_results = {
            'suite_name': 'baseline',
            'exit_code': result,
            'execution_time': execution_time,
            'success': result == 0,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\nBaseline Tests: {'COMPLETED' if result == 0 else 'FAILED'} ({execution_time:.1f}s)")
        
        return baseline_results
        
    def _parse_junit_xml(self, xml_file: Path) -> dict:
        """Parse JUnit XML results for detailed metrics"""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            return {
                'tests_total': int(root.get('tests', 0)),
                'tests_passed': int(root.get('tests', 0)) - int(root.get('failures', 0)) - int(root.get('errors', 0)),
                'tests_failed': int(root.get('failures', 0)),
                'tests_errors': int(root.get('errors', 0)),
                'tests_skipped': int(root.get('skipped', 0)),
                'test_time': float(root.get('time', 0.0))
            }
        except Exception as e:
            print(f"Warning: Could not parse XML results: {e}")
            return {}
            
    def _generate_final_report(self) -> dict:
        """Generate comprehensive test report"""
        
        total_time = time.time() - self.start_time if self.start_time else 0
        
        # Calculate overall statistics
        total_tests = sum(r.get('tests_total', 0) for r in self.test_results.values())
        total_passed = sum(r.get('tests_passed', 0) for r in self.test_results.values())
        total_failed = sum(r.get('tests_failed', 0) for r in self.test_results.values())
        total_errors = sum(r.get('tests_errors', 0) for r in self.test_results.values())
        
        suites_passed = sum(1 for r in self.test_results.values() if r.get('success', False))
        suites_total = len(self.test_results)
        
        overall_success = suites_passed == suites_total and total_failed == 0 and total_errors == 0
        
        final_report = {
            'overall_success': overall_success,
            'total_execution_time': total_time,
            'suites': {
                'total': suites_total,
                'passed': suites_passed,
                'failed': suites_total - suites_passed
            },
            'tests': {
                'total': total_tests,
                'passed': total_passed,
                'failed': total_failed,
                'errors': total_errors
            },
            'suite_results': self.test_results,
            'timestamp': datetime.now().isoformat(),
            'recommendations': self._generate_recommendations()
        }
        
        # Save detailed report
        report_file = self.reports_dir / f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
            
        # Print summary
        self._print_final_summary(final_report)
        
        return final_report
        
    def _generate_recommendations(self) -> list:
        """Generate recommendations based on test results"""
        recommendations = []
        
        for suite_name, results in self.test_results.items():
            if not results.get('success', False):
                if results.get('tests_failed', 0) > 0:
                    recommendations.append(f"Fix {results['tests_failed']} failing tests in {suite_name} suite")
                    
                if results.get('tests_errors', 0) > 0:
                    recommendations.append(f"Resolve {results['tests_errors']} test errors in {suite_name} suite")
                    
                if results.get('execution_time', 0) > TEST_SUITES.get(suite_name, {}).get('timeout', 3600):
                    recommendations.append(f"Optimize {suite_name} test performance - execution time exceeded timeout")
                    
        # Performance-specific recommendations
        performance_results = self.test_results.get('performance', {})
        if performance_results.get('tests_failed', 0) > 0:
            recommendations.append("Performance benchmarks not met - review application optimization")
            
        # Coverage recommendations
        if len(self.test_results) < 3:
            recommendations.append("Run complete test suite including integration and e2e tests")
            
        return recommendations
        
    def _print_final_summary(self, report: dict):
        """Print comprehensive test summary"""
        
        print(f"\n{'='*80}")
        print("COMPREHENSIVE TEST REPORT")
        print(f"{'='*80}")
        print(f"Overall Result: {'✅ PASSED' if report['overall_success'] else '❌ FAILED'}")
        print(f"Total Time: {report['total_execution_time']:.1f}s")
        print(f"Report saved: {self.reports_dir}")
        
        print(f"\nSuite Summary:")
        print(f"  Total Suites: {report['suites']['total']}")
        print(f"  Passed: {report['suites']['passed']}")
        print(f"  Failed: {report['suites']['failed']}")
        
        print(f"\nTest Summary:")
        print(f"  Total Tests: {report['tests']['total']}")
        print(f"  Passed: {report['tests']['passed']}")
        print(f"  Failed: {report['tests']['failed']}")
        print(f"  Errors: {report['tests']['errors']}")
        
        # Suite details
        print(f"\nSuite Details:")
        for suite_name, results in report['suite_results'].items():
            status = '✅' if results.get('success', False) else '❌'
            time_str = f"{results.get('execution_time', 0):.1f}s"
            test_count = results.get('tests_total', '?')
            print(f"  {status} {suite_name.upper()}: {test_count} tests in {time_str}")
            
        # Recommendations
        if report['recommendations']:
            print(f"\nRecommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")
                
        print(f"\n{'='*80}")
        
        if report['overall_success']:
            print("🎉 ALL TESTS PASSED - Application ready for production!")
            print("\nNext Steps:")
            print("- Review performance metrics in detailed reports")
            print("- Deploy to staging environment")
            print("- Schedule regular test execution")
        else:
            print("⚠️  TESTS FAILED - Review failures before proceeding")
            print("\nNext Steps:")
            print("- Review detailed test reports in tests/reports/")
            print("- Fix failing tests")
            print("- Re-run test suite")
            
        print(f"{'='*80}")

def main():
    """Main entry point for test runner"""
    
    parser = argparse.ArgumentParser(description="Comprehensive Test Runner")
    parser.add_argument('--suite', choices=list(TEST_SUITES.keys()), 
                       help="Run specific test suite")
    parser.add_argument('--smoke', action='store_true',
                       help="Run smoke tests only")
    parser.add_argument('--baseline', action='store_true',
                       help="Establish performance baseline")
    parser.add_argument('--all', action='store_true',
                       help="Run all test suites")
    parser.add_argument('--verbose', action='store_true',
                       help="Verbose output")
    parser.add_argument('--no-capture', action='store_true',
                       help="Don't capture stdout")
    parser.add_argument('--pdb', action='store_true',
                       help="Drop into debugger on failures")
    parser.add_argument('--maxfail', type=int, default=None,
                       help="Stop after N failures")
    
    args = parser.parse_args()
    
    # Determine project root
    project_root = Path(__file__).parent.parent
    
    # Initialize test runner
    runner = TestRunner(project_root)
    
    # Prepare pytest arguments
    pytest_args = {
        'verbose': args.verbose,
        'capture': 'no' if args.no_capture else 'yes',
        'pdb': args.pdb,
        'maxfail': args.maxfail
    }
    
    try:
        if args.smoke:
            results = runner.run_smoke_tests()
        elif args.baseline:
            results = runner.run_performance_baseline()
        elif args.suite:
            results = runner.run_test_suite(args.suite, **pytest_args)
        elif args.all:
            results = runner.run_comprehensive_tests(list(TEST_SUITES.keys()), **pytest_args)
        else:
            # Default: run core test suites
            results = runner.run_comprehensive_tests(['unit', 'integration'], **pytest_args)
            
        # Exit with appropriate code
        exit_code = 0 if results.get('overall_success', False) else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()