"""FastAPI routes for the streaming data API."""
import csv
import io
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.database import get_db
from app.models import Channel, LiveSnapshot
from app.schemas import (
    LiveStreamResponse,
    ChannelHistoryResponse,
    CategoryStats,
    Channel as ChannelSchema,
    LiveSnapshot as LiveSnapshotSchema
)

router = APIRouter()


def parse_time_window(window: str) -> datetime:
    """
    Parse time window string (e.g., '24h', '7d', '30d') to datetime.
    """
    now = datetime.utcnow()
    
    if window.endswith('h'):
        hours = int(window[:-1])
        return now - timedelta(hours=hours)
    elif window.endswith('d'):
        days = int(window[:-1])
        return now - timedelta(days=days)
    elif window.endswith('w'):
        weeks = int(window[:-1])
        return now - timedelta(weeks=weeks)
    else:
        raise ValueError(f"Invalid time window format: {window}")


@router.get("/live/top", response_model=List[LiveStreamResponse])
async def get_top_live_streams(
    platform: str = Query("twitch", description="Platform: twitch, kick, or youtube"),
    limit: int = Query(50, ge=1, le=500, description="Number of results to return"),
    sort_by: str = Query("viewers", description="Sort by: 'viewers' (current viewers) or 'followers' (follower count)"),
    db: Session = Depends(get_db)
):
    """
    Get the top live streams sorted by viewer count or follower count.
    Returns the most recent snapshot for each channel.
    
    Sort options:
    - 'viewers': Sort by current viewer count (default)
    - 'followers': Sort by channel follower count
    """
    # Subquery to get the latest snapshot ID for each channel
    subquery = (
        db.query(
            LiveSnapshot.channel_id,
            func.max(LiveSnapshot.collected_at).label("max_collected")
        )
        .join(Channel)
        .filter(Channel.platform == platform)
        .group_by(LiveSnapshot.channel_id)
        .subquery()
    )
    
    # Get the latest snapshots with channel info
    query = (
        db.query(LiveSnapshot, Channel)
        .join(Channel)
        .join(
            subquery,
            and_(
                LiveSnapshot.channel_id == subquery.c.channel_id,
                LiveSnapshot.collected_at == subquery.c.max_collected
            )
        )
        .filter(Channel.platform == platform)
    )
    
    # Apply sorting based on sort_by parameter
    if sort_by == "followers":
        query = query.order_by(desc(Channel.follower_count))
    else:  # Default to viewers
        query = query.order_by(desc(LiveSnapshot.viewer_count))
    
    results = query.limit(limit).all()
    
    return [
        LiveStreamResponse(
            platform=channel.platform,
            channel_id=channel.channel_id,
            username=channel.username,
            display_name=channel.display_name,
            title=snapshot.title,
            game_name=snapshot.game_name,
            viewer_count=snapshot.viewer_count,
            language=snapshot.language,
            started_at=snapshot.started_at,
            thumbnail_url=snapshot.thumbnail_url,
            stream_url=snapshot.stream_url,
            follower_count=channel.follower_count,
            collected_at=snapshot.collected_at
        )
        for snapshot, channel in results
    ]


@router.get("/live/most-active")
async def get_most_active_streamers(
    platform: str = Query("twitch", description="Platform: twitch, kick, or youtube"),
    window: str = Query("7d", description="Time window: e.g., '24h', '7d', '30d'"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Get the most active streamers by stream session count.
    Shows who has been live most frequently in the time window.
    
    Returns:
    - username, display_name
    - stream_count: Number of distinct streaming sessions
    - total_snapshots: Total data points collected
    - avg_viewers: Average viewer count across all streams
    - peak_viewers: Highest viewer count seen
    - last_seen: Most recent stream timestamp
    """
    try:
        start_time = parse_time_window(window)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Aggregate stream statistics by channel
    results = (
        db.query(
            Channel.channel_id,
            Channel.username,
            Channel.display_name,
            Channel.follower_count,
            Channel.profile_image_url,
            func.count(func.distinct(func.date_trunc('hour', LiveSnapshot.started_at))).label("stream_count"),
            func.count(LiveSnapshot.id).label("total_snapshots"),
            func.avg(LiveSnapshot.viewer_count).label("avg_viewers"),
            func.max(LiveSnapshot.viewer_count).label("peak_viewers"),
            func.max(LiveSnapshot.collected_at).label("last_seen")
        )
        .join(LiveSnapshot)
        .filter(
            Channel.platform == platform,
            LiveSnapshot.collected_at >= start_time
        )
        .group_by(
            Channel.channel_id,
            Channel.username,
            Channel.display_name,
            Channel.follower_count,
            Channel.profile_image_url
        )
        .order_by(desc("stream_count"))
        .limit(limit)
        .all()
    )
    
    # Ensure Kick platform data is properly handled
    if platform not in ["twitch", "kick", "youtube"]:
        raise HTTPException(status_code=400, detail="Invalid platform specified")
    
    # Update stream_url for Kick
    stream_url = None
    for row in results:
        stream_url = None
        if platform == "twitch":
            stream_url = f"https://www.twitch.tv/{row.username}"
        elif platform == "kick":
            stream_url = f"https://kick.com/{row.username}"
    
    return [
        {
            "platform": platform,
            "channel_id": row.channel_id,
            "username": row.username,
            "display_name": row.display_name,
            "follower_count": row.follower_count,
            "profile_image_url": row.profile_image_url,
            "stream_count": row.stream_count,
            "total_snapshots": row.total_snapshots,
            "avg_viewers": round(float(row.avg_viewers or 0), 2),
            "peak_viewers": row.peak_viewers or 0,
            "last_seen": row.last_seen,
            "stream_url": stream_url
        }
        for row in results
    ]


@router.get("/search", response_model=List[LiveStreamResponse])
async def search_streams(
    platform: str = Query("twitch", description="Platform: twitch, kick, or youtube"),
    q: str = Query(..., description="Search query (title, game, or username)"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Search for live streams by keyword in title, game name, or username.
    """
    search_term = f"%{q}%"
    
    # Subquery to get the latest snapshot for each channel
    subquery = (
        db.query(
            LiveSnapshot.channel_id,
            func.max(LiveSnapshot.collected_at).label("max_collected")
        )
        .group_by(LiveSnapshot.channel_id)
        .subquery()
    )
    
    # Search in title, game name, or username
    results = (
        db.query(LiveSnapshot, Channel)
        .join(Channel)
        .join(
            subquery,
            and_(
                LiveSnapshot.channel_id == subquery.c.channel_id,
                LiveSnapshot.collected_at == subquery.c.max_collected
            )
        )
        .filter(
            Channel.platform == platform,
            (
                LiveSnapshot.title.ilike(search_term) |
                LiveSnapshot.game_name.ilike(search_term) |
                Channel.username.ilike(search_term)
            )
        )
        .order_by(desc(LiveSnapshot.viewer_count))
        .limit(limit)
        .all()
    )
    
    return [
        LiveStreamResponse(
            platform=channel.platform,
            channel_id=channel.channel_id,
            username=channel.username,
            display_name=channel.display_name,
            title=snapshot.title,
            game_name=snapshot.game_name,
            viewer_count=snapshot.viewer_count,
            language=snapshot.language,
            started_at=snapshot.started_at,
            thumbnail_url=snapshot.thumbnail_url,
            stream_url=snapshot.stream_url,
            follower_count=channel.follower_count,
            collected_at=snapshot.collected_at
        )
        for snapshot, channel in results
    ]


@router.get("/channel/{platform}/{channel_id}/history", response_model=ChannelHistoryResponse)
async def get_channel_history(
    platform: str,
    channel_id: str,
    window: str = Query("24h", description="Time window: e.g., '24h', '7d', '30d'"),
    db: Session = Depends(get_db)
):
    """
    Get historical data for a specific channel.
    """
    try:
        start_time = parse_time_window(window)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Get channel
    channel = db.query(Channel).filter(
        Channel.platform == platform,
        Channel.channel_id == channel_id
    ).first()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Get snapshots within time window
    snapshots = (
        db.query(LiveSnapshot)
        .filter(
            LiveSnapshot.channel_id == channel.id,
            LiveSnapshot.collected_at >= start_time
        )
        .order_by(LiveSnapshot.collected_at)
        .all()
    )
    
    if not snapshots:
        return ChannelHistoryResponse(
            channel=ChannelSchema.model_validate(channel),
            snapshots=[],
            total_snapshots=0,
            avg_viewer_count=0.0,
            peak_viewer_count=0
        )
    
    # Calculate statistics
    viewer_counts = [s.viewer_count for s in snapshots]
    
    return ChannelHistoryResponse(
        channel=ChannelSchema.model_validate(channel),
        snapshots=[LiveSnapshotSchema.model_validate(s) for s in snapshots],
        total_snapshots=len(snapshots),
        avg_viewer_count=sum(viewer_counts) / len(viewer_counts),
        peak_viewer_count=max(viewer_counts)
    )


@router.get("/stats/categories", response_model=List[CategoryStats])
async def get_category_stats(
    platform: str = Query("twitch", description="Platform: twitch, kick, or youtube"),
    window: str = Query("7d", description="Time window: e.g., '24h', '7d', '30d'"),
    limit: int = Query(10, ge=1, le=100, description="Number of categories to return"),
    db: Session = Depends(get_db)
):
    """
    Get trending categories/games with statistics.
    """
    try:
        start_time = parse_time_window(window)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Aggregate statistics by game
    results = (
        db.query(
            LiveSnapshot.game_name,
            func.count(LiveSnapshot.id).label("total_streams"),
            func.sum(LiveSnapshot.viewer_count).label("total_viewers"),
            func.avg(LiveSnapshot.viewer_count).label("avg_viewers"),
            func.max(LiveSnapshot.viewer_count).label("peak_viewers")
        )
        .join(Channel)
        .filter(
            Channel.platform == platform,
            LiveSnapshot.collected_at >= start_time,
            LiveSnapshot.game_name.isnot(None)
        )
        .group_by(LiveSnapshot.game_name)
        .order_by(desc("total_viewers"))
        .limit(limit)
        .all()
    )
    
    return [
        CategoryStats(
            game_name=row.game_name,
            total_streams=row.total_streams,
            total_viewers=row.total_viewers or 0,
            avg_viewers=float(row.avg_viewers or 0),
            peak_viewers=row.peak_viewers or 0
        )
        for row in results
    ]


@router.get("/export/csv")
async def export_csv(
    platform: str = Query("twitch", description="Platform: twitch, kick, or youtube"),
    window: str = Query("24h", description="Time window: e.g., '24h', '7d', '30d'"),
    db: Session = Depends(get_db)
):
    """
    Export stream data as CSV file.
    """
    try:
        start_time = parse_time_window(window)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Get data
    results = (
        db.query(LiveSnapshot, Channel)
        .join(Channel)
        .filter(
            Channel.platform == platform,
            LiveSnapshot.collected_at >= start_time
        )
        .order_by(desc(LiveSnapshot.collected_at))
        .all()
    )
    
    if not results:
        raise HTTPException(status_code=404, detail="No data found for the specified time window")
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "collected_at",
        "platform",
        "channel_id",
        "username",
        "display_name",
        "title",
        "game_name",
        "viewer_count",
        "language",
        "started_at",
        "follower_count",
        "stream_url"
    ])
    
    # Write data
    for snapshot, channel in results:
        writer.writerow([
            snapshot.collected_at.isoformat() if snapshot.collected_at else "",
            channel.platform,
            channel.channel_id,
            channel.username,
            channel.display_name,
            snapshot.title,
            snapshot.game_name,
            snapshot.viewer_count,
            snapshot.language,
            snapshot.started_at.isoformat() if snapshot.started_at else "",
            channel.follower_count,
            snapshot.stream_url
        ])
    
    # Create response
    csv_content = output.getvalue()
    output.close()
    
    filename = f"streams_{platform}_{window}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
