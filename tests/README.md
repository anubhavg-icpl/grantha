# Grantha Testing Suite

This directory contains the comprehensive testing suite for the Grantha project, covering unit tests, integration tests, end-to-end tests, and performance tests.

## Directory Structure

```
tests/
├── README.md                    # This file
├── conftest.py                  # Basic pytest configuration and fixtures
├── conftest_full.py            # Full pytest configuration (for integration/e2e tests)
├── test_config.yaml            # Test configuration parameters
├── utils.py                    # Test utilities and helper functions
├── fixtures/
│   └── sample_responses.json   # Sample API responses for mocking
├── unit/                       # Unit tests
│   ├── test_basic_functionality.py
│   ├── test_config.py
│   ├── test_openai_client.py
│   └── test_wiki_generator.py
├── integration/                # Integration tests
│   ├── test_api_endpoints.py
│   └── test_websocket.py
├── e2e/                        # End-to-end tests
│   └── test_wiki_workflow.py
└── performance/                # Performance tests
    └── test_load_performance.py
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual functions and classes in isolation
- **Scope**: Single functions, methods, or classes
- **Dependencies**: Mocked external dependencies
- **Speed**: Fast (<5 seconds per test)
- **Run with**: `pytest tests/unit/`

### Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions and API endpoints
- **Scope**: Multiple components working together
- **Dependencies**: May use real database/services but mocked external APIs
- **Speed**: Medium (5-30 seconds per test)
- **Run with**: `pytest tests/integration/`

### End-to-End Tests (`tests/e2e/`)
- **Purpose**: Test complete user workflows and scenarios
- **Scope**: Full application workflows
- **Dependencies**: Full application stack
- **Speed**: Slow (30-300 seconds per test)
- **Run with**: `pytest tests/e2e/`

### Performance Tests (`tests/performance/`)
- **Purpose**: Test application performance and scalability
- **Scope**: Response times, memory usage, concurrent requests
- **Dependencies**: Full application stack
- **Speed**: Variable (30-300 seconds per test)
- **Run with**: `pytest tests/performance/`

## Test Markers

Use pytest markers to categorize and filter tests:

```bash
# Run only unit tests
pytest -m unit

# Run fast tests (exclude slow tests)
pytest -m "not slow"

# Run tests that don't require network
pytest -m "not network"

# Run performance tests
pytest -m performance

# Run integration tests but exclude slow ones
pytest -m "integration and not slow"
```

Available markers:
- `unit`: Unit tests that don't require external dependencies
- `integration`: Integration tests that test component interactions
- `e2e`: End-to-end tests that test complete workflows
- `slow`: Tests that take more than a few seconds to run
- `network`: Tests that require network access
- `performance`: Performance and load tests
- `requires_api_key`: Tests that require real API keys

## Running Tests

### Quick Start

```bash
# Run all fast tests
make test-fast

# Run unit tests only
make test-unit

# Run with coverage
make coverage

# Run all tests
make test-all
```

### Using pytest directly

```bash
# Basic test run
pytest

# Verbose output
pytest -v

# Run with coverage
pytest --cov=api

# Run specific test file
pytest tests/unit/test_config.py

# Run specific test method
pytest tests/unit/test_config.py::TestConfigModule::test_replace_env_placeholders

# Run tests in parallel
pytest -n auto

# Stop on first failure
pytest -x
```

### Using the test runner script

```bash
# Run all tests with coverage
python scripts/run_tests.py --type all --coverage

# Run only unit tests
python scripts/run_tests.py --type unit

# Run with parallel execution
python scripts/run_tests.py --parallel

# Include slow tests
python scripts/run_tests.py --slow
```

## Test Configuration

### Environment Variables

Tests use the following environment variables:

```bash
TESTING=1                    # Indicates test environment
GOOGLE_API_KEY=test_key     # Mock Google API key
OPENAI_API_KEY=test_key     # Mock OpenAI API key
OPENROUTER_API_KEY=test_key # Mock OpenRouter API key
```

### Configuration Files

- `pytest.ini`: Main pytest configuration
- `tests/test_config.yaml`: Test-specific configuration parameters
- `tests/conftest.py`: Basic fixtures and test setup
- `tests/conftest_full.py`: Full application fixtures (for integration tests)

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
class TestMyModule:
    def test_basic_functionality(self):
        # Test implementation
        result = my_function("input")
        assert result == "expected_output"
    
    @patch('my_module.external_api')
    def test_with_mocking(self, mock_api):
        mock_api.return_value = "mocked_response"
        result = my_function_with_api_call()
        assert result == "expected_result"
```

### Integration Test Example

```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.integration
class TestAPIEndpoints:
    def test_endpoint(self, client):
        response = client.get("/api/endpoint")
        assert response.status_code == 200
        assert "expected_field" in response.json()
```

### End-to-End Test Example

```python
import pytest

@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteWorkflow:
    def test_wiki_generation_workflow(self, client):
        # Test complete user workflow
        response = client.post("/api/wiki/generate", json=request_data)
        assert response.status_code == 200
        # Additional workflow steps...
```

## Fixtures

Common fixtures available in tests:

- `mock_env_vars`: Mock environment variables
- `temp_repo_dir`: Temporary directory for file operations
- `sample_wiki_data`: Sample wiki data for testing
- `test_client`: FastAPI test client (integration tests)

### Using Fixtures

```python
def test_with_fixtures(temp_repo_dir, sample_wiki_data):
    # temp_repo_dir is a temporary directory path
    # sample_wiki_data is a dictionary with test data
    pass
```

## Mocking Guidelines

### External APIs
Always mock external API calls in unit and integration tests:

```python
@patch('api.openai_client.OpenAI')
def test_openai_integration(self, mock_openai):
    mock_openai.return_value.chat.completions.create.return_value = mock_response
    # Test implementation
```

### File System Operations
Mock file system operations in unit tests:

```python
@patch('builtins.open', new_callable=mock_open, read_data='test data')
@patch('os.path.exists', return_value=True)
def test_file_operations(self, mock_exists, mock_file):
    # Test implementation
```

## Coverage Requirements

- **Minimum line coverage**: 80%
- **Minimum branch coverage**: 70%
- **Coverage reports**: Generated in HTML, XML, and terminal formats

### Viewing Coverage

```bash
# Generate and view HTML coverage report
make coverage
open htmlcov/index.html
```

## Performance Testing

Performance tests measure:

- **Response times**: API endpoint response times
- **Memory usage**: Memory consumption during operations
- **Concurrency**: Behavior under concurrent requests
- **Throughput**: Requests per second capacity

### Performance Thresholds

- Health endpoint: <100ms
- Configuration endpoints: <500ms
- Wiki generation: <2s (mocked)
- Cache operations: <1s

## Continuous Integration

Tests run automatically on:

- **Push to main/master**: Full test suite
- **Pull requests**: Unit and integration tests
- **Nightly builds**: Full test suite including performance tests

### CI Configuration

- **GitHub Actions**: `.github/workflows/ci.yml`
- **Test matrix**: Python 3.12, 3.13
- **Coverage reporting**: Codecov integration
- **Security scanning**: Bandit and Safety

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed (`pip install -e .[dev,test]`)
2. **Missing Environment Variables**: Check that test environment variables are set
3. **Slow Tests**: Use markers to exclude slow tests (`pytest -m "not slow"`)
4. **Mock Issues**: Ensure mocks are properly configured and match the actual API

### Debug Mode

```bash
# Run tests with debugging
pytest --pdb

# Run with maximum verbosity
pytest -vv --tb=long

# Run specific failing test
pytest tests/path/to/test.py::test_name -vv
```

## Contributing

When adding new tests:

1. **Choose the right category**: Unit, integration, e2e, or performance
2. **Use appropriate markers**: Mark tests with relevant pytest markers
3. **Mock external dependencies**: Don't make real API calls in tests
4. **Follow naming conventions**: Test files should start with `test_`
5. **Add docstrings**: Describe what each test verifies
6. **Maintain coverage**: Ensure new code has adequate test coverage

## Best Practices

1. **Keep tests independent**: Each test should be able to run in isolation
2. **Use descriptive names**: Test names should clearly describe what they test
3. **Test edge cases**: Include tests for error conditions and boundary cases
4. **Keep tests simple**: Each test should verify one specific behavior
5. **Use fixtures wisely**: Reuse setup code through fixtures
6. **Mock external dependencies**: Don't rely on external services in tests
7. **Maintain test data**: Keep test data in fixtures and separate files