# Streaming Dashboard

Live streaming data collection from Twitch, Kick, and YouTube.

## Quick Start

### 1. Make sure Docker Desktop is running

### 2. Run the start script

```bash
./start.sh
```

That's it! The dashboard will be available at **http://localhost:8000**

## What it does

The `start.sh` script will:
- ✅ Check Docker is running
- ✅ Build the application container
- ✅ Start PostgreSQL database
- ✅ Start the application
- ✅ Make it available on http://localhost:8000

## Access Points

- **Dashboard**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Useful Commands

```bash
# View logs
docker-compose logs -f

# View only app logs
docker-compose logs -f app

# Stop everything
docker-compose down

# Stop and remove all data
docker-compose down -v

# Restart
docker-compose restart
```

## Troubleshooting

### Docker not running
Make sure Docker Desktop is started.

### Port already in use
```bash
# Stop existing containers
docker-compose down

# Or kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### See what's happening
```bash
# View logs
docker-compose logs -f

# Check container status
docker-compose ps
```

## Configuration

Edit `.env` file to configure:
- API credentials (Twitch, Kick, YouTube)
- Collection interval
- Database settings
