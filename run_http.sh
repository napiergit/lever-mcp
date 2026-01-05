#!/bin/bash
# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "Loaded environment variables from .env"
fi

# Run the MCP server in streamable HTTP mode
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
# Use the fastmcp executable from the venv
./.venv/bin/fastmcp run src/server.py:mcp --transport streamable-http --port 8005
