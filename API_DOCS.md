# API Documentation

## Overview

The Live Streaming Data Collection API provides endpoints to access and analyze live streaming data collected from various platforms (currently Twitch, with Kick and YouTube coming soon).

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production, you should implement API keys or OAuth.

## Endpoints

### 1. Get Top Live Streams

Retrieve the top live streams sorted by viewer count or follower count.

**Endpoint:** `GET /live/top`

**Query Parameters:**

- `platform` (string, default: "twitch"): Platform to query (twitch/kick/youtube)
- `limit` (integer, default: 50, max: 500): Number of results to return
- `sort_by` (string, default: "viewers"): Sort by "viewers" (current viewer count) or "followers" (channel follower count)

**Example Request:**

```bash
# Top streams by current viewers (default)
curl "http://localhost:8000/live/top?platform=twitch&limit=10"

# Top streams by follower count
curl "http://localhost:8000/live/top?platform=twitch&limit=10&sort_by=followers"
```

**Example Response:**

```json
[
  {
    "platform": "twitch",
    "channel_id": "12345678",
    "username": "streamer_name",
    "display_name": "Streamer Name",
    "title": "Playing Awesome Game!",
    "game_name": "Valorant",
    "viewer_count": 50000,
    "language": "en",
    "started_at": "2024-01-15T14:30:00Z",
    "thumbnail_url": "https://...",
    "stream_url": "https://twitch.tv/streamer_name",
    "follower_count": 1000000,
    "collected_at": "2024-01-15T16:45:00Z"
  }
]
```

---

### 2. Get Most Active Streamers

Get streamers ranked by how frequently they stream (number of stream sessions).

**Endpoint:** `GET /live/most-active`

**Query Parameters:**

- `platform` (string, default: "twitch"): Platform to query
- `window` (string, default: "7d"): Time window (e.g., "24h", "7d", "30d")
- `limit` (integer, default: 10, max: 100): Number of results to return

**Example Request:**

```bash
# Most active streamers in the last 7 days
curl "http://localhost:8000/live/most-active?platform=twitch&window=7d&limit=10"
```

**Example Response:**

```json
[
  {
    "platform": "twitch",
    "channel_id": "12345678",
    "username": "streamer_name",
    "display_name": "Streamer Name",
    "follower_count": 1000000,
    "profile_image_url": "https://...",
    "stream_count": 42,
    "total_snapshots": 504,
    "avg_viewers": 45230.5,
    "peak_viewers": 78000,
    "last_seen": "2024-01-15T16:45:00Z",
    "stream_url": "https://twitch.tv/streamer_name"
  }
]
```

**Response Fields:**

- `stream_count`: Number of distinct streaming sessions (grouped by hour)
- `total_snapshots`: Total number of data points collected
- `avg_viewers`: Average viewer count across all streams
- `peak_viewers`: Highest viewer count recorded
- `last_seen`: Timestamp of most recent stream

---

### 3. Search Streams

Search for live streams by keyword in title, game name, or username.

**Endpoint:** `GET /search`

**Query Parameters:**

- `platform` (string, default: "twitch"): Platform to search
- `q` (string, required): Search query
- `limit` (integer, default: 20, max: 100): Number of results

**Example Request:**

```bash
curl "http://localhost:8000/search?platform=twitch&q=valorant&limit=20"
```

**Example Response:**

```json
[
  {
    "platform": "twitch",
    "channel_id": "87654321",
    "username": "valorant_pro",
    "display_name": "Valorant Pro",
    "title": "Ranked Valorant - Road to Radiant",
    "game_name": "Valorant",
    "viewer_count": 15000,
    "language": "en",
    "started_at": "2024-01-15T13:00:00Z",
    "thumbnail_url": "https://...",
    "stream_url": "https://twitch.tv/valorant_pro",
    "follower_count": 500000,
    "collected_at": "2024-01-15T16:45:00Z"
  }
]
```

---

### 4. Get Channel History

Retrieve historical data for a specific channel within a time window.

**Endpoint:** `GET /channel/{platform}/{channel_id}/history`

**Path Parameters:**

- `platform` (string): Platform (twitch/kick/youtube)
- `channel_id` (string): Platform-specific channel ID

**Query Parameters:**

- `window` (string, default: "24h"): Time window (e.g., "24h", "7d", "30d")

**Example Request:**

```bash
curl "http://localhost:8000/channel/twitch/12345678/history?window=24h"
```

**Example Response:**

```json
{
  "channel": {
    "id": 1,
    "platform": "twitch",
    "channel_id": "12345678",
    "username": "streamer_name",
    "display_name": "Streamer Name",
    "description": "Channel description",
    "profile_image_url": "https://...",
    "follower_count": 1000000,
    "created_at": "2024-01-10T10:00:00Z",
    "updated_at": "2024-01-15T16:45:00Z"
  },
  "snapshots": [
    {
      "id": 1,
      "channel_id": 1,
      "title": "Playing Games",
      "game_name": "Valorant",
      "game_id": "516575",
      "viewer_count": 50000,
      "language": "en",
      "started_at": "2024-01-15T14:30:00Z",
      "collected_at": "2024-01-15T14:35:00Z",
      "thumbnail_url": "https://...",
      "stream_url": "https://twitch.tv/streamer_name"
    }
  ],
  "total_snapshots": 24,
  "avg_viewer_count": 45000.5,
  "peak_viewer_count": 55000
}
```

---

### 5. Get Category Statistics

Get trending categories/games with aggregated statistics.

**Endpoint:** `GET /stats/categories`

**Query Parameters:**

- `platform` (string, default: "twitch"): Platform to query
- `window` (string, default: "7d"): Time window (e.g., "24h", "7d", "30d")
- `limit` (integer, default: 10, max: 100): Number of categories

**Example Request:**

```bash
curl "http://localhost:8000/stats/categories?platform=twitch&window=7d&limit=10"
```

**Example Response:**

```json
[
  {
    "game_name": "Valorant",
    "total_streams": 15000,
    "total_viewers": 5000000,
    "avg_viewers": 333.33,
    "peak_viewers": 100000
  },
  {
    "game_name": "League of Legends",
    "total_streams": 20000,
    "total_viewers": 8000000,
    "avg_viewers": 400.0,
    "peak_viewers": 150000
  }
]
```

---

### 6. Export Data as CSV

Export stream data as a CSV file for a given time window.

**Endpoint:** `GET /export/csv`

**Query Parameters:**

- `platform` (string, default: "twitch"): Platform to export
- `window` (string, default: "24h"): Time window (e.g., "24h", "7d", "30d")

**Example Request:**

```bash
curl "http://localhost:8000/export/csv?platform=twitch&window=24h" --output streams.csv
```

**CSV Format:**

```csv
collected_at,platform,channel_id,username,display_name,title,game_name,viewer_count,language,started_at,follower_count,stream_url
2024-01-15T16:45:00,twitch,12345678,streamer_name,Streamer Name,Playing Games,Valorant,50000,en,2024-01-15T14:30:00,1000000,https://twitch.tv/streamer_name
```

---

### 7. Health Check

Check the health status of the API and its dependencies.

**Endpoint:** `GET /health`

**Example Request:**

```bash
curl "http://localhost:8000/health"
```

**Example Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T16:45:00Z",
  "database": "healthy"
}
```

---

## Time Window Format

Time windows can be specified using the following formats:

- `24h` - 24 hours
- `7d` - 7 days
- `30d` - 30 days
- `2w` - 2 weeks

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**

- `200 OK` - Request successful
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Rate Limiting

Currently, there is no rate limiting. In production, implement rate limiting to prevent abuse.

---

## Data Freshness

Data is collected every 5 minutes (configurable). The `collected_at` field indicates when the data was captured.

---

## Best Practices

1. **Pagination**: For large datasets, use the `limit` parameter to control response size
2. **Caching**: Consider caching responses on the client side
3. **Time Windows**: Use appropriate time windows for your use case to balance data freshness and query performance
4. **CSV Export**: Use CSV export for bulk data analysis or integration with other tools

---

## Examples with Python

### Using requests library

```python
import requests

# Get top streams
response = requests.get(
    "http://localhost:8000/live/top",
    params={"platform": "twitch", "limit": 10}
)
streams = response.json()

for stream in streams:
    print(f"{stream['username']}: {stream['viewer_count']} viewers")
```

### Using httpx (async)

```python
import httpx
import asyncio

async def get_top_streams():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/live/top",
            params={"platform": "twitch", "limit": 10}
        )
        return response.json()

streams = asyncio.run(get_top_streams())
```

---

## Examples with JavaScript

### Using fetch

```javascript
// Get top streams
fetch("http://localhost:8000/live/top?platform=twitch&limit=10")
  .then((response) => response.json())
  .then((streams) => {
    streams.forEach((stream) => {
      console.log(`${stream.username}: ${stream.viewer_count} viewers`);
    });
  });
```

### Using axios

```javascript
const axios = require("axios");

async function getTopStreams() {
  const response = await axios.get("http://localhost:8000/live/top", {
    params: {
      platform: "twitch",
      limit: 10,
    },
  });
  return response.data;
}
```

---

## Support

For issues or questions, please check the logs:

- API logs: `docker-compose logs -f api`
- Collector logs: `docker-compose logs -f collector`
