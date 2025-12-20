"""Tests for API health endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.mlsdm.api.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_liveness(client):
    """Test liveness endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert data["service"] == "mlsdm-api"
    assert "timestamp" in data


def test_healthz_alias(client):
    """Test healthz alias endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


def test_readiness(client):
    """Test readiness endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
    assert "checks" in data
    assert "timestamp" in data


def test_readyz_alias(client):
    """Test readyz alias endpoint."""
    response = client.get("/readyz")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True


def test_metrics(client):
    """Test metrics endpoint."""
    response = client.get("/health/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "process_id" in data
    assert "cpu_percent" in data
    assert "memory_mb" in data
    assert "memory_percent" in data
    assert "uptime_seconds" in data


def test_metrics_alias(client):
    """Test metrics alias endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "memory_mb" in data
