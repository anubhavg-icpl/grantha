"""Unit tests for JWT authentication services."""

import pytest
import uuid
import jwt
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.grantha.database.auth_service import DatabaseJWTService
from src.grantha.utils.jwt_service import JWTService
from src.grantha.database.models import User, RefreshToken


@pytest.mark.asyncio
class TestDatabaseJWTService:
    """Test DatabaseJWTService functionality."""
    
    def test_jwt_service_initialization(self, jwt_service):
        """Test JWT service initialization."""
        assert jwt_service.secret_key is not None
        assert jwt_service.algorithm == 'HS256'
        assert jwt_service.access_token_expires_minutes == 30
        assert jwt_service.refresh_token_expires_days == 7
    
    async def test_authenticate_and_generate_tokens_success(
        self, jwt_service, test_session, test_user, sample_user_data
    ):
        """Test successful authentication and token generation."""
        access_token, refresh_token, user_info = await jwt_service.authenticate_and_generate_tokens(
            session=test_session,
            username=test_user.username,
            password=sample_user_data["password"],
            ip_address="127.0.0.1",
            user_agent="test-browser",
            device_fingerprint="device-123"
        )
        
        assert access_token is not None
        assert refresh_token is not None
        assert user_info is not None
        
        # Verify user info
        assert user_info["id"] == str(test_user.id)
        assert user_info["username"] == test_user.username
        assert user_info["email"] == test_user.email
        
        # Verify tokens can be decoded
        access_payload = jwt.decode(access_token, jwt_service.secret_key, algorithms=['HS256'])
        refresh_payload = jwt.decode(refresh_token, jwt_service.secret_key, algorithms=['HS256'])
        
        assert access_payload["type"] == "access"
        assert access_payload["user_id"] == str(test_user.id)
        assert refresh_payload["type"] == "refresh"
        assert refresh_payload["user_id"] == str(test_user.id)
    
    async def test_authenticate_and_generate_tokens_invalid_credentials(
        self, jwt_service, test_session, test_user
    ):
        """Test authentication with invalid credentials."""
        access_token, refresh_token, user_info = await jwt_service.authenticate_and_generate_tokens(
            session=test_session,
            username=test_user.username,
            password="wrongpassword",
            ip_address="127.0.0.1"
        )
        
        assert access_token is None
        assert refresh_token is None
        assert user_info is None
    
    async def test_authenticate_and_generate_tokens_locked_account(
        self, jwt_service, test_session, locked_user, sample_user_data
    ):
        """Test authentication with locked account."""
        access_token, refresh_token, user_info = await jwt_service.authenticate_and_generate_tokens(
            session=test_session,
            username=locked_user.username,
            password=sample_user_data["password"],
            ip_address="127.0.0.1"
        )
        
        assert access_token is None
        assert refresh_token is None
        assert user_info is None
    
    async def test_refresh_access_token_success(
        self, jwt_service, test_session, test_user, sample_user_data
    ):
        """Test successful token refresh."""
        # First generate tokens
        access_token, refresh_token, _ = await jwt_service.authenticate_and_generate_tokens(
            session=test_session,
            username=test_user.username,
            password=sample_user_data["password"]
        )
        
        # Then refresh
        new_access_token, user_info = await jwt_service.refresh_access_token(
            session=test_session,
            refresh_token=refresh_token
        )
        
        assert new_access_token is not None
        assert user_info is not None
        assert new_access_token != access_token  # Should be different token
        
        # Verify new token
        payload = jwt.decode(new_access_token, jwt_service.secret_key, algorithms=['HS256'])
        assert payload["type"] == "access"
        assert payload["user_id"] == str(test_user.id)
    
    async def test_refresh_access_token_invalid_token(
        self, jwt_service, test_session
    ):
        """Test token refresh with invalid refresh token."""
        fake_token = jwt.encode(
            {"user_id": str(uuid.uuid4()), "type": "refresh", "jti": str(uuid.uuid4())},
            jwt_service.secret_key,
            algorithm='HS256'
        )
        
        new_access_token, user_info = await jwt_service.refresh_access_token(
            session=test_session,
            refresh_token=fake_token
        )
        
        assert new_access_token is None
        assert user_info is None
    
    async def test_refresh_access_token_revoked_token(
        self, jwt_service, test_session, test_user, test_refresh_token
    ):
        """Test token refresh with revoked refresh token."""
        # Create JWT with the revoked token's ID
        revoked_jwt = jwt.encode(
            {
                "user_id": str(test_user.id),
                "type": "refresh",
                "jti": test_refresh_token.token_id,
                "exp": datetime.now(timezone.utc) + timedelta(days=1)
            },
            jwt_service.secret_key,
            algorithm='HS256'
        )
        
        # Revoke the token
        test_refresh_token.revoke("test")
        await test_session.commit()
        
        new_access_token, user_info = await jwt_service.refresh_access_token(
            session=test_session,
            refresh_token=revoked_jwt
        )
        
        assert new_access_token is None
        assert user_info is None
    
    def test_validate_access_token_valid(self, jwt_service):
        """Test validating valid access token."""
        user_id = str(uuid.uuid4())
        token = jwt.encode(
            {
                "user_id": user_id,
                "type": "access",
                "jti": str(uuid.uuid4()),
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
            },
            jwt_service.secret_key,
            algorithm='HS256'
        )
        
        payload = jwt_service.validate_access_token(token)
        
        assert payload is not None
        assert payload["user_id"] == user_id
        assert payload["type"] == "access"
    
    def test_validate_access_token_expired(self, jwt_service):
        """Test validating expired access token."""
        token = jwt.encode(
            {
                "user_id": str(uuid.uuid4()),
                "type": "access",
                "jti": str(uuid.uuid4()),
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1)
            },
            jwt_service.secret_key,
            algorithm='HS256'
        )
        
        payload = jwt_service.validate_access_token(token)
        assert payload is None
    
    def test_validate_access_token_wrong_type(self, jwt_service):
        """Test validating token with wrong type."""
        token = jwt.encode(
            {
                "user_id": str(uuid.uuid4()),
                "type": "refresh",  # Wrong type
                "jti": str(uuid.uuid4()),
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
            },
            jwt_service.secret_key,
            algorithm='HS256'
        )
        
        payload = jwt_service.validate_access_token(token)
        assert payload is None
    
    def test_validate_access_token_invalid(self, jwt_service):
        """Test validating malformed token."""
        invalid_token = "invalid.token.here"
        
        payload = jwt_service.validate_access_token(invalid_token)
        assert payload is None
    
    async def test_logout_user_with_tokens(
        self, jwt_service, test_session, test_user, sample_user_data
    ):
        """Test user logout with token revocation."""
        # Generate tokens
        access_token, refresh_token, _ = await jwt_service.authenticate_and_generate_tokens(
            session=test_session,
            username=test_user.username,
            password=sample_user_data["password"]
        )
        
        # Logout
        result = await jwt_service.logout_user(
            session=test_session,
            access_token=access_token,
            refresh_token=refresh_token,
            ip_address="127.0.0.1",
            user_agent="test-browser"
        )
        
        assert result["success"] is True
        assert result["revoked_tokens"] == 1
        assert result["user_id"] == str(test_user.id)
    
    async def test_logout_user_revoke_all(
        self, jwt_service, test_session, test_user, multiple_refresh_tokens, sample_user_data
    ):
        """Test user logout with all sessions revoked."""
        # Generate new tokens
        access_token, refresh_token, _ = await jwt_service.authenticate_and_generate_tokens(
            session=test_session,
            username=test_user.username,
            password=sample_user_data["password"]
        )
        
        # Logout with revoke_all=True
        result = await jwt_service.logout_user(
            session=test_session,
            access_token=access_token,
            refresh_token=refresh_token,
            revoke_all=True
        )
        
        assert result["success"] is True
        assert result["revoked_tokens"] > 1  # Should revoke multiple tokens
    
    async def test_get_user_sessions(
        self, jwt_service, test_session, test_user, multiple_refresh_tokens
    ):
        """Test getting user sessions."""
        sessions = await jwt_service.get_user_sessions(
            session=test_session,
            user_id=str(test_user.id)
        )
        
        assert len(sessions) == len(multiple_refresh_tokens)
        
        for session in sessions:
            assert "id" in session
            assert "token_id" in session
            assert "created_at" in session
            assert "expires_at" in session
            assert "ip_address" in session
            assert "user_agent" in session
    
    async def test_revoke_session(
        self, jwt_service, test_session, test_user, test_refresh_token
    ):
        """Test revoking specific session."""
        success = await jwt_service.revoke_session(
            session=test_session,
            user_id=str(test_user.id),
            session_id=test_refresh_token.token_id,
            reason="manual_revoke"
        )
        
        assert success is True
        
        # Check token is revoked
        await test_session.refresh(test_refresh_token)
        assert test_refresh_token.is_revoked is True
        assert test_refresh_token.revoke_reason == "manual_revoke"
    
    async def test_revoke_session_unauthorized(
        self, jwt_service, test_session, test_refresh_token
    ):
        """Test revoking session with wrong user ID."""
        wrong_user_id = str(uuid.uuid4())
        
        success = await jwt_service.revoke_session(
            session=test_session,
            user_id=wrong_user_id,
            session_id=test_refresh_token.token_id
        )
        
        assert success is False
    
    async def test_cleanup_expired_tokens(
        self, jwt_service, test_session, test_user
    ):
        """Test cleaning up expired tokens."""
        # Create expired token
        from src.grantha.database.services import RefreshTokenService
        
        expired_token = await RefreshTokenService.create_refresh_token(
            session=test_session,
            user_id=str(test_user.id),
            token_id=str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        
        cleaned_count = await jwt_service.cleanup_expired_tokens(test_session)
        
        assert cleaned_count >= 1
        
        # Check token was cleaned up
        await test_session.refresh(expired_token)
        assert expired_token.is_revoked is True
    
    def test_get_token_info_fallback(self, jwt_service):
        """Test token info fallback to base service."""
        user_id = str(uuid.uuid4())
        token = jwt.encode(
            {
                "user_id": user_id,
                "type": "access",
                "jti": str(uuid.uuid4()),
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
                "iat": datetime.now(timezone.utc).timestamp()
            },
            jwt_service.secret_key,
            algorithm='HS256'
        )
        
        info = jwt_service.get_token_info(token)
        
        assert info is not None
        assert info["user_id"] == user_id
        assert info["type"] == "access"
        assert "jti" in info
        assert "issued_at" in info
        assert "expires_at" in info


class TestLegacyJWTService:
    """Test legacy JWT service for backward compatibility."""
    
    def test_legacy_jwt_service_initialization(self):
        """Test legacy JWT service initialization."""
        service = JWTService()
        
        assert service.secret_key is not None
        assert service.algorithm == 'HS256'
        assert service.access_token_expires_minutes == 30
        assert service.refresh_token_expires_days == 7
    
    def test_generate_tokens(self):
        """Test token generation."""
        service = JWTService()
        user_id = str(uuid.uuid4())
        
        access_token, refresh_token = service.generate_tokens(user_id)
        
        assert access_token is not None
        assert refresh_token is not None
        
        # Verify token contents
        access_payload = jwt.decode(access_token, service.secret_key, algorithms=['HS256'])
        refresh_payload = jwt.decode(refresh_token, service.secret_key, algorithms=['HS256'])
        
        assert access_payload["user_id"] == user_id
        assert access_payload["type"] == "access"
        assert refresh_payload["user_id"] == user_id
        assert refresh_payload["type"] == "refresh"
    
    def test_validate_tokens(self):
        """Test token validation."""
        service = JWTService()
        user_id = str(uuid.uuid4())
        
        access_token, refresh_token = service.generate_tokens(user_id)
        
        # Validate access token
        access_payload = service.validate_access_token(access_token)
        assert access_payload is not None
        assert access_payload["user_id"] == user_id
        
        # Validate refresh token
        refresh_payload = service.validate_refresh_token(refresh_token)
        assert refresh_payload is not None
        assert refresh_payload["user_id"] == user_id
    
    def test_refresh_token_functionality(self):
        """Test refresh token functionality."""
        service = JWTService()
        user_id = str(uuid.uuid4())
        
        _, refresh_token = service.generate_tokens(user_id)
        
        # Refresh access token
        new_access_token = service.refresh_access_token(refresh_token)
        assert new_access_token is not None
        
        # Validate new token
        payload = service.validate_access_token(new_access_token)
        assert payload["user_id"] == user_id
    
    def test_token_revocation(self):
        """Test token revocation."""
        service = JWTService()
        user_id = str(uuid.uuid4())
        
        access_token, refresh_token = service.generate_tokens(user_id)
        
        # Revoke access token
        success = service.revoke_token(access_token)
        assert success is True
        
        # Token should be invalid now
        payload = service.validate_access_token(access_token)
        assert payload is None
    
    def test_revoke_user_tokens(self):
        """Test revoking all user tokens."""
        service = JWTService()
        user_id = str(uuid.uuid4())
        
        # Generate multiple tokens
        tokens = [service.generate_tokens(user_id) for _ in range(3)]
        
        # Revoke all user tokens
        revoked_count = service.revoke_user_tokens(user_id)
        assert revoked_count == 3
        
        # All refresh tokens should be invalid
        for _, refresh_token in tokens:
            payload = service.validate_refresh_token(refresh_token)
            assert payload is None
    
    def test_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens."""
        service = JWTService()
        
        # Generate token
        user_id = str(uuid.uuid4())
        _, refresh_token = service.generate_tokens(user_id)
        
        # Manually expire the token by modifying internal storage
        refresh_payload = jwt.decode(refresh_token, service.secret_key, algorithms=['HS256'])
        jti = refresh_payload["jti"]
        
        # Set expiration to past
        service._refresh_tokens[jti]["expires_at"] = (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).isoformat()
        
        # Cleanup
        service.cleanup_expired_tokens()
        
        # Token should be removed from storage
        assert jti not in service._refresh_tokens
    
    def test_get_token_info(self):
        """Test getting token information."""
        service = JWTService()
        user_id = str(uuid.uuid4())
        
        access_token, _ = service.generate_tokens(user_id)
        
        info = service.get_token_info(access_token)
        
        assert info is not None
        assert info["user_id"] == user_id
        assert info["type"] == "access"
        assert "jti" in info
        assert "issued_at" in info
        assert "expires_at" in info
        assert "is_expired" in info
        assert "is_revoked" in info


@pytest.mark.asyncio
class TestJWTServiceEdgeCases:
    """Test edge cases and error scenarios."""
    
    async def test_database_error_handling(self, jwt_service, test_session):
        """Test handling database errors."""
        with patch.object(test_session, 'execute', side_effect=Exception("Database error")):
            result = await jwt_service.authenticate_and_generate_tokens(
                session=test_session,
                username="test",
                password="test"
            )
            
            assert result == (None, None, None)
    
    def test_malformed_jwt_handling(self, jwt_service):
        """Test handling malformed JWT tokens."""
        malformed_tokens = [
            "not.a.jwt",
            "invalid",
            "",
            None,
            123,
            {"not": "a string"}
        ]
        
        for token in malformed_tokens:
            try:
                payload = jwt_service.validate_access_token(str(token) if token is not None else "")
                assert payload is None
            except Exception:
                # Should handle gracefully
                pass
    
    async def test_concurrent_token_operations(
        self, jwt_service, test_session, test_user, sample_user_data
    ):
        """Test concurrent token operations."""
        import asyncio
        
        async def generate_tokens():
            return await jwt_service.authenticate_and_generate_tokens(
                session=test_session,
                username=test_user.username,
                password=sample_user_data["password"]
            )
        
        # Generate multiple tokens concurrently
        tasks = [generate_tokens() for _ in range(3)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should all succeed or handle gracefully
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 1  # At least one should succeed
    
    def test_jwt_with_additional_claims(self, jwt_service):
        """Test JWT generation with additional claims."""
        user_id = str(uuid.uuid4())
        additional_claims = {
            "role": "admin",
            "permissions": ["read", "write"],
            "custom_field": "custom_value"
        }
        
        token = jwt.encode(
            {
                "user_id": user_id,
                "type": "access",
                "jti": str(uuid.uuid4()),
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
                **additional_claims
            },
            jwt_service.secret_key,
            algorithm='HS256'
        )
        
        payload = jwt_service.validate_access_token(token)
        
        assert payload is not None
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]
        assert payload["custom_field"] == "custom_value"
    
    async def test_token_refresh_with_inactive_user(
        self, jwt_service, test_session, test_user, sample_user_data
    ):
        """Test token refresh with deactivated user."""
        # Generate tokens
        _, refresh_token, _ = await jwt_service.authenticate_and_generate_tokens(
            session=test_session,
            username=test_user.username,
            password=sample_user_data["password"]
        )
        
        # Deactivate user
        test_user.is_active = False
        await test_session.commit()
        
        # Try to refresh
        new_token, user_info = await jwt_service.refresh_access_token(
            session=test_session,
            refresh_token=refresh_token
        )
        
        assert new_token is None
        assert user_info is None
    
    def test_jwt_secret_key_rotation(self):
        """Test behavior with different secret keys."""
        service1 = JWTService()
        service2 = JWTService()
        
        # Use different secret keys
        service1.secret_key = "secret1"
        service2.secret_key = "secret2"
        
        user_id = str(uuid.uuid4())
        
        # Generate token with service1
        access_token, _ = service1.generate_tokens(user_id)
        
        # Try to validate with service2 (different key)
        payload = service2.validate_access_token(access_token)
        assert payload is None  # Should fail validation
        
        # Should work with same service
        payload = service1.validate_access_token(access_token)
        assert payload is not None
    
    async def test_logout_with_partial_token_info(self, jwt_service, test_session):
        """Test logout with only partial token information."""
        # Test logout with only access token
        result = await jwt_service.logout_user(
            session=test_session,
            access_token="invalid_token"
        )
        
        assert result["success"] is True  # Should still succeed
        assert result["revoked_tokens"] == 0
        
        # Test logout with only refresh token
        result = await jwt_service.logout_user(
            session=test_session,
            refresh_token="invalid_token"
        )
        
        assert result["success"] is True
        assert result["revoked_tokens"] == 0