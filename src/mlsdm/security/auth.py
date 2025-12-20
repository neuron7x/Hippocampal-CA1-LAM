"""Security middleware and authentication."""

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Security scheme
security_scheme = HTTPBearer(auto_error=False)


async def verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)
) -> Optional[str]:
    """
    Verify API key from Authorization header.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        API key if valid, None if auth is disabled
        
    Raises:
        HTTPException: If authentication fails
    """
    from ..utils.config_loader import get_settings
    
    settings = get_settings()
    
    # If auth is disabled, allow all requests
    if settings.security.auth_mode == "none":
        return None
    
    # If auth is enabled, require valid credentials
    if credentials is None:
        logger.warning("Missing authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify API key
    if settings.security.auth_mode == "api_key":
        expected_key = settings.security.api_key
        if not expected_key:
            logger.error("API key auth enabled but no key configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication not configured properly"
            )
        
        if credentials.credentials != expected_key:
            logger.warning("Invalid API key provided")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key"
            )
        
        return credentials.credentials
    
    # OIDC mode
    if settings.security.auth_mode == "oidc":
        # TODO: Implement OIDC token verification
        logger.warning("OIDC auth not yet implemented")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OIDC authentication not yet implemented"
        )
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unknown authentication mode"
    )
