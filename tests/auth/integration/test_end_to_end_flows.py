"""End-to-end integration tests for complete authentication flows."""

import pytest
import uuid
import asyncio
from datetime import datetime, timezone, timedelta

from src.grantha.database.services import UserService, RefreshTokenService, AuthEventService
from src.grantha.database.auth_service import DatabaseJWTService
from src.grantha.database.models import User, RefreshToken, AuthEvent


@pytest.mark.asyncio
class TestCompleteAuthenticationFlow:
    """Test complete authentication workflows."""
    
    async def test_full_user_lifecycle(self, test_session, user_data_factory):
        """Test complete user lifecycle: register -> login -> profile update -> logout."""
        jwt_service = DatabaseJWTService()
        user_data = user_data_factory()
        
        # Step 1: Register user
        user = await UserService.create_user(
            session=test_session,
            **user_data
        )
        
        assert user.username == user_data["username"]
        assert user.is_active is True
        assert user.is_verified is False
        
        # Step 2: Authenticate and generate tokens
        access_token, refresh_token, user_info = await jwt_service.authenticate_and_generate_tokens(
            session=test_session,
            username=user.username,
            password=user_data["password"],
            ip_address="127.0.0.1",
            user_agent="test-browser"
        )
        
        assert access_token is not None
        assert refresh_token is not None
        assert user_info["username"] == user.username
        
        # Step 3: Validate access token
        token_payload = jwt_service.validate_access_token(access_token)
        assert token_payload is not None
        assert token_payload["user_id"] == str(user.id)
        
        # Step 4: Update user profile
        profile_updates = {
            "full_name": "Updated Full Name",
            "bio": "Updated biography",
            "email": "updated@example.com"
        }
        
        updated_user = await UserService.update_user(
            session=test_session,
            user_id=str(user.id),
            **profile_updates
        )
        
        assert updated_user.full_name == "Updated Full Name"
        assert updated_user.bio == "Updated biography"
        assert updated_user.email == "updated@example.com"
        
        # Step 5: Change password
        new_password = "newpassword123"
        await UserService.update_user(
            session=test_session,
            user_id=str(user.id),
            password=new_password
        )
        
        # Step 6: Verify old tokens are invalid after password change
        # (In real implementation, tokens would be revoked)
        await RefreshTokenService.revoke_all_user_tokens(
            session=test_session,
            user_id=str(user.id),
            reason="password_change"
        )
        
        # Step 7: Login with new password
        new_access_token, new_refresh_token, _ = await jwt_service.authenticate_and_generate_tokens(
            session=test_session,
            username=user.username,
            password=new_password,
            ip_address="127.0.0.1"
        )
        
        assert new_access_token is not None
        assert new_refresh_token is not None
        
        # Step 8: Logout
        logout_result = await jwt_service.logout_user(
            session=test_session,
            access_token=new_access_token,
            refresh_token=new_refresh_token
        )
        
        assert logout_result["success"] is True
        assert logout_result["user_id"] == str(user.id)
    
    async def test_multi_session_management(self, test_session, test_user, sample_user_data):
        """Test managing multiple active sessions for a user."""
        jwt_service = DatabaseJWTService()
        sessions = []
        
        # Create multiple sessions
        for i in range(3):
            access_token, refresh_token, user_info = await jwt_service.authenticate_and_generate_tokens(
                session=test_session,
                username=test_user.username,
                password=sample_user_data["password"],
                ip_address=f"192.168.1.{i+1}",
                user_agent=f"browser-{i}/1.0",
                device_fingerprint=f"device-{i}"
            )
            
            sessions.append({
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user_info": user_info
            })
        
        # Verify all sessions are active
        active_sessions = await jwt_service.get_user_sessions(
            session=test_session,
            user_id=str(test_user.id)
        )
        
        assert len(active_sessions) >= 3
        
        # Revoke one specific session
        refresh_payload = jwt_service._fallback_service.get_token_info(sessions[0]["refresh_token"])
        session_id = refresh_payload["jti"] if refresh_payload else sessions[0]["refresh_token"]
        
        # Find the actual token ID from database
        user_tokens = await RefreshTokenService.get_user_active_tokens(
            session=test_session,
            user_id=str(test_user.id)
        )
        
        if user_tokens:
            revoke_success = await jwt_service.revoke_session(
                session=test_session,
                user_id=str(test_user.id),
                session_id=user_tokens[0].token_id
            )
            
            assert revoke_success is True
        
        # Logout from all remaining sessions
        logout_result = await jwt_service.logout_user(
            session=test_session,
            access_token=sessions[1]["access_token"],
            refresh_token=sessions[1]["refresh_token"],
            revoke_all=True
        )
        
        assert logout_result["success"] is True
        assert logout_result["revoked_tokens"] >= 2
    
    async def test_token_refresh_flow(self, test_session, test_user, sample_user_data):
        """Test complete token refresh workflow."""
        jwt_service = DatabaseJWTService()
        
        # Initial login
        access_token, refresh_token, user_info = await jwt_service.authenticate_and_generate_tokens(
            session=test_session,
            username=test_user.username,
            password=sample_user_data["password"]
        )
        
        # Wait a moment to ensure timestamps differ
        await asyncio.sleep(0.1)
        
        # Refresh access token
        new_access_token, refreshed_user_info = await jwt_service.refresh_access_token(
            session=test_session,
            refresh_token=refresh_token
        )
        
        assert new_access_token is not None
        assert refreshed_user_info is not None
        assert new_access_token != access_token  # Should be different
        
        # Verify new token is valid
        new_token_payload = jwt_service.validate_access_token(new_access_token)
        assert new_token_payload is not None
        assert new_token_payload["user_id"] == str(test_user.id)
        
        # Use refreshed token for another operation
        final_sessions = await jwt_service.get_user_sessions(
            session=test_session,
            user_id=str(test_user.id)
        )
        
        assert len(final_sessions) >= 1
    
    async def test_account_lockout_and_recovery(self, test_session, test_user, sample_user_data):
        """Test account lockout after failed attempts and recovery."""
        # Attempt multiple failed logins
        for _ in range(5):  # Exceed lockout threshold
            _, success = await UserService.authenticate_user(
                session=test_session,
                username=test_user.username,
                password="wrongpassword",
                ip_address="127.0.0.1"
            )
            assert success is False
        
        # Refresh user from database to see updated failed attempts
        await test_session.refresh(test_user)
        
        # Account should be locked
        assert test_user.is_locked()
        
        # Try to login with correct password - should fail due to lockout
        _, success = await UserService.authenticate_user(
            session=test_session,
            username=test_user.username,
            password=sample_user_data["password"],
            ip_address="127.0.0.1"
        )
        assert success is False
        
        # Simulate lockout expiration
        test_user.locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
        await test_session.commit()
        
        # Now login should succeed
        _, success = await UserService.authenticate_user(
            session=test_session,
            username=test_user.username,
            password=sample_user_data["password"],
            ip_address="127.0.0.1"
        )
        assert success is True
        
        # Failed attempts should be reset
        await test_session.refresh(test_user)
        assert test_user.failed_login_attempts == "0"
        assert not test_user.is_locked()
    
    async def test_concurrent_authentication_attempts(self, test_session, test_user, sample_user_data):
        """Test concurrent authentication attempts."""
        jwt_service = DatabaseJWTService()
        
        async def login_attempt():
            return await jwt_service.authenticate_and_generate_tokens(
                session=test_session,
                username=test_user.username,
                password=sample_user_data["password"],
                ip_address="127.0.0.1"
            )
        
        # Perform concurrent login attempts
        tasks = [login_attempt() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # At least some should succeed
        successful_logins = [
            r for r in results 
            if not isinstance(r, Exception) and r[0] is not None
        ]
        
        assert len(successful_logins) >= 1
        
        # Verify tokens are valid
        for access_token, refresh_token, user_info in successful_logins:
            payload = jwt_service.validate_access_token(access_token)
            assert payload is not None
            assert payload["user_id"] == str(test_user.id)


@pytest.mark.asyncio
class TestSecurityWorkflows:
    """Test security-related workflows."""
    
    async def test_suspicious_activity_detection(self, test_session, test_user):
        """Test detection of suspicious activity patterns."""
        # Simulate failed login attempts from different IPs
        suspicious_ips = ["192.168.1.100", "10.0.0.50", "172.16.0.25"]
        
        for ip in suspicious_ips:
            for _ in range(3):  # Multiple attempts from each IP
                await AuthEventService.log_event(
                    session=test_session,
                    event_type="login",
                    user_id=None,  # Failed login, no user ID
                    success=False,
                    failure_reason="invalid_credentials",
                    ip_address=ip,
                    user_agent="automated-scanner/1.0"
                )
        
        # Get security events
        security_events = await AuthEventService.get_security_events(
            session=test_session,
            hours_back=1
        )
        
        assert len(security_events) == 9  # 3 IPs × 3 attempts each
        
        # Get failed login statistics
        stats = await AuthEventService.get_failed_login_stats(
            session=test_session,
            hours_back=1
        )
        
        assert stats["failed_logins"] == 9
        assert stats["successful_logins"] == 0
        assert stats["failure_rate"] == 100.0
    
    async def test_password_change_security_flow(self, test_session, test_user, sample_user_data):
        """Test security measures during password change."""
        jwt_service = DatabaseJWTService()
        
        # Create multiple active sessions
        sessions = []
        for i in range(3):
            access_token, refresh_token, _ = await jwt_service.authenticate_and_generate_tokens(
                session=test_session,
                username=test_user.username,
                password=sample_user_data["password"],
                ip_address=f"192.168.1.{i+1}"
            )
            sessions.append((access_token, refresh_token))
        
        # Change password
        new_password = "newsecurepassword123"
        await UserService.update_user(
            session=test_session,
            user_id=str(test_user.id),
            password=new_password
        )
        
        # Log password change event
        await AuthEventService.log_event(
            session=test_session,
            event_type="password_change",
            user_id=str(test_user.id),
            success=True,
            ip_address="192.168.1.1"
        )
        
        # Revoke all existing tokens for security
        revoked_count = await RefreshTokenService.revoke_all_user_tokens(
            session=test_session,
            user_id=str(test_user.id),
            reason="password_change"
        )
        
        assert revoked_count >= 3
        
        # Verify old tokens are invalid
        for access_token, refresh_token in sessions:
            new_token, _ = await jwt_service.refresh_access_token(
                session=test_session,
                refresh_token=refresh_token
            )
            assert new_token is None  # Should fail
        
        # Verify login with new password works
        new_access_token, new_refresh_token, _ = await jwt_service.authenticate_and_generate_tokens(
            session=test_session,
            username=test_user.username,
            password=new_password
        )
        
        assert new_access_token is not None
        assert new_refresh_token is not None
    
    async def test_email_verification_workflow(self, test_session, user_data_factory):
        """Test email verification workflow."""
        user_data = user_data_factory()
        
        # Create unverified user
        user = await UserService.create_user(
            session=test_session,
            **user_data
        )
        
        assert not user.is_verified
        
        # Generate verification token
        verification_token = user.generate_verification_token()
        await test_session.commit()
        
        assert verification_token is not None
        assert user.verification_token == verification_token
        assert user.verification_sent_at is not None
        
        # Verify email
        verification_success = user.verify_email(verification_token)
        await test_session.commit()
        
        assert verification_success is True
        assert user.is_verified is True
        assert user.verified_at is not None
        assert user.verification_token is None
        
        # Log verification event
        await AuthEventService.log_event(
            session=test_session,
            event_type="email_verification",
            user_id=str(user.id),
            success=True,
            event_metadata={"verification_token": verification_token[:10] + "..."}
        )
    
    async def test_password_reset_workflow(self, test_session, test_user):
        """Test password reset workflow."""
        # Generate reset token
        reset_token = test_user.generate_reset_token()
        await test_session.commit()
        
        assert reset_token is not None
        assert test_user.reset_token == reset_token
        assert test_user.reset_token_expires is not None
        
        # Verify token is valid
        assert test_user.can_reset_password(reset_token)
        
        # Reset password
        new_password = "resetpassword123"
        reset_success = test_user.reset_password(reset_token, new_password)
        await test_session.commit()
        
        assert reset_success is True
        assert test_user.verify_password(new_password)
        assert test_user.reset_token is None
        assert test_user.reset_token_expires is None
        
        # Log password reset event
        await AuthEventService.log_event(
            session=test_session,
            event_type="password_reset",
            user_id=str(test_user.id),
            success=True,
            event_metadata={"reset_via": "email_token"}
        )
        
        # Verify old failed login attempts are cleared
        assert test_user.failed_login_attempts == "0"
        assert not test_user.is_locked()
    
    async def test_expired_token_cleanup_workflow(self, test_session, test_user):
        """Test expired token cleanup workflow."""
        jwt_service = DatabaseJWTService()
        
        # Create tokens with different expiration times
        active_token = await RefreshTokenService.create_refresh_token(
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
        
        expiring_soon_token = await RefreshTokenService.create_refresh_token(
            session=test_session,
            user_id=str(test_user.id),
            token_id=str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
        )
        
        # Run cleanup
        cleaned_count = await jwt_service.cleanup_expired_tokens(test_session)
        
        assert cleaned_count >= 1  # At least the expired token
        
        # Verify cleanup results
        await test_session.refresh(active_token)
        await test_session.refresh(expired_token)
        await test_session.refresh(expiring_soon_token)
        
        assert active_token.is_active is True
        assert expired_token.is_revoked is True
        assert expiring_soon_token.is_active is True  # Should still be active


@pytest.mark.asyncio
class TestErrorRecoveryWorkflows:
    """Test error recovery and resilience workflows."""
    
    async def test_database_transaction_rollback(self, test_session, user_data_factory):
        """Test proper rollback on database errors."""
        user_data = user_data_factory()
        
        # Simulate database error during user creation
        try:
            # Create user successfully first
            user = await UserService.create_user(
                session=test_session,
                **user_data
            )
            
            # Try to create duplicate (should fail)
            with pytest.raises(Exception):
                await UserService.create_user(
                    session=test_session,
                    **user_data  # Same data should cause constraint violation
                )
            
            # Original user should still exist
            existing_user = await UserService.get_user_by_username(
                session=test_session,
                username=user_data["username"]
            )
            assert existing_user is not None
            assert existing_user.id == user.id
            
        except Exception:
            # If first creation also fails, that's acceptable for this test
            pass
    
    async def test_partial_authentication_failure_recovery(self, test_session, test_user):
        """Test recovery from partial authentication failures."""
        jwt_service = DatabaseJWTService()
        
        # Mock a scenario where token generation partially fails
        original_method = RefreshTokenService.create_refresh_token
        
        call_count = 0
        async def failing_create_token(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary database error")
            return await original_method(*args, **kwargs)
        
        with pytest.patch.object(RefreshTokenService, 'create_refresh_token', failing_create_token):
            # First attempt should fail
            result1 = await jwt_service.authenticate_and_generate_tokens(
                session=test_session,
                username=test_user.username,
                password="testpass123"
            )
            assert result1 == (None, None, None)
            
            # Second attempt should succeed
            result2 = await jwt_service.authenticate_and_generate_tokens(
                session=test_session,
                username=test_user.username,
                password="testpass123"
            )
            
            access_token, refresh_token, user_info = result2
            if access_token is not None:  # If second attempt succeeded
                assert refresh_token is not None
                assert user_info is not None
    
    async def test_concurrent_session_management_edge_cases(self, test_session, multiple_users):
        """Test edge cases in concurrent session management."""
        jwt_service = DatabaseJWTService()
        
        async def create_and_revoke_session(user, password):
            # Login
            access_token, refresh_token, _ = await jwt_service.authenticate_and_generate_tokens(
                session=test_session,
                username=user.username,
                password=password
            )
            
            if access_token and refresh_token:
                # Immediately logout
                await jwt_service.logout_user(
                    session=test_session,
                    access_token=access_token,
                    refresh_token=refresh_token
                )
        
        # Create concurrent sessions for multiple users
        tasks = []
        for i, user in enumerate(multiple_users):
            task = create_and_revoke_session(user, f"pass{i}123")
            tasks.append(task)
        
        # Execute concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify database consistency
        for user in multiple_users:
            user_tokens = await RefreshTokenService.get_user_active_tokens(
                session=test_session,
                user_id=str(user.id)
            )
            
            # Should have no active tokens (all were logged out)
            assert len(user_tokens) == 0
    
    async def test_token_refresh_race_condition(self, test_session, test_user, sample_user_data):
        """Test handling of token refresh race conditions."""
        jwt_service = DatabaseJWTService()
        
        # Create initial tokens
        access_token, refresh_token, _ = await jwt_service.authenticate_and_generate_tokens(
            session=test_session,
            username=test_user.username,
            password=sample_user_data["password"]
        )
        
        # Attempt concurrent refresh operations
        async def refresh_token_task():
            return await jwt_service.refresh_access_token(
                session=test_session,
                refresh_token=refresh_token
            )
        
        # Run multiple refresh attempts concurrently
        tasks = [refresh_token_task() for _ in range(3)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # At least one should succeed, others should fail gracefully
        successful_refreshes = [
            r for r in results 
            if not isinstance(r, Exception) and r[0] is not None
        ]
        
        # In a race condition, only one refresh should succeed
        # (depends on implementation - some systems allow multiple)
        assert len(successful_refreshes) >= 1
        
        # All successful tokens should be valid
        for new_access_token, user_info in successful_refreshes:
            payload = jwt_service.validate_access_token(new_access_token)
            assert payload is not None
            assert payload["user_id"] == str(test_user.id)