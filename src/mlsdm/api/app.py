"""Main FastAPI application."""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from .health import router as health_router
from ..security.auth import verify_api_key
from ..utils.config_loader import get_settings

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    settings = get_settings()
    
    app = FastAPI(
        title="MLSDM API",
        description="Hippocampal CA1 LAM - Memory Learning System API",
        version="1.0.0",
        debug=settings.debug
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure from settings
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    # Health endpoints don't require authentication
    app.include_router(health_router, prefix="", tags=["health"])
    
    # Protected API endpoints (require authentication)
    api_router = FastAPI()
    
    @api_router.get("/v1/info")
    async def get_info(api_key: str = Depends(verify_api_key)):
        """Get API information."""
        return {
            "service": "mlsdm-api",
            "version": "1.0.0",
            "mode": "api",
            "environment": settings.environment
        }
    
    # Mount protected endpoints
    app.mount("/api", api_router)
    
    @app.on_event("startup")
    async def startup_event():
        """Application startup handler."""
        logger.info("Starting MLSDM API service")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Auth mode: {settings.security.auth_mode}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown handler."""
        logger.info("Shutting down MLSDM API service")
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    return app


# Create app instance
app = create_app()
