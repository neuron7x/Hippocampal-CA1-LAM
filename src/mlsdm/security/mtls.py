"""mTLS configuration and middleware (placeholder)."""

from typing import Optional
from pathlib import Path
import logging
import ssl

logger = logging.getLogger(__name__)


class MTLSConfig:
    """mTLS configuration."""
    
    def __init__(
        self,
        ca_cert: Path,
        client_cert: Optional[Path] = None,
        client_key: Optional[Path] = None
    ):
        """
        Initialize mTLS configuration.
        
        Args:
            ca_cert: Path to CA certificate
            client_cert: Path to client certificate
            client_key: Path to client key
        """
        self.ca_cert = ca_cert
        self.client_cert = client_cert
        self.client_key = client_key
        logger.info(f"Initialized mTLS config with CA: {ca_cert}")
    
    def create_ssl_context(self) -> ssl.SSLContext:
        """
        Create SSL context for mTLS.
        
        Returns:
            Configured SSL context
        """
        context = ssl.create_default_context(
            purpose=ssl.Purpose.CLIENT_AUTH,
            cafile=str(self.ca_cert)
        )
        
        if self.client_cert and self.client_key:
            context.load_cert_chain(
                certfile=str(self.client_cert),
                keyfile=str(self.client_key)
            )
        
        context.verify_mode = ssl.CERT_REQUIRED
        return context


def get_mtls_context() -> Optional[ssl.SSLContext]:
    """
    Get mTLS SSL context if enabled.
    
    Returns:
        SSL context if mTLS is enabled, None otherwise
    """
    from ..utils.config_loader import get_settings
    
    settings = get_settings()
    
    if not settings.security.mtls_enabled:
        return None
    
    if not settings.security.mtls_ca_cert:
        logger.error("mTLS enabled but no CA cert configured")
        return None
    
    config = MTLSConfig(
        ca_cert=settings.security.mtls_ca_cert,
        client_cert=settings.security.mtls_client_cert,
        client_key=settings.security.mtls_client_key
    )
    
    return config.create_ssl_context()
