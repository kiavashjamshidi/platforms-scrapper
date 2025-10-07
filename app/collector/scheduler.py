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
        Collect live streams from Twitch using demo data.
        """
        logger.info("Starting Twitch stream collection...")
        collected_count = 0

        try:
            # Create demo Twitch data since Twitch API requires credentials
            logger.info("Creating demo Twitch stream data...")
            
            demo_streams = [
                {
                    "channel_id": "twitch_demo1",
                    "username": "ninja",
                    "display_name": "Ninja",
                    "title": "Fortnite Champion Series - Road to Victory!",
                    "game_name": "Fortnite",
                    "game_id": "33214",
                    "viewer_count": 45250,
                    "language": "en",
                    "started_at": datetime.utcnow(),
                    "thumbnail_url": None,
                    "stream_url": "https://twitch.tv/ninja"
                },
                {
                    "channel_id": "twitch_demo2", 
                    "username": "shroud",
                    "display_name": "shroud",
                    "title": "VALORANT Ranked Grind | !youtube !discord",
                    "game_name": "VALORANT",
                    "game_id": "516575",
                    "viewer_count": 32100,
                    "language": "en",
                    "started_at": datetime.utcnow(),
                    "thumbnail_url": None,
                    "stream_url": "https://twitch.tv/shroud"
                },
                {
                    "channel_id": "twitch_demo3",
                    "username": "pokimane", 
                    "display_name": "pokimane",
                    "title": "Just Chatting with Chat! | !socials",
                    "game_name": "Just Chatting",
                    "game_id": "509658",
                    "viewer_count": 28900,
                    "language": "en",
                    "started_at": datetime.utcnow(),
                    "thumbnail_url": None,
                    "stream_url": "https://twitch.tv/pokimane"
                },
                {
                    "channel_id": "twitch_demo4",
                    "username": "xqc",
                    "display_name": "xQc",
                    "title": "VARIETY GAMING | REACTING TO VIDEOS",
                    "game_name": "Variety",
                    "game_id": "509663",
                    "viewer_count": 51200,
                    "language": "en",
                    "started_at": datetime.utcnow(),
                    "thumbnail_url": None,
                    "stream_url": "https://twitch.tv/xqc"
                },
                {
                    "channel_id": "twitch_demo5",
                    "username": "asmongold",
                    "display_name": "Asmongold",
                    "title": "WoW Classic Hardcore - Permadeath Challenge",
                    "game_name": "World of Warcraft",
                    "game_id": "18122",
                    "viewer_count": 39700,
                    "language": "en",
                    "started_at": datetime.utcnow(),
                    "thumbnail_url": None,
                    "stream_url": "https://twitch.tv/asmongold"
                },
                {
                    "channel_id": "twitch_demo6",
                    "username": "lirik",
                    "display_name": "LIRIK",
                    "title": "Cyberpunk 2077 - Story Playthrough",
                    "game_name": "Cyberpunk 2077",
                    "game_id": "65876",
                    "viewer_count": 24600,
                    "language": "en",
                    "started_at": datetime.utcnow(),
                    "thumbnail_url": None,
                    "stream_url": "https://twitch.tv/lirik"
                }
            ]
            
            for stream_data in demo_streams:
                # Get or create channel
                channel = self.get_or_create_channel(
                    platform="twitch",
                    channel_id=stream_data["channel_id"],
                    username=stream_data["username"],
                    display_name=stream_data["display_name"],
                    follower_count=500000 + (collected_count * 100000)  # Vary follower counts
                )
                
                # Create snapshot
                self.create_snapshot(channel, stream_data)
                collected_count += 1
                logger.debug(f"Created demo stream for {stream_data['username']}")
                
            logger.info(f"Successfully created {collected_count} demo Twitch stream snapshots")
            
        except Exception as e:
            logger.error(f"Error creating demo Twitch data: {e}")

        logger.info("Twitch stream collection completed.")

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
