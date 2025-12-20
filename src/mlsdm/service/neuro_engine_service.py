"""Neuro engine service wrapping CA1 network."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
import time
import numpy as np
import psutil
import os

from ...core.ca1_network import CA1Network
from ..api.health import HealthResponse, MetricsResponse, _start_time
from ..utils.config_loader import get_settings

logger = logging.getLogger(__name__)


class GenerateRequest(BaseModel):
    """Request for neural generation."""
    input_pattern: List[float]
    steps: int = 10


class GenerateResponse(BaseModel):
    """Response from neural generation."""
    output_pattern: List[float]
    processing_time_ms: float


def create_neuro_app() -> FastAPI:
    """Create neuro engine FastAPI application."""
    
    settings = get_settings()
    
    app = FastAPI(
        title="MLSDM Neuro Engine",
        description="Hippocampal CA1 Neural Engine Service",
        version="1.0.0",
        debug=settings.debug
    )
    
    # Initialize CA1 network
    network: Optional[CA1Network] = None
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize network on startup."""
        nonlocal network
        logger.info("Starting MLSDM Neuro Engine")
        logger.info(f"Initializing CA1 network with {settings.neuro.n_neurons} neurons")
        
        try:
            network = CA1Network(
                n_neurons=settings.neuro.n_neurons,
                seed=settings.neuro.seed
            )
            logger.info("CA1 network initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CA1 network: {e}")
            raise
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown."""
        logger.info("Shutting down MLSDM Neuro Engine")
    
    # Health endpoints
    @app.get("/healthz", response_model=HealthResponse, tags=["health"])
    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def liveness() -> HealthResponse:
        """Liveness probe."""
        return HealthResponse(
            status="alive",
            timestamp=time.time(),
            service="mlsdm-neuro"
        )
    
    @app.get("/readyz", response_model=HealthResponse, tags=["health"])
    async def readiness() -> HealthResponse:
        """Readiness probe."""
        if network is None:
            raise HTTPException(status_code=503, detail="Network not initialized")
        return HealthResponse(
            status="ready",
            timestamp=time.time(),
            service="mlsdm-neuro"
        )
    
    @app.get("/metrics", response_model=MetricsResponse, tags=["health"])
    async def metrics() -> MetricsResponse:
        """Metrics endpoint."""
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
    
    # Neuro endpoints
    @app.post("/v1/neuro/generate", response_model=GenerateResponse, tags=["neuro"])
    async def generate(request: GenerateRequest) -> GenerateResponse:
        """
        Generate neural response from input pattern.
        
        Args:
            request: Generation request with input pattern
            
        Returns:
            Generated output pattern
        """
        if network is None:
            raise HTTPException(status_code=503, detail="Network not initialized")
        
        start_time = time.time()
        
        try:
            # Convert input to numpy array
            input_array = np.array(request.input_pattern)
            
            # Run network simulation
            # For now, just echo the input (placeholder for actual processing)
            output_array = input_array.copy()
            
            processing_time = (time.time() - start_time) * 1000
            
            return GenerateResponse(
                output_pattern=output_array.tolist(),
                processing_time_ms=processing_time
            )
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/v1/neuro/info", tags=["neuro"])
    async def get_neuro_info():
        """Get neuro engine information."""
        return {
            "service": "mlsdm-neuro",
            "version": "1.0.0",
            "mode": "neuro",
            "network": {
                "n_neurons": settings.neuro.n_neurons,
                "seed": settings.neuro.seed,
                "initialized": network is not None
            }
        }
    
    return app


# Create neuro app instance
neuro_app = create_neuro_app()
