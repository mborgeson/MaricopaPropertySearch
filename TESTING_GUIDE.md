# Testing Guide for MaricopaPropertySearch

## Overview

This guide provides comprehensive testing documentation for the MaricopaPropertySearch application following Phase 5 quality infrastructure implementation. The testing framework supports the unified architecture that achieved 75% file reduction through component consolidation.

## Table of Contents

- [Testing Strategy](#testing-strategy)
- [Framework Setup](#framework-setup)
- [Test Categories](#test-categories)
- [Running Tests](#running-tests)
- [Continuous Integration](#continuous-integration)
- [Performance Testing](#performance-testing)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Testing Strategy

### Component Coverage

The testing framework covers all 4 unified components:

1. **UnifiedMaricopaAPIClient** (`src/api_client_unified.py`)
   - Consolidates 6 previous API client implementations
   - Target coverage: 85% (critical path component)

2. **UnifiedDataCollector** (`src/unified_data_collector.py`)
   - Consolidates 4 data collection implementations
   - Target coverage: 80% (complex async operations)

3. **ThreadSafeDatabaseManager** (`src/threadsafe_database_manager.py`)
   - Consolidated database operations
   - Target coverage: 90% (data integrity critical)

4. **UnifiedGUILauncher** (`src/gui_launcher_unified.py`)
   - Consolidates 4 GUI launcher implementations
   - Target coverage: 75% (platform-dependent behavior)

### Testing Pyramid

```
    E2E Tests (5%)
   ┌─────────────────┐
  Integration Tests (15%)
 ┌─────────────────────┐
Unit Tests (80%)
```

## Framework Setup

### Prerequisites

```bash
# Install Python 3.12+
python --version  # Should be 3.12+

# Install testing dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-qt pytest-asyncio pytest-mock pytest-benchmark
```

### Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd MaricopaPropertySearch

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e .
```

### Configuration

The testing framework uses several configuration files:

- `pytest.ini` - Main pytest configuration
- `conftest.py` - Shared fixtures and configuration
- `.coveragerc` - Coverage reporting configuration
- `tests/__init__.py` - Test package configuration

## Test Categories

### 1. Unit Tests (`tests/unit/`)

Test individual components in isolation:

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific component tests
pytest tests/unit/test_api_client_unified.py -v
pytest tests/unit/test_unified_data_collector.py -v
pytest tests/unit/test_threadsafe_database_manager.py -v
pytest tests/unit/test_gui_launcher_unified.py -v
```

**Key Features:**
- Comprehensive mocking of dependencies
- Isolated component testing
- Performance assertions
- Error handling validation

### 2. Integration Tests (`tests/integration/`)

Test component interactions and data flow:

```bash
# Run integration tests
pytest tests/integration/ -v

# Run with database integration
pytest tests/integration/ -v --db-integration
```

**Key Features:**
- Component interaction testing
- End-to-end data flow validation
- Concurrent access testing
- Error propagation testing

### 3. Performance Tests (`tests/performance/`)

Benchmark performance and detect regressions:

```bash
# Run performance benchmarks
pytest tests/performance/ -v --benchmark-only

# Generate benchmark report
pytest tests/performance/ --benchmark-json=benchmark-results.json

# Compare with baseline
python scripts/check_performance_regression.py benchmark-results.json
```

**Performance Targets:**
- API response time: <0.1s
- Database query time: <0.05s
- GUI startup time: <2.0s
- Memory usage: <100MB

### 4. System Tests (`tests/system/`)

End-to-end workflow validation:

```bash
# Run system tests
pytest tests/system/ -v

# Run Missouri Avenue validation
pytest tests/system/ -v -m missouri_ave
```

## Running Tests

### Local Development

```bash
# Quick test run (unit tests only)
pytest tests/unit/ -x

# Full test suite
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific markers
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m performance    # Performance tests only
pytest -m slow          # Long-running tests
pytest -m missouri_ave  # Missouri Avenue validation
```

### Test Execution Strategies

#### Fast Feedback Loop
```bash
# Quick unit tests for active development
pytest tests/unit/ -x --ff
```

#### Comprehensive Testing
```bash
# Full test suite with coverage
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

#### Performance Monitoring
```bash
# Run benchmarks and check regression
pytest tests/performance/ --benchmark-only --benchmark-compare
```

## Continuous Integration

### GitHub Actions Pipeline

The CI/CD pipeline includes multiple quality gates:

1. **Code Quality Gate**
   - Black formatting
   - isort import sorting
   - flake8 style checking
   - mypy type checking
   - pylint code analysis

2. **Security Gate**
   - bandit security scanning
   - safety dependency scanning

3. **Unit Tests Gate**
   - Parallel execution by component
   - Coverage validation (80% threshold)

4. **Integration Tests Gate**
   - Component interaction testing
   - Database integration testing

5. **Performance Gate**
   - Benchmark execution
   - Regression detection

6. **System Tests Gate**
   - End-to-end workflow validation
   - Missouri Avenue workflow testing

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

## Performance Testing

### Benchmarking Framework

The performance testing framework uses `pytest-benchmark` for accurate measurements:

```python
def test_api_response_benchmark(benchmark):
    result = benchmark(api_client.search_property, "10215009")
    assert result['success'] is True
```

### Memory Profiling

```bash
# Run with memory profiling
python -m memory_profiler tests/performance/test_memory_usage.py

# Generate memory report
pytest tests/performance/ --memray
```

### Performance Baselines

Current performance baselines (targets):
- Basic search: <0.1s (current: 0.04s)
- Detailed search: <0.5s (current: 0.33s)
- Background collection: <2.0s per property
- Memory usage: <100MB during normal operations
- GUI startup: <2.0s

## Best Practices

### Writing Tests

1. **Use descriptive test names**
   ```python
   def test_api_client_handles_rate_limiting_gracefully():
   ```

2. **Follow AAA pattern**
   ```python
   def test_data_collection_success():
       # Arrange
       collector = UnifiedDataCollector(mock_api_client)

       # Act
       result = collector.collect_property_data("10215009")

       # Assert
       assert result['success'] is True
   ```

3. **Use appropriate fixtures**
   ```python
   def test_database_operations(mock_database_manager, mock_property_data):
   ```

4. **Test edge cases and error conditions**
   ```python
   def test_api_client_handles_timeout_errors():
   ```

### Test Organization

```
tests/
├── __init__.py
├── conftest.py
├── unit/
│   ├── test_api_client_unified.py
│   ├── test_unified_data_collector.py
│   ├── test_threadsafe_database_manager.py
│   └── test_gui_launcher_unified.py
├── integration/
│   └── test_component_integration.py
├── performance/
│   └── test_performance_benchmarks.py
└── system/
    └── test_missouri_ave_workflow.py
```

### Mocking Guidelines

1. **Mock external dependencies**
   ```python
   @patch('requests.Session.get')
   def test_api_call(mock_get):
   ```

2. **Use appropriate mock types**
   ```python
   # For async operations
   mock_client.search_property_async = AsyncMock()

   # For callable objects
   mock_callback = Mock(return_value=True)
   ```

3. **Verify mock interactions**
   ```python
   mock_get.assert_called_once_with(expected_url)
   ```

## Test Data Management

### Mock Data

The framework provides comprehensive mock data for testing:

- `mock_property_data` - Realistic property information
- `mock_tax_history` - Multi-year tax records
- `mock_api_responses` - Various API response scenarios
- `sample_database_records` - Database test data

### Test Environments

1. **Development**: SQLite, mock APIs, local testing
2. **Integration**: PostgreSQL, limited real APIs
3. **Production**: Live APIs (rate-limited), full database

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Ensure PYTHONPATH includes src directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or use pytest discovery
pytest --import-mode=importlib
```

#### 2. GUI Testing on Headless Systems
```bash
# Use Xvfb for headless GUI testing
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
export DISPLAY=:99
pytest tests/unit/test_gui_launcher_unified.py
```

#### 3. Database Connection Issues
```bash
# Check PostgreSQL service
systemctl status postgresql

# Verify connection
psql -h localhost -U test_user -d test_db -c "SELECT 1;"
```

#### 4. Performance Test Variations
```bash
# Run with more iterations for stable results
pytest tests/performance/ --benchmark-min-rounds=10
```

### Debug Modes

```bash
# Verbose output
pytest -v -s

# Debug on failure
pytest --pdb

# Capture logs
pytest --log-cli-level=DEBUG
```

## Coverage Analysis

### Generating Reports

```bash
# HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Terminal coverage report
pytest --cov=src --cov-report=term-missing

# XML coverage report (for CI)
pytest --cov=src --cov-report=xml
```

### Coverage Targets

- **Overall**: ≥80%
- **Critical paths**: ≥90%
- **API Client**: ≥85%
- **Database Manager**: ≥90%
- **Data Collector**: ≥80%
- **GUI Launcher**: ≥75%

## Integration with Development Workflow

### Local Development

1. **Before committing**
   ```bash
   # Run quick tests
   pytest tests/unit/ -x

   # Check formatting
   black --check src/ tests/

   # Run pre-commit hooks
   pre-commit run
   ```

2. **Before pushing**
   ```bash
   # Full test suite
   pytest --cov=src --cov-fail-under=80
   ```

3. **Performance monitoring**
   ```bash
   # Weekly performance check
   pytest tests/performance/ --benchmark-compare
   ```

### Code Review Process

1. **Required checks**
   - All tests pass
   - Coverage maintained or improved
   - No security vulnerabilities
   - Performance benchmarks met

2. **Review checklist**
   - [ ] Tests added for new functionality
   - [ ] Tests updated for modified functionality
   - [ ] Edge cases covered
   - [ ] Performance impact assessed
   - [ ] Documentation updated

## Maintenance

### Regular Tasks

1. **Weekly**
   - Update dependencies
   - Run full test suite
   - Check performance trends

2. **Monthly**
   - Review test coverage
   - Update performance baselines
   - Clean up obsolete tests

3. **Quarterly**
   - Framework upgrade planning
   - Test strategy review
   - Performance optimization

### Test Maintenance

1. **Remove obsolete tests**
   ```bash
   # Find unused test files
   python scripts/find_obsolete_tests.py
   ```

2. **Update test data**
   ```bash
   # Refresh mock data
   python scripts/update_test_data.py
   ```

3. **Performance baseline updates**
   ```bash
   # Update baselines after optimization
   python scripts/update_performance_baselines.py
   ```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [PyQt Testing Guide](https://pytest-qt.readthedocs.io/)
- [Pre-commit Hooks](https://pre-commit.com/)

## Support

For testing-related questions or issues:

1. Check this documentation
2. Review existing test examples
3. Consult the troubleshooting section
4. Create an issue in the project repository

---

**Note**: This testing framework is designed to protect the 75% consolidation gains achieved in Phase 2 and ensure reliable operation of the unified architecture.