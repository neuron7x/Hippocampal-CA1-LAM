"""Storage backend interface and implementations."""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
import json
import logging
from pathlib import Path
import pickle

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract storage backend interface."""
    
    @abstractmethod
    async def save(self, key: str, data: Any, version: int = 1) -> None:
        """
        Save data with versioning.
        
        Args:
            key: Storage key
            data: Data to save
            version: Data format version
        """
        pass
    
    @abstractmethod
    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load data from storage.
        
        Args:
            key: Storage key
            
        Returns:
            Loaded data with version info, or None if not found
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete data from storage.
        
        Args:
            key: Storage key
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists.
        
        Args:
            key: Storage key
            
        Returns:
            True if exists, False otherwise
        """
        pass


class FileStorageBackend(StorageBackend):
    """File-based storage backend."""
    
    def __init__(self, base_path: Path):
        """
        Initialize file storage backend.
        
        Args:
            base_path: Base directory for storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized FileStorageBackend at {base_path}")
    
    def _get_path(self, key: str) -> Path:
        """Get file path for key."""
        # Sanitize key to be filesystem-safe
        safe_key = key.replace('/', '_').replace('\\', '_')
        return self.base_path / f"{safe_key}.pkl"
    
    async def save(self, key: str, data: Any, version: int = 1) -> None:
        """Save data to file with atomic write."""
        file_path = self._get_path(key)
        temp_path = file_path.with_suffix('.tmp')
        
        payload = {
            'version': version,
            'data': data
        }
        
        try:
            # Write to temporary file first
            with open(temp_path, 'wb') as f:
                pickle.dump(payload, f)
            
            # Atomic rename
            temp_path.replace(file_path)
            logger.debug(f"Saved {key} to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save {key}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise
    
    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load data from file."""
        file_path = self._get_path(key)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'rb') as f:
                payload = pickle.load(f)
            logger.debug(f"Loaded {key} from {file_path}")
            return payload
        except Exception as e:
            logger.error(f"Failed to load {key}: {e}")
            raise
    
    async def delete(self, key: str) -> bool:
        """Delete file."""
        file_path = self._get_path(key)
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            logger.debug(f"Deleted {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {key}: {e}")
            raise
    
    async def exists(self, key: str) -> bool:
        """Check if file exists."""
        return self._get_path(key).exists()


def get_storage_backend() -> StorageBackend:
    """
    Get storage backend based on configuration.
    
    Returns:
        Configured storage backend
    """
    from ..utils.config_loader import get_settings
    
    settings = get_settings()
    
    if settings.storage.backend == "file":
        return FileStorageBackend(settings.storage.file_path)
    elif settings.storage.backend == "sqlite":
        # TODO: Implement SQLite backend
        logger.warning("SQLite backend not yet implemented, falling back to file")
        return FileStorageBackend(settings.storage.file_path)
    elif settings.storage.backend == "postgres":
        # TODO: Implement Postgres backend
        logger.warning("Postgres backend not yet implemented, falling back to file")
        return FileStorageBackend(settings.storage.file_path)
    elif settings.storage.backend == "redis":
        # TODO: Implement Redis backend
        logger.warning("Redis backend not yet implemented, falling back to file")
        return FileStorageBackend(settings.storage.file_path)
    else:
        raise ValueError(f"Unknown storage backend: {settings.storage.backend}")
