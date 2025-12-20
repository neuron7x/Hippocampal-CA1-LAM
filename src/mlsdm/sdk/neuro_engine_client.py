"""Python SDK for MLSDM neuro engine."""

from typing import List, Optional, Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)


class NeuroEngineClient:
    """Client for MLSDM Neuro Engine."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize neuro engine client.
        
        Args:
            base_url: Base URL of the neuro engine service
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)
        
        logger.info(f"Initialized NeuroEngineClient for {base_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def health(self) -> Dict[str, Any]:
        """
        Check service health.
        
        Returns:
            Health status
        """
        response = self._client.get(
            f"{self.base_url}/healthz",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def metrics(self) -> Dict[str, Any]:
        """
        Get service metrics.
        
        Returns:
            Service metrics
        """
        response = self._client.get(
            f"{self.base_url}/metrics",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def generate(
        self,
        input_pattern: List[float],
        steps: int = 10
    ) -> Dict[str, Any]:
        """
        Generate neural response from input pattern.
        
        Args:
            input_pattern: Input pattern to process
            steps: Number of simulation steps
            
        Returns:
            Generation response with output pattern
        """
        payload = {
            "input_pattern": input_pattern,
            "steps": steps
        }
        
        response = self._client.post(
            f"{self.base_url}/v1/neuro/generate",
            json=payload,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def info(self) -> Dict[str, Any]:
        """
        Get neuro engine information.
        
        Returns:
            Engine information
        """
        response = self._client.get(
            f"{self.base_url}/v1/neuro/info",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def close(self):
        """Close the client connection."""
        self._client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class AsyncNeuroEngineClient:
    """Async client for MLSDM Neuro Engine."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize async neuro engine client.
        
        Args:
            base_url: Base URL of the neuro engine service
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
        
        logger.info(f"Initialized AsyncNeuroEngineClient for {base_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def health(self) -> Dict[str, Any]:
        """Check service health."""
        response = await self._client.get(
            f"{self.base_url}/healthz",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        response = await self._client.get(
            f"{self.base_url}/metrics",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def generate(
        self,
        input_pattern: List[float],
        steps: int = 10
    ) -> Dict[str, Any]:
        """Generate neural response from input pattern."""
        payload = {
            "input_pattern": input_pattern,
            "steps": steps
        }
        
        response = await self._client.post(
            f"{self.base_url}/v1/neuro/generate",
            json=payload,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def info(self) -> Dict[str, Any]:
        """Get neuro engine information."""
        response = await self._client.get(
            f"{self.base_url}/v1/neuro/info",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the client connection."""
        await self._client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
