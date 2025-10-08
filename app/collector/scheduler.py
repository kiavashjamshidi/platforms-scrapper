"""Data collection scheduler."""
import asyncio
import sys
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.database import SessionLocal, init_db
from app.models import Channel, LiveSnapshot
from app.collector.twitch import TwitchClient
from app.collector.kick import KickClient  # Import official KickClient


# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/collector_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG"
)


class StreamCollector:
    """Main collector class for gathering stream data."""
    
    def __init__(self):
        self.db: Session = SessionLocal()
    
    def __del__(self):
        """Cleanup database session."""
        if hasattr(self, 'db'):
            self.db.close()
    
    def get_or_create_channel(
        self,
        platform: str,
        channel_id: str,
        username: str,
        display_name: str = None,
        description: str = None,
        profile_image_url: str = None,
        follower_count: int = 0
    ) -> Channel:
        """
        Get existing channel or create new one.
        """
        channel = self.db.query(Channel).filter(
            Channel.platform == platform,
            Channel.channel_id == channel_id
        ).first()
        
        if channel:
            # Update existing channel
            channel.username = username
            channel.display_name = display_name or username
            if description:
                channel.description = description
            if profile_image_url:
                channel.profile_image_url = profile_image_url
            if follower_count > 0:
                channel.follower_count = follower_count
            channel.updated_at = datetime.utcnow()
        else:
            # Create new channel
            channel = Channel(
                platform=platform,
                channel_id=channel_id,
                username=username,
                display_name=display_name or username,
                description=description,
                profile_image_url=profile_image_url,
                follower_count=follower_count
            )
            self.db.add(channel)
        
        self.db.commit()
        self.db.refresh(channel)
        return channel
    
    def create_snapshot(self, channel: Channel, stream_data: Dict[str, Any]) -> LiveSnapshot:
        """
        Create a new live snapshot record.
        """
        snapshot = LiveSnapshot(
            channel_id=channel.id,
            title=stream_data.get("title"),
            game_name=stream_data.get("game_name"),
            game_id=stream_data.get("game_id"),
            viewer_count=stream_data.get("viewer_count", 0),
            language=stream_data.get("language"),
            started_at=stream_data.get("started_at"),
            thumbnail_url=stream_data.get("thumbnail_url"),
            stream_url=stream_data.get("stream_url"),
            collected_at=datetime.utcnow()
        )
        
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot
    
    async def collect_twitch_streams(self):
        """
        Collect real live streams from Twitch using official API.
        """
        logger.info("Starting Twitch stream collection...")
        collected_count = 0

        # Check if we have Twitch API credentials
        if not settings.twitch_client_id or not settings.twitch_client_secret:
            logger.error("Twitch API credentials not found!")
            logger.error(f"twitch_client_id present: {bool(settings.twitch_client_id)}")
            logger.error(f"twitch_client_secret present: {bool(settings.twitch_client_secret)}")
            raise ValueError("Twitch API credentials are required")
        
        logger.info(f"Twitch credentials found - Client ID: {settings.twitch_client_id[:10]}...")
        try:
            # Use the official Twitch API client
            logger.info("Initializing TwitchClient...")
            async with TwitchClient() as client:
                logger.info("TwitchClient initialized, fetching streams...")
                
                # Get top live streams sorted by viewer count
                streams_response = await client.get_streams(first=50)
                streams_data = streams_response.get("data", [])
                
                logger.info(f"Received {len(streams_data)} streams from Twitch API")
                
                if not streams_data:
                    logger.error("No live streams returned from Twitch API")
                    raise ValueError("No live streams available from Twitch API")
                
                logger.info(f"Found {len(streams_data)} live streams from Twitch API")
                logger.info(f"First stream example: {streams_data[0].get('user_login')} - {streams_data[0].get('viewer_count')} viewers")
                
                # Get user IDs to fetch follower counts
                user_ids = [stream["user_id"] for stream in streams_data]
                logger.info(f"Fetching user info for {len(user_ids)} users...")
                
                users_response = await client.get_users(user_ids=user_ids)
                users_data = {user["id"]: user for user in users_response}
                logger.info(f"Received info for {len(users_data)} users")
                
                twitch_streams = []
                for stream in streams_data:
                    user_id = stream["user_id"]
                    user_data = users_data.get(user_id, {})
                    
                    twitch_streams.append({
                        "channel_id": user_id,
                        "username": stream["user_login"],
                        "display_name": stream["user_name"],
                        "title": stream["title"],
                        "game_name": stream["game_name"],
                        "game_id": stream["game_id"],
                        "viewer_count": stream["viewer_count"],
                        "language": stream["language"],
                        "started_at": datetime.fromisoformat(stream["started_at"].replace("Z", "+00:00")),
                        "thumbnail_url": stream["thumbnail_url"],
                        "stream_url": f"https://twitch.tv/{stream['user_login']}",
                        "follower_count": user_data.get("follower_count", 0)
                    })
                
                logger.info(f"Successfully parsed {len(twitch_streams)} Twitch streams")
                
        except Exception as e:
            logger.error(f"Error fetching real Twitch streams from official API: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't use demo data, just raise the exception
            raise
        
        try:
            logger.info(f"Saving {len(twitch_streams)} Twitch streams to database...")
            for stream_data in twitch_streams:
                # Get or create channel
                channel = self.get_or_create_channel(
                    platform="twitch",
                    channel_id=stream_data["channel_id"],
                    username=stream_data["username"],
                    display_name=stream_data.get("display_name", stream_data["username"]),
                    follower_count=stream_data.get("follower_count", 100000 + (collected_count * 2000))
                )
                
                # Create snapshot
                self.create_snapshot(channel, stream_data)
                collected_count += 1
                if collected_count <= 3:  # Log first 3 for debugging
                    logger.debug(f"Saved: {stream_data['username']} - {stream_data['viewer_count']} viewers")
                
            logger.info(f"Successfully collected {collected_count} Twitch stream snapshots")
            
        except Exception as e:
            logger.error(f"Error saving Twitch data to database: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def collect_kick_streams(self):
        """
        Collect real live streams from Kick using the KickAPI library.
        """
        logger.info("Starting Kick stream collection...")
        collected_count = 0

        try:
            # Try to get real live streams first
            logger.info("Attempting to fetch Kick streams from official API...")
            real_streams = await self._fetch_real_kick_streams()
            
            if not real_streams:
                # Log that we couldn't fetch real streams
                logger.warning("Failed to fetch real Kick streams - API may be unavailable or blocked")
                # Don't use demo data for Kick since it's misleading
                logger.info("Skipping Kick collection - no real streams available")
                return
            
            logger.info(f"Processing {len(real_streams)} Kick streams...")
            
            for stream_data in real_streams:
                # Get or create channel
                channel = self.get_or_create_channel(
                    platform="kick",
                    channel_id=stream_data["channel_id"],
                    username=stream_data["username"],
                    display_name=stream_data.get("display_name", stream_data["username"]),
                    follower_count=stream_data.get("follower_count", 10000 + (collected_count * 1000))
                )
                
                # Create snapshot
                self.create_snapshot(channel, stream_data)
                collected_count += 1
                if collected_count <= 3:  # Log first 3 for debugging
                    logger.debug(f"Saved Kick stream: {stream_data['username']}")
                
            logger.info(f"Successfully collected {collected_count} Kick stream snapshots")
            
        except Exception as e:
            logger.error(f"Error collecting Kick data: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't raise - allow other platform collection to continue

    async def _fetch_real_kick_streams(self) -> List[Dict[str, Any]]:
        """
        Fetch real live streams from Kick using official API.
        """
        from app.collector.kick import KickClient
        
        # Check if we have Kick API credentials
        if not settings.KICK_CLIENT_ID or not settings.KICK_CLIENT_SECRET:
            logger.warning("Kick API credentials not found in settings")
            logger.warning(f"KICK_CLIENT_ID present: {bool(settings.KICK_CLIENT_ID)}")
            logger.warning(f"KICK_CLIENT_SECRET present: {bool(settings.KICK_CLIENT_SECRET)}")
            return []
        
        logger.info(f"Kick credentials found - Client ID: {settings.KICK_CLIENT_ID[:10]}...")
        
        try:
            # Use the official Kick API client
            logger.info("Initializing KickClient...")
            async with KickClient(
                client_id=settings.KICK_CLIENT_ID,
                client_secret=settings.KICK_CLIENT_SECRET
            ) as client:
                logger.info("KickClient initialized successfully")
                logger.info("Fetching live streams from official Kick API...")
                
                # Get live streams from the official API
                livestreams = await client.get_live_streams(limit=50)
                
                logger.info(f"Received response from Kick API: {len(livestreams) if livestreams else 0} streams")
                
                if not livestreams:
                    logger.warning("No live streams returned from Kick API")
                    return []
                
                logger.info(f"Found {len(livestreams)} live streams from Kick API")
                if livestreams:
                    logger.info(f"First stream structure: {livestreams[0]}")
                
                streams = []
                for i, stream_data in enumerate(livestreams):
                    try:
                        # Parse the stream data from official API response
                        # Kick API returns slug at top level, not in a channel object
                        channel_slug = stream_data.get("slug")
                        channel_id = stream_data.get("channel_id")
                        
                        if not channel_slug or not channel_id:
                            logger.warning(f"Stream {i} missing channel slug or ID, skipping. Stream data keys: {stream_data.keys()}")
                            continue
                        
                        # Get follower count if available in stream data
                        follower_count = stream_data.get("followers_count", 0) or stream_data.get("follower_count", 0)
                        
                        # Get category info
                        category = stream_data.get("category", {}) or {}
                        game_name = category.get("name", "Just Chatting") if isinstance(category, dict) else "Just Chatting"
                        game_id = str(category.get("id", "1")) if isinstance(category, dict) else "1"
                        
                        streams.append({
                            "channel_id": str(channel_id),
                            "username": channel_slug,
                            "display_name": channel_slug,  # Kick doesn't provide separate display name in this endpoint
                            "title": stream_data.get("stream_title", f"Live on {channel_slug}"),
                            "game_name": game_name,
                            "game_id": game_id,
                            "viewer_count": stream_data.get("viewer_count", 0),
                            "language": stream_data.get("language", "en"),
                            "started_at": datetime.fromisoformat(stream_data["started_at"].replace("Z", "+00:00")) if stream_data.get("started_at") else datetime.utcnow(),
                            "thumbnail_url": stream_data.get("thumbnail"),
                            "stream_url": f"https://kick.com/{channel_slug}",
                            "follower_count": follower_count
                        })
                        
                    except Exception as e:
                        logger.warning(f"Error parsing stream {i} data: {e}")
                        logger.warning(f"Stream data: {stream_data}")
                        continue
                
                logger.info(f"Successfully parsed {len(streams)} Kick streams")
                return streams
                
        except Exception as e:
            logger.error(f"Error fetching real Kick streams from official API: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
                
        except Exception as e:
            logger.error(f"Error fetching real Kick streams from official API: {e}")
            return []

    def _get_demo_kick_streams(self) -> List[Dict[str, Any]]:
        """
        Get realistic demo Kick stream data as fallback.
        """
        return []

    async def run_collection(self):
        """
        Run data collection for all platforms.
        """
        logger.info("=" * 80)
        logger.info("Starting data collection cycle")
        logger.info("=" * 80)

        start_time = datetime.utcnow()

        # Collect from Twitch
        await self.collect_twitch_streams()

        # Collect from Kick
        await self.collect_kick_streams()

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        logger.info("=" * 80)
        logger.info(f"Collection cycle completed in {duration:.2f} seconds")
        logger.info("=" * 80)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about collected data.
        """
        stats = {}
        
        # Total channels
        stats["total_channels"] = self.db.query(Channel).count()
        
        # Total snapshots
        stats["total_snapshots"] = self.db.query(LiveSnapshot).count()
        
        # Snapshots by platform
        platform_counts = self.db.query(
            Channel.platform,
            func.count(LiveSnapshot.id)
        ).join(LiveSnapshot).group_by(Channel.platform).all()
        
        stats["snapshots_by_platform"] = {platform: count for platform, count in platform_counts}
        
        # Latest collection time
        latest = self.db.query(func.max(LiveSnapshot.collected_at)).scalar()
        stats["latest_collection"] = latest
        
        return stats


async def run_scheduler():
    """
    Main scheduler function that runs collection at intervals.
    """
    logger.info("Initializing Stream Data Collector")
    logger.info(f"Collection interval: {settings.collection_interval_minutes} minutes")
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    
    collector = StreamCollector()
    
    # Run first collection immediately
    try:
        await collector.run_collection()
    except Exception as e:
        logger.error(f"Initial collection failed: {e}")
    
    # Schedule periodic collections
    interval_seconds = settings.collection_interval_minutes * 60
    
    while True:
        try:
            logger.info(f"Waiting {settings.collection_interval_minutes} minutes until next collection...")
            await asyncio.sleep(interval_seconds)
            
            await collector.run_collection()
            
            # Log stats
            stats = collector.get_collection_stats()
            logger.info(f"Database stats: {stats}")
            
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
            # Wait before retrying
            await asyncio.sleep(60)


def main():
    """Entry point for the collector."""
    try:
        asyncio.run(run_scheduler())
    except KeyboardInterrupt:
        logger.info("Collector shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
