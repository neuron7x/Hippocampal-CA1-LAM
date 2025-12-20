"""Configuration loader and validator using Pydantic Settings."""

from typing import Optional, Literal
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import os
from pathlib import Path


class SecuritySettings(BaseSettings):
    """Security configuration."""
    
    auth_mode: Literal["api_key", "oidc", "none"] = Field(
        default="api_key",
        description="Authentication mode"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication"
    )
    oidc_issuer: Optional[str] = Field(
        default=None,
        description="OIDC issuer URL"
    )
    oidc_audience: Optional[str] = Field(
        default=None,
        description="OIDC audience"
    )
    mtls_enabled: bool = Field(
        default=False,
        description="Enable mTLS verification"
    )
    mtls_ca_cert: Optional[Path] = Field(
        default=None,
        description="Path to CA certificate for mTLS"
    )
    mtls_client_cert: Optional[Path] = Field(
        default=None,
        description="Path to client certificate"
    )
    mtls_client_key: Optional[Path] = Field(
        default=None,
        description="Path to client key"
    )
    
    class Config:
        env_prefix = "MLSDM_SECURITY_"
        case_sensitive = False


class ServerSettings(BaseSettings):
    """Server configuration."""
    
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")
    log_level: str = Field(default="info", description="Logging level")
    reload: bool = Field(default=False, description="Enable auto-reload")
    
    class Config:
        env_prefix = "MLSDM_SERVER_"
        case_sensitive = False


class NeuroEngineSettings(BaseSettings):
    """Neuro engine configuration."""
    
    n_neurons: int = Field(default=100, description="Number of neurons")
    seed: int = Field(default=42, description="Random seed for reproducibility")
    dt: float = Field(default=0.1, description="Time step in ms")
    
    class Config:
        env_prefix = "MLSDM_NEURO_"
        case_sensitive = False


class StorageSettings(BaseSettings):
    """Storage backend configuration."""
    
    backend: Literal["file", "sqlite", "postgres", "redis"] = Field(
        default="file",
        description="Storage backend type"
    )
    file_path: Path = Field(
        default=Path("/tmp/mlsdm_state"),
        description="Path for file-based storage"
    )
    database_url: Optional[str] = Field(
        default=None,
        description="Database connection URL"
    )
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL"
    )
    
    class Config:
        env_prefix = "MLSDM_STORAGE_"
        case_sensitive = False


class MLSDMSettings(BaseSettings):
    """Main MLSDM configuration."""
    
    # Sub-configurations
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    neuro: NeuroEngineSettings = Field(default_factory=NeuroEngineSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    
    # Global settings
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment"
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    
    class Config:
        env_prefix = "MLSDM_"
        case_sensitive = False
        env_nested_delimiter = "__"
    
    @field_validator("security", mode='before')
    @classmethod
    def load_security(cls, v):
        """Load security settings from environment."""
        if isinstance(v, dict):
            return SecuritySettings(**v)
        return v or SecuritySettings()
    
    @field_validator("server", mode='before')
    @classmethod
    def load_server(cls, v):
        """Load server settings from environment."""
        if isinstance(v, dict):
            return ServerSettings(**v)
        return v or ServerSettings()
    
    @field_validator("neuro", mode='before')
    @classmethod
    def load_neuro(cls, v):
        """Load neuro settings from environment."""
        if isinstance(v, dict):
            return NeuroEngineSettings(**v)
        return v or NeuroEngineSettings()
    
    @field_validator("storage", mode='before')
    @classmethod
    def load_storage(cls, v):
        """Load storage settings from environment."""
        if isinstance(v, dict):
            return StorageSettings(**v)
        return v or StorageSettings()


# Global settings instance
_settings: Optional[MLSDMSettings] = None


def get_settings() -> MLSDMSettings:
    """Get global settings instance (singleton)."""
    global _settings
    if _settings is None:
        _settings = MLSDMSettings()
    return _settings


def reload_settings() -> MLSDMSettings:
    """Reload settings from environment."""
    global _settings
    _settings = MLSDMSettings()
    return _settings
