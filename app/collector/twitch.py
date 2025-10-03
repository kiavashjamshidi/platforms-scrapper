"""Twitch API client for collecting live stream data."""
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
import httpx
from loguru import logger
from app.config import settings


class TwitchClient:
    """Client for interacting with Twitch Helix API."""
    
    BASE_URL = "https://api.twitch.tv/helix"
    AUTH_URL = "https://id.twitch.tv/oauth2/token"
    
    def __init__(self):
        self.client_id = settings.twitch_client_id
        self.client_secret = settings.twitch_client_secret
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient(timeout=30.0)
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.aclose()
    
    async def authenticate(self) -> str:
        """
        Authenticate with Twitch API using Client Credentials flow.
        Returns the access token.
        """
        try:
            logger.info("Authenticating with Twitch API...")
            
            response = await self._http_client.post(
                self.AUTH_URL,
                params={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials"
                }
            )
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data["access_token"]
            expires_in = data.get("expires_in", 3600)
            
            # Set expiration time with 5-minute buffer
            from datetime import timedelta
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 300)
            
            logger.info("Successfully authenticated with Twitch API")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Twitch API: {e}")
            raise
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid access token."""
        if not self.access_token or (self.token_expires_at and datetime.utcnow() >= self.token_expires_at):
            await self.authenticate()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.access_token}"
        }
    
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        retries: int = 0
    ) -> Dict[str, Any]:
        """
        Make a request to Twitch API with retry logic.
        """
        await self._ensure_authenticated()
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = await self._http_client.get(
                url,
                headers=self._get_headers(),
                params=params or {}
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401 and retries < settings.max_retries:
                # Token might be expired, re-authenticate
                logger.warning("Token expired, re-authenticating...")
                await self.authenticate()
                return await self._make_request(endpoint, params, retries + 1)
            elif retries < settings.max_retries:
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
    
    async def get_streams(
        self,
        first: int = 100,
        after: Optional[str] = None,
        game_id: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get live streams.
        
        Args:
            first: Number of streams to return (max 100)
            after: Cursor for pagination
            game_id: Filter by game ID
            language: Filter by language
            
        Returns:
            Dictionary containing 'data' (list of streams) and 'pagination'
        """
        params = {"first": min(first, 100)}
        
        if after:
            params["after"] = after
        if game_id:
            params["game_id"] = game_id
        if language:
            params["language"] = language
        
        return await self._make_request("streams", params)
    
    async def get_all_streams(
        self,
        max_results: int = 1000,
        game_id: Optional[str] = None,
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all live streams with pagination.
        
        Args:
            max_results: Maximum number of streams to fetch
            game_id: Filter by game ID
            language: Filter by language
            
        Returns:
            List of stream objects
        """
        all_streams = []
        cursor = None
        
        while len(all_streams) < max_results:
            remaining = max_results - len(all_streams)
            batch_size = min(100, remaining)
            
            result = await self.get_streams(
                first=batch_size,
                after=cursor,
                game_id=game_id,
                language=language
            )
            
            streams = result.get("data", [])
            if not streams:
                break
            
            all_streams.extend(streams)
            
            # Check if there's more data
            pagination = result.get("pagination", {})
            cursor = pagination.get("cursor")
            
            if not cursor:
                break
            
            logger.info(f"Fetched {len(all_streams)} streams so far...")
        
        logger.info(f"Total streams fetched: {len(all_streams)}")
        return all_streams
    
    async def get_users(self, user_ids: List[str] = None, logins: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get user information.
        
        Args:
            user_ids: List of user IDs (max 100)
            logins: List of usernames (max 100)
            
        Returns:
            List of user objects
        """
        params = {}
        
        if user_ids:
            params["id"] = user_ids[:100]
        if logins:
            params["login"] = logins[:100]
        
        result = await self._make_request("users", params)
        return [
            {
                "id": user.get("id"),
                "login": user.get("login"),
                "display_name": user.get("display_name"),
                "follower_count": user.get("follower_count", 0)  # Extract follower_count
            }
            for user in result.get("data", [])
        ]
    
    async def get_games(self, game_ids: List[str] = None, names: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get game information.
        
        Args:
            game_ids: List of game IDs (max 100)
            names: List of game names (max 100)
            
        Returns:
            List of game objects
        """
        params = {}
        
        if game_ids:
            params["id"] = game_ids[:100]
        if names:
            params["name"] = names[:100]
        
        result = await self._make_request("games", params)
        return result.get("data", [])
    
    async def get_top_games(self, first: int = 100, after: Optional[str] = None) -> Dict[str, Any]:
        """
        Get top games/categories.
        
        Args:
            first: Number of games to return (max 100)
            after: Cursor for pagination
            
        Returns:
            Dictionary containing 'data' and 'pagination'
        """
        params = {"first": min(first, 100)}
        if after:
            params["after"] = after
        
        return await self._make_request("games/top", params)
    
    async def search_channels(
        self,
        query: str,
        first: int = 20,
        live_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for channels.
        
        Args:
            query: Search query
            first: Number of results (max 100)
            live_only: Only return live channels
            
        Returns:
            List of channel objects
        """
        params = {
            "query": query,
            "first": min(first, 100),
            "live_only": live_only
        }
        
        result = await self._make_request("search/channels", params)
        return result.get("data", [])
    
    async def search_categories(self, query: str, first: int = 20) -> List[Dict[str, Any]]:
        """
        Search for categories/games.
        
        Args:
            query: Search query
            first: Number of results (max 100)
            
        Returns:
            List of category objects
        """
        params = {
            "query": query,
            "first": min(first, 100)
        }
        
        result = await self._make_request("search/categories", params)
        return result.get("data", [])
    
    async def get_follower_count(self, broadcaster_id: str) -> int:
        """
        Get the follower count for a specific channel using the Get Channel Followers endpoint.

        Args:
            broadcaster_id: The ID of the broadcaster to fetch the follower count for.

        Returns:
            The total number of followers for the broadcaster.
        """
        endpoint = f"channels/followers"
        params = {"broadcaster_id": broadcaster_id}
        result = await self._make_request(endpoint, params)
        return result.get("total", 0)
    
    @staticmethod
    def parse_stream_data(stream: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse stream data from Twitch API response.
        
        Args:
            stream: Stream object from API
            
        Returns:
            Normalized stream data
        """
        return {
            "channel_id": stream.get("user_id"),
            "username": stream.get("user_login"),
            "display_name": stream.get("user_name"),
            "title": stream.get("title"),
            "game_id": stream.get("game_id"),
            "game_name": stream.get("game_name"),
            "viewer_count": stream.get("viewer_count", 0),
            "language": stream.get("language"),
            "started_at": datetime.fromisoformat(stream.get("started_at", "").replace("Z", "+00:00"))
            if stream.get("started_at") else None,
            "thumbnail_url": stream.get("thumbnail_url", "").replace("{width}", "1920").replace("{height}", "1080"),
            "stream_url": f"https://www.twitch.tv/{stream.get('user_login')}"
        }
