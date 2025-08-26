"""JWT Token Service for Grantha Authentication System."""

import os
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple

import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

logger = logging.getLogger(__name__)


class JWTService:
    """JWT service for token generation, validation, and refresh token management."""
    
    def __init__(self):
        self.secret_key = os.environ.get('SECRET_KEY', 'grantha_dev_secret_change_in_production')
        self.algorithm = 'HS256'
        self.access_token_expires_minutes = 30  # Access token expires in 30 minutes
        self.refresh_token_expires_days = 7     # Refresh token expires in 7 days
        
        # In-memory store for refresh tokens (in production, use Redis or database)
        self._refresh_tokens: Dict[str, Dict[str, Any]] = {}
        self._revoked_tokens: set = set()  # Track revoked tokens
    
    def generate_tokens(self, user_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
        """
        Generate access and refresh tokens for a user.
        
        Args:
            user_id: Unique identifier for the user
            additional_claims: Additional claims to include in the access token
        
        Returns:
            Tuple of (access_token, refresh_token)
        """
        now = datetime.now(timezone.utc)
        
        # Generate access token
        access_payload = {
            'user_id': user_id,
            'type': 'access',
            'iat': now,
            'exp': now + timedelta(minutes=self.access_token_expires_minutes),
            'jti': str(uuid.uuid4())  # Unique token ID
        }
        
        # Add additional claims if provided
        if additional_claims:
            access_payload.update(additional_claims)
        
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        
        # Generate refresh token
        refresh_jti = str(uuid.uuid4())
        refresh_payload = {
            'user_id': user_id,
            'type': 'refresh',
            'iat': now,
            'exp': now + timedelta(days=self.refresh_token_expires_days),
            'jti': refresh_jti
        }
        
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
        
        # Store refresh token metadata
        self._refresh_tokens[refresh_jti] = {
            'user_id': user_id,
            'created_at': now.isoformat(),
            'expires_at': (now + timedelta(days=self.refresh_token_expires_days)).isoformat(),
            'active': True
        }
        
        logger.info(f"Generated tokens for user {user_id}")
        return access_token, refresh_token
    
    def validate_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate an access token and return its payload.
        
        Args:
            token: JWT access token to validate
        
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token is revoked
            if payload.get('jti') in self._revoked_tokens:
                logger.warning(f"Access token {payload.get('jti')} is revoked")
                return None
            
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
    
    def validate_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a refresh token and return its payload.
        
        Args:
            token: JWT refresh token to validate
        
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get('type') != 'refresh':
                logger.warning(f"Invalid token type: {payload.get('type')}")
                return None
            
            # Check if refresh token is active
            jti = payload.get('jti')
            if not jti or jti not in self._refresh_tokens:
                logger.warning(f"Refresh token {jti} not found")
                return None
            
            if not self._refresh_tokens[jti]['active']:
                logger.warning(f"Refresh token {jti} is inactive")
                return None
            
            return payload
            
        except ExpiredSignatureError:
            logger.warning("Refresh token has expired")
            return None
        except InvalidTokenError as e:
            logger.warning(f"Invalid refresh token: {str(e)}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Generate a new access token using a valid refresh token.
        
        Args:
            refresh_token: Valid JWT refresh token
        
        Returns:
            New access token if refresh token is valid, None otherwise
        """
        payload = self.validate_refresh_token(refresh_token)
        if not payload:
            return None
        
        user_id = payload.get('user_id')
        if not user_id:
            logger.warning("No user_id in refresh token payload")
            return None
        
        # Generate new access token only
        now = datetime.now(timezone.utc)
        access_payload = {
            'user_id': user_id,
            'type': 'access',
            'iat': now,
            'exp': now + timedelta(minutes=self.access_token_expires_minutes),
            'jti': str(uuid.uuid4())  # Unique token ID
        }
        
        new_access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        return new_access_token
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token (add to revoked tokens list).
        
        Args:
            token: JWT token to revoke
        
        Returns:
            True if token was revoked, False otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            jti = payload.get('jti')
            
            if jti:
                self._revoked_tokens.add(jti)
                
                # If it's a refresh token, mark as inactive
                if payload.get('type') == 'refresh' and jti in self._refresh_tokens:
                    self._refresh_tokens[jti]['active'] = False
                
                logger.info(f"Revoked token {jti}")
                return True
            
        except InvalidTokenError as e:
            logger.warning(f"Could not revoke invalid token: {str(e)}")
        
        return False
    
    def revoke_user_tokens(self, user_id: str) -> int:
        """
        Revoke all tokens for a specific user.
        
        Args:
            user_id: User ID whose tokens should be revoked
        
        Returns:
            Number of refresh tokens revoked
        """
        revoked_count = 0
        
        for jti, token_data in self._refresh_tokens.items():
            if token_data['user_id'] == user_id and token_data['active']:
                token_data['active'] = False
                self._revoked_tokens.add(jti)
                revoked_count += 1
        
        logger.info(f"Revoked {revoked_count} tokens for user {user_id}")
        return revoked_count
    
    def cleanup_expired_tokens(self):
        """Clean up expired refresh tokens from memory."""
        now = datetime.now(timezone.utc)
        expired_tokens = []
        
        for jti, token_data in self._refresh_tokens.items():
            expires_at = datetime.fromisoformat(token_data['expires_at'].replace('Z', '+00:00'))
            if expires_at < now:
                expired_tokens.append(jti)
        
        for jti in expired_tokens:
            del self._refresh_tokens[jti]
            self._revoked_tokens.discard(jti)
        
        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a token without validating expiration.
        
        Args:
            token: JWT token to inspect
        
        Returns:
            Token information if valid format, None otherwise
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm], 
                options={"verify_exp": False}
            )
            
            return {
                'user_id': payload.get('user_id'),
                'type': payload.get('type'),
                'jti': payload.get('jti'),
                'issued_at': payload.get('iat'),
                'expires_at': payload.get('exp'),
                'is_expired': datetime.now(timezone.utc).timestamp() > payload.get('exp', 0),
                'is_revoked': payload.get('jti') in self._revoked_tokens
            }
            
        except InvalidTokenError as e:
            logger.warning(f"Could not decode token: {str(e)}")
            return None


# Global JWT service instance
jwt_service = JWTService()