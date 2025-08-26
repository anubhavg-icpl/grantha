"""Database models for Grantha authentication system."""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship, validates
from passlib.context import CryptContext

from .base import Base, GUID

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    # Core user fields
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # User status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Profile fields
    full_name = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Authentication metadata
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(String(10), default="0", nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Email verification
    verification_token = Column(String(255), nullable=True, index=True)
    verification_sent_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Password reset
    reset_token = Column(String(255), nullable=True, index=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    auth_events = relationship("AuthEvent", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_user_username_active", "username", "is_active"),
        Index("idx_user_email_active", "email", "is_active"),
        Index("idx_user_verification_token", "verification_token"),
        Index("idx_user_reset_token", "reset_token"),
    )
    
    def __init__(self, **kwargs):
        # Handle password hashing
        if 'password' in kwargs:
            password = kwargs.pop('password')
            kwargs['password_hash'] = self.hash_password(password)
        super().__init__(**kwargs)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storing."""
        return pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the hash."""
        return pwd_context.verify(password, self.password_hash)
    
    def set_password(self, password: str):
        """Set a new password."""
        self.password_hash = self.hash_password(password)
    
    @validates('email')
    def validate_email(self, key, address):
        """Basic email validation."""
        if address and '@' not in address:
            raise ValueError("Invalid email address")
        return address
    
    @validates('username')
    def validate_username(self, key, username):
        """Username validation."""
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(username) > 50:
            raise ValueError("Username must be less than 50 characters")
        return username
    
    def is_locked(self) -> bool:
        """Check if account is locked due to failed login attempts."""
        if self.locked_until:
            return datetime.now(timezone.utc) < self.locked_until
        return False
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.now(timezone.utc)
        self.failed_login_attempts = "0"
        self.locked_until = None
    
    def increment_failed_login(self, max_attempts: int = 5, lockout_duration_minutes: int = 30):
        """Increment failed login attempts and lock if necessary."""
        current_attempts = int(self.failed_login_attempts or "0")
        current_attempts += 1
        self.failed_login_attempts = str(current_attempts)
        
        if current_attempts >= max_attempts:
            from datetime import timedelta
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=lockout_duration_minutes)
    
    def generate_verification_token(self) -> str:
        """Generate email verification token."""
        self.verification_token = str(uuid.uuid4())
        self.verification_sent_at = datetime.now(timezone.utc)
        return self.verification_token
    
    def verify_email(self, token: str) -> bool:
        """Verify email with token."""
        if self.verification_token == token and not self.is_verified:
            self.is_verified = True
            self.verified_at = datetime.now(timezone.utc)
            self.verification_token = None
            return True
        return False
    
    def generate_reset_token(self, expires_in_hours: int = 24) -> str:
        """Generate password reset token."""
        from datetime import timedelta
        self.reset_token = str(uuid.uuid4())
        self.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        return self.reset_token
    
    def can_reset_password(self, token: str) -> bool:
        """Check if password reset token is valid."""
        if not self.reset_token or not self.reset_token_expires:
            return False
        if self.reset_token != token:
            return False
        return datetime.now(timezone.utc) < self.reset_token_expires
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using token."""
        if self.can_reset_password(token):
            self.set_password(new_password)
            self.reset_token = None
            self.reset_token_expires = None
            self.failed_login_attempts = "0"
            self.locked_until = None
            return True
        return False
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary."""
        data = {
            'id': str(self.id),
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'bio': self.bio,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_superuser': self.is_superuser,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
        }
        
        if include_sensitive:
            data.update({
                'failed_login_attempts': int(self.failed_login_attempts or "0"),
                'is_locked': self.is_locked(),
                'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            })
        
        return data
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class RefreshToken(Base):
    """Refresh token model for JWT token management."""
    
    __tablename__ = "refresh_tokens"
    
    # Token fields
    token_id = Column(String(255), unique=True, nullable=False, index=True)  # JTI from JWT
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    
    # Token metadata
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    
    # Session tracking
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    user_agent = Column(String(500), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # Revocation metadata
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoke_reason = Column(String(100), nullable=True)  # logout, security, expired, etc.
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_refresh_token_user_active", "user_id", "is_active"),
        Index("idx_refresh_token_expires", "expires_at"),
        Index("idx_refresh_token_jti", "token_id"),
    )
    
    def revoke(self, reason: str = "manual"):
        """Revoke the refresh token."""
        self.is_active = False
        self.is_revoked = True
        self.revoked_at = datetime.now(timezone.utc)
        self.revoke_reason = reason
    
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) >= self.expires_at
    
    def is_valid(self) -> bool:
        """Check if token is valid (active and not expired)."""
        return self.is_active and not self.is_revoked and not self.is_expired()
    
    def to_dict(self) -> dict:
        """Convert refresh token to dictionary."""
        return {
            'id': str(self.id),
            'token_id': self.token_id,
            'user_id': str(self.user_id),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'is_revoked': self.is_revoked,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
            'revoke_reason': self.revoke_reason,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'is_expired': self.is_expired(),
            'is_valid': self.is_valid(),
        }
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, token_id='{self.token_id}', user_id={self.user_id})>"


class AuthEvent(Base):
    """Authentication event logging model."""
    
    __tablename__ = "auth_events"
    
    # Event identification
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True, index=True)  # Nullable for failed logins
    event_type = Column(String(50), nullable=False, index=True)  # login, logout, failed_login, password_change, etc.
    
    # Event details
    success = Column(Boolean, nullable=False, default=False)
    failure_reason = Column(String(255), nullable=True)
    
    # Request metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # Additional context
    event_metadata = Column(Text, nullable=True)  # JSON string for additional context
    
    # Session tracking
    session_id = Column(String(255), nullable=True, index=True)
    
    # Relationships
    user = relationship("User", back_populates="auth_events")
    
    # Indexes for performance and security monitoring
    __table_args__ = (
        Index("idx_auth_event_type_time", "event_type", "created_at"),
        Index("idx_auth_event_user_type", "user_id", "event_type"),
        Index("idx_auth_event_ip_time", "ip_address", "created_at"),
        Index("idx_auth_event_success_time", "success", "created_at"),
    )
    
    @staticmethod
    def create_login_event(user_id: str, success: bool, ip_address: str = None, 
                          user_agent: str = None, failure_reason: str = None, 
                          event_metadata: dict = None):
        """Create a login event."""
        return AuthEvent(
            user_id=user_id if success else None,
            event_type="login",
            success=success,
            failure_reason=failure_reason,
            ip_address=ip_address,
            user_agent=user_agent,
            event_metadata=str(event_metadata) if event_metadata else None
        )
    
    @staticmethod
    def create_logout_event(user_id: str, ip_address: str = None, 
                           user_agent: str = None, event_metadata: dict = None):
        """Create a logout event."""
        return AuthEvent(
            user_id=user_id,
            event_type="logout",
            success=True,
            ip_address=ip_address,
            user_agent=user_agent,
            event_metadata=str(event_metadata) if event_metadata else None
        )
    
    @staticmethod 
    def create_password_change_event(user_id: str, success: bool, ip_address: str = None,
                                   user_agent: str = None, event_metadata: dict = None):
        """Create a password change event."""
        return AuthEvent(
            user_id=user_id,
            event_type="password_change",
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            event_metadata=str(event_metadata) if event_metadata else None
        )
    
    def to_dict(self) -> dict:
        """Convert auth event to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'event_type': self.event_type,
            'success': self.success,
            'failure_reason': self.failure_reason,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'device_fingerprint': self.device_fingerprint,
            'event_metadata': self.event_metadata,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f"<AuthEvent(id={self.id}, event_type='{self.event_type}', success={self.success}, user_id={self.user_id})>"