#!/bin/bash
# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the MCP server in SSE mode
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
# Use the fastmcp executable from the venv
./.venv/bin/fastmcp run src/server.py:mcp --transport sse --port 8005
