"""Health and metrics endpoints for the API."""

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from typing import Dict, Optional
import time
import psutil
import os


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: float
    service: str = "mlsdm-api"


class ReadinessResponse(BaseModel):
    """Readiness check response model."""
    ready: bool
    timestamp: float
    checks: Dict[str, bool]


class MetricsResponse(BaseModel):
    """Metrics response model."""
    timestamp: float
    process_id: int
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    uptime_seconds: float


# Track service start time
_start_time = time.time()


@router.get("/health", response_model=HealthResponse, tags=["health"])
@router.get("/health/live", response_model=HealthResponse, tags=["health"])
@router.get("/healthz", response_model=HealthResponse, tags=["health"])
async def liveness() -> HealthResponse:
    """
    Liveness probe - checks if the service is alive.
    Returns 200 if the service is running.
    """
    return HealthResponse(
        status="alive",
        timestamp=time.time()
    )


@router.get("/health/ready", response_model=ReadinessResponse, tags=["health"])
@router.get("/readyz", response_model=ReadinessResponse, tags=["health"])
async def readiness() -> ReadinessResponse:
    """
    Readiness probe - checks if the service is ready to accept traffic.
    Returns 200 if all dependencies are available.
    """
    # TODO: Add actual dependency checks (database, cache, etc.)
    checks = {
        "api": True,
        "storage": True,  # Placeholder
    }
    
    return ReadinessResponse(
        ready=all(checks.values()),
        timestamp=time.time(),
        checks=checks
    )


@router.get("/health/metrics", response_model=MetricsResponse, tags=["health"])
@router.get("/metrics", response_model=MetricsResponse, tags=["health"])
async def metrics() -> MetricsResponse:
    """
    Metrics endpoint - provides runtime metrics.
    Returns process and system metrics.
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return MetricsResponse(
        timestamp=time.time(),
        process_id=os.getpid(),
        cpu_percent=process.cpu_percent(interval=0.1),
        memory_mb=memory_info.rss / (1024 * 1024),
        memory_percent=process.memory_percent(),
        uptime_seconds=time.time() - _start_time
    )
