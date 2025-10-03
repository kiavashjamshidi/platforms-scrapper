#!/bin/bash

# Setup Verification Script
# This script checks if all prerequisites are met before starting the application

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Live Streaming Data Collection Platform - Setup Check     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if there are any errors
HAS_ERRORS=0

# Function to print success
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error
error() {
    echo -e "${RED}✗${NC} $1"
    HAS_ERRORS=1
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "Checking prerequisites..."
echo ""

# Check Docker
echo "1. Checking Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    success "Docker is installed: $DOCKER_VERSION"
    
    # Check if Docker is running
    if docker info &> /dev/null; then
        success "Docker daemon is running"
    else
        error "Docker daemon is not running. Please start Docker."
    fi
else
    error "Docker is not installed. Please install Docker from https://www.docker.com/get-started"
fi
echo ""

# Check Docker Compose
echo "2. Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    success "Docker Compose is installed: $COMPOSE_VERSION"
elif docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    success "Docker Compose (plugin) is installed: $COMPOSE_VERSION"
else
    error "Docker Compose is not installed"
fi
echo ""

# Check .env file
echo "3. Checking configuration..."
if [ -f .env ]; then
    success ".env file exists"
    
    # Check for required variables
    if grep -q "TWITCH_CLIENT_ID=your_twitch_client_id_here" .env || \
       ! grep -q "TWITCH_CLIENT_ID=" .env; then
        warning ".env file contains default/missing Twitch Client ID"
        echo "   Please update TWITCH_CLIENT_ID in .env file"
        echo "   Get credentials from: https://dev.twitch.tv/console"
    else
        success "Twitch Client ID is configured"
    fi
    
    if grep -q "TWITCH_CLIENT_SECRET=your_twitch_client_secret_here" .env || \
       ! grep -q "TWITCH_CLIENT_SECRET=" .env; then
        warning ".env file contains default/missing Twitch Client Secret"
        echo "   Please update TWITCH_CLIENT_SECRET in .env file"
    else
        success "Twitch Client Secret is configured"
    fi
else
    warning ".env file not found"
    echo "   Creating from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        success "Created .env from .env.example"
        warning "Please edit .env and add your Twitch API credentials"
        echo ""
        echo "   Steps to get credentials:"
        echo "   1. Go to https://dev.twitch.tv/console"
        echo "   2. Click 'Register Your Application'"
        echo "   3. Fill in the form:"
        echo "      - Name: Your app name"
        echo "      - OAuth Redirect URLs: http://localhost:8000/auth/callback"
        echo "      - Category: Application Integration"
        echo "   4. Copy Client ID and Client Secret to .env file"
    else
        error ".env.example not found. Cannot create .env file."
    fi
fi
echo ""

# Check disk space
echo "4. Checking disk space..."
if command -v df &> /dev/null; then
    AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
    success "Available disk space: $AVAILABLE_SPACE"
    
    # Check if less than 1GB available (very rough check)
    AVAILABLE_KB=$(df . | awk 'NR==2 {print $4}')
    if [ "$AVAILABLE_KB" -lt 1048576 ]; then
        warning "Low disk space. At least 1GB recommended."
    fi
fi
echo ""

# Check network connectivity
echo "5. Checking network connectivity..."
if ping -c 1 google.com &> /dev/null || ping -c 1 8.8.8.8 &> /dev/null; then
    success "Network connectivity OK"
else
    warning "Network connectivity issue detected. May affect API calls."
fi
echo ""

# Check if ports are available
echo "6. Checking port availability..."
if command -v lsof &> /dev/null; then
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        warning "Port 8000 is already in use"
        echo "   The API may fail to start. Stop the process using port 8000 or change API_PORT in .env"
    else
        success "Port 8000 is available"
    fi
    
    if lsof -Pi :5432 -sTCP:LISTEN -t >/dev/null ; then
        warning "Port 5432 is already in use"
        echo "   PostgreSQL may fail to start. Stop the process using port 5432 or use a different port"
    else
        success "Port 5432 is available"
    fi
elif command -v netstat &> /dev/null; then
    if netstat -an | grep -q ":8000.*LISTEN" ; then
        warning "Port 8000 is already in use"
    else
        success "Port 8000 is available"
    fi
    
    if netstat -an | grep -q ":5432.*LISTEN" ; then
        warning "Port 5432 is already in use"
    else
        success "Port 5432 is available"
    fi
else
    warning "Cannot check port availability (lsof/netstat not found)"
fi
echo ""

# Check for existing containers
echo "7. Checking for existing containers..."
if docker ps -a --format '{{.Names}}' | grep -q "streaming_"; then
    warning "Found existing containers from previous runs"
    echo "   You may want to clean them up with: docker-compose down"
    docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep "streaming_"
else
    success "No existing containers found"
fi
echo ""

# Check Docker resources (if on Mac/Windows)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "8. Docker Desktop detected (macOS)..."
    warning "Ensure Docker Desktop has at least 4GB RAM allocated"
    echo "   Check: Docker Desktop → Preferences → Resources"
    echo ""
fi

# Summary
echo "════════════════════════════════════════════════════════════════"
echo ""

if [ $HAS_ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Ensure your Twitch API credentials are set in .env"
    echo "  2. Run: ./start.sh  OR  make quick-start"
    echo ""
else
    echo -e "${RED}✗ Some issues were found. Please fix them before proceeding.${NC}"
    echo ""
    echo "Common fixes:"
    echo "  - Install Docker: https://www.docker.com/get-started"
    echo "  - Start Docker Desktop"
    echo "  - Configure .env with Twitch credentials"
    echo ""
    exit 1
fi

# Ask if user wants to continue
read -p "Do you want to start the services now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting services..."
    exec ./start.sh
fi
