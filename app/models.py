"""SQLAlchemy database models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, BigInteger, Index
from sqlalchemy.orm import relationship
from app.database import Base


class Channel(Base):
    """Channel/streamer information table."""
    
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(20), nullable=False, index=True)  # twitch, kick
    channel_id = Column(String(100), nullable=False, index=True)  # Platform-specific ID
    username = Column(String(100), nullable=False, index=True)
    display_name = Column(String(100))
    description = Column(Text)
    profile_image_url = Column(String(500))
    follower_count = Column(BigInteger, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to snapshots
    snapshots = relationship("LiveSnapshot", back_populates="channel", cascade="all, delete-orphan")
    
    # Unique constraint on platform + channel_id
    __table_args__ = (
        Index('idx_platform_channel_id', 'platform', 'channel_id', unique=True),
    )
    
    def __repr__(self):
        return f"<Channel {self.platform}:{self.username}>"


class LiveSnapshot(Base):
    """Time-stamped snapshots of live stream data."""
    
    __tablename__ = "live_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)
    
    # Stream details
    title = Column(String(500))
    game_name = Column(String(200), index=True)
    game_id = Column(String(100))
    viewer_count = Column(Integer, default=0, index=True)
    language = Column(String(10), index=True)
    
    # Timestamps
    started_at = Column(DateTime)
    collected_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # URLs
    thumbnail_url = Column(String(500))
    stream_url = Column(String(500))
    
    # Relationship to channel
    channel = relationship("Channel", back_populates="snapshots")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_collected_at', 'collected_at'),
        Index('idx_game_collected', 'game_name', 'collected_at'),
        Index('idx_channel_collected', 'channel_id', 'collected_at'),
    )
    
    def __repr__(self):
        return f"<LiveSnapshot {self.channel_id} at {self.collected_at}>"
