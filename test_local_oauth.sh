#!/bin/bash

# Local OAuth Testing Script
# This script helps you test the complete OAuth flow locally

set -e

echo "=================================="
echo "🧪 Local OAuth Testing Suite"
echo "=================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ No .env file found!"
    echo ""
    echo "Please create a .env file with your Google OAuth credentials:"
    echo "  cp .env.example .env"
    echo ""
    echo "Then edit .env and add:"
    echo "  GOOGLE_CLIENT_ID=your_client_id"
    echo "  GOOGLE_CLIENT_SECRET=your_client_secret"
    echo "  MCP_SERVER_BASE_URL=http://localhost:8000"
    echo ""
    echo "Also add http://localhost:8000/oauth/callback as an authorized"
    echo "redirect URI in your Google Cloud Console."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check required variables
if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    echo "❌ Missing required environment variables!"
    echo ""
    echo "Please set in .env:"
    echo "  GOOGLE_CLIENT_ID=your_client_id"
    echo "  GOOGLE_CLIENT_SECRET=your_client_secret"
    exit 1
fi

echo "✅ Environment variables loaded"
echo "   Client ID: ${GOOGLE_CLIENT_ID:0:20}..."
echo "   Base URL: ${MCP_SERVER_BASE_URL:-http://localhost:8000}"
echo ""

# Check if server is running
SERVER_URL="${MCP_SERVER_BASE_URL:-http://localhost:8000}"
if ! curl -s -f "$SERVER_URL" > /dev/null 2>&1; then
    echo "❌ MCP server is not running at $SERVER_URL"
    echo ""
    echo "Please start the server in another terminal:"
    echo "  ./run_http.sh"
    echo ""
    echo "Or:"
    echo "  python -m uvicorn lever_mcp.server:mcp.app --host 0.0.0.0 --port 8000"
    exit 1
fi

echo "✅ MCP server is running at $SERVER_URL"
echo ""

# Install dependencies if needed
if ! python -c "import dotenv" 2>/dev/null; then
    echo "📦 Installing python-dotenv..."
    pip install python-dotenv
fi

# Run tests
echo "=================================="
echo "🧪 Running End-to-End Tests"
echo "=================================="
echo ""

python tests/test_oauth_e2e.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "✅ All tests passed!"
    echo "=================================="
    echo ""
    echo "Next steps:"
    echo "  1. Run the mock Toqan client to test the full OAuth flow:"
    echo "     python tests/mock_toqan_client.py"
    echo ""
    echo "  2. The client will:"
    echo "     - Open your browser for Google authorization"
    echo "     - Exchange the code for an access token"
    echo "     - Send a test email using the token"
    echo ""
    echo "  3. If everything works, deploy to production!"
    echo ""
else
    echo ""
    echo "=================================="
    echo "❌ Some tests failed"
    echo "=================================="
    echo ""
    echo "Please fix the issues above before proceeding."
    exit 1
fi
