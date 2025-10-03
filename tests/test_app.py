"""Test suite for the streaming data collection platform."""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Channel, LiveSnapshot
from app.schemas import LiveStreamResponse, ChannelHistoryResponse


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_channel(db):
    """Create a sample channel for testing."""
    channel = Channel(
        platform="twitch",
        channel_id="12345678",
        username="test_streamer",
        display_name="Test Streamer",
        description="Test channel",
        profile_image_url="https://example.com/avatar.jpg",
        follower_count=10000
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


@pytest.fixture
def sample_snapshots(db, sample_channel):
    """Create sample snapshots for testing."""
    snapshots = []
    base_time = datetime.utcnow()
    
    for i in range(5):
        snapshot = LiveSnapshot(
            channel_id=sample_channel.id,
            title=f"Test Stream {i}",
            game_name="Test Game",
            game_id="123",
            viewer_count=1000 + (i * 100),
            language="en",
            started_at=base_time - timedelta(hours=2),
            collected_at=base_time - timedelta(minutes=i * 5),
            thumbnail_url="https://example.com/thumb.jpg",
            stream_url="https://twitch.tv/test_streamer"
        )
        db.add(snapshot)
        snapshots.append(snapshot)
    
    db.commit()
    return snapshots


class TestModels:
    """Test database models."""
    
    def test_create_channel(self, db):
        """Test creating a channel."""
        channel = Channel(
            platform="twitch",
            channel_id="12345",
            username="testuser",
            display_name="Test User"
        )
        db.add(channel)
        db.commit()
        
        assert channel.id is not None
        assert channel.platform == "twitch"
        assert channel.username == "testuser"
    
    def test_create_snapshot(self, db, sample_channel):
        """Test creating a live snapshot."""
        snapshot = LiveSnapshot(
            channel_id=sample_channel.id,
            title="Test Stream",
            game_name="Test Game",
            viewer_count=1000
        )
        db.add(snapshot)
        db.commit()
        
        assert snapshot.id is not None
        assert snapshot.channel_id == sample_channel.id
        assert snapshot.viewer_count == 1000
    
    def test_channel_snapshot_relationship(self, db, sample_channel, sample_snapshots):
        """Test relationship between channel and snapshots."""
        assert len(sample_channel.snapshots) == len(sample_snapshots)
        assert all(s.channel_id == sample_channel.id for s in sample_channel.snapshots)


class TestTwitchClient:
    """Test Twitch API client."""
    
    @pytest.mark.asyncio
    async def test_parse_stream_data(self):
        """Test parsing stream data from Twitch API response."""
        from app.collector.twitch import TwitchClient
        
        raw_stream = {
            "user_id": "123456",
            "user_login": "teststreamer",
            "user_name": "TestStreamer",
            "title": "Playing Games",
            "game_id": "789",
            "game_name": "Test Game",
            "viewer_count": 5000,
            "language": "en",
            "started_at": "2024-01-01T12:00:00Z",
            "thumbnail_url": "https://example.com/thumb-{width}x{height}.jpg"
        }
        
        parsed = TwitchClient.parse_stream_data(raw_stream)
        
        assert parsed["channel_id"] == "123456"
        assert parsed["username"] == "teststreamer"
        assert parsed["display_name"] == "TestStreamer"
        assert parsed["viewer_count"] == 5000
        assert parsed["game_name"] == "Test Game"
        assert "1920x1080" in parsed["thumbnail_url"]


class TestSchemas:
    """Test Pydantic schemas."""
    
    def test_channel_schema(self, sample_channel):
        """Test Channel schema validation."""
        from app.schemas import Channel as ChannelSchema
        
        schema = ChannelSchema.model_validate(sample_channel)
        assert schema.username == "test_streamer"
        assert schema.platform == "twitch"
    
    def test_live_snapshot_schema(self, sample_snapshots):
        """Test LiveSnapshot schema validation."""
        from app.schemas import LiveSnapshot as SnapshotSchema
        
        schema = SnapshotSchema.model_validate(sample_snapshots[0])
        assert schema.title == "Test Stream 0"
        assert schema.viewer_count >= 1000


class TestUtilities:
    """Test utility functions."""
    
    def test_parse_time_window(self):
        """Test time window parsing."""
        from app.api.routes import parse_time_window
        
        now = datetime.utcnow()
        
        # Test hours
        result = parse_time_window("24h")
        assert (now - result).total_seconds() / 3600 == pytest.approx(24, rel=0.01)
        
        # Test days
        result = parse_time_window("7d")
        assert (now - result).days == 7
        
        # Test weeks
        result = parse_time_window("2w")
        assert (now - result).days == 14
        
        # Test invalid format
        with pytest.raises(ValueError):
            parse_time_window("invalid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
