# Local Development Setup

## Prerequisites

1. **PostgreSQL** - Install and start:
   ```bash
   brew install postgresql@14
   brew services start postgresql@14
   ```

2. **Python 3.11+** - Check version:
   ```bash
   python3 --version
   ```

## Setup (First Time)

### 1. Create Database

```bash
# Create user
psql postgres -c "CREATE USER streamdata WITH PASSWORD 'streamdata_password';"

# Create database
psql postgres -c "CREATE DATABASE streaming_platform OWNER streamdata;"

# Grant privileges
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE streaming_platform TO streamdata;"
```

### 2. Verify .env Configuration

Make sure `.env` file has correct local settings:

```env
DATABASE_URL=postgresql://streamdata:streamdata_password@localhost:5432/streaming_platform
API_HOST=0.0.0.0
API_PORT=8000
```

## Running the Application

Simply run:

```bash
./run-local.sh
```

This will:
- ✅ Check PostgreSQL is running
- ✅ Create virtual environment if needed
- ✅ Install dependencies
- ✅ Start the application on http://localhost:8000

## Access the Dashboard

Open in your browser:
- **Dashboard**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Manual Collection

Trigger data collection manually:

```bash
curl -X POST "http://localhost:8000/api/collect-all"
```

## Stopping the Application

Press `Ctrl + C` in the terminal where the app is running.

## Troubleshooting

### PostgreSQL not running

```bash
brew services start postgresql@14
pg_isready -h localhost -p 5432
```

### Database connection error

```bash
# Check if database exists
psql -l | grep streaming_platform

# If not, create it:
psql postgres -c "CREATE DATABASE streaming_platform OWNER streamdata;"
```

### Port 8000 already in use

```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use a different port in .env
API_PORT=8001
```

### Clear database and start fresh

```bash
psql postgres -c "DROP DATABASE IF EXISTS streaming_platform;"
psql postgres -c "CREATE DATABASE streaming_platform OWNER streamdata;"
./run-local.sh
```

## Development Tips

### Activate virtual environment manually

```bash
source .venv/bin/activate
```

### Run with auto-reload

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### View logs

The app logs to console. Look for:
```
INFO: Starting Live Streaming Data Collection API
INFO: Twitch credentials found
INFO: Received X streams from Twitch API
```

### Check what's in the database

```bash
psql -U streamdata -d streaming_platform

# List tables
\dt

# Check channels
SELECT platform, channel_name, followers FROM channels LIMIT 10;

# Check live snapshots
SELECT platform, channel_name, current_viewers, created_at 
FROM live_snapshots 
ORDER BY created_at DESC LIMIT 10;
```
