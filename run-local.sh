#!/bin/bash

echo "🚀 Starting Local Streaming Dashboard"
echo ""

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "⚠️  PostgreSQL is not running on localhost:5432"
    echo ""
    echo "Please start PostgreSQL first:"
    echo "  brew services start postgresql"
    echo ""
    exit 1
fi

echo "✅ PostgreSQL is running"

# Check if database exists, if not create it
if ! psql -h localhost -U streamdata -lqt | cut -d \| -f 1 | grep -qw streaming_platform 2>/dev/null; then
    echo "📦 Creating database..."
    createdb -h localhost -U streamdata streaming_platform 2>/dev/null || true
fi

echo "✅ Database ready"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Run the application
echo "🚀 Starting application on http://localhost:8000"
echo ""
echo "📊 Dashboard: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo "💚 Health: http://localhost:8000/api/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
