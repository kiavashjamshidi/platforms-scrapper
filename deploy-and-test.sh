#!/bin/bash

echo "🚀 Deploying to Fly.io..."
echo ""

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null && ! command -v fly &> /dev/null; then
    echo "❌ Fly CLI not found. Install it first:"
    echo ""
    echo "curl -L https://fly.io/install.sh | sh"
    echo 'export PATH="$HOME/.fly/bin:$PATH"'
    echo ""
    exit 1
fi

# Use flyctl or fly command
FLY_CMD="flyctl"
if ! command -v flyctl &> /dev/null; then
    FLY_CMD="fly"
fi

echo "📦 Deploying application..."
$FLY_CMD deploy --app streaming-dashboard-kiavash

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔍 Checking app status..."
$FLY_CMD status --app streaming-dashboard-kiavash

echo ""
echo "📊 Testing endpoints..."
echo ""

echo "1️⃣  Health check:"
curl -s "https://streaming-dashboard-kiavash.fly.dev/api/health" | python3 -m json.tool 2>/dev/null || echo "❌ Health check failed"

echo ""
echo ""
echo "2️⃣  Twitch streams (first 3):"
curl -s "https://streaming-dashboard-kiavash.fly.dev/api/streams?platform=twitch&limit=3" | python3 -m json.tool 2>/dev/null || echo "❌ API call failed"

echo ""
echo ""
echo "3️⃣  Trigger manual collection:"
curl -s -X POST "https://streaming-dashboard-kiavash.fly.dev/api/collect-all"

echo ""
echo ""
echo "⏳ Waiting 10 seconds for collection to complete..."
sleep 10

echo ""
echo "4️⃣  Check streams again (should have fresh data):"
curl -s "https://streaming-dashboard-kiavash.fly.dev/api/streams?platform=twitch&limit=3" | python3 -m json.tool

echo ""
echo ""
echo "📝 To view logs:"
echo "$FLY_CMD logs --app streaming-dashboard-kiavash"
echo ""
echo "📝 To view logs in real-time:"
echo "$FLY_CMD logs --app streaming-dashboard-kiavash --follow"
