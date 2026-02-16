"""
KanVer - Konum Tabanlı Acil Kan Bağış Ağı
FastAPI Backend Application
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from .database import get_db, engine
from .core import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="KanVer API",
    description="Konum Tabanlı Acil Kan Bağış Ağı - RESTful API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Configuration for Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler.
    Tests database connection on application startup.
    """
    logger.info("Starting up KanVer API...")
    try:
        # Test database connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler.
    Closes database connections gracefully.
    """
    logger.info("Shutting down KanVer API...")
    await engine.dispose()
    logger.info("✅ Database connections closed")


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": "KanVer API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """Simple health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "KanVer API",
    }


@app.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check endpoint with database connection status.
    Returns service status, database connectivity, and version info.
    """
    health_status = {
        "status": "healthy",
        "service": "KanVer API",
        "version": "1.0.0",
        "database": {
            "connected": False,
            "message": ""
        }
    }
    
    # Check database connection
    try:
        # Execute a simple query to verify connection
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        
        health_status["database"]["connected"] = True
        health_status["database"]["message"] = "Database connection successful"
        
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"]["connected"] = False
        health_status["database"]["message"] = f"Database connection failed: {str(e)}"
    
    return health_status


# Import routers
from .routers import auth

# Include routers
app.include_router(auth.router, prefix="/api/auth")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
