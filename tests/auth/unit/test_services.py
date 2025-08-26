"""Unit tests for authentication database services."""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from src.grantha.database.services import UserService, RefreshTokenService, AuthEventService
from src.grantha.database.models import User, RefreshToken, AuthEvent


@pytest.mark.asyncio
class TestUserService:
    """Test UserService functionality."""
    
    async def test_create_user(self, test_session, sample_user_data):
        """Test user creation."""
        user = await UserService.create_user(
            session=test_session,
            **sample_user_data
        )
        
        assert user.username == sample_user_data["username"]
        assert user.email == sample_user_data["email"]
        assert user.full_name == sample_user_data["full_name"]
        assert user.bio == sample_user_data["bio"]
        assert user.is_active is True
        assert user.is_verified is False
        assert user.is_superuser is False
        assert user.verify_password(sample_user_data["password"])
    
    async def test_create_user_duplicate_username(self, test_session, sample_user_data):
        """Test creating user with duplicate username fails."""
        # Create first user
        await UserService.create_user(session=test_session, **sample_user_data)
        
        # Try to create duplicate
        with pytest.raises(Exception):  # Should raise IntegrityError
            await UserService.create_user(session=test_session, **sample_user_data)
    
    async def test_create_user_duplicate_email(self, test_session, sample_user_data):
        """Test creating user with duplicate email fails."""
        # Create first user
        await UserService.create_user(session=test_session, **sample_user_data)
        
        # Try to create user with same email but different username
        duplicate_data = sample_user_data.copy()
        duplicate_data["username"] = "different_username"
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            await UserService.create_user(session=test_session, **duplicate_data)
    
    async def test_get_user_by_id(self, test_session, test_user):
        """Test getting user by ID."""
        user_id = str(test_user.id)
        retrieved_user = await UserService.get_user_by_id(test_session, user_id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == test_user.id
        assert retrieved_user.username == test_user.username
    
    async def test_get_user_by_id_not_found(self, test_session):
        """Test getting non-existent user by ID."""
        fake_id = str(uuid.uuid4())
        user = await UserService.get_user_by_id(test_session, fake_id)
        assert user is None
    
    async def test_get_user_by_username(self, test_session, test_user):
        """Test getting user by username."""
        user = await UserService.get_user_by_username(test_session, test_user.username)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.username == test_user.username
    
    async def test_get_user_by_email(self, test_session, test_user):
        """Test getting user by email."""
        user = await UserService.get_user_by_email(test_session, test_user.email)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
    
    async def test_authenticate_user_success(self, test_session, test_user, sample_user_data):
        """Test successful user authentication."""
        user, success = await UserService.authenticate_user(
            session=test_session,
            username=test_user.username,
            password=sample_user_data["password"],
            ip_address="127.0.0.1",
            user_agent="test-browser"
        )
        
        assert success is True
        assert user is not None
        assert user.id == test_user.id
        assert user.last_login is not None
        assert user.failed_login_attempts == "0"
    
    async def test_authenticate_user_by_email(self, test_session, test_user, sample_user_data):
        """Test authentication using email instead of username."""
        user, success = await UserService.authenticate_user(
            session=test_session,
            username=test_user.email,  # Using email as username
            password=sample_user_data["password"],
            ip_address="127.0.0.1"
        )
        
        assert success is True
        assert user is not None
        assert user.id == test_user.id
    
    async def test_authenticate_user_wrong_password(self, test_session, test_user):
        """Test authentication with wrong password."""
        user, success = await UserService.authenticate_user(
            session=test_session,
            username=test_user.username,
            password="wrongpassword",
            ip_address="127.0.0.1"
        )
        
        assert success is False
        assert user is not None  # User object returned even on failure
        assert int(user.failed_login_attempts) > 0  # Failed attempts incremented
    
    async def test_authenticate_user_not_found(self, test_session):
        """Test authentication with non-existent user."""
        user, success = await UserService.authenticate_user(
            session=test_session,
            username="nonexistent",
            password="anypassword",
            ip_address="127.0.0.1"
        )
        
        assert success is False
        assert user is None
    
    async def test_authenticate_locked_user(self, test_session, locked_user, sample_user_data):
        """Test authentication with locked user account."""
        user, success = await UserService.authenticate_user(
            session=test_session,
            username=locked_user.username,
            password=sample_user_data["password"],
            ip_address="127.0.0.1"
        )
        
        assert success is False
        assert user is not None
        assert user.is_locked()
    
    async def test_update_user(self, test_session, test_user):
        """Test updating user information."""
        updates = {
            "full_name": "Updated Name",
            "bio": "Updated bio",
            "email": "updated@example.com"
        }
        
        updated_user = await UserService.update_user(
            session=test_session,
            user_id=str(test_user.id),
            **updates
        )
        
        assert updated_user is not None
        assert updated_user.full_name == "Updated Name"
        assert updated_user.bio == "Updated bio"
        assert updated_user.email == "updated@example.com"
    
    async def test_update_user_password(self, test_session, test_user):
        """Test updating user password."""
        new_password = "newpassword123"
        
        updated_user = await UserService.update_user(
            session=test_session,
            user_id=str(test_user.id),
            password=new_password
        )
        
        assert updated_user is not None
        assert updated_user.verify_password(new_password)
        assert not updated_user.verify_password("testpass123")  # Old password
    
    async def test_deactivate_user(self, test_session, test_user, multiple_refresh_tokens):
        """Test deactivating user account."""
        success = await UserService.deactivate_user(
            session=test_session,
            user_id=str(test_user.id)
        )
        
        assert success is True
        
        # Check user is deactivated
        deactivated_user = await UserService.get_user_by_id(test_session, str(test_user.id))
        assert deactivated_user.is_active is False
        
        # Check refresh tokens are revoked
        for token in multiple_refresh_tokens:
            await test_session.refresh(token)
            assert token.is_revoked is True
    
    async def test_list_users(self, test_session, multiple_users):
        """Test listing users with pagination."""
        users = await UserService.list_users(
            session=test_session,
            limit=3,
            offset=0,
            active_only=True
        )
        
        assert len(users) == 3
        assert all(user.is_active for user in users)
        
        # Test pagination
        more_users = await UserService.list_users(
            session=test_session,
            limit=5,
            offset=2
        )
        
        assert len(more_users) == 3  # Remaining users


@pytest.mark.asyncio
class TestRefreshTokenService:
    """Test RefreshTokenService functionality."""
    
    async def test_create_refresh_token(self, test_session, test_user):
        """Test creating refresh token."""
        token_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        token = await RefreshTokenService.create_refresh_token(
            session=test_session,
            user_id=str(test_user.id),
            token_id=token_id,
            expires_at=expires_at,
            ip_address="127.0.0.1",
            user_agent="test-browser",
            device_fingerprint="device-123"
        )
        
        assert token.token_id == token_id
        assert token.user_id == test_user.id
        assert token.expires_at == expires_at
        assert token.ip_address == "127.0.0.1"
        assert token.user_agent == "test-browser"
        assert token.device_fingerprint == "device-123"
        assert token.is_active is True
    
    async def test_get_refresh_token(self, test_session, test_refresh_token):
        """Test getting refresh token by ID."""
        token = await RefreshTokenService.get_refresh_token(
            session=test_session,
            token_id=test_refresh_token.token_id
        )
        
        assert token is not None
        assert token.id == test_refresh_token.id
        assert token.token_id == test_refresh_token.token_id
    
    async def test_validate_refresh_token_valid(self, test_session, test_refresh_token):
        """Test validating valid refresh token."""
        token = await RefreshTokenService.validate_refresh_token(
            session=test_session,
            token_id=test_refresh_token.token_id
        )
        
        assert token is not None
        assert token.is_valid()
    
    async def test_validate_refresh_token_revoked(self, test_session, test_refresh_token):
        """Test validating revoked refresh token."""
        # Revoke the token first
        test_refresh_token.revoke("test")
        await test_session.commit()
        
        token = await RefreshTokenService.validate_refresh_token(
            session=test_session,
            token_id=test_refresh_token.token_id
        )
        
        assert token is None  # Should return None for invalid token
    
    async def test_validate_refresh_token_expired(self, test_session, test_user):
        """Test validating expired refresh token."""
        # Create expired token
        token_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) - timedelta(days=1)  # Expired
        
        expired_token = await RefreshTokenService.create_refresh_token(
            session=test_session,
            user_id=str(test_user.id),
            token_id=token_id,
            expires_at=expires_at
        )
        
        token = await RefreshTokenService.validate_refresh_token(
            session=test_session,
            token_id=token_id
        )
        
        assert token is None  # Should return None for expired token
    
    async def test_revoke_refresh_token(self, test_session, test_refresh_token):
        """Test revoking refresh token."""
        success = await RefreshTokenService.revoke_refresh_token(
            session=test_session,
            token_id=test_refresh_token.token_id,
            reason="manual_revoke"
        )
        
        assert success is True
        
        # Refresh token from database
        await test_session.refresh(test_refresh_token)
        assert test_refresh_token.is_revoked is True
        assert test_refresh_token.revoke_reason == "manual_revoke"
        assert test_refresh_token.revoked_at is not None
    
    async def test_revoke_all_user_tokens(self, test_session, test_user, multiple_refresh_tokens):
        """Test revoking all tokens for a user."""
        revoked_count = await RefreshTokenService.revoke_all_user_tokens(
            session=test_session,
            user_id=str(test_user.id),
            reason="logout_all"
        )
        
        assert revoked_count == len(multiple_refresh_tokens)
        
        # Check all tokens are revoked
        for token in multiple_refresh_tokens:
            await test_session.refresh(token)
            assert token.is_revoked is True
            assert token.revoke_reason == "logout_all"
    
    async def test_cleanup_expired_tokens(self, test_session, test_user):
        """Test cleaning up expired tokens."""
        # Create a mix of valid and expired tokens
        valid_token = await RefreshTokenService.create_refresh_token(
            session=test_session,
            user_id=str(test_user.id),
            token_id=str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        
        expired_token = await RefreshTokenService.create_refresh_token(
            session=test_session,
            user_id=str(test_user.id),
            token_id=str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        
        cleanup_count = await RefreshTokenService.cleanup_expired_tokens(test_session)
        
        assert cleanup_count == 1  # Only expired token should be cleaned up
        
        # Check tokens
        await test_session.refresh(valid_token)
        await test_session.refresh(expired_token)
        
        assert valid_token.is_revoked is False
        assert expired_token.is_revoked is True
        assert expired_token.revoke_reason == "expired"
    
    async def test_get_user_active_tokens(self, test_session, test_user, multiple_refresh_tokens):
        """Test getting active tokens for a user."""
        # Revoke one token
        await RefreshTokenService.revoke_refresh_token(
            session=test_session,
            token_id=multiple_refresh_tokens[0].token_id,
            reason="test"
        )
        
        active_tokens = await RefreshTokenService.get_user_active_tokens(
            session=test_session,
            user_id=str(test_user.id),
            limit=10
        )
        
        assert len(active_tokens) == len(multiple_refresh_tokens) - 1
        assert all(token.is_active for token in active_tokens)


@pytest.mark.asyncio
class TestAuthEventService:
    """Test AuthEventService functionality."""
    
    async def test_log_event(self, test_session, test_user):
        """Test logging auth events."""
        event = await AuthEventService.log_event(
            session=test_session,
            event_type="login",
            user_id=str(test_user.id),
            success=True,
            ip_address="127.0.0.1",
            user_agent="test-browser",
            event_metadata={"device": "mobile"}
        )
        
        assert event.event_type == "login"
        assert event.user_id == test_user.id
        assert event.success is True
        assert event.ip_address == "127.0.0.1"
        assert event.user_agent == "test-browser"
        assert "device" in event.event_metadata
    
    async def test_log_event_failed_login(self, test_session):
        """Test logging failed login event without user ID."""
        event = await AuthEventService.log_event(
            session=test_session,
            event_type="login",
            user_id=None,
            success=False,
            failure_reason="user_not_found",
            ip_address="127.0.0.1"
        )
        
        assert event.user_id is None
        assert event.success is False
        assert event.failure_reason == "user_not_found"
    
    async def test_get_user_events(self, test_session, test_user):
        """Test getting events for a user."""
        # Create multiple events
        await AuthEventService.log_event(
            session=test_session,
            event_type="login",
            user_id=str(test_user.id),
            success=True
        )
        
        await AuthEventService.log_event(
            session=test_session,
            event_type="logout",
            user_id=str(test_user.id),
            success=True
        )
        
        await AuthEventService.log_event(
            session=test_session,
            event_type="password_change",
            user_id=str(test_user.id),
            success=True
        )
        
        # Get all events
        events = await AuthEventService.get_user_events(
            session=test_session,
            user_id=str(test_user.id),
            limit=10
        )
        
        assert len(events) == 3
        assert all(event.user_id == test_user.id for event in events)
        
        # Get specific event type
        login_events = await AuthEventService.get_user_events(
            session=test_session,
            user_id=str(test_user.id),
            event_type="login"
        )
        
        assert len(login_events) == 1
        assert login_events[0].event_type == "login"
    
    async def test_get_security_events(self, test_session, test_user):
        """Test getting security-relevant events."""
        # Create various events
        await AuthEventService.log_event(
            session=test_session,
            event_type="login",
            user_id=str(test_user.id),
            success=False,
            failure_reason="invalid_password"
        )
        
        await AuthEventService.log_event(
            session=test_session,
            event_type="login",
            user_id=str(test_user.id),
            success=True
        )
        
        await AuthEventService.log_event(
            session=test_session,
            event_type="password_change",
            user_id=str(test_user.id),
            success=True
        )
        
        security_events = await AuthEventService.get_security_events(
            session=test_session,
            hours_back=24,
            limit=10
        )
        
        assert len(security_events) == 3  # All events are security-relevant
        
        # Should include failed and successful events
        event_types = [event.event_type for event in security_events]
        assert "login" in event_types
        assert "password_change" in event_types
    
    async def test_get_failed_login_stats(self, test_session, test_user, cleanup_auth_events):
        """Test getting failed login statistics."""
        # Create various login events
        await AuthEventService.log_event(
            session=test_session,
            event_type="login",
            user_id=None,
            success=False,
            failure_reason="user_not_found"
        )
        
        await AuthEventService.log_event(
            session=test_session,
            event_type="login",
            user_id=str(test_user.id),
            success=False,
            failure_reason="invalid_password"
        )
        
        await AuthEventService.log_event(
            session=test_session,
            event_type="login",
            user_id=str(test_user.id),
            success=True
        )
        
        stats = await AuthEventService.get_failed_login_stats(
            session=test_session,
            hours_back=24
        )
        
        assert stats["failed_logins"] == 2
        assert stats["successful_logins"] == 1
        assert stats["failure_rate"] == 66.67  # 2/3 * 100
        assert len(stats["top_failure_reasons"]) > 0
        
        # Check failure reasons
        reasons = [r["reason"] for r in stats["top_failure_reasons"]]
        assert "user_not_found" in reasons
        assert "invalid_password" in reasons


@pytest.mark.asyncio
class TestServiceErrorHandling:
    """Test error handling in services."""
    
    async def test_user_service_database_error(self, test_session):
        """Test handling database errors in UserService."""
        # Try to create user with invalid data
        with patch.object(test_session, 'commit', side_effect=Exception("Database error")):
            with pytest.raises(Exception):
                await UserService.create_user(
                    session=test_session,
                    username="test",
                    password="test"
                )
    
    async def test_refresh_token_service_invalid_user_id(self, test_session):
        """Test RefreshTokenService with invalid user ID."""
        invalid_user_id = "invalid-uuid"
        
        with pytest.raises(Exception):  # Should raise ValueError for invalid UUID
            await RefreshTokenService.create_refresh_token(
                session=test_session,
                user_id=invalid_user_id,
                token_id=str(uuid.uuid4()),
                expires_at=datetime.now(timezone.utc) + timedelta(days=7)
            )
    
    async def test_auth_event_service_invalid_metadata(self, test_session, test_user):
        """Test AuthEventService with invalid metadata."""
        # Non-serializable metadata should still work (converted to string)
        event = await AuthEventService.log_event(
            session=test_session,
            event_type="test",
            user_id=str(test_user.id),
            success=True,
            event_metadata={"complex": {"nested": "data"}}
        )
        
        assert event.event_metadata is not None


@pytest.mark.asyncio
class TestServiceConcurrency:
    """Test concurrent operations on services."""
    
    async def test_concurrent_user_creation(self, test_session, user_data_factory):
        """Test concurrent user creation."""
        import asyncio
        
        # Create multiple users concurrently
        tasks = []
        for i in range(5):
            user_data = user_data_factory(username=f"concurrent_user_{i}")
            task = UserService.create_user(session=test_session, **user_data)
            tasks.append(task)
        
        # Should all succeed
        users = await asyncio.gather(*tasks)
        assert len(users) == 5
        assert all(user.username.startswith("concurrent_user_") for user in users)
    
    async def test_concurrent_token_operations(self, test_session, test_user):
        """Test concurrent token operations."""
        import asyncio
        
        # Create tokens concurrently
        create_tasks = []
        for i in range(3):
            task = RefreshTokenService.create_refresh_token(
                session=test_session,
                user_id=str(test_user.id),
                token_id=f"concurrent_token_{i}",
                expires_at=datetime.now(timezone.utc) + timedelta(days=7)
            )
            create_tasks.append(task)
        
        tokens = await asyncio.gather(*create_tasks)
        assert len(tokens) == 3
        
        # Revoke tokens concurrently
        revoke_tasks = [
            RefreshTokenService.revoke_refresh_token(
                session=test_session,
                token_id=token.token_id,
                reason="concurrent_test"
            )
            for token in tokens
        ]
        
        results = await asyncio.gather(*revoke_tasks)
        assert all(results)  # All should succeed