"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# Channel Schemas
class ChannelBase(BaseModel):
    """Base channel schema."""
    platform: str
    channel_id: str
    username: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    profile_image_url: Optional[str] = None
    follower_count: int = 0


class ChannelCreate(ChannelBase):
    """Schema for creating a channel."""
    pass


class ChannelUpdate(BaseModel):
    """Schema for updating a channel."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    profile_image_url: Optional[str] = None
    follower_count: Optional[int] = None


class Channel(ChannelBase):
    """Channel schema with database fields."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Live Snapshot Schemas
class LiveSnapshotBase(BaseModel):
    """Base live snapshot schema."""
    title: Optional[str] = None
    game_name: Optional[str] = None
    game_id: Optional[str] = None
    viewer_count: int = 0
    language: Optional[str] = None
    started_at: Optional[datetime] = None
    thumbnail_url: Optional[str] = None
    stream_url: Optional[str] = None


class LiveSnapshotCreate(LiveSnapshotBase):
    """Schema for creating a live snapshot."""
    channel_id: int


class LiveSnapshot(LiveSnapshotBase):
    """Live snapshot schema with database fields."""
    id: int
    channel_id: int
    collected_at: datetime
    
    class Config:
        from_attributes = True


class LiveSnapshotWithChannel(LiveSnapshot):
    """Live snapshot with channel information."""
    channel: Channel
    
    class Config:
        from_attributes = True


# API Response Schemas
class LiveStreamResponse(BaseModel):
    """Response schema for live stream data."""
    platform: str
    channel_id: str
    username: str
    display_name: Optional[str]
    title: Optional[str]
    game_name: Optional[str]
    viewer_count: int
    language: Optional[str]
    started_at: Optional[datetime]
    thumbnail_url: Optional[str]
    stream_url: Optional[str]
    follower_count: int
    collected_at: datetime


class ChannelHistoryResponse(BaseModel):
    """Response schema for channel history."""
    channel: Channel
    snapshots: List[LiveSnapshot]
    total_snapshots: int
    avg_viewer_count: float
    peak_viewer_count: int


class CategoryStats(BaseModel):
    """Statistics for a game category."""
    game_name: str
    total_streams: int
    total_viewers: int
    avg_viewers: float
    peak_viewers: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    database: str
