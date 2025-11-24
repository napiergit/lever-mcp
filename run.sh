#!/bin/bash
# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the MCP server
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
# Use the fastmcp executable from the venv
./.venv/bin/fastmcp run src/lever_mcp/server.py:mcp
