"""Test script to run data collection and see debug output."""
import asyncio
import sys
from app.collector.scheduler import StreamCollector
from loguru import logger

# Configure logger to show everything
logger.remove()
logger.add(sys.stdout, level="DEBUG", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

async def test_collection():
    """Run a single collection cycle."""
    collector = StreamCollector()
    try:
        await collector.run_collection()
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if hasattr(collector, 'db'):
            collector.db.close()

if __name__ == "__main__":
    logger.info("Starting test collection...")
    asyncio.run(test_collection())
    logger.info("Test collection complete!")
