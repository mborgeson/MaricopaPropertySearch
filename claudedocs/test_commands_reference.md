# Test Commands Reference & Expected Results

## Quick Start Testing Commands

### 1. Essential Test Commands (Copy & Paste Ready)

```bash
# Navigate to project root
cd /c/Users/MattBorgeson/Development/Work/MaricopaPropertySearch/

# Install testing dependencies
pip install pytest pytest-cov pytest-qt pytest-benchmark pytest-html pytest-mock bandit flake8 mypy black

# Run comprehensive test suite
python claudedocs/execute_comprehensive_tests.py --suite all

# Quick development testing (2-3 minutes)
python claudedocs/execute_comprehensive_tests.py --fast

# Critical path validation (5-10 minutes)
python claudedocs/execute_comprehensive_tests.py --critical
```

### 2. Individual Test Suite Commands

```bash
# Unit Tests with Coverage (Target: >90% for critical modules)
pytest tests/unit/ -v --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=80

# Integration Tests (Component interaction validation)
pytest tests/integration/ -v --tb=short -m integration

# Performance Benchmarks (Response time validation)
pytest tests/performance/ -v --benchmark-only --benchmark-sort=mean -m performance

# End-to-End Tests (Complete user workflows)
pytest tests/e2e/ -v --tb=long -m e2e

# GUI Tests (User interface validation)  
pytest tests/ -v -m gui --tb=short

# Security Scan (Vulnerability detection)
bandit -r src/ -f json -o tests/reports/security_report.json

# Code Quality Checks
flake8 src/ --output-file=tests/reports/flake8.txt
mypy src/ --junit-xml=tests/reports/mypy.xml  
black --check src/
```

---

## Expected Test Results & Benchmarks

### 2.1 Unit Test Coverage Targets

| Module | Target Coverage | Critical Functions |
|--------|-----------------|-------------------|
| `RUN_APPLICATION.py` | 95% | dependency_validation, database_connection_check |
| `threadsafe_database_manager.py` | 95% | connection pooling, concurrent operations |
| `api_client.py` | 90% | authentication, retry logic, rate limiting |
| `enhanced_main_window.py` | 90% | GUI initialization, search validation |
| `web_scraper.py` | 85% | driver management, data extraction |

### 2.2 Performance Benchmarks

| Operation | Target (95th %ile) | Command to Verify |
|-----------|-------------------|-------------------|
| Application Startup | <3s | `time python RUN_APPLICATION.py --check-only` |
| Database Search | <2s | `pytest tests/performance/test_database_performance.py -k search` |
| API Response | <10s | `pytest tests/performance/test_api_performance.py -k response` |
| GUI Interaction | <100ms | `pytest tests/unit/test_enhanced_main_window.py -k responsiveness` |

### 2.3 Integration Test Scenarios

```bash
# Search Workflow Integration
pytest tests/integration/test_search_workflow.py::test_end_to_end_property_search_by_owner -v

# Multi-Source Data Consolidation  
pytest tests/integration/test_data_enhancement.py::test_multi_source_consolidation -v

# Error Handling & Recovery
pytest tests/integration/test_error_handling.py::test_network_failure_recovery -v

# Background Processing
pytest tests/integration/test_background_processing.py::test_concurrent_enhancement -v
```

---

## Test Execution Workflows

### 3.1 Development Workflow (Daily)

```bash
# Pre-commit checks (1-2 minutes)
black src/ --check && flake8 src/ && pytest tests/unit/ -x --tb=short

# Development testing (5 minutes)
python claudedocs/execute_comprehensive_tests.py --fast

# Coverage check
pytest tests/unit/ --cov=src --cov-report=term --cov-fail-under=80
```

### 3.2 CI/CD Pipeline Stages

```yaml
# Stage 1: Fast Feedback (2-3 minutes)
jobs:
  - name: "Code Quality"
    command: "flake8 src/ && mypy src/ && black --check src/"
    
  - name: "Unit Tests"  
    command: "pytest tests/unit/ -v --cov=src --cov-fail-under=80"
    
  - name: "Security Scan"
    command: "bandit -r src/ -ll"

# Stage 2: Integration Testing (10 minutes)
jobs:
  - name: "Integration Tests"
    command: "pytest tests/integration/ -v -m integration"
    
  - name: "Performance Benchmarks"
    command: "pytest tests/performance/ -v --benchmark-only"

# Stage 3: End-to-End Validation (30 minutes)  
jobs:
  - name: "E2E Tests"
    command: "pytest tests/e2e/ -v -m e2e"
    
  - name: "Visual Regression"
    command: "pytest tests/e2e/ -v -m visual"
```

### 3.3 Release Validation Workflow

```bash
# Complete test suite with reporting
python claudedocs/execute_comprehensive_tests.py --suite all

# Generate detailed coverage report
pytest tests/ --cov=src --cov-report=html:tests/reports/coverage_html

# Performance regression check
pytest tests/performance/ --benchmark-compare=baseline.json

# User acceptance scenarios
pytest tests/e2e/test_user_acceptance.py -v --tb=long
```

---

## Expected Test Results

### 4.1 Success Criteria

**Unit Tests:**
```
==================== test session starts ====================
collected 45 items

tests/unit/test_run_application.py::test_dependency_validation ✓
tests/unit/test_threadsafe_database_manager.py::test_connection_pool ✓
tests/unit/test_api_client.py::test_authentication ✓
tests/unit/test_enhanced_main_window.py::test_gui_initialization ✓
tests/unit/test_web_scraper.py::test_driver_setup ✓

==================== 45 passed in 120.45s ====================
Coverage: 87% (Target: >80% ✓)
```

**Integration Tests:**
```
==================== test session starts ====================
collected 15 items

tests/integration/test_search_workflow.py::test_complete_search ✓
tests/integration/test_data_enhancement.py::test_multi_source ✓
tests/integration/test_error_handling.py::test_recovery ✓

==================== 15 passed in 300.12s ====================
```

**Performance Benchmarks:**
```
==================== test session starts ====================
Name                           Min      Max     Mean    StdDev
test_database_search_speed   0.1234   0.2456   0.1845   0.0123
test_api_response_time       0.5432   1.2345   0.8765   0.1234
test_gui_interaction_time    0.0012   0.0045   0.0023   0.0005

All benchmarks within acceptable ranges ✓
```

### 4.2 Quality Gate Validation

**Quality Gates Checklist:**
- ✅ Unit Tests: 100% pass rate (45/45)
- ✅ Integration Tests: 95% pass rate (14/15)  
- ✅ Code Coverage: 87% (>80% target)
- ✅ Performance Benchmarks: Within limits
- ✅ Security Scan: No critical vulnerabilities
- ✅ Code Quality: No critical issues

**Release Readiness:** ✅ APPROVED

---

## Troubleshooting Common Issues

### 5.1 Test Environment Setup Issues

**Issue:** `ImportError: No module named 'src.module_name'`
```bash
# Solution: Add src to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
# Or use relative imports in tests
```

**Issue:** `PostgreSQL connection failed`
```bash
# Solution: Start test database
docker run --name postgres-test -e POSTGRES_DB=maricopa_test -e POSTGRES_PASSWORD=test -p 5432:5432 -d postgres:13
```

**Issue:** `ChromeDriver not found`
```bash
# Solution: Install ChromeDriver
# Windows:
choco install chromedriver
# Linux:
sudo apt-get install chromium-chromedriver
```

### 5.2 Performance Test Failures

**Issue:** Tests failing performance benchmarks
```bash
# Check system resources
pytest tests/performance/ -v --benchmark-only --benchmark-autosave
# Compare with baseline
pytest tests/performance/ --benchmark-compare=baseline.json --benchmark-compare-fail=min:5%
```

**Issue:** GUI tests hanging
```bash
# Use virtual display
export QT_QPA_PLATFORM=offscreen
# Or install Xvfb on Linux
sudo apt-get install xvfb
xvfb-run -a pytest tests/ -m gui
```

### 5.3 Coverage Issues

**Issue:** Coverage below target
```bash
# Identify uncovered lines
pytest tests/unit/ --cov=src --cov-report=html
# Open tests/reports/coverage_html/index.html to see detailed coverage

# Focus on critical modules first
pytest tests/unit/test_database_manager.py --cov=src.threadsafe_database_manager --cov-report=term-missing
```

---

## Continuous Monitoring Commands

### 6.1 Daily Health Checks

```bash
# Quick smoke test (1 minute)
pytest tests/unit/ -m smoke --tb=no -q

# Performance trend monitoring
pytest tests/performance/ --benchmark-only --benchmark-json=daily_benchmark.json

# Coverage trend tracking
pytest tests/unit/ --cov=src --cov-report=json:daily_coverage.json
```

### 6.2 Weekly Full Validation

```bash
# Complete test suite with reporting
python claudedocs/execute_comprehensive_tests.py --suite all

# Generate trend analysis
python tests/analyze_test_trends.py --period=weekly

# Update performance baselines if needed
pytest tests/performance/ --benchmark-only --benchmark-save=weekly_baseline
```

### 6.3 Release Preparation

```bash
# Pre-release validation
python claudedocs/execute_comprehensive_tests.py --suite all

# Generate release report
python tests/generate_release_report.py --version=1.2.0

# Validate all quality gates
python tests/validate_quality_gates.py --strict
```

---

## Integration with Development Tools

### 7.1 VS Code Integration

**`.vscode/tasks.json`:**
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run Fast Tests",
            "type": "shell", 
            "command": "python",
            "args": ["claudedocs/execute_comprehensive_tests.py", "--fast"],
            "group": "test"
        },
        {
            "label": "Run Unit Tests",
            "type": "shell",
            "command": "pytest", 
            "args": ["tests/unit/", "-v"],
            "group": "test"
        }
    ]
}
```

### 7.2 Git Hooks Integration

**`.git/hooks/pre-commit`:**
```bash
#!/bin/bash
# Pre-commit testing
python claudedocs/execute_comprehensive_tests.py --fast
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

### 7.3 GitHub Actions Integration

**`.github/workflows/test.yml`:**
```yaml
name: Comprehensive Testing
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-testing.txt
      - name: Run comprehensive tests
        run: python claudedocs/execute_comprehensive_tests.py --critical
```

---

## Summary

This test command reference provides:

1. **Copy-paste ready commands** for immediate test execution
2. **Clear performance benchmarks** with specific targets
3. **Expected results examples** for validation
4. **Troubleshooting guides** for common issues
5. **Integration examples** with development tools

**Key Success Metrics:**
- Unit test coverage >80% overall, >90% for critical modules
- All performance benchmarks within acceptable ranges  
- Zero critical security vulnerabilities
- 100% unit test pass rate
- <5% integration test failure rate

Use these commands and benchmarks to ensure the consolidated Maricopa Property Search application maintains high quality and reliability standards.