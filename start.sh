#!/bin/bash

# Quick Start Script for Streaming Data Collector

set -e

echo "🚀 Live Streaming Data Collection Platform - Quick Start"
echo "=========================================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it with your Twitch API credentials."
    echo ""
    echo "📝 Required steps:"
    echo "   1. Go to https://dev.twitch.tv/console"
    echo "   2. Register your application"
    echo "   3. Copy Client ID and Client Secret to .env file"
    echo ""
    echo "After updating .env, run this script again."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Build and start containers
echo "🔨 Building Docker containers..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "streaming_api.*Up"; then
    echo "✅ API service is running"
else
    echo "❌ API service failed to start"
    docker-compose logs api
    exit 1
fi

if docker-compose ps | grep -q "streaming_collector.*Up"; then
    echo "✅ Collector service is running"
else
    echo "⚠️  Collector service may have issues"
fi

if docker-compose ps | grep -q "streaming_db.*Up"; then
    echo "✅ Database is running"
else
    echo "❌ Database failed to start"
    exit 1
fi

echo ""
echo "=========================================================="
echo "✅ All services are running!"
echo "=========================================================="
echo ""
echo "📊 Access Points:"
echo "   API Documentation:  http://localhost:8000/docs"
echo "   Alternative Docs:   http://localhost:8000/redoc"
echo "   Health Check:       http://localhost:8000/health"
echo ""
echo "📝 Useful Commands:"
echo "   View API logs:       docker-compose logs -f api"
echo "   View collector logs: docker-compose logs -f collector"
echo "   View all logs:       docker-compose logs -f"
echo "   Stop services:       docker-compose down"
echo "   Restart services:    docker-compose restart"
echo ""
echo "🎯 Example API Calls:"
echo "   curl http://localhost:8000/api/v1/live/top?platform=twitch&limit=10"
echo "   curl http://localhost:8000/api/v1/search?platform=twitch&q=valorant"
echo ""
echo "Happy streaming! 🎮"
