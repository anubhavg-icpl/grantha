"""Enhanced JWT service with database integration."""

import os
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple, List

import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession

from .services import UserService, RefreshTokenService, AuthEventService
from ..utils.jwt_service import JWTService as BaseJWTService

logger = logging.getLogger(__name__)


class DatabaseJWTService:
    """Enhanced JWT service with database persistence."""
    
    def __init__(self):
        self.secret_key = os.environ.get('SECRET_KEY', 'grantha_dev_secret_change_in_production')
        self.algorithm = 'HS256'
        self.access_token_expires_minutes = 30  # Access token expires in 30 minutes
        self.refresh_token_expires_days = 7     # Refresh token expires in 7 days
        
        # Keep a fallback to the original service for compatibility
        self._fallback_service = BaseJWTService()
    
    async def authenticate_and_generate_tokens(
        self,
        session: AsyncSession,
        username: str,
        password: str,
        ip_address: str = None,
        user_agent: str = None,
        device_fingerprint: str = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """
        Authenticate user and generate JWT tokens with database persistence.
        
        Returns:
            Tuple of (access_token, refresh_token, user_info) or (None, None, None) if failed
        """
        try:
            # Authenticate user
            user, success = await UserService.authenticate_user(
                session, username, password, ip_address, user_agent
            )
            
            if not success or not user:
                logger.warning(f"Authentication failed for user: {username}")
                return None, None, None
            
            # Generate tokens
            now = datetime.now(timezone.utc)
            user_id = str(user.id)
            
            # Generate access token
            access_payload = {
                'user_id': user_id,
                'username': user.username,
                'type': 'access',
                'iat': now,
                'exp': now + timedelta(minutes=self.access_token_expires_minutes),
                'jti': str(uuid.uuid4())
            }
            
            # Add additional claims if provided
            if additional_claims:
                access_payload.update(additional_claims)
            
            access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
            
            # Generate refresh token
            refresh_jti = str(uuid.uuid4())
            refresh_payload = {
                'user_id': user_id,
                'username': user.username,
                'type': 'refresh',
                'iat': now,
                'exp': now + timedelta(days=self.refresh_token_expires_days),
                'jti': refresh_jti
            }
            
            refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
            
            # Store refresh token in database
            await RefreshTokenService.create_refresh_token(
                session=session,
                user_id=user_id,
                token_id=refresh_jti,
                expires_at=now + timedelta(days=self.refresh_token_expires_days),
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint
            )
            
            user_info = {
                'id': user_id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'is_verified': user.is_verified,
                'is_superuser': user.is_superuser
            }
            
            logger.info(f"Generated tokens for user {username} (id: {user_id})")
            return access_token, refresh_token, user_info
            
        except Exception as e:
            logger.error(f"Error generating tokens for user {username}: {e}")
            return None, None, None
    
    async def refresh_access_token(
        self,
        session: AsyncSession,
        refresh_token: str
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Generate a new access token using a valid refresh token.
        
        Returns:
            Tuple of (access_token, user_info) or (None, None) if failed
        """
        try:
            # Decode and validate refresh token
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get('type') != 'refresh':
                logger.warning("Invalid token type for refresh")
                return None, None
            
            refresh_jti = payload.get('jti')
            user_id = payload.get('user_id')
            
            if not refresh_jti or not user_id:
                logger.warning("Missing JTI or user_id in refresh token")
                return None, None
            
            # Validate refresh token in database
            db_token = await RefreshTokenService.validate_refresh_token(session, refresh_jti)
            if not db_token:
                logger.warning(f"Refresh token {refresh_jti} is invalid or expired")
                return None, None
            
            # Get user information
            user = await UserService.get_user_by_id(session, user_id)
            if not user or not user.is_active:
                logger.warning(f"User {user_id} not found or inactive")
                return None, None
            
            # Generate new access token
            now = datetime.now(timezone.utc)
            access_payload = {
                'user_id': user_id,
                'username': user.username,
                'type': 'access',
                'iat': now,
                'exp': now + timedelta(minutes=self.access_token_expires_minutes),
                'jti': str(uuid.uuid4())
            }
            
            new_access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
            
            user_info = {
                'id': user_id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'is_verified': user.is_verified,
                'is_superuser': user.is_superuser
            }
            
            logger.info(f"Refreshed access token for user {user.username}")
            return new_access_token, user_info
            
        except ExpiredSignatureError:
            logger.warning("Refresh token has expired")
            return None, None
        except InvalidTokenError as e:
            logger.warning(f"Invalid refresh token: {str(e)}")
            return None, None
        except Exception as e:
            logger.error(f"Error refreshing access token: {e}")
            return None, None
    
    def validate_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate an access token and return its payload.
        
        This method doesn't require database access for basic validation.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get('type') != 'access':
                logger.warning(f"Invalid token type: {payload.get('type')}")
                return None
            
            return payload
            
        except ExpiredSignatureError:
            logger.warning("Access token has expired")
            return None
        except InvalidTokenError as e:
            logger.warning(f"Invalid access token: {str(e)}")
            return None
    
    async def logout_user(
        self,
        session: AsyncSession,
        access_token: str = None,
        refresh_token: str = None,
        revoke_all: bool = False,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        Logout user by revoking tokens.
        
        Returns:
            Dictionary with logout status and details
        """
        try:
            user_id = None
            revoked_count = 0
            
            # Try to get user ID from access token
            if access_token:
                try:
                    payload = jwt.decode(
                        access_token, 
                        self.secret_key, 
                        algorithms=[self.algorithm], 
                        options={"verify_exp": False}
                    )
                    user_id = payload.get('user_id')
                except InvalidTokenError:
                    pass
            
            # Revoke refresh token if provided
            if refresh_token:
                try:
                    refresh_payload = jwt.decode(
                        refresh_token, 
                        self.secret_key, 
                        algorithms=[self.algorithm], 
                        options={"verify_exp": False}
                    )
                    refresh_jti = refresh_payload.get('jti')
                    if not user_id:
                        user_id = refresh_payload.get('user_id')
                    
                    if refresh_jti:
                        success = await RefreshTokenService.revoke_refresh_token(
                            session, refresh_jti, "logout"
                        )
                        if success:
                            revoked_count += 1
                            
                except InvalidTokenError:
                    pass
            
            # Revoke all tokens for user if requested
            if revoke_all and user_id:
                additional_revoked = await RefreshTokenService.revoke_all_user_tokens(
                    session, user_id, "logout_all"
                )
                revoked_count += additional_revoked
            
            # Log logout event
            if user_id:
                await AuthEventService.log_event(
                    session=session,
                    event_type="logout",
                    user_id=user_id,
                    success=True,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    event_metadata={
                        'revoked_tokens': revoked_count,
                        'logout_all': revoke_all
                    }
                )
            
            logger.info(f"Logged out user {user_id}, revoked {revoked_count} tokens")
            
            return {
                'success': True,
                'user_id': user_id,
                'revoked_tokens': revoked_count,
                'message': f"Successfully logged out, revoked {revoked_count} tokens"
            }
            
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return {
                'success': False,
                'user_id': None,
                'revoked_tokens': 0,
                'message': f"Logout failed: {str(e)}"
            }
    
    async def get_user_sessions(
        self,
        session: AsyncSession,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get active sessions (refresh tokens) for a user."""
        try:
            tokens = await RefreshTokenService.get_user_active_tokens(session, user_id)
            
            sessions = []
            for token in tokens:
                sessions.append({
                    'id': str(token.id),
                    'token_id': token.token_id,
                    'created_at': token.created_at.isoformat(),
                    'expires_at': token.expires_at.isoformat(),
                    'ip_address': token.ip_address,
                    'user_agent': token.user_agent,
                    'device_fingerprint': token.device_fingerprint,
                    'is_current': False  # This would need additional logic to determine
                })
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting user sessions for {user_id}: {e}")
            return []
    
    async def revoke_session(
        self,
        session: AsyncSession,
        user_id: str,
        session_id: str,
        reason: str = "manual"
    ) -> bool:
        """Revoke a specific session by token ID."""
        try:
            # Verify the token belongs to the user
            token = await RefreshTokenService.get_refresh_token(session, session_id)
            if not token or str(token.user_id) != user_id:
                return False
            
            success = await RefreshTokenService.revoke_refresh_token(
                session, session_id, reason
            )
            
            if success:
                await AuthEventService.log_event(
                    session=session,
                    event_type="session_revoked",
                    user_id=user_id,
                    success=True,
                    event_metadata={'session_id': session_id, 'reason': reason}
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error revoking session {session_id} for user {user_id}: {e}")
            return False
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a token without validating expiration.
        
        This is a compatibility method that doesn't require database access.
        """
        return self._fallback_service.get_token_info(token)
    
    async def cleanup_expired_tokens(self, session: AsyncSession) -> int:
        """Clean up expired refresh tokens from database."""
        try:
            cleaned_count = await RefreshTokenService.cleanup_expired_tokens(session)
            logger.info(f"Cleaned up {cleaned_count} expired tokens")
            return cleaned_count
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            return 0


# Global enhanced JWT service instance
database_jwt_service = DatabaseJWTService()