# Contributing to Maricopa Property Search

Welcome to the Maricopa Property Search project! This guide provides essential information for developers contributing to the project.

## 🚨 **CRITICAL: GitHub CI/CD Requirements**

**Before pushing any code to GitHub, ALL changes must pass automated quality gates.**

### Required Code Formatting

The project uses **strict code formatting** enforced by GitHub Actions CI/CD pipeline:

#### Black Code Formatter (REQUIRED)
- **All Python files must be formatted with Black**
- **GitHub Actions will FAIL if any file is not Black-formatted**
- **Error message**: "Code Formatting Check: Black" with exit code 123

**Install Black in virtual environment:**
```bash
# Create virtual environment if not exists
python3 -m venv venv
source venv/bin/activate

# Install Black formatter
pip install black

# Format all source files
python -m black src/
```

#### Other Quality Tools (ENFORCED)
- **isort**: Import sorting and organization
- **Flake8**: Code linting and style checking
- **Pylint**: Advanced code analysis
- **mypy**: Type checking
- **Bandit**: Security vulnerability scanning

### Quick Setup for New Contributors

```bash
# 1. Clone and setup
git clone <repository-url>
cd MaricopaPropertySearch

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies + development tools
pip install -r requirements.txt
pip install black isort flake8 pylint mypy bandit

# 4. Install pre-commit hooks (RECOMMENDED)
pip install pre-commit
pre-commit install

# 5. Format code before any commit
python -m black src/
python -m isort src/
```

### Pre-Commit Hooks (STRONGLY RECOMMENDED)

The project includes pre-commit hooks that automatically run quality checks:

**Install and activate:**
```bash
pip install pre-commit
pre-commit install
```

**Pre-commit hooks will automatically:**
- Format code with Black
- Sort imports with isort
- Run Flake8 linting
- Check for security issues with Bandit
- Validate type hints with mypy

## GitHub Actions CI/CD Pipeline

### 9-Stage Quality Pipeline

Every push to GitHub triggers a comprehensive quality pipeline:

1. **Code Formatting Check (Black)** ⚠️ **WILL FAIL IF NOT FORMATTED**
2. **Import Organization (isort)**
3. **Code Linting (Flake8, Pylint)**
4. **Type Checking (mypy)**
5. **Security Scanning (Bandit, Safety)**
6. **Unit Tests by Component** (80%+ coverage required)
7. **Integration Tests**
8. **Performance Benchmarks**
9. **System Workflow Validation**

### Pipeline Status Indicators

✅ **All checks pass**: Your code is ready for review
❌ **Any check fails**: Fix issues before review
⚠️ **Most common failure**: Black formatting (exit code 123)

## Development Workflow

### 1. Before Making Changes

```bash
# Ensure your environment is ready
source venv/bin/activate
python -m black --check src/  # Check if formatting needed
```

### 2. Making Changes

- Follow existing code patterns and unified architecture
- Maintain 80%+ test coverage for new code
- Add type hints to all functions
- Write descriptive commit messages

### 3. Before Committing

```bash
# Format all code (REQUIRED)
python -m black src/

# Check imports
python -m isort src/

# Run basic tests
pytest tests/

# Check types
mypy src/
```

### 4. Commit and Push

```bash
git add .
git commit -m "Your descriptive commit message"
git push origin your-branch
```

**GitHub Actions will automatically run all quality checks.**

## Code Quality Standards

### Test Coverage Requirements
- **Minimum**: 80% coverage for all components
- **Target**: 90% coverage for new features
- **Critical Components**: 95% coverage required

### Code Style Requirements
- **Black formatting**: 100% compliance (enforced)
- **Type hints**: Required for all public functions
- **Docstrings**: Required for all public APIs
- **Import organization**: Alphabetical with isort

### Security Requirements
- **Bandit scanning**: Zero high-severity issues
- **Safety checks**: No known vulnerabilities in dependencies
- **Secret scanning**: No hardcoded secrets or keys

## Architecture Guidelines

### Unified Component Design
The project uses a unified architecture (75% file reduction achieved in Phase 2):

- **UnifiedMaricopaAPIClient**: Single API client with progressive loading
- **UnifiedDataCollector**: Background processing with priority queues
- **ThreadSafeDatabaseManager**: Unified database operations
- **UnifiedGUILauncher**: Cross-platform GUI with intelligent detection

### Integration Patterns
- **Follow existing patterns**: Study existing components before adding new ones
- **Preserve backward compatibility**: Maintain API compatibility
- **Progressive enhancement**: Build on existing unified architecture
- **Cross-platform support**: Ensure WSL/Linux/Windows compatibility

## Testing Requirements

### Unit Tests (REQUIRED)
- **Location**: `tests/unit/`
- **Coverage**: 80%+ minimum
- **Naming**: `test_<component>_<functionality>.py`
- **Framework**: pytest with custom fixtures

### Integration Tests
- **Location**: `tests/integration/`
- **Focus**: Component interactions and workflows
- **Database**: Test with mock, SQLite, and PostgreSQL modes

### Performance Tests
- **Location**: `tests/performance/`
- **Benchmarks**: Validate against established baselines
- **Targets**: 0.04s basic search, 0.33s comprehensive search

## Troubleshooting Common Issues

### GitHub Actions Failures

**Black Formatting Error (Exit Code 123)**
```bash
# Fix with:
source venv/bin/activate
python -m black src/
git add .
git commit -m "Fix Black formatting"
git push
```

**Import Organization Issues**
```bash
# Fix with:
python -m isort src/
```

**Test Coverage Below 80%**
```bash
# Check coverage:
pytest --cov=src --cov-report=term
# Add tests for uncovered code
```

**Type Checking Failures**
```bash
# Check types:
mypy src/
# Add missing type hints
```

## Getting Help

### Documentation Resources
1. **README.md**: Project overview and setup instructions
2. **CLAUDE.md**: Developer guide with architecture details
3. **TROUBLESHOOTING_GUIDE.md**: Common issues and solutions
4. **UNIFIED_INTERFACES.md**: Complete API documentation
5. **Phase Completion Memorials**: Detailed technical achievements

### Quality Infrastructure
- **CI/CD Pipeline**: `.github/workflows/ci-cd.yml`
- **Pre-commit Configuration**: `.pre-commit-config.yaml`
- **Test Configuration**: `pytest.ini`
- **Test Fixtures**: `tests/conftest.py`

### Quick Commands Reference

```bash
# Essential formatting (run before every commit)
python -m black src/

# Full quality check
python -m black src/ && python -m isort src/ && pytest --cov=src

# Pre-commit hook test
pre-commit run --all-files

# Test specific component
pytest tests/unit/test_api_client_unified.py -v
```

## Project Phases and Status

- ✅ **Phase 1**: Windows → Linux path migration (COMPLETE)
- ✅ **Phase 2**: Component consolidation - 75% file reduction (COMPLETE)
- ✅ **Phase 3**: WSL GUI configuration with native Wayland (COMPLETE)
- ✅ **Phase 4**: Documentation updates and unified interfaces (COMPLETE)
- ✅ **Phase 5**: Quality infrastructure with CI/CD pipeline (COMPLETE)
- 🔄 **Phase 6**: Advanced features with Playwright integration (IN PROGRESS)

---

## ⚠️ **IMPORTANT REMINDERS**

1. **Always run Black formatter before committing**
2. **GitHub Actions WILL FAIL without proper formatting**
3. **Use pre-commit hooks to catch issues early**
4. **Maintain 80%+ test coverage for all new code**
5. **Follow unified architecture patterns**

**The CI/CD pipeline protects code quality - embrace it as a development tool!**