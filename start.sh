#!/bin/bash

echo "🚀 Starting Streaming Dashboard with Docker"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Please make sure you have a .env file with your API credentials."
    exit 1
fi

echo "✅ .env file found"
echo ""

# Build and start containers
echo "🏗️  Building and starting containers..."
docker compose up --build -d

echo ""
echo "✅ Containers started!"
echo ""
echo "📊 Dashboard: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo "💚 Health: http://localhost:8000/api/health"
echo ""
echo "📝 To view logs: docker compose logs -f"
echo "📝 To stop: docker compose down"
