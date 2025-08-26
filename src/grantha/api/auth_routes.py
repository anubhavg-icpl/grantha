"""Enhanced authentication routes with database integration."""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import (
    get_db_session, UserService, RefreshTokenService, 
    AuthEventService, database_jwt_service
)
from ..models.api_models import (
    LoginRequest, LoginResponse, RefreshTokenRequest, RefreshTokenResponse,
    LogoutRequest, TokenInfoResponse, UserRegistrationRequest, UserResponse,
    ChangePasswordRequest, AuthStatusResponse
)
from ..core.config import get_config

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

# Create router
enhanced_auth_router = APIRouter()


def get_client_info(request: Request) -> dict:
    """Extract client information from request."""
    return {
        'ip_address': request.client.host if request.client else None,
        'user_agent': request.headers.get('user-agent'),
        'device_fingerprint': request.headers.get('x-device-fingerprint')
    }


@enhanced_auth_router.post("/register", response_model=UserResponse)
async def register_user(
    request: UserRegistrationRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Register a new user account."""
    try:
        client_info = get_client_info(http_request)
        
        # Check if user already exists
        existing_user = await UserService.get_user_by_username(db, request.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        if request.email:
            existing_email = await UserService.get_user_by_email(db, request.email)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Create user
        user = await UserService.create_user(
            session=db,
            username=request.username,
            password=request.password,
            email=request.email,
            full_name=request.full_name,
            bio=request.bio
        )
        
        # Log registration event
        await AuthEventService.log_event(
            session=db,
            event_type="registration",
            user_id=str(user.id),
            success=True,
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent'],
            device_fingerprint=client_info['device_fingerprint']
        )
        
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            bio=user.bio,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            created_at=user.created_at.isoformat() if user.created_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@enhanced_auth_router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Authenticate user and return JWT tokens."""
    try:
        client_info = get_client_info(http_request)
        
        # Authenticate user and generate tokens
        access_token, refresh_token, user_info = await database_jwt_service.authenticate_and_generate_tokens(
            session=db,
            username=request.username,
            password=request.password,
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent'],
            device_fingerprint=client_info['device_fingerprint'],
            additional_claims={
                "auth_method": "password"
            }
        )
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60,  # 30 minutes
            user_id=user_info['id'],
            username=user_info['username'],
            email=user_info['email'],
            full_name=user_info['full_name'],
            is_verified=user_info['is_verified'],
            is_superuser=user_info['is_superuser']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@enhanced_auth_router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """Refresh access token using refresh token."""
    try:
        client_info = get_client_info(http_request)
        
        access_token, user_info = await database_jwt_service.refresh_access_token(
            session=db,
            refresh_token=request.refresh_token
        )
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Log token refresh event
        await AuthEventService.log_event(
            session=db,
            event_type="token_refresh",
            user_id=user_info['id'],
            success=True,
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent']
        )
        
        return RefreshTokenResponse(
            access_token=access_token,
            expires_in=30 * 60  # 30 minutes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@enhanced_auth_router.post("/logout")
async def logout(
    http_request: Request,
    logout_request: Optional[LogoutRequest] = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db_session)
):
    """Logout user and revoke tokens."""
    try:
        client_info = get_client_info(http_request)
        
        access_token = credentials.credentials if credentials else None
        refresh_token = logout_request.refresh_token if logout_request else None
        revoke_all = logout_request.revoke_all if logout_request else False
        
        logout_result = await database_jwt_service.logout_user(
            session=db,
            access_token=access_token,
            refresh_token=refresh_token,
            revoke_all=revoke_all,
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent']
        )
        
        return {
            "message": logout_result['message'],
            "revoked_tokens": logout_result['revoked_tokens']
        }
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@enhanced_auth_router.get("/me", response_model=UserResponse)
async def get_current_user(
    http_request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
):
    """Get current user information."""
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Validate access token
        token_payload = database_jwt_service.validate_access_token(credentials.credentials)
        if not token_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = token_payload.get('user_id')
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user from database
        user = await UserService.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            bio=user.bio,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            created_at=user.created_at.isoformat() if user.created_at else None,
            last_login=user.last_login.isoformat() if user.last_login else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@enhanced_auth_router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: dict,
    http_request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
):
    """Update current user information."""
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Validate access token
        token_payload = database_jwt_service.validate_access_token(credentials.credentials)
        if not token_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = token_payload.get('user_id')
        client_info = get_client_info(http_request)
        
        # Update user
        updated_user = await UserService.update_user(db, user_id, **update_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Log profile update event
        await AuthEventService.log_event(
            session=db,
            event_type="profile_update",
            user_id=user_id,
            success=True,
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent'],
            event_metadata={'updated_fields': list(update_data.keys())}
        )
        
        return UserResponse(
            id=str(updated_user.id),
            username=updated_user.username,
            email=updated_user.email,
            full_name=updated_user.full_name,
            bio=updated_user.bio,
            is_active=updated_user.is_active,
            is_verified=updated_user.is_verified,
            is_superuser=updated_user.is_superuser,
            created_at=updated_user.created_at.isoformat() if updated_user.created_at else None,
            last_login=updated_user.last_login.isoformat() if updated_user.last_login else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user information"
        )


@enhanced_auth_router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    http_request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
):
    """Change user password."""
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Validate access token
        token_payload = database_jwt_service.validate_access_token(credentials.credentials)
        if not token_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = token_payload.get('user_id')
        client_info = get_client_info(http_request)
        
        # Get current user
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not user.verify_password(request.current_password):
            await AuthEventService.log_event(
                session=db,
                event_type="password_change",
                user_id=user_id,
                success=False,
                failure_reason="incorrect_current_password",
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent']
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        await UserService.update_user(db, user_id, password=request.new_password)
        
        # Revoke all refresh tokens for security
        revoked_count = await RefreshTokenService.revoke_all_user_tokens(
            db, user_id, "password_change"
        )
        
        # Log successful password change
        await AuthEventService.log_event(
            session=db,
            event_type="password_change",
            user_id=user_id,
            success=True,
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent'],
            event_metadata={'revoked_tokens': revoked_count}
        )
        
        return {
            "message": "Password changed successfully",
            "revoked_tokens": revoked_count,
            "note": "All sessions have been logged out for security"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@enhanced_auth_router.get("/sessions")
async def get_user_sessions(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user's active sessions."""
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Validate access token
        token_payload = database_jwt_service.validate_access_token(credentials.credentials)
        if not token_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = token_payload.get('user_id')
        
        sessions = await database_jwt_service.get_user_sessions(db, user_id)
        
        return {
            "sessions": sessions,
            "count": len(sessions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get sessions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sessions"
        )


@enhanced_auth_router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    http_request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
):
    """Revoke a specific session."""
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Validate access token
        token_payload = database_jwt_service.validate_access_token(credentials.credentials)
        if not token_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = token_payload.get('user_id')
        
        success = await database_jwt_service.revoke_session(
            db, user_id, session_id, "manual_revoke"
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return {"message": "Session revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )


# Legacy compatibility endpoints
@enhanced_auth_router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status():
    """Check if authentication is required (legacy compatibility)."""
    config = get_config()
    return AuthStatusResponse(auth_required=config.wiki_auth_mode)


@enhanced_auth_router.get("/token/info", response_model=TokenInfoResponse)
async def get_token_info(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get information about the current token (legacy compatibility)."""
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        token_info = database_jwt_service.get_token_info(credentials.credentials)
        if not token_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return TokenInfoResponse(
            user_id=token_info['user_id'],
            token_type=token_info['type'],
            issued_at=token_info['issued_at'],
            expires_at=token_info['expires_at'],
            is_expired=token_info['is_expired'],
            is_revoked=token_info.get('is_revoked', False),
            jti=token_info['jti']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get token info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get token info"
        )