"""Main FastAPI application."""
from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from loguru import logger

from app.config import settings
from app.database import get_db, init_db
from app.api.routes import router as api_router
from app.schemas import HealthResponse

# Initialize database on startup
init_db()

# Create FastAPI app
app = FastAPI(
    title="Live Streaming Data Collection API",
    description="Collect and analyze live streaming data from Twitch, Kick, and YouTube",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes (without prefix since routes are at root level)
app.include_router(api_router, tags=["streams"])


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Live Streaming Data Collection API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        timestamp=datetime.utcnow(),
        database=db_status
    )


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Starting Live Streaming Data Collection API")
    logger.info(f"API version: 1.0.0")
    logger.info(f"Database URL: {settings.database_url.split('@')[-1]}")  # Hide credentials


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Shutting down Live Streaming Data Collection API")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
