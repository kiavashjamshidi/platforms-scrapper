# System Architecture

## Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Live Streaming Platform                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          External APIs                               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐      ┌──────────┐      ┌──────────┐                  │
│  │  Twitch  │      │   Kick   │      │ YouTube  │                  │
│  │ Helix API│      │   API    │      │ Live API │                  │
│  └────┬─────┘      └─────┬────┘      └─────┬────┘                  │
│       │                  │                  │                       │
│       └──────────────────┴──────────────────┘                       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           │ HTTPS Requests
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                    Data Collector Service                            │
├─────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    Scheduler (APScheduler)                  │    │
│  │                  Runs every 5 minutes                       │    │
│  └──────────────────────────┬─────────────────────────────────┘    │
│                             │                                        │
│  ┌──────────────────────────▼─────────────────────────────────┐    │
│  │              Platform-Specific Collectors                   │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │    │
│  │  │   Twitch     │  │     Kick     │  │   YouTube    │     │    │
│  │  │   Client     │  │   Client     │  │   Client     │     │    │
│  │  │  (Active)    │  │  (Planned)   │  │  (Planned)   │     │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │    │
│  └──────────────────────────┬─────────────────────────────────┘    │
│                             │                                        │
│  ┌──────────────────────────▼─────────────────────────────────┐    │
│  │           Data Parser & Normalizer                          │    │
│  │  • Parse API responses                                      │    │
│  │  • Extract relevant fields                                  │    │
│  │  • Normalize data format                                    │    │
│  └──────────────────────────┬─────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ Store Data
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                      PostgreSQL Database                             │
├─────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────┐          ┌──────────────────────┐          │
│  │  channels          │          │  live_snapshots      │          │
│  ├────────────────────┤          ├──────────────────────┤          │
│  │ • id               │          │ • id                 │          │
│  │ • platform         │◄─────────┤ • channel_id (FK)    │          │
│  │ • channel_id       │          │ • title              │          │
│  │ • username         │          │ • game_name          │          │
│  │ • display_name     │          │ • viewer_count       │          │
│  │ • follower_count   │          │ • language           │          │
│  │ • created_at       │          │ • started_at         │          │
│  │ • updated_at       │          │ • collected_at       │          │
│  └────────────────────┘          │ • stream_url         │          │
│                                   └──────────────────────┘          │
│                                                                      │
│  Indexes:                                                            │
│  • platform + channel_id (unique)                                   │
│  • collected_at (for time-based queries)                            │
│  • game_name + collected_at (for category stats)                    │
│  • viewer_count (for sorting)                                       │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               │ Query Data
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                       FastAPI Service                                │
├─────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    API Routes                               │    │
│  │  ┌──────────────────────────────────────────────────┐      │    │
│  │  │  GET /live/top                                    │      │    │
│  │  │  • Returns top streams by viewer count           │      │    │
│  │  └──────────────────────────────────────────────────┘      │    │
│  │  ┌──────────────────────────────────────────────────┐      │    │
│  │  │  GET /search                                      │      │    │
│  │  │  • Search streams by keyword                     │      │    │
│  │  └──────────────────────────────────────────────────┘      │    │
│  │  ┌──────────────────────────────────────────────────┐      │    │
│  │  │  GET /channel/{platform}/{id}/history            │      │    │
│  │  │  • Get channel historical data                   │      │    │
│  │  └──────────────────────────────────────────────────┘      │    │
│  │  ┌──────────────────────────────────────────────────┐      │    │
│  │  │  GET /stats/categories                            │      │    │
│  │  │  • Get trending category statistics              │      │    │
│  │  └──────────────────────────────────────────────────┘      │    │
│  │  ┌──────────────────────────────────────────────────┐      │    │
│  │  │  GET /export/csv                                  │      │    │
│  │  │  • Export data as CSV file                       │      │    │
│  │  └──────────────────────────────────────────────────┘      │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                  Middleware & Features                      │    │
│  │  • CORS (Cross-Origin Resource Sharing)                    │    │
│  │  • Automatic API documentation (/docs, /redoc)             │    │
│  │  • Request validation (Pydantic)                           │    │
│  │  • Error handling                                          │    │
│  │  • Health checks                                           │    │
│  └────────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               │ HTTP/JSON
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                          Clients                                     │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │  Web     │  │  Mobile  │  │  CLI     │  │ Business │           │
│  │  Browser │  │   App    │  │  Tools   │  │Dashboard │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Collection Flow (Every 5 minutes)

```
1. Scheduler triggers collection
   ↓
2. Authenticate with Twitch API (OAuth 2.0)
   ↓
3. Fetch live streams (paginated, up to 100)
   ↓
4. Parse and normalize stream data
   ↓
5. For each stream:
   ├── Check if channel exists in DB
   │   ├── Yes → Update channel info
   │   └── No  → Create new channel record
   ↓
6. Create snapshot record with:
   • Link to channel
   • Stream details
   • Viewer count
   • Timestamp
   ↓
7. Commit to database
   ↓
8. Log statistics
   ↓
9. Wait for next cycle
```

### Query Flow (API Request)

```
1. Client sends HTTP request
   ↓
2. FastAPI receives request
   ↓
3. Validate request parameters (Pydantic)
   ↓
4. Execute database query (SQLAlchemy)
   ↓
5. Transform results to response schema
   ↓
6. Return JSON response
   ↓
7. Client processes data
```

## Component Details

### 1. Twitch Client (`app/collector/twitch.py`)

**Responsibilities:**

- OAuth 2.0 authentication
- API request handling
- Rate limit management
- Response parsing
- Error handling with retries

**Key Features:**

- Automatic token refresh
- Exponential backoff on failures
- Pagination support
- Data normalization

**API Endpoints Used:**

- `/oauth2/token` - Authentication
- `/helix/streams` - Live streams
- `/helix/users` - User info
- `/helix/games` - Game metadata
- `/helix/games/top` - Trending games

### 2. Scheduler (`app/collector/scheduler.py`)

**Responsibilities:**

- Periodic data collection
- Collection orchestration
- Error recovery
- Statistics logging

**Configuration:**

- Interval: 5 minutes (configurable)
- Max streams: 100 per collection
- Retry attempts: 3 with exponential backoff

### 3. Database Models (`app/models.py`)

**channels table:**

- Stores static channel information
- Unique constraint: (platform, channel_id)
- Updated on each collection

**live_snapshots table:**

- Time-series data
- Links to channels via foreign key
- Indexed for fast queries

**Relationship:**

- One channel → Many snapshots
- Cascade delete enabled

### 4. API Service (`app/main.py`, `app/api/routes.py`)

**Features:**

- RESTful API design
- Automatic validation
- Interactive documentation
- CORS support
- Health monitoring

**Response Formats:**

- JSON (default)
- CSV (export endpoint)

### 5. Database (`PostgreSQL`)

**Indexes:**

```sql
-- Channels
CREATE UNIQUE INDEX idx_platform_channel_id ON channels(platform, channel_id);

-- Live Snapshots
CREATE INDEX idx_collected_at ON live_snapshots(collected_at);
CREATE INDEX idx_game_collected ON live_snapshots(game_name, collected_at);
CREATE INDEX idx_channel_collected ON live_snapshots(channel_id, collected_at);
```

**Optimization:**

- Connection pooling (10 connections)
- Pre-ping for connection health
- Indexed foreign keys

## Docker Architecture

```
┌─────────────────────────────────────────────────────┐
│              Docker Compose Network                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────┐  ┌──────────────────┐        │
│  │  API Container   │  │Collector Container│       │
│  │  Port: 8000      │  │  Background       │       │
│  │  FastAPI         │  │  Scheduler        │       │
│  └────────┬─────────┘  └────────┬──────────┘       │
│           │                     │                   │
│           └──────────┬──────────┘                   │
│                      │                              │
│           ┌──────────▼───────────┐                  │
│           │  DB Container        │                  │
│           │  Port: 5432          │                  │
│           │  PostgreSQL 15       │                  │
│           │  Volume: postgres_data│                 │
│           └──────────────────────┘                  │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Network:**

- Internal Docker network
- PostgreSQL only accessible within network
- API exposed on host port 8000

**Volumes:**

- `postgres_data` - Persistent database storage
- `.:/app` - Source code (development mode)

**Health Checks:**

- Database: `pg_isready` command
- API: Depends on database health

## Scaling Considerations

### Horizontal Scaling

```
Load Balancer
      ↓
  ┌───┴───┐
  │       │
API-1   API-2 ... API-N
  │       │
  └───┬───┘
      ↓
  PostgreSQL
      ↑
  Collector
```

**Steps:**

1. Deploy multiple API instances
2. Add load balancer (nginx/traefik)
3. Single collector instance
4. Consider Redis for caching
5. Database connection pooling

### Vertical Scaling

- Increase Docker resource limits
- Optimize database configuration
- Add read replicas for queries
- Implement caching layer

## Security Architecture

**Current (Development):**

- No authentication
- All endpoints public
- CORS: Allow all origins

**Production Recommendations:**

```
┌──────────────────────────────────────┐
│  Reverse Proxy (nginx)               │
│  • SSL/TLS termination               │
│  • Rate limiting                     │
│  • DDoS protection                   │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│  API Gateway                          │
│  • API key validation                │
│  • OAuth 2.0                         │
│  • Request throttling                │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│  Application                          │
│  • Input validation                  │
│  • SQL injection prevention          │
│  • Secure credentials                │
└──────────────────────────────────────┘
```

## Monitoring & Observability

**Logs:**

- Application logs: Loguru
- Database logs: PostgreSQL logs
- Container logs: Docker logs

**Metrics (Proposed):**

- Prometheus for metrics collection
- Grafana for visualization
- Key metrics:
  - Collection success rate
  - API response times
  - Database query performance
  - Error rates

**Health Checks:**

- `/health` endpoint
- Database connectivity
- Service status

## Future Enhancements

1. **Additional Platforms:**
   - Kick.com integration
   - YouTube Live integration

2. **Features:**
   - WebSocket for real-time updates
   - Advanced analytics
   - Alerting system
   - Webhook notifications

3. **Performance:**
   - Redis caching
   - Celery for distributed tasks
   - Database partitioning
   - CDN for static content

4. **Monitoring:**
   - Prometheus metrics
   - Grafana dashboards
   - Error tracking (Sentry)
   - APM (Application Performance Monitoring)
