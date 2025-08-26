# Grantha Authentication Test Suite

This comprehensive test suite ensures the security, reliability, and performance of the Grantha authentication system. The tests cover both backend and frontend components with comprehensive scenarios for critical authentication flows.

## 🏗️ Test Architecture

```
tests/auth/
├── conftest.py                    # Test configuration and fixtures
├── unit/                         # Unit tests for individual components
│   ├── test_models.py           # Database model tests
│   ├── test_services.py         # Service layer tests  
│   └── test_jwt_service.py      # JWT service tests
├── integration/                 # Integration tests
│   ├── test_api_endpoints.py    # API endpoint tests
│   └── test_end_to_end_flows.py # Complete authentication flows
├── security/                    # Security-focused tests
│   └── test_security_features.py # Security validation tests
├── frontend/                    # Frontend component tests
│   ├── test_auth_store.py       # Authentication store tests
│   └── test_components.py       # UI component tests
├── performance/                 # Performance tests
│   └── test_performance.py      # Load and scalability tests
└── README.md                    # This file
```

## 🧪 Test Categories

### Unit Tests (`unit/`)

**Database Models (`test_models.py`)**
- User model password hashing and verification
- Account lockout mechanisms
- Token generation and validation
- Email verification workflows
- Password reset functionality
- Model relationships and data integrity

**Service Layer (`test_services.py`)**
- User creation, authentication, and management
- Refresh token lifecycle management
- Authentication event logging
- Database transaction handling
- Error recovery mechanisms

**JWT Service (`test_jwt_service.py`)**
- Token generation and validation
- Refresh token rotation
- Token expiration handling
- Security features (algorithm validation, secret key management)
- Legacy compatibility

### Integration Tests (`integration/`)

**API Endpoints (`test_api_endpoints.py`)**
- User registration and validation
- Login/logout flows
- Token refresh mechanisms
- Profile management
- Session management
- Error handling and edge cases

**End-to-End Flows (`test_end_to_end_flows.py`)**
- Complete user lifecycle (register → login → profile update → logout)
- Multi-session management
- Account security workflows
- Password change flows
- Concurrent authentication scenarios

### Security Tests (`security/`)

**Security Features (`test_security_features.py`)**
- Password security (hashing, complexity, timing attacks)
- JWT security (algorithm validation, token structure)
- Account lockout and brute force protection
- Session security and hijacking prevention
- Input validation and injection prevention
- Audit trail integrity

### Frontend Tests (`frontend/`)

**Authentication Store (`test_auth_store.py`)**
- State management and persistence
- Token storage and retrieval
- Authentication actions (login, logout, register)
- Profile management functions
- Session management
- Error handling and recovery

**UI Components (`test_components.py`)**
- Registration form validation and submission
- User profile display and editing
- Password change form
- Session manager functionality
- Authentication guards
- Component integration scenarios

### Performance Tests (`performance/`)

**Performance and Scalability (`test_performance.py`)**
- Authentication performance under load
- Database query optimization
- Token generation and validation speed
- Concurrent user handling
- Memory usage patterns
- Caching effectiveness

## 🚀 Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Ensure database is set up
alembic upgrade head
```

### Run All Authentication Tests

```bash
# Run complete auth test suite
pytest tests/auth/ -v

# Run with coverage
pytest tests/auth/ --cov=src.grantha.database --cov=src.grantha.api.auth_routes --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/auth/unit/ -v

# Integration tests
pytest tests/auth/integration/ -v

# Security tests
pytest tests/auth/security/ -v

# Frontend tests
pytest tests/auth/frontend/ -v

# Performance tests (may take longer)
pytest tests/auth/performance/ -v -s
```

### Run Tests by Functionality

```bash
# Database model tests
pytest tests/auth/unit/test_models.py -v

# API endpoint tests
pytest tests/auth/integration/test_api_endpoints.py -v

# Security validation
pytest tests/auth/security/test_security_features.py -v

# Performance benchmarks
pytest tests/auth/performance/test_performance.py -v -s
```

### Test Markers

Use pytest markers to run specific types of tests:

```bash
# Run only unit tests
pytest -m unit tests/auth/

# Run integration tests
pytest -m integration tests/auth/

# Run security tests
pytest -m security tests/auth/

# Skip slow tests
pytest -m "not slow" tests/auth/

# Run network-dependent tests
pytest -m network tests/auth/
```

## 📊 Test Coverage Goals

| Component | Target Coverage | Current Focus |
|-----------|----------------|---------------|
| Database Models | >95% | Password security, token management |
| Service Layer | >90% | Authentication flows, error handling |
| JWT Service | >95% | Token lifecycle, security features |
| API Endpoints | >85% | Request/response validation |
| Frontend Store | >80% | State management, token handling |
| UI Components | >75% | Form validation, user interactions |

## 🔧 Test Configuration

### Environment Variables

```bash
# Test database (uses in-memory SQLite by default)
DATABASE_URL=sqlite+aiosqlite:///:memory:

# JWT secret for testing
SECRET_KEY=test_secret_key_for_jwt

# Test mode flag
TESTING=1
```

### Fixtures Available

**Database Fixtures:**
- `test_session` - Async database session
- `test_user` - Pre-created test user
- `test_admin` - Admin user
- `verified_user` - Verified user
- `locked_user` - Account-locked user
- `multiple_users` - List of test users

**Authentication Fixtures:**
- `jwt_service` - JWT service instance
- `sample_user_data` - User registration data
- `sample_token_data` - JWT token data
- `auth_headers` - Authentication headers

**Mock Fixtures:**
- `mock_request` - FastAPI request mock
- `mock_api_client` - Frontend API client mock
- `mock_browser_env` - Browser environment mock

## 🔍 Test Scenarios Covered

### Authentication Flows
- ✅ User registration with validation
- ✅ Login with username/email
- ✅ Multi-factor authentication preparation
- ✅ Password reset workflows
- ✅ Email verification
- ✅ Account lockout and recovery

### Session Management
- ✅ JWT token generation and validation
- ✅ Refresh token rotation
- ✅ Session invalidation
- ✅ Concurrent session handling
- ✅ Session cleanup and expiration

### Security Features
- ✅ Password hashing and verification
- ✅ Brute force protection
- ✅ Session hijacking prevention
- ✅ Input validation and sanitization
- ✅ SQL injection prevention
- ✅ XSS prevention
- ✅ CSRF protection

### Error Scenarios
- ✅ Network failures
- ✅ Database connectivity issues
- ✅ Invalid token handling
- ✅ Malformed requests
- ✅ Rate limiting
- ✅ Concurrent access conflicts

### Performance Characteristics
- ✅ Authentication under load
- ✅ Database query performance
- ✅ Memory usage patterns
- ✅ Scalability limits
- ✅ Token validation speed

## 🐛 Debugging Tests

### Verbose Output

```bash
# Show detailed test output
pytest tests/auth/ -v -s

# Show SQL queries (for database tests)
pytest tests/auth/unit/test_models.py -v -s --log-cli-level=DEBUG
```

### Test Specific Scenarios

```bash
# Test specific function
pytest tests/auth/unit/test_models.py::TestUserModel::test_password_hashing -v

# Test with specific user data
pytest tests/auth/integration/test_api_endpoints.py::TestUserLogin -v
```

### Performance Profiling

```bash
# Run performance tests with profiling
pytest tests/auth/performance/ -v -s --profile

# Memory usage testing
pytest tests/auth/performance/test_performance.py::TestMemoryUsage -v -s
```

## 📈 Continuous Integration

The test suite is designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions configuration
- name: Run Authentication Tests
  run: |
    pytest tests/auth/ \
      --cov=src.grantha.database \
      --cov=src.grantha.api.auth_routes \
      --cov-report=xml \
      --junit-xml=test-results.xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## 🔄 Test Data Management

### Test Database
- Uses in-memory SQLite for speed
- Automatically creates/tears down schema
- Isolated test transactions
- Proper cleanup between tests

### Test Users
- Pre-created test users with various states
- Configurable user data factories
- Realistic test scenarios
- Proper password hashing

### Mock Services
- HTTP request/response mocking
- Browser environment simulation
- API client mocking
- Time-sensitive operation mocking

## ⚡ Performance Benchmarks

The test suite includes performance benchmarks for:

- **Authentication Speed**: < 1 second per login
- **Token Validation**: < 1ms per token
- **Database Queries**: < 100ms for user lookups
- **Concurrent Logins**: 70%+ success rate under load
- **Memory Usage**: < 100MB for 1000+ sessions

## 🛡️ Security Testing

Security tests validate:

- **Password Security**: Bcrypt hashing, timing attack resistance
- **Token Security**: JWT validation, algorithm security
- **Session Security**: Hijacking prevention, proper invalidation
- **Input Validation**: SQL injection, XSS prevention
- **Access Control**: Authentication guards, role-based access
- **Audit Trail**: Event logging, security monitoring

## 📝 Contributing to Tests

When adding new authentication features:

1. **Add Unit Tests**: Test individual component functionality
2. **Add Integration Tests**: Test component interactions
3. **Add Security Tests**: Validate security implications
4. **Update Performance Tests**: Ensure scalability
5. **Document Test Cases**: Update this README

### Test Naming Conventions

```python
# Unit tests
def test_user_password_hashing():
def test_jwt_token_generation():

# Integration tests  
def test_login_flow_success():
def test_registration_validation_errors():

# Security tests
def test_brute_force_protection():
def test_session_hijacking_prevention():

# Performance tests
def test_login_performance():
def test_concurrent_authentication_load():
```

---

**Quality Guardian Dharma**: Every authentication flow must be thoroughly tested, every security feature validated, and every performance characteristic measured. The tests are the shield that protects user data and system integrity.