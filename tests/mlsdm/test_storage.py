"""Tests for storage backend."""

import pytest
import tempfile
from pathlib import Path
from src.mlsdm.utils.storage import FileStorageBackend


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield FileStorageBackend(Path(tmpdir))


@pytest.mark.asyncio
async def test_save_and_load(temp_storage):
    """Test saving and loading data."""
    data = {"test": "value", "number": 42}
    
    await temp_storage.save("test_key", data, version=1)
    
    result = await temp_storage.load("test_key")
    assert result is not None
    assert result["version"] == 1
    assert result["data"] == data


@pytest.mark.asyncio
async def test_load_nonexistent(temp_storage):
    """Test loading nonexistent key."""
    result = await temp_storage.load("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_exists(temp_storage):
    """Test checking if key exists."""
    data = {"test": "value"}
    
    assert not await temp_storage.exists("test_key")
    
    await temp_storage.save("test_key", data)
    
    assert await temp_storage.exists("test_key")


@pytest.mark.asyncio
async def test_delete(temp_storage):
    """Test deleting data."""
    data = {"test": "value"}
    
    await temp_storage.save("test_key", data)
    assert await temp_storage.exists("test_key")
    
    deleted = await temp_storage.delete("test_key")
    assert deleted is True
    assert not await temp_storage.exists("test_key")


@pytest.mark.asyncio
async def test_delete_nonexistent(temp_storage):
    """Test deleting nonexistent key."""
    deleted = await temp_storage.delete("nonexistent")
    assert deleted is False


@pytest.mark.asyncio
async def test_atomic_save(temp_storage):
    """Test atomic save operation."""
    # Save initial data
    await temp_storage.save("test_key", {"value": 1}, version=1)
    
    # Save updated data - should be atomic
    await temp_storage.save("test_key", {"value": 2}, version=2)
    
    # Load should get the latest version
    result = await temp_storage.load("test_key")
    assert result["version"] == 2
    assert result["data"]["value"] == 2
