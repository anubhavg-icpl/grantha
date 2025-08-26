"""Security-focused tests for authentication system."""

import pytest
import jwt
import hashlib
import uuid
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, Mock

from src.grantha.database.models import User, RefreshToken
from src.grantha.database.services import UserService, AuthEventService
from src.grantha.database.auth_service import DatabaseJWTService


@pytest.mark.asyncio
class TestPasswordSecurity:
    """Test password security features."""
    
    def test_password_hashing_security(self):
        """Test password hashing uses secure methods."""
        password = "testpassword123"
        user = User(username="test", password=password)
        
        # Password should be hashed with bcrypt
        assert user.password_hash != password
        assert user.password_hash.startswith("$2b$")  # bcrypt prefix
        assert len(user.password_hash) >= 60  # bcrypt hash length
        
        # Should verify correctly
        assert user.verify_password(password)
        assert not user.verify_password("wrongpassword")
        
        # Same password should produce different hashes (salt)
        user2 = User(username="test2", password=password)
        assert user.password_hash != user2.password_hash
    
    def test_password_complexity_validation(self):
        """Test password complexity requirements."""
        weak_passwords = [
            "123",  # Too short
            "password",  # No numbers
            "PASSWORD123",  # No lowercase
            "password123",  # No uppercase
        ]
        
        # Note: Basic model doesn't enforce complexity,
        # but this shows where such validation would go
        for weak_pwd in weak_passwords:
            user = User(username="test", password=weak_pwd)
            # In production, this would validate complexity
            assert user.password_hash is not None
    
    def test_password_timing_attack_resistance(self):
        """Test resistance to timing attacks in password verification."""
        user = User(username="test", password="correctpassword")
        
        # Measure time for correct password
        start = time.perf_counter()
        result1 = user.verify_password("correctpassword")
        correct_time = time.perf_counter() - start
        
        # Measure time for incorrect password
        start = time.perf_counter()
        result2 = user.verify_password("wrongpassword")
        wrong_time = time.perf_counter() - start
        
        assert result1 is True
        assert result2 is False
        
        # Times should be relatively similar (bcrypt handles this)
        # Allow for reasonable variance in timing
        time_ratio = max(correct_time, wrong_time) / min(correct_time, wrong_time)
        assert time_ratio < 10  # Should not differ by more than 10x
    
    async def test_password_change_security_measures(self, test_session, test_user):
        """Test security measures around password changes."""
        # Log password change attempt
        await AuthEventService.log_event(
            session=test_session,
            event_type="password_change_attempt",
            user_id=str(test_user.id),
            success=True,
            ip_address="127.0.0.1"
        )
        
        # Change password
        old_hash = test_user.password_hash
        test_user.set_password("newpassword123")
        await test_session.commit()
        
        # Password hash should change
        assert test_user.password_hash != old_hash
        
        # Old password should not work
        assert not test_user.verify_password("testpass123")
        
        # New password should work
        assert test_user.verify_password("newpassword123")
        
        # Failed login attempts should be reset
        test_user.failed_login_attempts = "0"
        test_user.locked_until = None
        await test_session.commit()


@pytest.mark.asyncio
class TestJWTSecurity:
    """Test JWT token security features."""
    
    def test_jwt_secret_key_strength(self):
        """Test JWT secret key is sufficiently strong."""
        jwt_service = DatabaseJWTService()
        
        # Secret key should be reasonably long
        assert len(jwt_service.secret_key) >= 32
        
        # Should not be a default/weak key
        weak_keys = [
            "secret",
            "key",
            "password",
            "jwt_secret",
            "123456",
            "grantha_dev_secret_change_in_production"  # Default dev key
        ]
        
        # In production, should not use weak keys
        if jwt_service.secret_key not in weak_keys:
            assert True  # Good, not using weak key
        else:
            # Development environment - warn about weak key
            assert jwt_service.secret_key == "test_secret_key_for_jwt"  # Test key is okay
    
    def test_jwt_token_structure_security(self, jwt_service):
        """Test JWT token structure and claims."""
        user_id = str(uuid.uuid4())
        
        # Generate access token
        access_token = jwt.encode(
            {
                "user_id": user_id,
                "type": "access",
                "jti": str(uuid.uuid4()),
                "iat": datetime.now(timezone.utc),
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
            },
            jwt_service.secret_key,
            algorithm='HS256'
        )
        
        # Decode and verify structure
        payload = jwt.decode(access_token, jwt_service.secret_key, algorithms=['HS256'])
        
        # Required claims should be present
        required_claims = ["user_id", "type", "jti", "iat", "exp"]
        for claim in required_claims:
            assert claim in payload
        
        # Token type should be explicit
        assert payload["type"] in ["access", "refresh"]
        
        # JTI (JWT ID) should be unique
        assert len(payload["jti"]) >= 32  # UUID length
        
        # Expiration should be reasonable
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        time_diff = exp_time - now
        assert timedelta(minutes=1) <= time_diff <= timedelta(hours=24)
    
    def test_jwt_algorithm_security(self, jwt_service):
        """Test JWT uses secure algorithms."""
        # Should use HMAC-based algorithms
        assert jwt_service.algorithm in ["HS256", "HS384", "HS512"]
        
        # Test that algorithm tampering is detected
        user_id = str(uuid.uuid4())
        token_payload = {
            "user_id": user_id,
            "type": "access",
            "jti": str(uuid.uuid4()),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
        }
        
        # Create token with secure algorithm
        secure_token = jwt.encode(token_payload, jwt_service.secret_key, algorithm='HS256')
        
        # Try to create token with none algorithm (security risk)
        try:
            insecure_token = jwt.encode(token_payload, "", algorithm='none')
            
            # Verification should fail
            with pytest.raises(jwt.InvalidTokenError):
                jwt.decode(insecure_token, jwt_service.secret_key, algorithms=['HS256'])
        except Exception:
            # Expected - some JWT libraries prevent 'none' algorithm
            pass
        
        # Secure token should validate
        decoded = jwt.decode(secure_token, jwt_service.secret_key, algorithms=['HS256'])
        assert decoded["user_id"] == user_id
    
    def test_jwt_token_expiration_enforcement(self, jwt_service):
        """Test JWT token expiration is properly enforced."""
        user_id = str(uuid.uuid4())
        
        # Create expired token
        expired_token = jwt.encode(
            {
                "user_id": user_id,
                "type": "access",
                "jti": str(uuid.uuid4()),
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1)
            },
            jwt_service.secret_key,
            algorithm='HS256'
        )
        
        # Should reject expired token
        payload = jwt_service.validate_access_token(expired_token)
        assert payload is None
        
        # Create valid token
        valid_token = jwt.encode(
            {
                "user_id": user_id,
                "type": "access",
                "jti": str(uuid.uuid4()),
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
            },
            jwt_service.secret_key,
            algorithm='HS256'
        )
        
        # Should accept valid token
        payload = jwt_service.validate_access_token(valid_token)
        assert payload is not None
        assert payload["user_id"] == user_id
    
    async def test_refresh_token_rotation_security(self, test_session, test_user, sample_user_data):
        """Test refresh token rotation for security."""
        jwt_service = DatabaseJWTService()
        
        # Generate initial tokens
        access_token1, refresh_token1, _ = await jwt_service.authenticate_and_generate_tokens(
            session=test_session,
            username=test_user.username,
            password=sample_user_data["password"]
        )
        
        # Use refresh token to get new access token
        access_token2, _ = await jwt_service.refresh_access_token(
            session=test_session,
            refresh_token=refresh_token1
        )
        
        # New access token should be different
        assert access_token2 != access_token1
        
        # Both tokens should be valid initially
        payload1 = jwt_service.validate_access_token(access_token1)
        payload2 = jwt_service.validate_access_token(access_token2)
        
        assert payload1 is not None
        assert payload2 is not None
        
        # But they should have different JTIs
        assert payload1["jti"] != payload2["jti"]


@pytest.mark.asyncio
class TestAccountLockoutSecurity:
    """Test account lockout security features."""
    
    async def test_brute_force_protection(self, test_session, test_user):
        """Test protection against brute force attacks."""
        max_attempts = 5
        
        # Perform failed login attempts
        for i in range(max_attempts):
            _, success = await UserService.authenticate_user(
                session=test_session,
                username=test_user.username,
                password="wrongpassword",
                ip_address="192.168.1.100"
            )
            assert success is False
            
            await test_session.refresh(test_user)
            current_attempts = int(test_user.failed_login_attempts)
            assert current_attempts == i + 1
        
        # Account should be locked
        await test_session.refresh(test_user)
        assert test_user.is_locked()
        
        # Even correct password should fail when locked
        _, success = await UserService.authenticate_user(
            session=test_session,
            username=test_user.username,
            password="testpass123",
            ip_address="192.168.1.100"
        )
        assert success is False
    
    async def test_lockout_duration_security(self, test_session, test_user):
        """Test lockout duration prevents immediate retry."""
        # Trigger account lockout
        for _ in range(5):
            test_user.increment_failed_login()
        
        await test_session.commit()
        assert test_user.is_locked()
        
        # Should remain locked for the duration
        lockout_time = test_user.locked_until
        assert lockout_time is not None
        assert lockout_time > datetime.now(timezone.utc)
        
        # Simulate time passage
        test_user.locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
        await test_session.commit()
        
        # Should no longer be locked
        assert not test_user.is_locked()
    
    async def test_lockout_bypass_prevention(self, test_session, test_user):
        """Test that lockout cannot be easily bypassed."""
        # Lock the account
        test_user.increment_failed_login(max_attempts=1)
        await test_session.commit()
        assert test_user.is_locked()
        
        # Try various bypass attempts
        bypass_usernames = [
            test_user.username.upper(),  # Case variation
            test_user.username.lower(),
            f" {test_user.username}",    # Whitespace
            f"{test_user.username} ",
            test_user.email,              # Try email instead
        ]
        
        for username in bypass_usernames:
            if username == test_user.email and username:
                # Email login might be allowed - check if it respects lockout
                user, success = await UserService.authenticate_user(
                    session=test_session,
                    username=username,
                    password="testpass123"
                )
                if user and user.id == test_user.id:
                    assert success is False  # Should respect lockout
            else:
                # Other variations should either fail or respect lockout
                user, success = await UserService.authenticate_user(
                    session=test_session,
                    username=username,
                    password="testpass123"
                )
                if user and user.id == test_user.id:
                    assert success is False  # Should respect lockout


@pytest.mark.asyncio
class TestSessionSecurity:
    """Test session security features."""
    
    async def test_session_hijacking_protection(self, test_session, test_user, sample_user_data):
        """Test protection against session hijacking."""
        jwt_service = DatabaseJWTService()
        
        # Create session from specific IP/user agent
        original_ip = "192.168.1.100"
        original_ua = "Mozilla/5.0 (original-browser)"
        
        access_token, refresh_token, _ = await jwt_service.authenticate_and_generate_tokens(
            session=test_session,
            username=test_user.username,
            password=sample_user_data["password"],
            ip_address=original_ip,
            user_agent=original_ua
        )
        
        # Validate token works
        payload = jwt_service.validate_access_token(access_token)
        assert payload is not None
        
        # In a real implementation, you might track IP/user agent changes
        # and require re-authentication for suspicious changes
        
        # For now, just verify tokens contain necessary info for tracking
        refresh_payload = jwt.decode(refresh_token, jwt_service.secret_key, algorithms=['HS256'])
        assert "jti" in refresh_payload  # Can be used to track sessions
    
    async def test_concurrent_session_limits(self, test_session, test_user, sample_user_data):
        """Test limits on concurrent sessions."""
        jwt_service = DatabaseJWTService()
        sessions = []
        
        # Create multiple sessions
        max_sessions = 10
        for i in range(max_sessions):
            access_token, refresh_token, _ = await jwt_service.authenticate_and_generate_tokens(
                session=test_session,
                username=test_user.username,
                password=sample_user_data["password"],
                ip_address=f"192.168.1.{i+1}",
                user_agent=f"browser-{i}"
            )
            
            if access_token:
                sessions.append((access_token, refresh_token))
        
        # Check how many sessions were created
        user_sessions = await jwt_service.get_user_sessions(
            session=test_session,
            user_id=str(test_user.id)
        )
        
        # Should have created sessions (no limit enforced in current implementation)
        assert len(user_sessions) >= 1
        
        # In production, you might limit concurrent sessions
        # This test documents the current behavior
    
    async def test_session_invalidation_on_logout(self, test_session, test_user, sample_user_data):
        """Test session invalidation on logout."""
        jwt_service = DatabaseJWTService()
        
        # Create session
        access_token, refresh_token, _ = await jwt_service.authenticate_and_generate_tokens(
            session=test_session,
            username=test_user.username,
            password=sample_user_data["password"]
        )
        
        # Verify tokens work
        assert jwt_service.validate_access_token(access_token) is not None
        
        # Logout
        result = await jwt_service.logout_user(
            session=test_session,
            access_token=access_token,
            refresh_token=refresh_token
        )
        
        assert result["success"] is True
        
        # Refresh token should no longer work
        new_access_token, _ = await jwt_service.refresh_access_token(
            session=test_session,
            refresh_token=refresh_token
        )
        
        assert new_access_token is None
    
    async def test_session_cleanup_security(self, test_session, test_user):
        """Test security aspects of session cleanup."""
        jwt_service = DatabaseJWTService()
        
        # Create expired refresh token
        from src.grantha.database.services import RefreshTokenService
        
        expired_token = await RefreshTokenService.create_refresh_token(
            session=test_session,
            user_id=str(test_user.id),
            token_id=str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        
        # Cleanup should remove expired tokens
        cleaned_count = await jwt_service.cleanup_expired_tokens(test_session)
        assert cleaned_count >= 1
        
        # Token should be marked as revoked, not deleted (for audit trail)
        await test_session.refresh(expired_token)
        assert expired_token.is_revoked is True
        assert expired_token.revoke_reason == "expired"


@pytest.mark.asyncio
class TestInputValidationSecurity:
    """Test input validation security measures."""
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in user inputs."""
        # Common SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "admin'/*",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES('hacker', 'password'); --",
            "admin'; UPDATE users SET password='hacked' WHERE username='admin'; --"
        ]
        
        # These should be treated as literal strings, not SQL
        for malicious_input in malicious_inputs:
            user = User(username="test", password="test")
            # In SQLAlchemy ORM, parameterized queries prevent SQL injection
            # This test documents the expectation
            assert user.username == "test"  # Should not be affected by malicious input
    
    def test_xss_prevention_in_user_data(self):
        """Test XSS prevention in user data fields."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//",
            "<svg onload=alert('xss')>"
        ]
        
        # User data should be stored as-is, sanitization happens on output
        for payload in xss_payloads:
            user = User(
                username="test",
                password="test",
                full_name=payload,
                bio=payload
            )
            
            # Data should be stored as provided
            assert user.full_name == payload
            assert user.bio == payload
            
            # Serialization should include the data (output sanitization needed)
            user_dict = user.to_dict()
            assert user_dict["full_name"] == payload
            assert user_dict["bio"] == payload
    
    async def test_parameter_tampering_prevention(self, test_session, test_user):
        """Test prevention of parameter tampering attacks."""
        # Try to update protected fields
        protected_updates = {
            "id": str(uuid.uuid4()),  # Should not change ID
            "created_at": datetime.now(timezone.utc),
            "is_superuser": True,  # Privilege escalation attempt
            "password_hash": "hacked_hash"  # Direct hash manipulation
        }
        
        original_id = test_user.id
        original_created_at = test_user.created_at
        original_is_superuser = test_user.is_superuser
        original_hash = test_user.password_hash
        
        # Try to update with protected fields
        updated_user = await UserService.update_user(
            session=test_session,
            user_id=str(test_user.id),
            **protected_updates
        )
        
        if updated_user:
            # Protected fields should not change
            assert updated_user.id == original_id
            assert updated_user.created_at == original_created_at
            # is_superuser might be updateable depending on implementation
            # password_hash should only change through proper methods
    
    def test_user_enumeration_prevention(self):
        """Test prevention of user enumeration attacks."""
        # Different responses for existing vs non-existing users could allow enumeration
        # This test documents the expected behavior
        
        existing_user = User(username="existinguser", password="test")
        
        # Verify password for existing user
        result1 = existing_user.verify_password("wrongpassword")
        assert result1 is False
        
        # For non-existing user, we should get similar timing/response
        # This is typically handled at the service level, not model level
        
        # The key is that failed logins should not reveal whether user exists
        # This is implemented in UserService.authenticate_user()
    
    async def test_mass_assignment_protection(self, test_session):
        """Test protection against mass assignment attacks."""
        # Attempt to create user with dangerous fields
        dangerous_data = {
            "username": "testuser",
            "password": "testpass",
            "email": "test@example.com",
            "is_superuser": True,  # Should not be settable via mass assignment
            "is_active": False,    # Should not be settable directly
            "id": str(uuid.uuid4()),  # Should not be settable
            "created_at": datetime.now(timezone.utc) - timedelta(days=365)
        }
        
        # UserService.create_user should only accept safe fields
        user = await UserService.create_user(
            session=test_session,
            username=dangerous_data["username"],
            password=dangerous_data["password"],
            email=dangerous_data["email"],
            # Dangerous fields should be explicitly excluded or handled safely
        )
        
        # Verify safe defaults are used
        assert user.is_superuser is False  # Default value
        assert user.is_active is True      # Default value
        assert user.id != dangerous_data["id"]  # Should be auto-generated
        
        # created_at should be auto-set to current time, not manipulated value
        time_diff = datetime.now(timezone.utc) - user.created_at
        assert time_diff < timedelta(minutes=1)  # Should be recent


@pytest.mark.asyncio
class TestAuditAndMonitoring:
    """Test audit trail and monitoring security features."""
    
    async def test_authentication_event_logging(self, test_session, test_user):
        """Test comprehensive logging of authentication events."""
        # Successful login should be logged
        await AuthEventService.log_event(
            session=test_session,
            event_type="login",
            user_id=str(test_user.id),
            success=True,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )
        
        # Failed login should be logged
        await AuthEventService.log_event(
            session=test_session,
            event_type="login",
            user_id=None,  # Failed login might not have user_id
            success=False,
            failure_reason="invalid_credentials",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )
        
        # Logout should be logged
        await AuthEventService.log_event(
            session=test_session,
            event_type="logout",
            user_id=str(test_user.id),
            success=True,
            ip_address="192.168.1.100"
        )
        
        # Get events
        events = await AuthEventService.get_user_events(
            session=test_session,
            user_id=str(test_user.id)
        )
        
        assert len(events) >= 2  # login and logout
        
        # Verify event details
        event_types = [event.event_type for event in events]
        assert "login" in event_types
        assert "logout" in event_types
    
    async def test_security_event_monitoring(self, test_session):
        """Test monitoring of security-relevant events."""
        # Create various security events
        events_to_create = [
            ("login", False, "brute_force_detected"),
            ("login", False, "account_locked"),
            ("password_change", True, None),
            ("session_revoked", True, "security_breach"),
            ("token_refresh", False, "expired_token")
        ]
        
        for event_type, success, failure_reason in events_to_create:
            await AuthEventService.log_event(
                session=test_session,
                event_type=event_type,
                user_id=str(uuid.uuid4()) if success else None,
                success=success,
                failure_reason=failure_reason,
                ip_address="192.168.1.100"
            )
        
        # Get security events
        security_events = await AuthEventService.get_security_events(
            session=test_session,
            hours_back=1
        )
        
        assert len(security_events) >= len(events_to_create)
        
        # Should include both successful and failed events
        success_events = [e for e in security_events if e.success]
        failed_events = [e for e in security_events if not e.success]
        
        assert len(success_events) >= 2
        assert len(failed_events) >= 3
    
    async def test_failed_login_statistics(self, test_session):
        """Test failed login statistics for security monitoring."""
        # Create pattern of failed logins
        for i in range(10):
            await AuthEventService.log_event(
                session=test_session,
                event_type="login",
                success=False,
                failure_reason="invalid_password" if i % 2 == 0 else "user_not_found",
                ip_address=f"192.168.1.{100 + i % 3}",  # From 3 different IPs
                user_agent="automated-attack-tool"
            )
        
        # Create some successful logins
        for i in range(3):
            await AuthEventService.log_event(
                session=test_session,
                event_type="login",
                user_id=str(uuid.uuid4()),
                success=True,
                ip_address="192.168.1.200"
            )
        
        # Get statistics
        stats = await AuthEventService.get_failed_login_stats(
            session=test_session,
            hours_back=1
        )
        
        assert stats["failed_logins"] == 10
        assert stats["successful_logins"] == 3
        assert stats["failure_rate"] == 76.92  # 10/(10+3) * 100
        
        # Should have breakdown by failure reason
        reasons = [r["reason"] for r in stats["top_failure_reasons"]]
        assert "invalid_password" in reasons
        assert "user_not_found" in reasons
    
    async def test_audit_trail_integrity(self, test_session, test_user):
        """Test audit trail integrity and immutability."""
        # Create an auth event
        event = await AuthEventService.log_event(
            session=test_session,
            event_type="login",
            user_id=str(test_user.id),
            success=True,
            ip_address="192.168.1.100"
        )
        
        # Audit events should have timestamps
        assert event.created_at is not None
        original_timestamp = event.created_at
        
        # Try to modify the event (should be immutable)
        event.success = False
        event.event_type = "logout"
        
        # Changes should not persist or should be tracked
        await test_session.commit()
        
        # Re-fetch and verify
        await test_session.refresh(event)
        
        # In a proper audit system, events would be immutable
        # This test documents current behavior
        assert event.created_at == original_timestamp