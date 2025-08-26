"""Unit tests for authentication database models."""

import pytest
import uuid
from datetime import datetime, timezone, timedelta

from src.grantha.database.models import User, RefreshToken, AuthEvent


class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation_with_password(self, sample_user_data):
        """Test user creation with password hashing."""
        user = User(**sample_user_data)
        
        assert user.username == sample_user_data["username"]
        assert user.email == sample_user_data["email"]
        assert user.password_hash != sample_user_data["password"]  # Should be hashed
        assert user.verify_password(sample_user_data["password"])  # Should verify correctly
        assert not user.verify_password("wrongpassword")  # Should reject wrong password
    
    def test_user_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpass123"
        user = User(username="test", password=password)
        
        # Password should be hashed
        assert user.password_hash != password
        assert len(user.password_hash) > 0
        
        # Should verify correct password
        assert user.verify_password(password)
        
        # Should reject incorrect password
        assert not user.verify_password("wrongpass")
    
    def test_user_set_password(self):
        """Test setting a new password."""
        user = User(username="test", password="oldpass")
        old_hash = user.password_hash
        
        user.set_password("newpass")
        
        assert user.password_hash != old_hash
        assert user.verify_password("newpass")
        assert not user.verify_password("oldpass")
    
    def test_user_validation(self):
        """Test user field validation."""
        # Test username validation
        with pytest.raises(ValueError, match="Username must be at least 3 characters"):
            User(username="ab", password="test")
        
        with pytest.raises(ValueError, match="Username must be less than 50 characters"):
            User(username="a" * 51, password="test")
        
        # Test email validation
        with pytest.raises(ValueError, match="Invalid email address"):
            User(username="test", email="invalid-email", password="test")
    
    def test_user_account_locking(self):
        """Test account locking functionality."""
        user = User(username="test", password="test")
        
        # Initially not locked
        assert not user.is_locked()
        
        # Increment failed login attempts
        user.increment_failed_login(max_attempts=3)
        assert not user.is_locked()  # Should not be locked yet
        
        user.increment_failed_login(max_attempts=3)
        user.increment_failed_login(max_attempts=3)
        assert user.is_locked()  # Should be locked after 3 attempts
        
        # Test lockout expiration
        user.locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
        assert not user.is_locked()  # Lock should have expired
    
    def test_user_login_tracking(self):
        """Test login tracking functionality."""
        user = User(username="test", password="test")
        
        # Initially no login data
        assert user.last_login is None
        assert user.failed_login_attempts == "0"
        
        # Update last login
        user.update_last_login()
        assert user.last_login is not None
        assert user.failed_login_attempts == "0"
        assert user.locked_until is None
    
    def test_user_token_generation(self):
        """Test token generation for email verification and password reset."""
        user = User(username="test", password="test", email="test@example.com")
        
        # Test verification token
        token = user.generate_verification_token()
        assert token is not None
        assert user.verification_token == token
        assert user.verification_sent_at is not None
        
        # Test email verification
        assert user.verify_email(token)
        assert user.is_verified
        assert user.verified_at is not None
        assert user.verification_token is None
        
        # Test password reset token
        reset_token = user.generate_reset_token()
        assert reset_token is not None
        assert user.reset_token == reset_token
        assert user.reset_token_expires is not None
        
        # Test password reset
        new_password = "newpassword"
        assert user.reset_password(reset_token, new_password)
        assert user.verify_password(new_password)
        assert user.reset_token is None
        assert user.reset_token_expires is None
    
    def test_user_to_dict(self):
        """Test user serialization to dictionary."""
        user = User(
            username="test",
            email="test@example.com",
            password="test",
            full_name="Test User"
        )
        
        # Test basic serialization
        data = user.to_dict()
        assert data["username"] == "test"
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert "password_hash" not in data  # Should not include sensitive data
        
        # Test sensitive data inclusion
        sensitive_data = user.to_dict(include_sensitive=True)
        assert "failed_login_attempts" in sensitive_data
        assert "is_locked" in sensitive_data


class TestRefreshTokenModel:
    """Test RefreshToken model functionality."""
    
    def test_refresh_token_creation(self):
        """Test refresh token creation."""
        user_id = uuid.uuid4()
        token_id = "test-token-123"
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        token = RefreshToken(
            token_id=token_id,
            user_id=user_id,
            expires_at=expires_at,
            ip_address="127.0.0.1",
            user_agent="test-browser"
        )
        
        assert token.token_id == token_id
        assert token.user_id == user_id
        assert token.expires_at == expires_at
        assert token.is_active is True
        assert token.is_revoked is False
    
    def test_refresh_token_validation(self):
        """Test refresh token validation logic."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        token = RefreshToken(
            token_id="test-token",
            user_id=uuid.uuid4(),
            expires_at=expires_at
        )
        
        # Should be valid initially
        assert token.is_valid()
        assert not token.is_expired()
        
        # Test expiration
        token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        assert token.is_expired()
        assert not token.is_valid()  # Should be invalid when expired
        
        # Test revocation
        token.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        token.revoke("manual")
        assert not token.is_valid()  # Should be invalid when revoked
        assert token.is_revoked
        assert token.revoked_at is not None
        assert token.revoke_reason == "manual"
    
    def test_refresh_token_revocation(self):
        """Test refresh token revocation."""
        token = RefreshToken(
            token_id="test-token",
            user_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        
        # Initially active
        assert token.is_active
        assert not token.is_revoked
        assert token.revoked_at is None
        
        # Revoke token
        reason = "security_breach"
        token.revoke(reason)
        
        assert not token.is_active
        assert token.is_revoked
        assert token.revoked_at is not None
        assert token.revoke_reason == reason
    
    def test_refresh_token_to_dict(self):
        """Test refresh token serialization."""
        token = RefreshToken(
            token_id="test-token",
            user_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        data = token.to_dict()
        
        assert data["token_id"] == "test-token"
        assert data["ip_address"] == "192.168.1.1"
        assert data["user_agent"] == "Mozilla/5.0"
        assert data["is_active"] is True
        assert data["is_revoked"] is False
        assert "expires_at" in data
        assert "is_expired" in data
        assert "is_valid" in data


class TestAuthEventModel:
    """Test AuthEvent model functionality."""
    
    def test_auth_event_creation(self):
        """Test auth event creation."""
        user_id = uuid.uuid4()
        event = AuthEvent(
            user_id=user_id,
            event_type="login",
            success=True,
            ip_address="127.0.0.1",
            user_agent="test-browser"
        )
        
        assert event.user_id == user_id
        assert event.event_type == "login"
        assert event.success is True
        assert event.ip_address == "127.0.0.1"
        assert event.user_agent == "test-browser"
    
    def test_auth_event_factory_methods(self):
        """Test auth event factory methods."""
        user_id = str(uuid.uuid4())
        
        # Test login event
        login_event = AuthEvent.create_login_event(
            user_id=user_id,
            success=True,
            ip_address="127.0.0.1"
        )
        assert login_event.event_type == "login"
        assert login_event.success is True
        assert login_event.user_id == user_id
        
        # Test failed login event
        failed_login = AuthEvent.create_login_event(
            user_id=None,  # No user ID for failed login
            success=False,
            failure_reason="invalid_credentials",
            ip_address="127.0.0.1"
        )
        assert failed_login.event_type == "login"
        assert failed_login.success is False
        assert failed_login.failure_reason == "invalid_credentials"
        assert failed_login.user_id is None
        
        # Test logout event
        logout_event = AuthEvent.create_logout_event(
            user_id=user_id,
            ip_address="127.0.0.1"
        )
        assert logout_event.event_type == "logout"
        assert logout_event.success is True
        assert logout_event.user_id == user_id
        
        # Test password change event
        pwd_change = AuthEvent.create_password_change_event(
            user_id=user_id,
            success=True,
            ip_address="127.0.0.1"
        )
        assert pwd_change.event_type == "password_change"
        assert pwd_change.success is True
        assert pwd_change.user_id == user_id
    
    def test_auth_event_to_dict(self):
        """Test auth event serialization."""
        event = AuthEvent(
            user_id=uuid.uuid4(),
            event_type="login",
            success=True,
            ip_address="127.0.0.1",
            user_agent="test-browser",
            failure_reason=None,
            event_metadata='{"device": "mobile"}'
        )
        
        data = event.to_dict()
        
        assert data["event_type"] == "login"
        assert data["success"] is True
        assert data["ip_address"] == "127.0.0.1"
        assert data["user_agent"] == "test-browser"
        assert data["event_metadata"] == '{"device": "mobile"}'
        assert "created_at" in data
    
    def test_auth_event_metadata_handling(self):
        """Test auth event metadata handling."""
        metadata = {"device": "mobile", "location": "home"}
        
        event = AuthEvent(
            user_id=uuid.uuid4(),
            event_type="login",
            success=True,
            event_metadata=str(metadata)
        )
        
        assert event.event_metadata == str(metadata)
        
        # Test with None metadata
        event_no_meta = AuthEvent(
            user_id=uuid.uuid4(),
            event_type="logout",
            success=True
        )
        
        assert event_no_meta.event_metadata is None


class TestModelRelationships:
    """Test model relationships."""
    
    def test_user_refresh_token_relationship(self):
        """Test User-RefreshToken relationship."""
        user = User(username="test", password="test")
        
        # Create refresh tokens
        token1 = RefreshToken(
            token_id="token1",
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        token2 = RefreshToken(
            token_id="token2",
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        
        # Note: In actual testing with database, these relationships would work
        # Here we're just testing the model structure
        assert hasattr(user, 'refresh_tokens')
        assert hasattr(token1, 'user')
    
    def test_user_auth_event_relationship(self):
        """Test User-AuthEvent relationship."""
        user = User(username="test", password="test")
        
        event = AuthEvent(
            user_id=user.id,
            event_type="login",
            success=True
        )
        
        # Test relationship attributes exist
        assert hasattr(user, 'auth_events')
        assert hasattr(event, 'user')


class TestModelValidationEdgeCases:
    """Test edge cases and validation scenarios."""
    
    def test_user_password_edge_cases(self):
        """Test password validation edge cases."""
        # Test empty password
        with pytest.raises(Exception):  # Model validation should prevent this
            User(username="test", password="")
        
        # Test very long password (should be handled)
        long_password = "a" * 1000
        user = User(username="test", password=long_password)
        assert user.verify_password(long_password)
    
    def test_token_expiration_edge_cases(self):
        """Test token expiration edge cases."""
        # Token that expires exactly now
        token = RefreshToken(
            token_id="test",
            user_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc)
        )
        
        # Should be considered expired (>= comparison)
        assert token.is_expired()
        
        # Token that expires in 1 microsecond
        token.expires_at = datetime.now(timezone.utc) + timedelta(microseconds=1)
        assert not token.is_expired()
    
    def test_user_lockout_edge_cases(self):
        """Test user account lockout edge cases."""
        user = User(username="test", password="test")
        
        # Test lockout with zero max attempts
        user.increment_failed_login(max_attempts=0)
        assert user.is_locked()
        
        # Test lockout duration of zero
        user.increment_failed_login(max_attempts=1, lockout_duration_minutes=0)
        # Should still lock for the minimum duration
        assert user.locked_until is not None
    
    def test_auth_event_large_metadata(self):
        """Test auth event with large metadata."""
        large_metadata = {"data": "x" * 10000}
        
        event = AuthEvent(
            user_id=uuid.uuid4(),
            event_type="test",
            success=True,
            event_metadata=str(large_metadata)
        )
        
        assert len(event.event_metadata) > 10000
        assert event.to_dict()["event_metadata"] == str(large_metadata)