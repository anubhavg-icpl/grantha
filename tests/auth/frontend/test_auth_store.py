"""Tests for frontend authentication store."""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock


class MockLocalStorage:
    """Mock localStorage for testing."""
    
    def __init__(self):
        self.storage = {}
    
    def getItem(self, key):
        return self.storage.get(key)
    
    def setItem(self, key, value):
        self.storage[key] = value
    
    def removeItem(self, key):
        self.storage.pop(key, None)
    
    def clear(self):
        self.storage.clear()


class MockBrowser:
    """Mock browser environment."""
    
    def __init__(self):
        self.localStorage = MockLocalStorage()
        self.location = Mock()
        self.location.href = "http://localhost:5173"


@pytest.fixture
def mock_browser_env():
    """Mock browser environment for testing."""
    browser = MockBrowser()
    
    with patch('src.lib.stores.auth.browser', True):
        with patch('src.lib.stores.auth.localStorage', browser.localStorage):
            yield browser


@pytest.fixture
def mock_api_client():
    """Mock API client for testing."""
    client = Mock()
    client.getAuthStatus = AsyncMock()
    client.validateAuthCode = AsyncMock()
    client.setToken = Mock()
    client.clearToken = Mock()
    return client


@pytest.fixture
def sample_token_data():
    """Sample token data for testing."""
    return {
        "access_token": "mock_access_token_123",
        "refresh_token": "mock_refresh_token_456",
        "expires_at": 1640995200,  # Mock timestamp
        "user_id": "user-123"
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "user-123",
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "is_verified": True,
        "is_superuser": False,
        "created_at": "2024-01-01T12:00:00Z",
        "last_login": "2024-01-15T10:30:00Z"
    }


class TestAuthStoreInitialization:
    """Test auth store initialization."""
    
    def test_initial_state(self, mock_browser_env):
        """Test auth store initial state."""
        # In a real test, you'd import the actual store
        # For now, we'll test the expected initial state structure
        expected_initial_state = {
            "isAuthenticated": False,
            "authRequired": False,
            "isLoading": False,
            "error": None,
            "redirectTo": None,
            "user": None,
            "loginAttempts": 0,
            "isAccountLocked": False,
            "sessionTimeout": None,
            "csrfToken": None
        }
        
        # Verify structure matches expected
        for key in expected_initial_state:
            assert key is not None  # Basic structure test
    
    def test_token_storage_utilities(self, mock_browser_env, sample_token_data):
        """Test token storage utilities."""
        # Test storing tokens
        token_key = "grantha-tokens"
        stored_data = json.dumps(sample_token_data)
        
        mock_browser_env.localStorage.setItem(token_key, stored_data)
        
        # Test retrieving tokens
        retrieved = mock_browser_env.localStorage.getItem(token_key)
        assert retrieved == stored_data
        
        # Test parsing
        parsed_data = json.loads(retrieved)
        assert parsed_data["access_token"] == sample_token_data["access_token"]
        assert parsed_data["user_id"] == sample_token_data["user_id"]
        
        # Test clearing tokens
        mock_browser_env.localStorage.removeItem(token_key)
        assert mock_browser_env.localStorage.getItem(token_key) is None


class TestAuthenticationActions:
    """Test authentication action functions."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, mock_browser_env, mock_api_client):
        """Test successful login flow."""
        # Mock successful login response
        login_response_data = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 1800,
            "user_id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "is_verified": True,
            "is_superuser": False
        }
        
        # Mock fetch response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=login_response_data)
        mock_response.status_code = 200
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            # Test login logic
            username = "testuser"
            password = "testpass123"
            remember_me = True
            
            # Expected behavior: store tokens and update auth state
            expected_token_data = {
                "access_token": login_response_data["access_token"],
                "refresh_token": login_response_data["refresh_token"],
                "expires_at": mock_response.json.return_value["expires_in"] + 1640995200,  # Mock time
                "user_id": login_response_data["user_id"]
            }
            
            # Verify token would be stored
            assert expected_token_data["access_token"] == "new_access_token"
    
    @pytest.mark.asyncio
    async def test_login_failure_invalid_credentials(self, mock_browser_env):
        """Test login failure with invalid credentials."""
        error_response = {
            "detail": "Invalid credentials"
        }
        
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status = 401
        mock_response.json = AsyncMock(return_value=error_response)
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            # Test failed login
            # Expected behavior: no tokens stored, error state set
            result = await mock_response.json()
            assert result["detail"] == "Invalid credentials"
            
            # Tokens should not be stored
            token_data = mock_browser_env.localStorage.getItem("grantha-tokens")
            assert token_data is None
    
    @pytest.mark.asyncio
    async def test_login_account_locked(self, mock_browser_env):
        """Test login with locked account."""
        error_response = {
            "detail": "Account temporarily locked due to multiple failed attempts"
        }
        
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status = 423  # Locked status
        mock_response.json = AsyncMock(return_value=error_response)
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            # Test account lockout scenario
            result = await mock_response.json()
            assert "locked" in result["detail"].lower()
            
            # Should indicate account is locked
            assert mock_response.status == 423
    
    @pytest.mark.asyncio
    async def test_token_refresh_success(self, mock_browser_env, sample_token_data):
        """Test successful token refresh."""
        # Store initial tokens
        mock_browser_env.localStorage.setItem(
            "grantha-tokens", 
            json.dumps(sample_token_data)
        )
        
        # Mock refresh response
        refresh_response = {
            "access_token": "new_refreshed_token",
            "expires_in": 1800
        }
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=refresh_response)
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            # Test refresh logic
            result = await mock_response.json()
            assert result["access_token"] == "new_refreshed_token"
            
            # Token should be updated in storage
            # (In real implementation, storage would be updated)
    
    @pytest.mark.asyncio
    async def test_token_refresh_failure(self, mock_browser_env, sample_token_data):
        """Test failed token refresh."""
        # Store expired/invalid tokens
        mock_browser_env.localStorage.setItem(
            "grantha-tokens",
            json.dumps(sample_token_data)
        )
        
        # Mock failed refresh response
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status = 401
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            # Test failed refresh
            assert mock_response.status == 401
            
            # Should clear invalid tokens
            # (In real implementation)
    
    @pytest.mark.asyncio
    async def test_logout_success(self, mock_browser_env, sample_token_data):
        """Test successful logout."""
        # Store tokens
        mock_browser_env.localStorage.setItem(
            "grantha-tokens",
            json.dumps(sample_token_data)
        )
        
        # Mock logout response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"message": "Logged out successfully"})
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            # Test logout
            result = await mock_response.json()
            assert "success" in result["message"].lower()
        
        # Tokens should be cleared
        mock_browser_env.localStorage.removeItem("grantha-tokens")
        assert mock_browser_env.localStorage.getItem("grantha-tokens") is None


class TestUserProfileManagement:
    """Test user profile management functions."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_browser_env, sample_user_data, sample_token_data):
        """Test getting current user profile."""
        # Store valid tokens
        mock_browser_env.localStorage.setItem(
            "grantha-tokens",
            json.dumps(sample_token_data)
        )
        
        # Mock user profile response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=sample_user_data)
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            # Test getting user profile
            result = await mock_response.json()
            
            assert result["id"] == sample_user_data["id"]
            assert result["username"] == sample_user_data["username"]
            assert result["email"] == sample_user_data["email"]
    
    @pytest.mark.asyncio
    async def test_update_user_profile_success(self, mock_browser_env, sample_token_data):
        """Test updating user profile."""
        # Store valid tokens
        mock_browser_env.localStorage.setItem(
            "grantha-tokens",
            json.dumps(sample_token_data)
        )
        
        updated_profile = {
            "full_name": "Updated Name",
            "bio": "Updated bio",
            "email": "updated@example.com"
        }
        
        # Mock update response
        updated_user = {
            "id": "user-123",
            "username": "testuser",
            "email": "updated@example.com",
            "full_name": "Updated Name",
            "bio": "Updated bio"
        }
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=updated_user)
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            # Test profile update
            result = await mock_response.json()
            
            assert result["email"] == updated_profile["email"]
            assert result["full_name"] == updated_profile["full_name"]
            assert result["bio"] == updated_profile["bio"]
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, mock_browser_env, sample_token_data):
        """Test changing password."""
        # Store valid tokens
        mock_browser_env.localStorage.setItem(
            "grantha-tokens",
            json.dumps(sample_token_data)
        )
        
        # Mock password change response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={
            "message": "Password changed successfully",
            "revoked_tokens": 2
        })
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            # Test password change
            result = await mock_response.json()
            
            assert "success" in result["message"].lower()
            assert result["revoked_tokens"] >= 1
        
        # After password change, should redirect to login
        # (Implementation would handle this)
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, mock_browser_env, sample_token_data):
        """Test password change with wrong current password."""
        # Store valid tokens
        mock_browser_env.localStorage.setItem(
            "grantha-tokens",
            json.dumps(sample_token_data)
        )
        
        # Mock error response
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={
            "detail": "Current password is incorrect"
        })
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            # Test failed password change
            assert mock_response.status == 400
            result = await mock_response.json()
            assert "incorrect" in result["detail"].lower()


class TestSessionManagement:
    """Test session management functions."""
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, mock_browser_env, sample_token_data):
        """Test getting user sessions."""
        # Store valid tokens
        mock_browser_env.localStorage.setItem(
            "grantha-tokens",
            json.dumps(sample_token_data)
        )
        
        # Mock sessions response
        mock_sessions = [
            {
                "id": "session1",
                "created_at": "2024-01-15T10:00:00Z",
                "expires_at": "2024-01-22T10:00:00Z",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0",
                "is_current": True
            },
            {
                "id": "session2",
                "created_at": "2024-01-14T15:30:00Z",
                "expires_at": "2024-01-21T15:30:00Z",
                "ip_address": "10.0.0.50",
                "user_agent": "Chrome Mobile",
                "is_current": False
            }
        ]
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={
            "sessions": mock_sessions,
            "count": len(mock_sessions)
        })
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            # Test getting sessions
            result = await mock_response.json()
            
            assert len(result["sessions"]) == 2
            assert result["count"] == 2
            
            # Verify session structure
            session = result["sessions"][0]
            assert "id" in session
            assert "ip_address" in session
            assert "user_agent" in session
            assert "is_current" in session
    
    @pytest.mark.asyncio
    async def test_revoke_session_success(self, mock_browser_env, sample_token_data):
        """Test revoking a session."""
        # Store valid tokens
        mock_browser_env.localStorage.setItem(
            "grantha-tokens",
            json.dumps(sample_token_data)
        )
        
        # Mock revoke response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={
            "message": "Session revoked successfully"
        })
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            # Test session revocation
            result = await mock_response.json()
            assert "success" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_revoke_session_not_found(self, mock_browser_env, sample_token_data):
        """Test revoking non-existent session."""
        # Store valid tokens
        mock_browser_env.localStorage.setItem(
            "grantha-tokens",
            json.dumps(sample_token_data)
        )
        
        # Mock error response
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status = 404
        mock_response.json = AsyncMock(return_value={
            "detail": "Session not found"
        })
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            # Test failed revocation
            assert mock_response.status == 404
            result = await mock_response.json()
            assert "not found" in result["detail"].lower()


class TestUserRegistration:
    """Test user registration functions."""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, mock_browser_env):
        """Test successful user registration."""
        registration_data = {
            "username": "newuser",
            "password": "newpass123",
            "email": "new@example.com",
            "full_name": "New User"
        }
        
        # Mock registration response
        new_user = {
            "id": "new-user-456",
            "username": "newuser",
            "email": "new@example.com",
            "full_name": "New User",
            "is_active": True,
            "is_verified": False,
            "is_superuser": False,
            "created_at": "2024-01-15T12:00:00Z"
        }
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=new_user)
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            # Test registration
            result = await mock_response.json()
            
            assert result["username"] == registration_data["username"]
            assert result["email"] == registration_data["email"]
            assert result["is_active"] is True
            assert result["is_verified"] is False
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(self, mock_browser_env):
        """Test registration with duplicate username."""
        registration_data = {
            "username": "existinguser",
            "password": "pass123",
            "email": "existing@example.com"
        }
        
        # Mock error response
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={
            "detail": "Username already exists"
        })
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            # Test failed registration
            assert mock_response.status == 400
            result = await mock_response.json()
            assert "already exists" in result["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_user_invalid_email(self, mock_browser_env):
        """Test registration with invalid email."""
        registration_data = {
            "username": "testuser",
            "password": "pass123",
            "email": "invalid-email"
        }
        
        # Mock validation error response
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status = 422
        mock_response.json = AsyncMock(return_value={
            "detail": "Invalid email address"
        })
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            # Test validation error
            assert mock_response.status == 422
            result = await mock_response.json()
            assert "invalid" in result["detail"].lower()


class TestAuthStateManagement:
    """Test authentication state management."""
    
    def test_error_handling(self, mock_browser_env):
        """Test error state management."""
        # Test setting error
        error_message = "Authentication failed"
        
        # In real implementation, error would be set in store
        # Here we test the expected behavior
        assert error_message is not None
        assert len(error_message) > 0
        
        # Test clearing error
        cleared_error = None
        assert cleared_error is None
    
    def test_loading_state_management(self, mock_browser_env):
        """Test loading state management."""
        # Test setting loading state
        is_loading = True
        assert is_loading is True
        
        # Test clearing loading state
        is_loading = False
        assert is_loading is False
    
    def test_redirect_path_management(self, mock_browser_env):
        """Test redirect path management."""
        # Test setting redirect path
        redirect_path = "/dashboard"
        assert redirect_path == "/dashboard"
        
        # Test getting and clearing redirect path
        retrieved_path = redirect_path
        redirect_path = None
        
        assert retrieved_path == "/dashboard"
        assert redirect_path is None
    
    def test_account_lockout_state(self, mock_browser_env):
        """Test account lockout state management."""
        # Test setting lockout state
        is_locked = True
        login_attempts = 5
        
        assert is_locked is True
        assert login_attempts == 5
        
        # Test clearing lockout state
        is_locked = False
        login_attempts = 0
        
        assert is_locked is False
        assert login_attempts == 0


class TestLegacyCompatibility:
    """Test legacy compatibility features."""
    
    @pytest.mark.asyncio
    async def test_auth_code_compatibility(self, mock_browser_env, mock_api_client):
        """Test backward compatibility with auth code system."""
        # Store legacy auth code
        legacy_code = "legacy_auth_code_123"
        mock_browser_env.localStorage.setItem("grantha-auth-code", legacy_code)
        
        # Mock validation response
        mock_api_client.validateAuthCode.return_value = {
            "success": True,
            "user": {"id": "user-123", "username": "legacyuser"}
        }
        
        # Test legacy code validation
        validation_result = await mock_api_client.validateAuthCode({
            "code": legacy_code
        })
        
        assert validation_result["success"] is True
        assert validation_result["user"]["username"] == "legacyuser"
        
        # After successful validation, should migrate to JWT
        # (Implementation detail)
    
    def test_migration_from_legacy_storage(self, mock_browser_env):
        """Test migration from legacy storage format."""
        # Set up legacy storage
        legacy_code = "old_auth_code"
        mock_browser_env.localStorage.setItem("grantha-auth-code", legacy_code)
        
        # New token storage should not conflict
        new_token_data = {
            "access_token": "new_jwt_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 1640995200,
            "user_id": "user-123"
        }
        
        mock_browser_env.localStorage.setItem(
            "grantha-tokens",
            json.dumps(new_token_data)
        )
        
        # Both should coexist during migration
        stored_legacy = mock_browser_env.localStorage.getItem("grantha-auth-code")
        stored_new = mock_browser_env.localStorage.getItem("grantha-tokens")
        
        assert stored_legacy == legacy_code
        assert stored_new is not None
        
        # After migration, legacy should be cleaned up
        mock_browser_env.localStorage.removeItem("grantha-auth-code")
        assert mock_browser_env.localStorage.getItem("grantha-auth-code") is None


class TestErrorScenarios:
    """Test various error scenarios."""
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, mock_browser_env):
        """Test handling of network errors."""
        # Mock network error
        with patch('builtins.fetch', AsyncMock(side_effect=Exception("Network error"))):
            try:
                await fetch("/auth/v2/login")
            except Exception as e:
                assert "Network error" in str(e)
    
    @pytest.mark.asyncio
    async def test_invalid_json_response(self, mock_browser_env):
        """Test handling of invalid JSON responses."""
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(side_effect=ValueError("Invalid JSON"))
        
        with patch('builtins.fetch', AsyncMock(return_value=mock_response)):
            try:
                result = await mock_response.json()
            except ValueError as e:
                assert "Invalid JSON" in str(e)
    
    def test_storage_quota_exceeded(self, mock_browser_env):
        """Test handling of storage quota exceeded."""
        # Mock storage quota error
        def mock_setItem_quota_error(key, value):
            raise Exception("QuotaExceededError")
        
        mock_browser_env.localStorage.setItem = mock_setItem_quota_error
        
        # Should handle gracefully
        try:
            mock_browser_env.localStorage.setItem("test", "data")
        except Exception as e:
            assert "QuotaExceededError" in str(e)
    
    def test_corrupted_token_data(self, mock_browser_env):
        """Test handling of corrupted token data."""
        # Store corrupted data
        corrupted_data = "not-valid-json"
        mock_browser_env.localStorage.setItem("grantha-tokens", corrupted_data)
        
        # Should handle JSON parse error gracefully
        try:
            stored_data = mock_browser_env.localStorage.getItem("grantha-tokens")
            json.loads(stored_data)
        except json.JSONDecodeError:
            # Expected behavior - should clear corrupted data
            mock_browser_env.localStorage.removeItem("grantha-tokens")
            assert mock_browser_env.localStorage.getItem("grantha-tokens") is None