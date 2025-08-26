"""Database services for user management and authentication."""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload

from .models import User, RefreshToken, AuthEvent

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management operations."""
    
    @staticmethod
    async def create_user(
        session: AsyncSession,
        username: str,
        password: str,
        email: str = None,
        full_name: str = None,
        bio: str = None,
        is_verified: bool = False,
        is_superuser: bool = False
    ) -> User:
        """Create a new user."""
        try:
            user = User(
                username=username,
                password=password,  # Will be hashed in the model's __init__
                email=email,
                full_name=full_name,
                bio=bio,
                is_verified=is_verified,
                is_superuser=is_superuser
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"Created user: {username} (id: {user.id})")
            return user
        
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to create user {username}: {e}")
            raise
    
    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            uuid_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            result = await session.execute(
                select(User).where(User.id == uuid_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by id {user_id}: {e}")
            return None
    
    @staticmethod
    async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            result = await session.execute(
                select(User).where(and_(
                    User.username == username,
                    User.is_active == True
                ))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            return None
    
    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            result = await session.execute(
                select(User).where(and_(
                    User.email == email,
                    User.is_active == True
                ))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None
    
    @staticmethod
    async def authenticate_user(
        session: AsyncSession, 
        username: str, 
        password: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Tuple[Optional[User], bool]:
        """
        Authenticate user with username/password.
        
        Returns:
            (User, success) tuple where success indicates if login succeeded
        """
        try:
            # Get user by username or email
            user = await UserService.get_user_by_username(session, username)
            if not user:
                user = await UserService.get_user_by_email(session, username)
            
            if not user:
                # Log failed login attempt
                event = AuthEvent.create_login_event(
                    user_id=None,
                    success=False,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    failure_reason="user_not_found"
                )
                session.add(event)
                await session.commit()
                return None, False
            
            # Check if account is locked
            if user.is_locked():
                event = AuthEvent.create_login_event(
                    user_id=str(user.id),
                    success=False,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    failure_reason="account_locked"
                )
                session.add(event)
                await session.commit()
                return user, False
            
            # Verify password
            if user.verify_password(password):
                # Successful login
                user.update_last_login()
                event = AuthEvent.create_login_event(
                    user_id=str(user.id),
                    success=True,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                session.add(event)
                await session.commit()
                return user, True
            else:
                # Failed login - increment failed attempts
                user.increment_failed_login()
                event = AuthEvent.create_login_event(
                    user_id=str(user.id),
                    success=False,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    failure_reason="invalid_password"
                )
                session.add(event)
                await session.commit()
                return user, False
                
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to authenticate user {username}: {e}")
            return None, False
    
    @staticmethod
    async def update_user(
        session: AsyncSession,
        user_id: str,
        **updates
    ) -> Optional[User]:
        """Update user fields."""
        try:
            user = await UserService.get_user_by_id(session, user_id)
            if not user:
                return None
            
            for field, value in updates.items():
                if hasattr(user, field) and field not in ['id', 'created_at', 'password']:
                    setattr(user, field, value)
            
            # Handle password separately for proper hashing
            if 'password' in updates:
                user.set_password(updates['password'])
            
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"Updated user {user_id}")
            return user
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            return None
    
    @staticmethod
    async def deactivate_user(session: AsyncSession, user_id: str) -> bool:
        """Deactivate a user account."""
        try:
            user = await UserService.get_user_by_id(session, user_id)
            if not user:
                return False
            
            user.is_active = False
            await session.commit()
            
            # Revoke all refresh tokens
            await RefreshTokenService.revoke_all_user_tokens(session, user_id, "account_deactivated")
            
            logger.info(f"Deactivated user {user_id}")
            return True
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to deactivate user {user_id}: {e}")
            return False
    
    @staticmethod
    async def list_users(
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        active_only: bool = True
    ) -> List[User]:
        """List users with pagination."""
        try:
            query = select(User)
            
            if active_only:
                query = query.where(User.is_active == True)
            
            query = query.offset(offset).limit(limit).order_by(User.created_at.desc())
            
            result = await session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return []


class RefreshTokenService:
    """Service for refresh token management."""
    
    @staticmethod
    async def create_refresh_token(
        session: AsyncSession,
        user_id: str,
        token_id: str,
        expires_at: datetime,
        ip_address: str = None,
        user_agent: str = None,
        device_fingerprint: str = None
    ) -> RefreshToken:
        """Create a new refresh token record."""
        try:
            uuid_user_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            
            token = RefreshToken(
                token_id=token_id,
                user_id=uuid_user_id,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint
            )
            
            session.add(token)
            await session.commit()
            await session.refresh(token)
            
            logger.info(f"Created refresh token {token_id} for user {user_id}")
            return token
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to create refresh token: {e}")
            raise
    
    @staticmethod
    async def get_refresh_token(session: AsyncSession, token_id: str) -> Optional[RefreshToken]:
        """Get refresh token by token ID."""
        try:
            result = await session.execute(
                select(RefreshToken).where(
                    RefreshToken.token_id == token_id
                ).options(selectinload(RefreshToken.user))
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get refresh token {token_id}: {e}")
            return None
    
    @staticmethod
    async def validate_refresh_token(session: AsyncSession, token_id: str) -> Optional[RefreshToken]:
        """Validate and return refresh token if valid."""
        try:
            token = await RefreshTokenService.get_refresh_token(session, token_id)
            
            if token and token.is_valid():
                return token
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to validate refresh token {token_id}: {e}")
            return None
    
    @staticmethod
    async def revoke_refresh_token(
        session: AsyncSession, 
        token_id: str, 
        reason: str = "manual"
    ) -> bool:
        """Revoke a refresh token."""
        try:
            token = await RefreshTokenService.get_refresh_token(session, token_id)
            
            if not token:
                return False
            
            token.revoke(reason)
            await session.commit()
            
            logger.info(f"Revoked refresh token {token_id} (reason: {reason})")
            return True
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to revoke refresh token {token_id}: {e}")
            return False
    
    @staticmethod
    async def revoke_all_user_tokens(
        session: AsyncSession, 
        user_id: str, 
        reason: str = "logout_all"
    ) -> int:
        """Revoke all active refresh tokens for a user."""
        try:
            uuid_user_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            
            result = await session.execute(
                select(RefreshToken).where(and_(
                    RefreshToken.user_id == uuid_user_id,
                    RefreshToken.is_active == True,
                    RefreshToken.is_revoked == False
                ))
            )
            tokens = list(result.scalars().all())
            
            revoked_count = 0
            for token in tokens:
                token.revoke(reason)
                revoked_count += 1
            
            await session.commit()
            
            logger.info(f"Revoked {revoked_count} tokens for user {user_id}")
            return revoked_count
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to revoke all tokens for user {user_id}: {e}")
            return 0
    
    @staticmethod
    async def cleanup_expired_tokens(session: AsyncSession) -> int:
        """Clean up expired refresh tokens."""
        try:
            now = datetime.now(timezone.utc)
            
            result = await session.execute(
                select(RefreshToken).where(
                    RefreshToken.expires_at < now
                )
            )
            tokens = list(result.scalars().all())
            
            cleanup_count = 0
            for token in tokens:
                if not token.is_revoked:
                    token.revoke("expired")
                    cleanup_count += 1
            
            await session.commit()
            
            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} expired refresh tokens")
            
            return cleanup_count
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to cleanup expired tokens: {e}")
            return 0
    
    @staticmethod
    async def get_user_active_tokens(
        session: AsyncSession, 
        user_id: str,
        limit: int = 10
    ) -> List[RefreshToken]:
        """Get active refresh tokens for a user."""
        try:
            uuid_user_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            
            result = await session.execute(
                select(RefreshToken).where(and_(
                    RefreshToken.user_id == uuid_user_id,
                    RefreshToken.is_active == True,
                    RefreshToken.is_revoked == False
                )).order_by(desc(RefreshToken.created_at)).limit(limit)
            )
            
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Failed to get active tokens for user {user_id}: {e}")
            return []


class AuthEventService:
    """Service for authentication event logging and monitoring."""
    
    @staticmethod
    async def log_event(
        session: AsyncSession,
        event_type: str,
        user_id: str = None,
        success: bool = True,
        failure_reason: str = None,
        ip_address: str = None,
        user_agent: str = None,
        device_fingerprint: str = None,
        event_metadata: dict = None,
        session_id: str = None
    ) -> AuthEvent:
        """Log an authentication event."""
        try:
            uuid_user_id = uuid.UUID(user_id) if user_id and isinstance(user_id, str) else user_id
            
            event = AuthEvent(
                user_id=uuid_user_id,
                event_type=event_type,
                success=success,
                failure_reason=failure_reason,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                event_metadata=str(event_metadata) if event_metadata else None,
                session_id=session_id
            )
            
            session.add(event)
            await session.commit()
            
            return event
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to log auth event: {e}")
            raise
    
    @staticmethod
    async def get_user_events(
        session: AsyncSession,
        user_id: str,
        limit: int = 50,
        event_type: str = None
    ) -> List[AuthEvent]:
        """Get authentication events for a user."""
        try:
            uuid_user_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            
            query = select(AuthEvent).where(AuthEvent.user_id == uuid_user_id)
            
            if event_type:
                query = query.where(AuthEvent.event_type == event_type)
            
            query = query.order_by(desc(AuthEvent.created_at)).limit(limit)
            
            result = await session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Failed to get events for user {user_id}: {e}")
            return []
    
    @staticmethod
    async def get_security_events(
        session: AsyncSession,
        hours_back: int = 24,
        limit: int = 100
    ) -> List[AuthEvent]:
        """Get recent security-relevant events."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            
            query = select(AuthEvent).where(and_(
                AuthEvent.created_at >= cutoff_time,
                or_(
                    AuthEvent.success == False,
                    AuthEvent.event_type.in_(['login', 'logout', 'password_change'])
                )
            )).order_by(desc(AuthEvent.created_at)).limit(limit)
            
            result = await session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Failed to get security events: {e}")
            return []
    
    @staticmethod
    async def get_failed_login_stats(
        session: AsyncSession,
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """Get failed login statistics."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            
            # Count failed logins
            failed_result = await session.execute(
                select(func.count()).where(and_(
                    AuthEvent.event_type == 'login',
                    AuthEvent.success == False,
                    AuthEvent.created_at >= cutoff_time
                ))
            )
            failed_count = failed_result.scalar() or 0
            
            # Count successful logins
            success_result = await session.execute(
                select(func.count()).where(and_(
                    AuthEvent.event_type == 'login',
                    AuthEvent.success == True,
                    AuthEvent.created_at >= cutoff_time
                ))
            )
            success_count = success_result.scalar() or 0
            
            # Top failure reasons
            reason_result = await session.execute(
                select(
                    AuthEvent.failure_reason,
                    func.count().label('count')
                ).where(and_(
                    AuthEvent.event_type == 'login',
                    AuthEvent.success == False,
                    AuthEvent.created_at >= cutoff_time,
                    AuthEvent.failure_reason.isnot(None)
                )).group_by(AuthEvent.failure_reason).order_by(desc('count')).limit(10)
            )
            
            failure_reasons = [
                {'reason': row.failure_reason, 'count': row.count}
                for row in reason_result
            ]
            
            return {
                'period_hours': hours_back,
                'failed_logins': failed_count,
                'successful_logins': success_count,
                'failure_rate': round(failed_count / max(failed_count + success_count, 1) * 100, 2),
                'top_failure_reasons': failure_reasons
            }
            
        except Exception as e:
            logger.error(f"Failed to get failed login stats: {e}")
            return {
                'period_hours': hours_back,
                'failed_logins': 0,
                'successful_logins': 0,
                'failure_rate': 0.0,
                'top_failure_reasons': []
            }