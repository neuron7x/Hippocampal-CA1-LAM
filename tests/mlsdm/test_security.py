"""Tests for security authentication."""

import pytest
from fastapi import HTTPException
from src.mlsdm.security.auth import verify_api_key
from fastapi.security import HTTPAuthorizationCredentials


@pytest.mark.asyncio
async def test_verify_api_key_with_none_auth(monkeypatch):
    """Test API key verification when auth is disabled."""
    monkeypatch.setenv("MLSDM_SECURITY__AUTH_MODE", "none")
    from src.mlsdm.utils.config_loader import reload_settings
    reload_settings()
    
    result = await verify_api_key(None)
    assert result is None


@pytest.mark.asyncio
async def test_verify_api_key_missing_credentials(monkeypatch):
    """Test API key verification with missing credentials."""
    monkeypatch.setenv("MLSDM_SECURITY__AUTH_MODE", "api_key")
    monkeypatch.setenv("MLSDM_SECURITY__API_KEY", "test-key")
    from src.mlsdm.utils.config_loader import reload_settings
    reload_settings()
    
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(None)
    
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_verify_api_key_valid(monkeypatch):
    """Test API key verification with valid key."""
    monkeypatch.setenv("MLSDM_SECURITY__AUTH_MODE", "api_key")
    monkeypatch.setenv("MLSDM_SECURITY__API_KEY", "test-key")
    from src.mlsdm.utils.config_loader import reload_settings
    reload_settings()
    
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="test-key"
    )
    
    result = await verify_api_key(credentials)
    assert result == "test-key"


@pytest.mark.asyncio
async def test_verify_api_key_invalid(monkeypatch):
    """Test API key verification with invalid key."""
    monkeypatch.setenv("MLSDM_SECURITY__AUTH_MODE", "api_key")
    monkeypatch.setenv("MLSDM_SECURITY__API_KEY", "test-key")
    from src.mlsdm.utils.config_loader import reload_settings
    reload_settings()
    
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="wrong-key"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(credentials)
    
    assert exc_info.value.status_code == 403
