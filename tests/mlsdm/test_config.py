"""Tests for configuration loader."""

import os
import pytest
from src.mlsdm.utils.config_loader import (
    get_settings,
    reload_settings,
    SecuritySettings,
    ServerSettings,
    NeuroEngineSettings,
    StorageSettings,
    MLSDMSettings
)


def test_default_settings():
    """Test default configuration values."""
    settings = MLSDMSettings()
    
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.server.host == "0.0.0.0"
    assert settings.server.port == 8000
    assert settings.security.auth_mode == "api_key"
    assert settings.neuro.n_neurons == 100
    assert settings.neuro.seed == 42


def test_env_override(monkeypatch):
    """Test environment variable override."""
    monkeypatch.setenv("MLSDM_ENVIRONMENT", "production")
    monkeypatch.setenv("MLSDM_DEBUG", "true")
    monkeypatch.setenv("MLSDM_SERVER__PORT", "9000")
    monkeypatch.setenv("MLSDM_SECURITY__AUTH_MODE", "none")
    
    settings = MLSDMSettings()
    
    assert settings.environment == "production"
    assert settings.debug is True
    assert settings.server.port == 9000
    assert settings.security.auth_mode == "none"


def test_security_settings():
    """Test security settings."""
    settings = SecuritySettings(
        auth_mode="oidc",
        oidc_issuer="https://auth.example.com",
        mtls_enabled=True
    )
    
    assert settings.auth_mode == "oidc"
    assert settings.oidc_issuer == "https://auth.example.com"
    assert settings.mtls_enabled is True


def test_get_settings_singleton():
    """Test settings singleton behavior."""
    settings1 = get_settings()
    settings2 = get_settings()
    
    assert settings1 is settings2


def test_reload_settings():
    """Test settings reload."""
    settings1 = get_settings()
    settings2 = reload_settings()
    
    # Should be different instances
    assert settings1 is not settings2
    # But with same values (if env hasn't changed)
    assert settings1.environment == settings2.environment
