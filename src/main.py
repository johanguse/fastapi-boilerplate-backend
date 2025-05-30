"""
FastAPI Boilerplate - Main Application Entry Point
Domain-Driven Design Structure
"""

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
import logging
import time

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from src.auth.router import router as auth_router
from src.config.settings import config
from src.projects.router import router as projects_router
from src.teams.router import router as teams_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {config.APP_NAME} v{config.APP_VERSION}")
    yield
    # Shutdown
    logger.info("Shutting down application")


async def add_process_time_header(request: Request, call_next: Callable) -> Response:
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


async def logger_exception_handler(
    _request: Request, exc: HTTPException
) -> HTTPException:
    """Log HTTP exceptions."""
    logger.error(f"HTTPException: {exc.status_code} - {exc.detail}")
    raise exc


app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    debug=config.DEBUG,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add correlation ID middleware
app.add_middleware(CorrelationIdMiddleware, header_name="X-Correlation-ID")

# Add process time middleware
app.middleware("http")(add_process_time_header)

# Add exception handler
app.exception_handler(HTTPException)(logger_exception_handler)

# Include domain routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(teams_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": f"Welcome to {config.APP_NAME} API"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": config.APP_VERSION}
