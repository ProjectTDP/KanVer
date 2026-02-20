from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import test_db_connection, verify_postgis_extension, engine
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import KanVerException
from app.middleware.logging_middleware import LoggingMiddleware
from app.routers import auth
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

    yield

    # Shutdown
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

# CORS middleware (must be first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# Logging middleware (after CORS)
app.add_middleware(LoggingMiddleware)


# Global exception handler for KanVerException
@app.exception_handler(KanVerException)
async def kanver_exception_handler(request: Request, exc: KanVerException):
    """
    KanVer özel exception'larını yakalayıp JSON döndür.

    Provides consistent error response format for all custom exceptions.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )


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
