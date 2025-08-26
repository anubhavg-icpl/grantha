"""Authentication test configuration and fixtures."""

import asyncio
import os
import pytest
import tempfile
import uuid
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator, Dict, Any
from unittest.mock import Mock, AsyncMock

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["TESTING"] = "1"
os.environ["SECRET_KEY"] = "test_secret_key_for_jwt"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from src.grantha.database.models import User, RefreshToken, AuthEvent
from src.grantha.database.base import Base
from src.grantha.database.services import UserService, RefreshTokenService, AuthEventService
from src.grantha.database.auth_service import DatabaseJWTService


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "password": "testpass123",
        "email": "test@example.com",
        "full_name": "Test User",
        "bio": "A test user"
    }


@pytest.fixture
def sample_admin_data():
    """Sample admin user data."""
    return {
        "username": "admin",
        "password": "adminpass123",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "is_superuser": True,
        "is_verified": True
    }


@pytest_asyncio.fixture
async def test_user(test_session: AsyncSession, sample_user_data) -> User:
    """Create a test user."""
    user = await UserService.create_user(
        session=test_session,
        **sample_user_data
    )
    return user


@pytest_asyncio.fixture
async def test_admin(test_session: AsyncSession, sample_admin_data) -> User:
    """Create a test admin user."""
    admin = await UserService.create_user(
        session=test_session,
        **sample_admin_data
    )
    return admin


@pytest_asyncio.fixture
async def verified_user(test_session: AsyncSession, sample_user_data) -> User:
    """Create a verified test user."""
    data = sample_user_data.copy()
    data['is_verified'] = True
    user = await UserService.create_user(
        session=test_session,
        **data
    )
    return user


@pytest_asyncio.fixture
async def locked_user(test_session: AsyncSession, sample_user_data) -> User:
    """Create a locked test user."""
    user = await UserService.create_user(
        session=test_session,
        **sample_user_data
    )
    
    # Lock the account
    user.increment_failed_login(max_attempts=3, lockout_duration_minutes=30)
    await test_session.commit()
    
    return user


@pytest_asyncio.fixture
async def test_refresh_token(test_session: AsyncSession, test_user: User) -> RefreshToken:
    """Create a test refresh token."""
    token_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    refresh_token = await RefreshTokenService.create_refresh_token(
        session=test_session,
        user_id=str(test_user.id),
        token_id=token_id,
        expires_at=expires_at,
        ip_address="127.0.0.1",
        user_agent="test-agent"
    )
    
    return refresh_token


@pytest.fixture
def jwt_service():
    """JWT service instance for testing."""
    return DatabaseJWTService()


@pytest.fixture
def mock_request():
    """Mock FastAPI request object."""
    mock_req = Mock()
    mock_req.client.host = "127.0.0.1"
    mock_req.headers = {
        "user-agent": "test-browser/1.0",
        "x-device-fingerprint": "test-device-123"
    }
    return mock_req


@pytest.fixture
def auth_headers():
    """Generate auth headers for testing."""
    def _headers(token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    return _headers


@pytest.fixture
def sample_login_request():
    """Sample login request data."""
    return {
        "username": "testuser",
        "password": "testpass123"
    }


@pytest.fixture
def sample_registration_request():
    """Sample registration request data."""
    return {
        "username": "newuser",
        "password": "newpass123",
        "email": "new@example.com",
        "full_name": "New User"
    }


@pytest.fixture
def sample_password_change_request():
    """Sample password change request."""
    return {
        "current_password": "testpass123",
        "new_password": "newtestpass123"
    }


@pytest_asyncio.fixture
async def multiple_users(test_session: AsyncSession):
    """Create multiple test users."""
    users = []
    
    for i in range(5):
        user_data = {
            "username": f"user{i}",
            "password": f"pass{i}123",
            "email": f"user{i}@example.com",
            "full_name": f"User {i}"
        }
        user = await UserService.create_user(session=test_session, **user_data)
        users.append(user)
    
    return users


@pytest_asyncio.fixture
async def multiple_refresh_tokens(test_session: AsyncSession, test_user: User):
    """Create multiple refresh tokens for a user."""
    tokens = []
    
    for i in range(3):
        token_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        token = await RefreshTokenService.create_refresh_token(
            session=test_session,
            user_id=str(test_user.id),
            token_id=token_id,
            expires_at=expires_at,
            ip_address=f"192.168.1.{i+1}",
            user_agent=f"browser-{i}/1.0"
        )
        tokens.append(token)
    
    return tokens


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Configure logging for tests."""
    import logging
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)


# Rate limiting and security fixtures
@pytest.fixture
def rate_limit_attempts():
    """Configuration for rate limiting tests."""
    return {
        "max_attempts": 5,
        "window_seconds": 60,
        "lockout_duration": 300  # 5 minutes
    }


@pytest.fixture
def security_config():
    """Security configuration for tests."""
    return {
        "password_min_length": 8,
        "password_require_uppercase": True,
        "password_require_lowercase": True,
        "password_require_numbers": True,
        "password_require_symbols": False,
        "max_login_attempts": 5,
        "account_lockout_duration": 1800,  # 30 minutes
        "jwt_access_token_expires": 1800,   # 30 minutes
        "jwt_refresh_token_expires": 604800  # 7 days
    }


@pytest.fixture
def mock_time():
    """Mock time for testing time-sensitive operations."""
    from unittest.mock import patch
    with patch('src.grantha.database.models.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield mock_dt


# API client fixtures
@pytest.fixture
def api_client():
    """Mock API client for frontend testing."""
    client = Mock()
    client.login = AsyncMock()
    client.register = AsyncMock()
    client.refresh_token = AsyncMock()
    client.logout = AsyncMock()
    client.get_current_user = AsyncMock()
    client.update_profile = AsyncMock()
    client.change_password = AsyncMock()
    client.get_sessions = AsyncMock()
    client.revoke_session = AsyncMock()
    return client


@pytest.fixture
def browser_environment():
    """Mock browser environment for frontend tests."""
    return {
        "localStorage": {},
        "sessionStorage": {},
        "location": Mock(href="http://localhost:5173"),
        "history": Mock(),
        "fetch": AsyncMock()
    }


# Test data generators
@pytest.fixture
def user_data_factory():
    """Factory for generating test user data."""
    def _create_user_data(
        username: str = None,
        email: str = None,
        password: str = "testpass123",
        **kwargs
    ) -> Dict[str, Any]:
        base_username = username or f"user_{uuid.uuid4().hex[:8]}"
        base_email = email or f"{base_username}@example.com"
        
        return {
            "username": base_username,
            "email": base_email,
            "password": password,
            "full_name": f"Test {base_username.title()}",
            "bio": f"Bio for {base_username}",
            **kwargs
        }
    
    return _create_user_data


@pytest.fixture
def token_data_factory():
    """Factory for generating test token data."""
    def _create_token_data(
        user_id: str = None,
        expires_in: int = 1800,  # 30 minutes
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "user_id": user_id or str(uuid.uuid4()),
            "access_token": f"access_token_{uuid.uuid4().hex}",
            "refresh_token": f"refresh_token_{uuid.uuid4().hex}",
            "expires_in": expires_in,
            "token_type": "bearer",
            **kwargs
        }
    
    return _create_token_data


# Async helper fixtures
@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Cleanup fixtures
@pytest_asyncio.fixture
async def cleanup_auth_events(test_session: AsyncSession):
    """Clean up auth events after tests."""
    yield
    
    # Clean up auth events created during tests
    from sqlalchemy import delete
    await test_session.execute(delete(AuthEvent))
    await test_session.commit()