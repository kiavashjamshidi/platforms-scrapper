# Live Streaming Data Collection Platform

A backend service for collecting and analyzing live streaming data from platforms like Twitch (Kick and YouTube support coming soon).

## Features

- Collects live stream data every 5 minutes
- Stores data in PostgreSQL
- Provides REST API access via FastAPI
- Fully containerized with Docker Compose

## Setup

1. **Environment Configuration**:
   Create a `.env` file with the following:

   ```env
   POSTGRES_USER=streamdata
   POSTGRES_PASSWORD=your_secure_password
   POSTGRES_DB=streaming_platform
   TWITCH_CLIENT_ID=your_client_id_here
   TWITCH_CLIENT_SECRET=your_client_secret_here
   ```

2. **Run with Docker Compose**:

   ```bash
   docker-compose up --build
   ```

3. **Access the Application**:
   - API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Health Check: [http://localhost:8000/health](http://localhost:8000/health)

## API Example

- **Get Top Live Streams**:
  ```bash
  curl "http://localhost:8000/live/top?platform=twitch&limit=10"
  ```
