import asyncio
from app.collector.kick import KickClient

async def test_kick_client():
    async with KickClient() as client:
        streams = await client.get_live_streams(limit=5)
        print("Kick API Response:", streams)

if __name__ == "__main__":
    asyncio.run(test_kick_client())