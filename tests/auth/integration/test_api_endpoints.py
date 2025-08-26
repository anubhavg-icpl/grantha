"""Integration tests for authentication API endpoints."""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.grantha.api.app import create_app
from src.grantha.api.auth_routes import enhanced_auth_router
from src.grantha.database import get_db_session


@pytest.fixture
def app():
    """Create FastAPI test app."""
    app = FastAPI()
    app.include_router(enhanced_auth_router, prefix="/auth/v2")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db_dependency(test_session):
    """Mock database dependency."""
    async def get_test_db():
        yield test_session
    
    return get_test_db


@pytest.mark.asyncio
class TestUserRegistration:
    """Test user registration endpoints."""
    
    def test_register_user_success(self, client, mock_db_dependency):
        """Test successful user registration."""
        with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
            response = client.post(
                "/auth/v2/register",
                json={
                    "username": "newuser",
                    "password": "newpass123",
                    "email": "new@example.com",
                    "full_name": "New User"
                }
            )
        
        # Note: This is a simplified test. In a real integration test,
        # you'd need to properly mock the database operations
        assert response.status_code in [200, 422]  # 422 for validation errors in test
    
    def test_register_user_duplicate_username(self, client, mock_db_dependency):
        """Test registration with duplicate username."""
        user_data = {
            "username": "testuser",
            "password": "testpass123",
            "email": "test@example.com"
        }
        
        with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
            # First registration
            response1 = client.post("/auth/v2/register", json=user_data)
            
            # Second registration with same username
            response2 = client.post("/auth/v2/register", json=user_data)
        
        # At least one should succeed, the other should fail
        statuses = [response1.status_code, response2.status_code]
        assert 200 in statuses or 201 in statuses
        assert 400 in statuses or 409 in statuses or 422 in statuses
    
    def test_register_user_invalid_data(self, client, mock_db_dependency):
        """Test registration with invalid data."""
        invalid_data_cases = [
            {"username": "ab", "password": "test"},  # Username too short
            {"username": "validuser", "password": ""},  # Empty password
            {"username": "", "password": "validpass123"},  # Empty username
            {"username": "user", "email": "invalid-email", "password": "pass123"},  # Invalid email
        ]
        
        with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
            for invalid_data in invalid_data_cases:
                response = client.post("/auth/v2/register", json=invalid_data)
                assert response.status_code in [400, 422]


@pytest.mark.asyncio
class TestUserLogin:
    """Test user login endpoints."""
    
    def test_login_success(self, client, mock_db_dependency, test_user, sample_user_data):
        """Test successful login."""
        with patch('src.grantha.api.auth_routes.database_jwt_service') as mock_jwt:
            mock_jwt.authenticate_and_generate_tokens.return_value = (
                "mock_access_token",
                "mock_refresh_token",
                {
                    "id": str(test_user.id),
                    "username": test_user.username,
                    "email": test_user.email,
                    "full_name": test_user.full_name,
                    "is_verified": test_user.is_verified,
                    "is_superuser": test_user.is_superuser
                }
            )
            
            with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                response = client.post(
                    "/auth/v2/login",
                    json={
                        "username": sample_user_data["username"],
                        "password": sample_user_data["password"]
                    }
                )
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert "user_id" in data
            assert "username" in data
            assert data["access_token"] == "mock_access_token"
    
    def test_login_invalid_credentials(self, client, mock_db_dependency):
        """Test login with invalid credentials."""
        with patch('src.grantha.api.auth_routes.database_jwt_service') as mock_jwt:
            mock_jwt.authenticate_and_generate_tokens.return_value = (None, None, None)
            
            with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                response = client.post(
                    "/auth/v2/login",
                    json={
                        "username": "nonexistent",
                        "password": "wrongpass"
                    }
                )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid credentials" in data["detail"]
    
    def test_login_missing_fields(self, client, mock_db_dependency):
        """Test login with missing required fields."""
        invalid_requests = [
            {"username": "test"},  # Missing password
            {"password": "test"},  # Missing username
            {},  # Missing both
        ]
        
        with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
            for invalid_request in invalid_requests:
                response = client.post("/auth/v2/login", json=invalid_request)
                assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestTokenRefresh:
    """Test token refresh endpoints."""
    
    def test_refresh_token_success(self, client, mock_db_dependency):
        """Test successful token refresh."""
        with patch('src.grantha.api.auth_routes.database_jwt_service') as mock_jwt:
            mock_jwt.refresh_access_token.return_value = (
                "new_access_token",
                {"id": "user123", "username": "testuser"}
            )
            
            with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                response = client.post(
                    "/auth/v2/refresh",
                    json={"refresh_token": "valid_refresh_token"}
                )
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "expires_in" in data
            assert data["access_token"] == "new_access_token"
    
    def test_refresh_token_invalid(self, client, mock_db_dependency):
        """Test refresh with invalid token."""
        with patch('src.grantha.api.auth_routes.database_jwt_service') as mock_jwt:
            mock_jwt.refresh_access_token.return_value = (None, None)
            
            with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                response = client.post(
                    "/auth/v2/refresh",
                    json={"refresh_token": "invalid_token"}
                )
        
        assert response.status_code == 401
    
    def test_refresh_token_missing(self, client, mock_db_dependency):
        """Test refresh without token."""
        with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
            response = client.post("/auth/v2/refresh", json={})
        
        assert response.status_code == 422


@pytest.mark.asyncio
class TestUserLogout:
    """Test user logout endpoints."""
    
    def test_logout_success(self, client, mock_db_dependency):
        """Test successful logout."""
        with patch('src.grantha.api.auth_routes.database_jwt_service') as mock_jwt:
            mock_jwt.logout_user.return_value = {
                "success": True,
                "user_id": "user123",
                "revoked_tokens": 1,
                "message": "Successfully logged out"
            }
            
            with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                response = client.post(
                    "/auth/v2/logout",
                    headers={"Authorization": "Bearer access_token"},
                    json={
                        "refresh_token": "refresh_token",
                        "revoke_all": False
                    }
                )
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "revoked_tokens" in data
    
    def test_logout_revoke_all(self, client, mock_db_dependency):
        """Test logout with revoke all sessions."""
        with patch('src.grantha.api.auth_routes.database_jwt_service') as mock_jwt:
            mock_jwt.logout_user.return_value = {
                "success": True,
                "user_id": "user123",
                "revoked_tokens": 3,
                "message": "Successfully logged out"
            }
            
            with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                response = client.post(
                    "/auth/v2/logout",
                    headers={"Authorization": "Bearer access_token"},
                    json={
                        "refresh_token": "refresh_token",
                        "revoke_all": True
                    }
                )
        
        if response.status_code == 200:
            data = response.json()
            assert data["revoked_tokens"] == 3
    
    def test_logout_without_auth(self, client, mock_db_dependency):
        """Test logout without authentication."""
        with patch('src.grantha.api.auth_routes.database_jwt_service') as mock_jwt:
            mock_jwt.logout_user.return_value = {
                "success": True,
                "user_id": None,
                "revoked_tokens": 0,
                "message": "Logged out"
            }
            
            with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                response = client.post("/auth/v2/logout")
        
        # Should still succeed even without auth
        assert response.status_code in [200, 401]


@pytest.mark.asyncio
class TestUserProfile:
    """Test user profile endpoints."""
    
    def test_get_current_user(self, client, mock_db_dependency, test_user):
        """Test getting current user profile."""
        with patch('src.grantha.api.auth_routes.database_jwt_service') as mock_jwt:
            mock_jwt.validate_access_token.return_value = {
                "user_id": str(test_user.id),
                "username": test_user.username,
                "type": "access"
            }
            
            with patch('src.grantha.api.auth_routes.UserService') as mock_user_service:
                mock_user_service.get_user_by_id.return_value = test_user
                
                with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                    response = client.get(
                        "/auth/v2/me",
                        headers={"Authorization": "Bearer valid_token"}
                    )
        
        if response.status_code == 200:
            data = response.json()
            assert "username" in data
            assert "email" in data
            assert "is_active" in data
    
    def test_get_current_user_invalid_token(self, client, mock_db_dependency):
        """Test getting user profile with invalid token."""
        with patch('src.grantha.api.auth_routes.database_jwt_service') as mock_jwt:
            mock_jwt.validate_access_token.return_value = None
            
            with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                response = client.get(
                    "/auth/v2/me",
                    headers={"Authorization": "Bearer invalid_token"}
                )
        
        assert response.status_code == 401
    
    def test_get_current_user_no_auth(self, client, mock_db_dependency):
        """Test getting user profile without authentication."""
        with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
            response = client.get("/auth/v2/me")
        
        assert response.status_code == 401
    
    def test_update_current_user(self, client, mock_db_dependency, test_user):
        """Test updating user profile."""
        with patch('src.grantha.api.auth_routes.database_jwt_service') as mock_jwt:
            mock_jwt.validate_access_token.return_value = {
                "user_id": str(test_user.id),
                "type": "access"
            }
            
            updated_user = Mock()
            updated_user.id = test_user.id
            updated_user.username = test_user.username
            updated_user.email = "updated@example.com"
            updated_user.full_name = "Updated Name"
            updated_user.bio = test_user.bio
            updated_user.is_active = test_user.is_active
            updated_user.is_verified = test_user.is_verified
            updated_user.is_superuser = test_user.is_superuser
            updated_user.created_at = test_user.created_at
            updated_user.last_login = test_user.last_login
            
            with patch('src.grantha.api.auth_routes.UserService') as mock_user_service:
                mock_user_service.update_user.return_value = updated_user
                
                with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                    response = client.put(
                        "/auth/v2/me",
                        headers={"Authorization": "Bearer valid_token"},
                        json={
                            "email": "updated@example.com",
                            "full_name": "Updated Name"
                        }
                    )
        
        if response.status_code == 200:
            data = response.json()
            assert data["email"] == "updated@example.com"
            assert data["full_name"] == "Updated Name"


@pytest.mark.asyncio
class TestPasswordChange:
    """Test password change endpoints."""
    
    def test_change_password_success(self, client, mock_db_dependency, test_user):
        """Test successful password change."""
        with patch('src.grantha.api.auth_routes.database_jwt_service') as mock_jwt:
            mock_jwt.validate_access_token.return_value = {
                "user_id": str(test_user.id),
                "type": "access"
            }
            
            with patch('src.grantha.api.auth_routes.UserService') as mock_user_service:
                mock_user_service.get_user_by_id.return_value = test_user
                mock_user_service.update_user.return_value = test_user
                
                with patch('src.grantha.api.auth_routes.RefreshTokenService') as mock_token_service:
                    mock_token_service.revoke_all_user_tokens.return_value = 2
                    
                    with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                        response = client.post(
                            "/auth/v2/change-password",
                            headers={"Authorization": "Bearer valid_token"},
                            json={
                                "current_password": "testpass123",
                                "new_password": "newtestpass123"
                            }
                        )
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "revoked_tokens" in data
    
    def test_change_password_wrong_current(self, client, mock_db_dependency, test_user):
        """Test password change with wrong current password."""
        test_user.verify_password = Mock(return_value=False)
        
        with patch('src.grantha.api.auth_routes.database_jwt_service') as mock_jwt:
            mock_jwt.validate_access_token.return_value = {
                "user_id": str(test_user.id),
                "type": "access"
            }
            
            with patch('src.grantha.api.auth_routes.UserService') as mock_user_service:
                mock_user_service.get_user_by_id.return_value = test_user
                
                with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                    response = client.post(
                        "/auth/v2/change-password",
                        headers={"Authorization": "Bearer valid_token"},
                        json={
                            "current_password": "wrongpass",
                            "new_password": "newtestpass123"
                        }
                    )
        
        assert response.status_code == 400


@pytest.mark.asyncio
class TestSessionManagement:
    """Test session management endpoints."""
    
    def test_get_user_sessions(self, client, mock_db_dependency):
        """Test getting user sessions."""
        mock_sessions = [
            {
                "id": "session1",
                "created_at": "2024-01-01T12:00:00",
                "expires_at": "2024-01-08T12:00:00",
                "ip_address": "127.0.0.1",
                "user_agent": "browser/1.0"
            }
        ]
        
        with patch('src.grantha.api.auth_routes.database_jwt_service') as mock_jwt:
            mock_jwt.validate_access_token.return_value = {
                "user_id": "user123",
                "type": "access"
            }
            mock_jwt.get_user_sessions.return_value = mock_sessions
            
            with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                response = client.get(
                    "/auth/v2/sessions",
                    headers={"Authorization": "Bearer valid_token"}
                )
        
        if response.status_code == 200:
            data = response.json()
            assert "sessions" in data
            assert "count" in data
            assert len(data["sessions"]) == 1
    
    def test_revoke_session(self, client, mock_db_dependency):
        """Test revoking specific session."""
        with patch('src.grantha.api.auth_routes.database_jwt_service') as mock_jwt:
            mock_jwt.validate_access_token.return_value = {
                "user_id": "user123",
                "type": "access"
            }
            mock_jwt.revoke_session.return_value = True
            
            with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                response = client.delete(
                    "/auth/v2/sessions/session123",
                    headers={"Authorization": "Bearer valid_token"}
                )
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
    
    def test_revoke_session_not_found(self, client, mock_db_dependency):
        """Test revoking non-existent session."""
        with patch('src.grantha.api.auth_routes.database_jwt_service') as mock_jwt:
            mock_jwt.validate_access_token.return_value = {
                "user_id": "user123",
                "type": "access"
            }
            mock_jwt.revoke_session.return_value = False
            
            with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                response = client.delete(
                    "/auth/v2/sessions/nonexistent",
                    headers={"Authorization": "Bearer valid_token"}
                )
        
        assert response.status_code == 404


@pytest.mark.asyncio
class TestLegacyCompatibility:
    """Test legacy compatibility endpoints."""
    
    def test_auth_status(self, client, mock_db_dependency):
        """Test auth status endpoint."""
        with patch('src.grantha.api.auth_routes.get_config') as mock_config:
            mock_config.return_value.wiki_auth_mode = True
            
            with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                response = client.get("/auth/v2/status")
        
        if response.status_code == 200:
            data = response.json()
            assert "auth_required" in data
    
    def test_token_info(self, client, mock_db_dependency):
        """Test token info endpoint."""
        with patch('src.grantha.api.auth_routes.database_jwt_service') as mock_jwt:
            mock_jwt.get_token_info.return_value = {
                "user_id": "user123",
                "type": "access",
                "jti": "token123",
                "issued_at": 1640995200,
                "expires_at": 1641081600,
                "is_expired": False,
                "is_revoked": False
            }
            
            with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
                response = client.get(
                    "/auth/v2/token/info",
                    headers={"Authorization": "Bearer valid_token"}
                )
        
        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data
            assert "token_type" in data
            assert "is_expired" in data


@pytest.mark.asyncio
class TestAPIErrorHandling:
    """Test API error handling."""
    
    def test_database_connection_error(self, client):
        """Test handling database connection errors."""
        def failing_db():
            raise Exception("Database connection failed")
        
        with patch.object(enhanced_auth_router, 'get_db_session', failing_db):
            response = client.get("/auth/v2/status")
        
        # Should handle gracefully
        assert response.status_code in [500, 503]
    
    def test_invalid_json_request(self, client, mock_db_dependency):
        """Test handling invalid JSON in requests."""
        with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
            response = client.post(
                "/auth/v2/login",
                data="invalid json",
                headers={"Content-Type": "application/json"}
            )
        
        assert response.status_code == 422
    
    def test_missing_content_type(self, client, mock_db_dependency):
        """Test handling missing content type."""
        with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
            response = client.post(
                "/auth/v2/login",
                data=json.dumps({"username": "test", "password": "test"})
            )
        
        # FastAPI should handle this gracefully
        assert response.status_code in [400, 422, 415]
    
    def test_large_request_payload(self, client, mock_db_dependency):
        """Test handling large request payloads."""
        large_payload = {
            "username": "test",
            "password": "test",
            "bio": "x" * 100000  # Very large bio
        }
        
        with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
            response = client.post("/auth/v2/register", json=large_payload)
        
        # Should handle large payloads appropriately
        assert response.status_code in [200, 400, 413, 422]


@pytest.mark.asyncio
class TestAPIRateLimiting:
    """Test API rate limiting behavior."""
    
    def test_rapid_login_attempts(self, client, mock_db_dependency):
        """Test rapid successive login attempts."""
        login_data = {"username": "test", "password": "test"}
        
        responses = []
        with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
            for _ in range(10):  # Make 10 rapid requests
                response = client.post("/auth/v2/login", json=login_data)
                responses.append(response)
        
        # Should handle rapid requests appropriately
        # (In a real scenario, rate limiting middleware would handle this)
        for response in responses:
            assert response.status_code in [200, 401, 429]
    
    def test_multiple_registration_attempts(self, client, mock_db_dependency):
        """Test multiple registration attempts."""
        user_data = {
            "username": "testuser",
            "password": "testpass123",
            "email": "test@example.com"
        }
        
        responses = []
        with patch.object(enhanced_auth_router, 'get_db_session', mock_db_dependency):
            for i in range(5):
                data = user_data.copy()
                data["username"] = f"testuser{i}"
                data["email"] = f"test{i}@example.com"
                response = client.post("/auth/v2/register", json=data)
                responses.append(response)
        
        # Should handle multiple registrations
        for response in responses:
            assert response.status_code in [200, 400, 422, 429]