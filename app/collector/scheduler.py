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
from app.collector.kick import KickClient  # Import KickClient


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
        Collect live streams from Twitch.
        """
        logger.info("Starting Twitch stream collection...")
        collected_count = 0
        
        try:
            async with TwitchClient() as client:
                # Get live streams
                streams = await client.get_all_streams(
                    max_results=settings.max_streams_per_collection
                )
                
                logger.info(f"Collected {len(streams)} live streams from Twitch")
                
                # Extract user IDs for batch fetching user info
                user_ids = [stream.get("user_id") for stream in streams if stream.get("user_id")]
                
                # Fetch user information in batches (Twitch allows max 100 per request)
                user_info_map = {}
                for i in range(0, len(user_ids), 100):
                    batch = user_ids[i:i+100]
                    try:
                        users = await client.get_users(user_ids=batch)
                        for user in users:
                            user_info_map[user.get("id")] = user
                    except Exception as e:
                        logger.warning(f"Failed to fetch user info for batch: {e}")
                
                logger.info(f"Fetched user info for {len(user_info_map)} channels")
                
                # Process each stream
                for stream in streams:
                    try:
                        # Parse stream data
                        stream_data = TwitchClient.parse_stream_data(stream)
                        
                        # Get user info if available
                        user_info = user_info_map.get(stream_data["channel_id"], {})
                        profile_image = user_info.get("profile_image_url")
                        description = user_info.get("description")
                        view_count = user_info.get("view_count", 0)  # Total channel views
                        follower_count = user_info.get("follower_count", 0)  # Extract follower_count
                        
                        # Fetch follower count
                        follower_count = await client.get_follower_count(stream_data["channel_id"])

                        # Get or create channel
                        channel = self.get_or_create_channel(
                            platform="twitch",
                            channel_id=stream_data["channel_id"],
                            username=stream_data["username"],
                            display_name=stream_data["display_name"],
                            description=description,
                            profile_image_url=profile_image,
                            follower_count=follower_count  # Pass follower_count
                        )
                        
                        # Create snapshot
                        self.create_snapshot(channel, stream_data)
                        collected_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing stream {stream.get('user_login')}: {e}")
                        continue
                
                logger.info(f"Successfully stored {collected_count} stream snapshots")
                
                # Log statistics
                total_viewers = sum(s.get("viewer_count", 0) for s in streams)
                logger.info(f"Total viewers across all streams: {total_viewers:,}")
                
        except Exception as e:
            logger.error(f"Error during Twitch collection: {e}")
            raise
    
    async def collect_kick_streams(self):
        """
        Collect live streams from Kick.
        """
        logger.info("Starting Kick stream collection...")
        collected_count = 0

        # Check if Kick credentials are available
        kick_client_id = settings.kick_client_id
        kick_client_secret = settings.kick_client_secret
        
        if not kick_client_id or not kick_client_secret:
            logger.warning(f"Kick credentials not found. ID: {bool(kick_client_id)}, Secret: {bool(kick_client_secret)}. Skipping Kick collection.")
            return

        try:
            async with KickClient(kick_client_id, kick_client_secret) as client:
                # Get live streams (might return list of slugs)
                streams = await client.get_live_streams(limit=settings.max_streams_per_collection)
                logger.info(f"Collected {len(streams)} live streams from Kick")

                # Process each stream
                for stream in streams:
                    try:
                        # Check if stream is a string (slug) or dict (stream object)
                        if isinstance(stream, str):
                            # If it's a slug, fetch the full channel info
                            slug = stream
                            logger.debug(f"Fetching channel info for slug: {slug}")
                            channel_info = await client.get_channel_info(slug)
                            
                            # Extract livestream data from channel info
                            livestream = channel_info.get("livestream", {})
                            if not livestream:
                                logger.warning(f"No active livestream for channel {slug}")
                                continue
                                
                            # Extract channel and stream data
                            username = channel_info.get("slug", slug)
                            follower_count = channel_info.get("followers_count", channel_info.get("follower_count", 0))
                            
                            stream_data = {
                                "channel_id": str(channel_info.get("id", slug)),
                                "username": username,
                                "display_name": channel_info.get("user", {}).get("username", username),
                                "title": livestream.get("session_title", ""),
                                "game_name": livestream.get("categories", [{}])[0].get("name", "") if livestream.get("categories") else "",
                                "viewer_count": livestream.get("viewer_count", 0),
                                "language": livestream.get("language", "en"),
                                "started_at": datetime.fromisoformat(livestream.get("created_at", "")) if livestream.get("created_at") else datetime.utcnow(),
                                "thumbnail_url": livestream.get("thumbnail", {}).get("url", ""),
                                "stream_url": f"https://kick.com/{slug}"
                            }
                        else:
                            # It's already a stream object
                            logger.debug(f"Full Kick stream response: {stream}")
                            
                            # Extract slug directly from stream response
                            slug = stream.get("slug", "")
                            username = slug  # Username is typically the slug
                            
                            # Parse started_at with timezone
                            started_at_str = stream.get("started_at", "")
                            if started_at_str:
                                # Remove 'Z' and parse
                                started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
                            else:
                                started_at = datetime.utcnow()
                            
                            # Extract thumbnail (it's a direct URL string, not a dict)
                            thumbnail = stream.get("thumbnail", "")
                            
                            # Extract category name
                            category = stream.get("category", {})
                            game_name = category.get("name", "") if isinstance(category, dict) else ""
                            
                            stream_data = {
                                "channel_id": str(stream.get("channel_id", slug)),
                                "username": username,
                                "display_name": username,
                                "title": stream.get("stream_title", ""),
                                "game_name": game_name,
                                "viewer_count": stream.get("viewer_count", 0),
                                "language": stream.get("language", "en"),
                                "started_at": started_at,
                                "thumbnail_url": thumbnail,
                                "stream_url": f"https://kick.com/{slug}" if slug else ""
                            }

                            # Fetch follower count from channel info
                            follower_count = 0
                            if slug:
                                try:
                                    channel_info = await client.get_channel_info(slug)
                                    follower_count = channel_info.get("followers_count", channel_info.get("follower_count", channel_info.get("followersCount", 0)))
                                    logger.debug(f"Fetched follower count for {slug}: {follower_count}")
                                except Exception as e:
                                    logger.warning(f"Could not fetch channel info for {slug}: {e}")
                                    follower_count = 0

                        logger.debug(f"Processing Kick stream - slug: {slug}, username: {username}, followers: {follower_count}")

                        # Get or create channel
                        channel = self.get_or_create_channel(
                            platform="kick",
                            channel_id=stream_data["channel_id"],
                            username=stream_data["username"],
                            display_name=stream_data["display_name"],
                            follower_count=follower_count  # Use fetched follower count
                        )

                        # Create snapshot
                        self.create_snapshot(channel, stream_data)
                        collected_count += 1

                    except Exception as e:
                        logger.error(f"Error processing Kick stream {stream.get('slug', 'unknown')}: {e}")
                        continue

                logger.info(f"Successfully stored {collected_count} Kick stream snapshots")

        except Exception as e:
            logger.error(f"Error during Kick collection: {e}")
            raise

        logger.info("Kick stream collection completed.")

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
