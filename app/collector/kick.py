"""Kick API client for collecting live stream data."""
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
import httpx
from loguru import logger
from app.config import settings


class KickClient:
    """Client for interacting with Kick's official API."""

    OAUTH_URL = "https://id.kick.com/oauth/token"
    BASE_URL = "https://api.kick.com/public/v1"
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._http_client: Optional[httpx.AsyncClient] = None
        self._access_token: Optional[str] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient(timeout=30.0)
        await self._get_access_token()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.aclose()

    async def _get_access_token(self) -> str:
        """
        Get OAuth2 access token using client credentials.
        """
        try:
            response = await self._http_client.post(
                self.OAUTH_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            )
            response.raise_for_status()
            token_data = response.json()
            self._access_token = token_data["access_token"]
            logger.info("Successfully obtained Kick access token")
            return self._access_token
        except Exception as e:
            logger.error(f"Failed to get Kick access token: {e}")
            raise

    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        retries: int = 0
    ) -> Dict[str, Any]:
        """
        Make a request to Kick's API with retry logic.
        """
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"Authorization": f"Bearer {self._access_token}"}

        try:
            response = await self._http_client.get(
                url,
                headers=headers,
                params=params or {}
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if retries < settings.max_retries:
                # Exponential backoff
                wait_time = settings.retry_backoff_factor ** retries
                logger.warning(f"Request failed, retrying in {wait_time}s... (attempt {retries + 1})")
                await asyncio.sleep(wait_time)
                return await self._make_request(endpoint, params, retries + 1)
            else:
                logger.error(f"Request failed after {settings.max_retries} retries: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error making request to {endpoint}: {e}")
            raise

    async def get_live_streams(self, limit: int = 100, language: str = "en") -> List[Dict[str, Any]]:
        """
        Get live streams from Kick.

        Args:
            limit: Number of streams to return (max 100).
            language: Language filter for streams.

        Returns:
            List of live stream objects.
        """
        endpoint = "livestreams"
        params = {
            "limit": min(limit, 100),
            "sort": "viewer_count",
            "language": language
        }
        result = await self._make_request(endpoint, params)
        logger.debug(f"Livestreams API response (first 2): {result.get('data', [])[:2]}")
        return result.get("data", [])

    async def get_channel_info(self, channel_slug: str) -> Dict[str, Any]:
        """
        Get channel information from Kick using the official API.

        Args:
            channel_slug: The slug of the channel to fetch information for.

        Returns:
            Channel information object with followers count.
        """
        try:
            endpoint = f"channels/{channel_slug}"
            result = await self._make_request(endpoint)
            
            logger.debug(f"Channel info for {channel_slug}: followers={result.get('followers_count', 0)}")
            return result
            
        except Exception as e:
            logger.warning(f"Failed to fetch channel info for {channel_slug}: {e}")
            return {}