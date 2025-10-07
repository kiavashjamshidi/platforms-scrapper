"""Database connection and session management."""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Use SQLite for free deployment, PostgreSQL for local development
if os.getenv("ENVIRONMENT") == "production":
    # SQLite for production deployment (completely free)
    database_url = "sqlite:///./streaming_data.db"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    # PostgreSQL for local development
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from app.models import Channel, LiveSnapshot  # Import models
    Base.metadata.create_all(bind=engine)
