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
    # Only show streams from the last 1 hour to ensure they're actually live
    recent_time = datetime.utcnow() - timedelta(hours=1)
    
    # Subquery to get the latest snapshot ID for each channel (only recent ones)
    subquery = (
        db.query(
            LiveSnapshot.channel_id,
            func.max(LiveSnapshot.collected_at).label("max_collected")
        )
        .join(Channel)
        .filter(
            Channel.platform == platform,
            LiveSnapshot.collected_at >= recent_time
        )
        .group_by(LiveSnapshot.channel_id)
        .subquery()
    )
    
    # Get the latest snapshots with channel info, exclude channels with 0 followers for Kick
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
        .filter(
            Channel.platform == platform,
            LiveSnapshot.collected_at >= recent_time
        )
    )
    
    # For Kick, filter out channels with 0 followers as they're likely inactive or have data issues
    # Commenting out this filter to show more streams
    # if platform == "kick":
    #     query = query.filter(Channel.follower_count > 0)
    
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
    # Use PostgreSQL date_trunc to count distinct hourly sessions
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
            "stream_url": stream_url,
            # Calculate total hours: snapshots are collected every 2 minutes
            "total_duration_minutes": row.total_snapshots * 2
        }
        for row in results
    ]


@router.get("/search")
async def search_streams(
    platform: str = Query("kick", description="Platform: twitch or kick"),
    q: str = Query(..., description="Search query"),
    limit: int = Query(50, ge=1, le=500, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Search streams by title, channel name, or category - Frontend compatible format.
    """
    try:
        # Use the working database search
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
        
        # Convert to frontend format
        streams = []
        for snapshot, channel in results:
            streams.append({
                "title": snapshot.title or "Untitled Stream",
                "channel": channel.username or channel.channel_id,
                "platform": platform,
                "viewers": snapshot.viewer_count or 0,
                "followers": channel.follower_count or 0,
                "category": snapshot.game_name or "Unknown",
                "language": snapshot.language or "English",
                "started_at": snapshot.started_at.isoformat() if snapshot.started_at else None,
                "url": snapshot.stream_url or f"https://{platform}.com/{channel.username}"
            })
        
        return {"streams": streams}
        
    except Exception as e:
        print(f"Search error: {e}")
        # Return empty results instead of fake demo data
        return {
            "streams": [],
            "message": f"No search results found for '{q}' on {platform}. The database may be empty or still collecting data."
        }


@router.get("/channel/{platform}/{channel_id}/history", response_model=ChannelHistoryResponse)
async def get_channel_history(
    platform: str,
    channel_id: str,
    window: str = Query("24h", description="Time window: e.g., '24h', '7d', '30d'"),
    db: Session = Depends(get_db)
):
    """
    Get historical data for a specific channel.
    channel_id can be either the numerical channel ID or the username.
    """
    try:
        start_time = parse_time_window(window)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Try to find channel by channel_id first, then by username if not found
    channel = db.query(Channel).filter(
        Channel.platform == platform,
        Channel.channel_id == channel_id
    ).first()
    
    if not channel:
        # If not found by channel_id, try by username
        channel = db.query(Channel).filter(
            Channel.platform == platform,
            Channel.username == channel_id
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


# Frontend-compatible endpoints
@router.get("/streams")
async def get_streams(
    platform: str = Query("kick", description="Platform: twitch or kick"),
    limit: int = Query(50, ge=1, le=500, description="Number of results to return"),
    sort_by: str = Query("viewers", description="Sort by: 'viewers' or 'followers'"),
    db: Session = Depends(get_db)
):
    """
    Get live streams for frontend compatibility.
    """
    try:
        # Call the existing top live streams endpoint and convert to expected format
        api_streams = await get_top_live_streams(platform=platform, limit=limit, sort_by=sort_by, db=db)
        
        if not api_streams:
            # If no streams returned, use demo data
            print(f"No streams found in database for platform {platform}")
            raise Exception("No streams found")
        
        # Convert API response to frontend-expected format
        streams = []
        for stream in api_streams:
            streams.append({
                "title": stream.title,
                "channel": stream.username,
                "platform": stream.platform,
                "viewers": stream.viewer_count,
                "followers": stream.follower_count,
                "category": stream.game_name,
                "language": stream.language or "English",
                "started_at": stream.started_at.isoformat() if stream.started_at else None,
                "url": stream.stream_url
            })
        
        print(f"Successfully converted {len(streams)} streams for frontend")
        return {"streams": streams}
    except Exception as e:
        print(f"Error in get_streams: {e}")
        # Return empty result with a message instead of fake demo data
        return {
            "streams": [],
            "message": f"No live streams available for {platform}. Data collection may be in progress or the platform API may be unavailable."
        }


@router.get("/categories")
async def get_categories(
    platform: str = Query("twitch", description="Platform: twitch or kick"),
    limit: int = Query(50, ge=1, le=500, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Get categories for frontend compatibility.
    """
    try:
        # Call the existing stats endpoint
        categories = await get_category_stats(platform=platform, window="24h", limit=limit, db=db)
        
        # Convert to expected format
        result = []
        for cat in categories:
            result.append({
                "name": cat.game_name,
                "streams": cat.total_streams,
                "viewers": cat.total_viewers,
                "avg_viewers": cat.avg_viewers,
                "peak_viewers": cat.peak_viewers,
                "platform": platform
            })
        
        return {"categories": result}
    except Exception as e:
        print(f"Error fetching categories: {e}")
        # Return empty result instead of fake demo data
        return {
            "categories": [],
            "message": f"No category data available for {platform}. Data collection may be in progress."
        }


@router.get("/channel-history")
async def get_channel_history_search(
    platform: str = Query("kick", description="Platform: twitch or kick"),
    channel: str = Query(..., description="Channel ID or username"),
    timeWindow: str = Query("24h", description="Time window: 24h, 7d, 30d"),
    db: Session = Depends(get_db)
):
    """
    Get channel history by searching for channel name/username.
    """
    try:
        # First, try to find the channel by username or channel_id
        channel_obj = db.query(Channel).filter(
            and_(
                Channel.platform == platform,
                func.lower(Channel.username).like(f"%{channel.lower()}%")
            )
        ).first()
        
        if not channel_obj:
            # Try by channel_id
            channel_obj = db.query(Channel).filter(
                and_(
                    Channel.platform == platform, 
                    Channel.channel_id == channel
                )
            ).first()
        
        if channel_obj:
            # Get actual history
            since = parse_time_window(timeWindow)
            
            history_query = db.query(LiveSnapshot).filter(
                and_(
                    LiveSnapshot.channel_id == channel_obj.id,
                    LiveSnapshot.collected_at >= since
                )
            ).order_by(LiveSnapshot.collected_at.desc())
            
            snapshots = history_query.all()
            
            if snapshots:
                # Convert to chart data format
                chart_data = []
                for snapshot in reversed(snapshots):  # Reverse for chronological order
                    chart_data.append({
                        "timestamp": snapshot.collected_at.isoformat(),
                        "viewers": snapshot.viewer_count or 0,
                        "followers": channel_obj.follower_count or 0,
                        "isLive": True
                    })
                
                summary = {
                    "totalStreams": len(snapshots),
                    "avgViewers": int(sum(s.viewer_count or 0 for s in snapshots) / len(snapshots)) if snapshots else 0,
                    "maxViewers": max((s.viewer_count or 0 for s in snapshots), default=0),
                    "totalFollowers": channel_obj.follower_count or 0
                }
                
                return {
                    "channel": channel_obj.username or channel,
                    "timeWindow": timeWindow,
                    "data": chart_data,
                    "summary": summary,
                    "found": True
                }
        
        # Channel not found, return empty result
        return {
            "channel": channel,
            "timeWindow": timeWindow,
            "data": [],
            "summary": {
                "totalStreams": 0,
                "avgViewers": 0,
                "maxViewers": 0,
                "totalFollowers": 0
            },
            "found": False,
            "message": f"Channel '{channel}' not found on {platform}"
        }
        
    except Exception as e:
        print(f"Error in channel history search: {e}")
        # Return error response
        return {
            "channel": channel,
            "timeWindow": timeWindow,
            "data": [],
            "summary": {
                "totalStreams": 0,
                "avgViewers": 0,
                "maxViewers": 0,
                "totalFollowers": 0
            },
            "found": False,
            "error": str(e)
        }


@router.post("/collect-all")
async def collect_all_data():
    """
    Trigger data collection for all platforms.
    """
    try:
        # Import here to avoid circular imports
        from app.collector.scheduler import StreamCollector
        
        # Create collector instance and run collection
        collector = StreamCollector()
        
        # Run collection for both platforms
        await collector.collect_kick_streams()
        await collector.collect_twitch_streams()
        
        return {"status": "success", "message": "Data collection completed successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to start collection: {str(e)}"}


@router.post("/clear-data")
async def clear_all_data(db: Session = Depends(get_db)):
    """
    Clear all stream data from database (for testing purposes).
    """
    try:
        # Delete all snapshots first (due to foreign key constraints)
        db.query(LiveSnapshot).delete()
        # Delete all channels
        db.query(Channel).delete()
        db.commit()
        
        return {"status": "success", "message": "All data cleared successfully"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Failed to clear data: {str(e)}"}


@router.get("/search-db", response_model=List[LiveStreamResponse])
async def search_streams_database(
    platform: str = Query("twitch", description="Platform: twitch, kick, or youtube"),
    q: str = Query(..., description="Search query (title, game, or username)"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Search for live streams by keyword in title, game name, or username - Database format.
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
