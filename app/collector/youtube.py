"""YouTube API client for data collection."""
import asyncio
from typing import List, Dict, Any
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger

class YouTubeClient:
    """Client for interacting with the YouTube API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.youtube = build("youtube", "v3", developerKey=api_key)

    async def get_live_streams(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch live streams from YouTube."""
        try:
            # Search for live streams
            request = self.youtube.search().list(
                part="snippet",
                type="video",
                eventType="live",
                maxResults=min(limit, 50)  # YouTube API max is 50
            )
            response = request.execute()
            streams = response.get("items", [])
            
            if not streams:
                logger.info("No live streams found")
                return []
            
            # Extract video IDs for detailed information
            video_ids = []
            for item in streams:
                if isinstance(item["id"], dict) and "videoId" in item["id"]:
                    video_ids.append(item["id"]["videoId"])
                elif isinstance(item["id"], str):
                    video_ids.append(item["id"])
            
            # Get detailed video information including viewer counts
            if video_ids:
                video_request = self.youtube.videos().list(
                    part="snippet,liveStreamingDetails,statistics",
                    id=",".join(video_ids)
                )
                video_response = video_request.execute()
                
                # Combine search results with detailed video info
                detailed_streams = []
                video_details = {v["id"]: v for v in video_response.get("items", [])}
                
                for stream in streams:
                    video_id = stream["id"].get("videoId") if isinstance(stream["id"], dict) else stream["id"]
                    if video_id in video_details:
                        # Merge stream data with detailed video info
                        detailed_stream = stream.copy()
                        detailed_stream["videoDetails"] = video_details[video_id]
                        detailed_streams.append(detailed_stream)
                
                return detailed_streams
            
            return streams
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return []

    async def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """Fetch channel information by channel ID."""
        try:
            request = self.youtube.channels().list(
                part="snippet,statistics",
                id=channel_id
            )
            response = request.execute()
            if "items" in response and len(response["items"]) > 0:
                return response["items"][0]
            return {}
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass