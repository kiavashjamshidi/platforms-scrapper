# Live Streaming Data Collection Dashboard

A local dashboard for collecting and analyzing live streaming data from Twitch, Kick, and YouTube.

## Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 14+

**Install PostgreSQL (macOS):**
```bash
brew install postgresql@14
brew services start postgresql@14
```

### 2. Setup Database

```bash
# Create user
psql postgres -c "CREATE USER streamdata WITH PASSWORD 'streamdata_password';"

# Create database
psql postgres -c "CREATE DATABASE streaming_platform OWNER streamdata;"
```

### 3. Run the Application

```bash
./run-local.sh
```

This will:
- Check PostgreSQL is running
- Create virtual environment if needed
- Install dependencies
- Start the application on http://localhost:8000

## Access Points

- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Features

- ✅ Real-time data collection from Twitch, Kick, and YouTube
- ✅ Automatic collection every 2 minutes
- ✅ Search and filter streams
- ✅ Sort by viewers, followers, etc.
- ✅ View stream details (language, duration, start time)

## Manual Collection

Trigger data collection manually:

```bash
curl -X POST "http://localhost:8000/api/collect-all"
```

## Configuration

Edit `.env` file to configure:
- Database connection
- API credentials (Twitch, Kick, YouTube)
- Collection interval

## Troubleshooting

### PostgreSQL not running
```bash
brew services start postgresql@14
```

### Database connection error
```bash
# Check PostgreSQL status
pg_isready -h localhost -p 5432

# Recreate database
dropdb streaming_platform
createdb streaming_platform -O streamdata
```

### Port 8000 already in use
```bash
# Find process using port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in .env
API_PORT=8001
```

## Development

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest tests/
```

## Project Structure

```
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── api/
│   │   └── routes.py        # API endpoints
│   └── collector/
│       ├── scheduler.py     # Data collection scheduler
│       ├── twitch.py        # Twitch API client
│       ├── kick.py          # Kick API client
│       └── youtube.py       # YouTube API client
├── static/
│   └── index.html           # Dashboard UI
└── .env                     # Environment variables
```
