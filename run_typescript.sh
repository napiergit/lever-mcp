#!/bin/bash
# Startup script for TypeScript MCP server

echo "Starting Lever MCP TypeScript Server..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed. Please install Node.js 18+ and npm."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed. Please install npm."
    exit 1
fi

# Navigate to TypeScript directory
cd src/mcp/ts

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing TypeScript dependencies..."
    npm install
fi

# Build the project if needed
if [ ! -d "dist" ] || [ "src/server.ts" -nt "dist/server.js" ]; then
    echo "Building TypeScript project..."
    npm run build
fi

# Check environment variables
if [ -z "$LEVER_API_KEY" ]; then
    echo "Warning: LEVER_API_KEY not set. Lever functionality will be limited."
fi

if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    echo "Warning: Google OAuth not configured. Email functionality will return payloads only."
fi

# Run the TypeScript server
echo "Running TypeScript MCP server..."
npm start
