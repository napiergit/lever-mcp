#!/bin/bash
# Development script - choose between Python and TypeScript

echo "Lever MCP Server - Development Mode"
echo "=================================="
echo "1. Run Python implementation"
echo "2. Run TypeScript implementation" 
echo "3. Run TypeScript in development mode (watch)"
echo "4. Test both implementations"
echo ""
read -p "Choose option (1-4): " choice

case $choice in
    1)
        echo "Starting Python development server..."
        ./run_python.sh
        ;;
    2)
        echo "Starting TypeScript production server..."
        ./run_typescript.sh
        ;;
    3)
        echo "Starting TypeScript development server (watch mode)..."
        cd src/mcp/ts
        if [ ! -d "node_modules" ]; then
            echo "Installing dependencies..."
            npm install
        fi
        npm run dev
        ;;
    4)
        echo "Testing both implementations..."
        echo ""
        echo "Testing TypeScript server..."
        cd src/mcp/ts
        if [ ! -d "dist" ]; then
            npm run build
        fi
        echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node dist/server.js | head -5
        echo ""
        echo "TypeScript server test completed."
        echo ""
        echo "Note: Python server requires virtual environment setup to test."
        echo "Run './run_python.sh' to set up and test Python server."
        ;;
    *)
        echo "Invalid option. Please choose 1-4."
        ;;
esac
