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
from kickapi import KickAPI


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
        self._kick_api = None  # Initialize KickAPI instance
    
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
        Collect live streams from Kick using demo data.
        """
        logger.info("Starting Kick stream collection...")
        collected_count = 0

        try:
            # Create demo data since Kick API requires credentials
            logger.info("Creating demo Kick stream data...")
            
            demo_streams = [
                {
                    "channel_id": "demo1",
                    "username": "gaming_pro_1",
                    "display_name": "Gaming Pro 1",
                    "title": "🔥 EPIC Gaming Session - Come Join!",
                    "game_name": "Just Chatting",
                    "game_id": "1",
                    "viewer_count": 1250,
                    "language": "en",
                    "started_at": datetime.utcnow(),
                    "thumbnail_url": None,
                    "stream_url": "https://kick.com/gaming_pro_1"
                },
                {
                    "channel_id": "demo2", 
                    "username": "kick_streamer_2",
                    "display_name": "Kick Streamer 2",
                    "title": "Fortnite Victory Royales! | !socials",
                    "game_name": "Fortnite",
                    "game_id": "2",
                    "viewer_count": 850,
                    "language": "en",
                    "started_at": datetime.utcnow(),
                    "thumbnail_url": None,
                    "stream_url": "https://kick.com/kick_streamer_2"
                },
                {
                    "channel_id": "demo3",
                    "username": "minecraft_builder", 
                    "display_name": "Minecraft Builder",
                    "title": "Building Epic Castle! Creative Mode",
                    "game_name": "Minecraft",
                    "game_id": "3",
                    "viewer_count": 2100,
                    "language": "en",
                    "started_at": datetime.utcnow(),
                    "thumbnail_url": None,
                    "stream_url": "https://kick.com/minecraft_builder"
                },
                {
                    "channel_id": "demo4",
                    "username": "valorant_ace",
                    "display_name": "Valorant Ace",
                    "title": "Ranked Grind - Road to Radiant",
                    "game_name": "VALORANT",
                    "game_id": "4",
                    "viewer_count": 750,
                    "language": "en",
                    "started_at": datetime.utcnow(),
                    "thumbnail_url": None,
                    "stream_url": "https://kick.com/valorant_ace"
                },
                {
                    "channel_id": "demo5",
                    "username": "irl_adventures",
                    "display_name": "IRL Adventures",
                    "title": "City Walk - Exploring Downtown",
                    "game_name": "IRL",
                    "game_id": "5",
                    "viewer_count": 450,
                    "language": "en",
                    "started_at": datetime.utcnow(),
                    "thumbnail_url": None,
                    "stream_url": "https://kick.com/irl_adventures"
                }
            ]
            
            for stream_data in demo_streams:
                # Get or create channel
                channel = self.get_or_create_channel(
                    platform="kick",
                    channel_id=stream_data["channel_id"],
                    username=stream_data["username"],
                    display_name=stream_data["display_name"],
                    follower_count=10000 + (collected_count * 1000)  # Vary follower counts
                )
                
                # Create snapshot
                self.create_snapshot(channel, stream_data)
                collected_count += 1
                logger.debug(f"Created demo stream for {stream_data['username']}")
                
            logger.info(f"Successfully created {collected_count} demo Kick stream snapshots")
            
        except Exception as e:
            logger.error(f"Error creating demo Kick data: {e}")

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
