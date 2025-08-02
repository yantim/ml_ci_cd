# Testing and Quality Gates

This document describes the comprehensive testing and quality gates implemented for the ML CI/CD pipeline.

## Overview

Our testing strategy includes:
- **Unit Tests** with ≥80% coverage requirement
- **Integration Tests** for API endpoints
- **Docker Integration Tests** for containerized deployment
- **Static Code Analysis** with multiple tools
- **Security Scanning** for vulnerabilities
- **Automated CI/CD Pipeline** with GitHub Actions

## Test Structure

```
tests/
├── __init__.py
├── test_basic.py              # Basic project structure tests
├── test_data_preparation.py   # Data utilities tests
├── test_mlflow_model.py       # MLflow model wrapper tests
├── test_api.py               # FastAPI endpoint tests
├── test_training.py          # Training pipeline tests
└── test_integration.py       # Integration and Docker tests
```

## Quality Gate Tools

### 1. Code Formatting & Linting
- **Ruff**: Modern Python linter and formatter (replaces flake8, isort, etc.)
- **Black**: Code formatter for consistent style
- **isort**: Import statement organizer

### 2. Type Checking
- **MyPy**: Static type checker with custom configuration

### 3. Security Scanning
- **Bandit**: Security vulnerability scanner for Python code
- **Trivy**: Container and filesystem vulnerability scanner (in CI)

### 4. Test Coverage
- **pytest-cov**: Coverage measurement with ≥80% requirement
- **HTML/XML reports**: Visual coverage reports

## Configuration Files

| File | Purpose |
|------|---------|
| `pytest.ini` | Test configuration, coverage settings, markers |
| `ruff.toml` | Ruff linting and formatting rules |
| `mypy.ini` | Type checking configuration |
| `.bandit` | Security scanning rules |

## Running Tests Locally

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run all quality gates
python run_quality_gates.py

# Or use Make commands
make all-checks
```

### Individual Commands

#### Unit Tests
```bash
# Run unit tests with coverage
make test-unit
# OR
pytest tests/ -v --cov=src --cov-report=html -m "not integration and not docker"
```

#### Integration Tests
```bash
# Run integration tests
make test-integration
# OR
pytest tests/test_integration.py -v -m "integration and not docker"
```

#### Docker Tests
```bash
# Run Docker-based integration tests
make test-docker
# OR
pytest tests/test_integration.py -v -m "docker"
```

#### Code Quality
```bash
# Linting
make lint
ruff check src tests

# Formatting
make format
black src tests
isort src tests

# Type checking
mypy src --config-file mypy.ini

# Security scanning
make security
bandit -r src
```

## Test Categories

### Unit Tests
- **Data Preparation (`test_data_preparation.py`)**
  - `load_dataset()`, `save_dataset()`
  - `tokenize_data()`, `split_data()`
  - `simple_tokenizer()`

- **MLflow Model Wrapper (`test_mlflow_model.py`)**
  - Model loading and context setup
  - Prediction with different input formats
  - Model saving as PyFunc

- **FastAPI Application (`test_api.py`)**
  - Health endpoint testing
  - Prediction endpoint with various scenarios
  - Error handling and validation

- **Training Pipeline (`test_training.py`)**
  - Configuration loading
  - Tokenizer and model initialization
  - PEFT setup (LoRA)
  - Dataset preprocessing

### Integration Tests
- **API Server Integration (`test_integration.py`)**
  - Server startup and health checks
  - End-to-end API testing
  - OpenAPI documentation availability

- **Docker Integration**
  - Container build and startup
  - Health endpoint through Docker
  - API functionality in containerized environment

## CI/CD Pipeline

Our GitHub Actions workflow (`.github/workflows/ci.yml`) includes:

### 1. Quality Gates Job
- Ruff linting and formatting
- Black code formatting check  
- isort import sorting
- MyPy type checking
- Bandit security scanning

### 2. Unit Tests Job
- Tests across Python 3.10 and 3.11
- Coverage reporting with ≥80% requirement
- Upload to Codecov

### 3. Integration Tests Job
- Non-Docker integration tests
- Docker image building
- Docker-based API testing

### 4. Security Scan Job
- Trivy vulnerability scanning
- SARIF report upload to GitHub Security

### 5. Docker Build Job
- Production image building
- Container health testing
- Image artifact storage

## Coverage Targets

We enforce a minimum of **80% test coverage** on the `src/` directory:

```bash
pytest --cov=src --cov-fail-under=80
```

Current coverage areas:
- ✅ Data preparation utilities
- ✅ MLflow model wrapper core functionality
- ✅ FastAPI endpoints and error handling
- ✅ Configuration management
- ⚠️ Training pipeline (complex, partially covered)
- ❌ Deployment scripts (not used in current setup)

## Test Markers

We use pytest markers to categorize tests:

```python
@pytest.mark.integration  # Integration tests
@pytest.mark.docker       # Docker-based tests
@pytest.mark.slow         # Long-running tests
@pytest.mark.asyncio      # Async tests
```

Run specific test categories:
```bash
# Only unit tests
pytest -m "not integration and not docker"

# Only integration tests
pytest -m "integration"

# Skip slow tests
pytest -m "not slow"
```

## Continuous Integration

### Local CI Simulation
```bash
# Run the same checks as CI
make ci-local
```

### GitHub Actions Triggers
- **Pull Requests**: Full test suite on all target branches
- **Push to main/develop**: Full pipeline including optional training tests
- **Manual dispatch**: Available for on-demand runs

### Quality Gate Enforcement
- All quality gates must pass before merge
- Coverage must be ≥80%
- No high-severity security issues
- All linting and formatting checks pass

## Adding New Tests

### Unit Test Template
```python
import pytest
from unittest.mock import Mock, patch
from src.your_module import YourClass

class TestYourClass:
    
    @pytest.fixture
    def mock_instance(self):
        return YourClass()
    
    def test_your_function(self, mock_instance):
        # Arrange
        expected = "expected_result"
        
        # Act
        result = mock_instance.your_function()
        
        # Assert
        assert result == expected
```

### Integration Test Template
```python
@pytest.mark.integration
def test_api_endpoint():
    import requests
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
```

## Troubleshooting

### Common Issues

1. **Coverage too low**
   - Add more unit tests for uncovered functions
   - Mock external dependencies
   - Test error paths and edge cases

2. **Integration tests failing**
   - Check if services are running
   - Verify network connectivity
   - Ensure Docker is available

3. **Linting errors**
   - Run `make format` to auto-fix formatting
   - Check Ruff configuration in `ruff.toml`
   - Update code to follow style guidelines

4. **Type checking issues**
   - Add type hints gradually
   - Configure MyPy exclusions if needed
   - Use `# type: ignore` for complex cases

### Debug Commands
```bash
# Verbose test output
pytest -v -s

# Run specific test
pytest tests/test_api.py::TestAPI::test_root_endpoint -v

# Debug coverage
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Check what files are being tested
pytest --collect-only
```

## Metrics and Reporting

### Coverage Reports
- **Terminal**: Real-time coverage summary
- **HTML**: `htmlcov/index.html` - Interactive coverage report
- **XML**: `coverage.xml` - For CI integration

### Security Reports
- **Bandit**: `bandit-report.json` - Vulnerability findings
- **Trivy**: SARIF format uploaded to GitHub Security tab

### CI Artifacts
- Coverage reports per Python version
- Docker images for deployment
- Security scan results

## Best Practices

1. **Test Pyramid**: More unit tests, fewer integration tests
2. **Mock External Dependencies**: Keep tests fast and reliable
3. **Test Edge Cases**: Error conditions, empty inputs, invalid data
4. **Clear Test Names**: Describe what is being tested
5. **Independent Tests**: No dependencies between test cases
6. **Fast Feedback**: Quality gates should run quickly
7. **Comprehensive Coverage**: Test both happy path and error cases

## Future Improvements

- [ ] Add performance benchmarking tests
- [ ] Implement contract testing for API
- [ ] Add property-based testing with Hypothesis
- [ ] Increase training pipeline test coverage
- [ ] Add end-to-end ML workflow tests
- [ ] Implement test data management
- [ ] Add visual regression testing for plots/outputs
