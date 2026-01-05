#!/bin/bash
# Startup script for Python MCP server

echo "Starting Lever MCP Python Server..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies if needed
if [ ! -f ".venv/pyvenv.cfg" ] || ! pip show fastmcp > /dev/null 2>&1; then
    echo "Installing Python dependencies..."
    pip install -e .
fi

# Check environment variables
if [ -z "$LEVER_API_KEY" ]; then
    echo "Warning: LEVER_API_KEY not set. Lever functionality will be limited."
fi

if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    echo "Warning: Google OAuth not configured. Email functionality will return payloads only."
fi

# Run the Python server
echo "Running Python MCP server..."
cd src
python -m server
