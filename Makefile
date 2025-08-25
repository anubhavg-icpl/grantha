# Grantha Project Makefile
# Provides convenient commands for testing, development, and deployment

.PHONY: help install test test-unit test-integration test-e2e test-performance test-all
.PHONY: coverage lint format type-check security-scan clean setup-dev
.PHONY: docker-build docker-test run-local deploy-local

# Default target
help:
	@echo "Grantha Project - Available Commands:"
	@echo ""
	@echo "Setup Commands:"
	@echo "  install        Install project dependencies"
	@echo "  setup-dev      Setup development environment"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test           Run all tests with coverage"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-e2e       Run end-to-end tests only"
	@echo "  test-performance Run performance tests only"
	@echo "  test-fast      Run fast tests (exclude slow/network tests)"
	@echo ""
	@echo "Quality Commands:"
	@echo "  coverage       Generate coverage report"
	@echo "  lint           Run code linting"
	@echo "  format         Format code with black and isort"
	@echo "  type-check     Run type checking with mypy"
	@echo "  security-scan  Run security scans"
	@echo ""
	@echo "Development Commands:"
	@echo "  run-local      Run the API locally"
	@echo "  clean          Clean build artifacts and cache"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build   Build Docker image"
	@echo "  docker-test    Run tests in Docker container"
	@echo ""

# Installation and Setup
install:
	@echo "Installing Grantha dependencies..."
	pip install -e .[dev,test]

setup-dev: install
	@echo "Setting up development environment..."
	pre-commit install
	@echo "Development environment setup complete!"

# Testing Commands
test: test-unit test-integration

test-unit:
	@echo "Running unit tests..."
	python -m pytest tests/unit -v --cov=api --cov-report=term-missing

test-integration:
	@echo "Running integration tests..."
	python -m pytest tests/integration -v

test-e2e:
	@echo "Running end-to-end tests..."
	python -m pytest tests/e2e -v --timeout=300

test-performance:
	@echo "Running performance tests..."
	python -m pytest tests/performance -v -m performance

test-all:
	@echo "Running all tests..."
	python scripts/run_tests.py --type all --coverage

test-fast:
	@echo "Running fast tests..."
	python -m pytest tests/ -v -m "not slow and not network" --cov=api

# Coverage
coverage:
	@echo "Generating coverage report..."
	python -m pytest tests/unit tests/integration --cov=api --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

# Code Quality
lint:
	@echo "Running code linting..."
	flake8 api tests --max-line-length=100
	@echo "Linting complete!"

format:
	@echo "Formatting code..."
	black api tests --line-length=100
	isort api tests --profile=black
	@echo "Code formatting complete!"

type-check:
	@echo "Running type checks..."
	mypy api --ignore-missing-imports
	@echo "Type checking complete!"

security-scan:
	@echo "Running security scans..."
	bandit -r api -f json -o bandit-report.json || true
	safety check --json --output safety-report.json || true
	@echo "Security scan complete! Check bandit-report.json and safety-report.json"

# Development
run-local:
	@echo "Starting Grantha API locally..."
	python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/
	rm -f coverage.xml pytest-report.html test-results.xml
	@echo "Clean complete!"

# Docker Commands
docker-build:
	@echo "Building Docker image..."
	docker build -t grantha-api:latest .

docker-test: docker-build
	@echo "Running tests in Docker container..."
	docker run --rm -v $(PWD):/app grantha-api:latest python -m pytest tests/ -v

# Pre-commit hooks
pre-commit-all:
	@echo "Running all pre-commit hooks..."
	pre-commit run --all-files

# Database operations (if needed)
db-reset:
	@echo "Resetting test database..."
	# Add database reset commands here if needed

# Continuous Integration helpers
ci-setup:
	pip install -e .[dev,test]

ci-test:
	python -m pytest tests/ -v --cov=api --cov-report=xml --cov-report=term-missing --junit-xml=test-results.xml

ci-security:
	bandit -r api -f json -o bandit-report.json
	safety check --json --output safety-report.json

# Documentation (if needed)
docs-build:
	@echo "Building documentation..."
	# Add documentation build commands here

docs-serve:
	@echo "Serving documentation locally..."
	# Add documentation serve commands here

# Environment setup for different stages
env-test:
	@echo "Setting up test environment variables..."
	export TESTING=1
	export GOOGLE_API_KEY=test_key
	export OPENAI_API_KEY=test_key

env-dev:
	@echo "Setting up development environment variables..."
	@echo "Make sure to set up your .env file with real API keys"

# Performance testing with specific metrics
perf-load:
	@echo "Running load performance tests..."
	python -m pytest tests/performance/test_load_performance.py -v

perf-memory:
	@echo "Running memory performance tests..."
	python -m pytest tests/performance/ -v -k memory

# Debugging helpers
debug-test:
	@echo "Running tests with debugging..."
	python -m pytest tests/ -v -s --pdb

debug-coverage:
	@echo "Running coverage with debugging..."
	python -m pytest tests/ --cov=api --cov-report=html --pdb-trace

# Release helpers
version-check:
	@echo "Current version:"
	@python -c "import toml; print(toml.load('pyproject.toml')['project']['version'])"

# Health check
health-check:
	@echo "Running health checks..."
	python -c "import requests; print('API Health:', requests.get('http://localhost:8000/health').json())" || echo "API not running"

# Quick development workflow
dev: format lint test-fast
	@echo "Development workflow complete!"

# Full CI/CD workflow simulation
ci: ci-setup format lint type-check ci-test ci-security
	@echo "CI workflow complete!"
