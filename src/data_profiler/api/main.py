"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from data_profiler import __version__
from data_profiler.api.routes import profile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    logger.info("Starting Data Profiler API v%s", __version__)
    yield
    logger.info("Shutting down Data Profiler API")


# Create FastAPI application
app = FastAPI(
    title="Data Profiler API",
    description="High-performance data profiling service for analyzing datasets at scale",
    version=__version__,
    lifespan=lifespan,
    default_response_class=ORJSONResponse,  # Use orjson for faster JSON serialization
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(profile.router, prefix="/api/v1", tags=["profiling"])


@app.get("/", tags=["health"])
async def root() -> dict:
    """Root endpoint."""
    return {
        "service": "Data Profiler API",
        "version": __version__,
        "status": "operational",
    }


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": __version__}
