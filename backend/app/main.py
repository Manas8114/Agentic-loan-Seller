"""
FastAPI Application Entry Point

Main application configuration with middleware, routes, and lifecycle events.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.database import init_db, close_db
from app.api.v1 import api_router
from app.core.logging import get_logger, setup_logging


# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "Starting application",
        app_name=settings.app_name,
        version=settings.app_version,
        debug=settings.debug
    )
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    ## Agentic AI Personal Loan Sales System
    
    An intelligent loan origination system powered by multi-agent AI.
    
    ### Features
    - 🤖 **Conversational AI**: Natural language loan application
    - ✅ **Automated KYC**: Real-time identity verification
    - 📊 **Smart Underwriting**: Rule-based + ML risk assessment
    - 📄 **Instant Sanction**: Automated PDF generation
    
    ### Agents
    - **Master Agent**: Orchestrates conversation flow
    - **Sales Agent**: Collects loan requirements
    - **Verification Agent**: Handles KYC
    - **Underwriting Agent**: Makes credit decisions
    - **Sanction Agent**: Generates approval letters
    """,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    """Handle validation errors with detailed response."""
    logger.warning(
        "Validation error",
        path=request.url.path,
        errors=exc.errors()
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation Error",
            "errors": [
                {
                    "field": ".".join(str(loc) for loc in err["loc"]),
                    "message": err["msg"],
                    "type": err["type"]
                }
                for err in exc.errors()
            ]
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# Include API routes
app.include_router(api_router)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    """
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Welcome to Agentic Loan Sales API",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Disabled in production",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
