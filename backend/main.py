"""
KanVer - Konum Tabanlı Acil Kan Bağış Ağı
FastAPI Backend Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "KanVer API",
    }


# TODO: Import and include routers
# from app.api.v1 import auth, requests, donations, users
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
# app.include_router(requests.router, prefix="/api/v1/requests", tags=["Blood Requests"])
# app.include_router(donations.router, prefix="/api/v1/donations", tags=["Donations"])
# app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
