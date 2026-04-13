from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.config import settings
from app.database import test_db_connection, verify_postgis_extension, engine
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import KanVerException
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.error_handler import (
    kanver_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)
from app.routers import auth, users, hospitals, requests, donors, donations, notifications, admin
from app.background.timeout_checker import run_timeout_checker, stop_timeout_checker
import logging

# Setup application logging
setup_logging()
logger = get_logger(__name__)


# Lifespan context manager (modern approach, replaces deprecated @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama yaşam döngüsü yönetimi"""
    # Startup
    logger.info("KanVer API starting up...")
    db_ok = await test_db_connection()
    if db_ok:
        logger.info("Database connection established")
        # Verify PostGIS extension
        postgis_ok = await verify_postgis_extension()
        if postgis_ok:
            logger.info("PostGIS extension verified")
        else:
            logger.warning("PostGIS extension not found - spatial queries will fail")
    else:
        logger.warning("Database connection failed")

    # Start background tasks
    timeout_task = asyncio.create_task(run_timeout_checker())
    logger.info("Background timeout checker task started")

    yield

    # Shutdown
    stop_timeout_checker()
    timeout_task.cancel()
    try:
        await timeout_task
    except asyncio.CancelledError:
        pass
    logger.info("KanVer API shutting down...")
    # Dispose database engine
    await engine.dispose()


# FastAPI app instance with lifespan
app = FastAPI(
    title="KanVer API",
    description="Konum Tabanlı Acil Kan & Aferez Bağış Ağı",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware (must be first - outermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# Security headers middleware (after CORS)
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiter middleware (after security headers, before logging)
app.add_middleware(
    RateLimiterMiddleware,
    requests_per_minute=settings.RATE_LIMIT_REQUESTS,
    auth_requests_per_minute=settings.RATE_LIMIT_AUTH_REQUESTS
)

# Logging middleware (innermost middleware)
app.add_middleware(LoggingMiddleware)


# Register exception handlers
app.add_exception_handler(KanVerException, kanver_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API bilgisi"""
    return {
        "name": "KanVer API",
        "version": "0.1.0",
        "description": "Konum Tabanlı Acil Kan & Aferez Bağış Ağı",
        "docs": "/docs",
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "kanver-backend"}


# Detailed health check with DB
@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """Detaylı sistem durumu (DB bağlantısı ve PostGIS dahil)"""
    db_status = await test_db_connection()
    postgis_status = await verify_postgis_extension() if db_status else False

    return {
        "status": "healthy" if db_status and postgis_status else "unhealthy",
        "service": "kanver-backend",
        "database": {
            "connected": db_status,
            "postgis_enabled": postgis_status
        },
    }


# Auth router - /api/auth/*
app.include_router(auth.router, prefix="/api/auth")

# Users router - /api/users/*
app.include_router(users.router, prefix="/api/users")

# Hospitals router - /api/hospitals/*
app.include_router(hospitals.router, prefix="/api/hospitals")

# Requests router - /api/requests/*
app.include_router(requests.router, prefix="/api/requests")

# Donors router - /api/donors/*
app.include_router(donors.router, prefix="/api/donors")

# Donations router - /api/donations/*
app.include_router(donations.router, prefix="/api/donations")

# Notifications router - /api/notifications/*
app.include_router(notifications.router, prefix="/api/notifications")

# Admin router - /api/admin/*
app.include_router(admin.router, prefix="/api/admin")
