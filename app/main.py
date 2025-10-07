"""Main FastAPI application."""
from datetime import datetime
from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from loguru import logger
import os
import asyncio

from app.config import settings
from app.database import get_db, init_db
from app.api.routes import router as api_router
from app.schemas import HealthResponse
from app.collector.scheduler import StreamCollector

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

# Mount static files
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/dashboard", tags=["dashboard"])
async def dashboard():
    """Serve the dashboard HTML."""
    static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    dashboard_file = os.path.join(static_path, "index.html")
    if os.path.exists(dashboard_file):
        return FileResponse(dashboard_file)
    else:
        return {"error": "Dashboard not found", "static_path": static_path}


@app.get("/", tags=["root"])
async def root():
    """Root endpoint - redirect to dashboard."""
    static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    dashboard_file = os.path.join(static_path, "index.html")
    if os.path.exists(dashboard_file):
        return FileResponse(dashboard_file)
    else:
        return {
            "message": "Live Streaming Data Collection API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
            "dashboard": "/dashboard"
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


@app.post("/collect-data", tags=["collection"])
async def trigger_data_collection(background_tasks: BackgroundTasks):
    """Manually trigger data collection for both platforms."""
    background_tasks.add_task(collect_all_data)
    return {"message": "Data collection started for both platforms", "status": "running"}


@app.post("/collect-kick", tags=["collection"])
async def trigger_kick_collection(background_tasks: BackgroundTasks):
    """Manually trigger Kick data collection."""
    background_tasks.add_task(collect_kick_data)
    return {"message": "Kick data collection started", "status": "running"}


@app.post("/collect-twitch", tags=["collection"])
async def trigger_twitch_collection(background_tasks: BackgroundTasks):
    """Manually trigger Twitch data collection."""
    background_tasks.add_task(collect_twitch_data)
    return {"message": "Twitch data collection started", "status": "running"}


async def collect_kick_data():
    """Collect data from Kick platform."""
    try:
        logger.info("Starting Kick data collection...")
        collector = StreamCollector()
        await collector.collect_kick_streams()
        logger.info("Kick data collection completed")
    except Exception as e:
        logger.error(f"Error during Kick data collection: {e}")


async def collect_twitch_data():
    """Collect data from Twitch platform."""
    try:
        logger.info("Starting Twitch data collection...")
        collector = StreamCollector()
        await collector.collect_twitch_streams()
        logger.info("Twitch data collection completed")
    except Exception as e:
        logger.error(f"Error during Twitch data collection: {e}")


async def collect_all_data():
    """Collect data from both platforms."""
    await collect_kick_data()
    await collect_twitch_data()


# Background task to collect data periodically
async def start_background_tasks():
    """Start background data collection tasks."""
    while True:
        try:
            await collect_all_data()
            await asyncio.sleep(120)  # Collect every 2 minutes
        except Exception as e:
            logger.error(f"Background task error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Starting Live Streaming Data Collection API")
    logger.info(f"API version: 1.0.0")
    logger.info(f"Database URL: {settings.database_url.split('@')[-1]}")  # Hide credentials
    
    # Start background data collection
    asyncio.create_task(start_background_tasks())


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
