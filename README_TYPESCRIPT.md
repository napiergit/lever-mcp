# Lever MCP TypeScript Server

A TypeScript implementation of the Lever MCP server with identical functionality to the Python version.

## Project Structure

```
src/
├── mcp/
│   ├── py/           # Python implementation (original)
│   │   ├── server.py
│   │   ├── client.py
│   │   ├── gmail_client.py
│   │   └── oauth_config.py
│   └── ts/           # TypeScript implementation (new)
│       ├── package.json
│       ├── tsconfig.json
│       ├── src/
│       │   ├── server.ts
│       │   ├── client.ts
│       │   ├── gmail-client.ts
│       │   ├── oauth-config.ts
│       │   └── email-templates.ts
│       └── dist/     # Compiled JavaScript (generated)
```

## Features

The TypeScript MCP server provides identical functionality to the Python version:

### Lever Integration
- **list_candidates**: List candidates from Lever
- **get_candidate**: Get specific candidate by ID
- **create_requisition**: Create new job requisitions

### Gmail Integration
- **send_email**: Send themed HTML emails via Gmail API
- **get_oauth_url**: Get OAuth authorization URL
- **exchange_oauth_code**: Exchange authorization code for access token
- **get_browser_agent_oauth_url**: Browser-optimized OAuth flow
- **poll_oauth_code**: Poll for OAuth completion (browser agents)
- **check_oauth_status**: Check OAuth configuration status

### Email Themes
- 🎂 **birthday**: Celebration theme with colorful gradient
- 🏴‍☠️ **pirate**: Nautical theme with dark styling
- 🚀 **space**: Cosmic theme with stellar gradients
- ⚔️ **medieval**: Royal theme with parchment styling
- 💥 **superhero**: Comic book theme with bold colors
- 🌴 **tropical**: Beach theme with warm colors

### Utility Functions
- **echo**: Echo messages for testing
- **health**: Server health check
- **test_connection**: Verify MCP connectivity

## Setup

### Prerequisites
- Node.js 18+ and npm
- Same environment variables as Python version:
  - `LEVER_API_KEY`: Your Lever API key
  - `GOOGLE_CLIENT_ID`: Google OAuth client ID
  - `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
  - `MCP_SERVER_BASE_URL`: Base URL for OAuth callbacks

### Installation

1. **Install dependencies:**
   ```bash
   cd src/mcp/ts
   npm install
   ```

2. **Build the project:**
   ```bash
   npm run build
   ```

3. **Development mode (with auto-rebuild):**
   ```bash
   npm run dev
   ```

## Usage

### Running the MCP Server

**Production mode:**
```bash
cd src/mcp/ts
npm start
```

**Development mode:**
```bash
cd src/mcp/ts
npm run dev
```

### Testing the Server

The TypeScript server uses the same MCP protocol as the Python version:

```bash
# List available tools
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node dist/server.js

# Health check
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"health","arguments":{}}}' | node dist/server.js

# Test connection
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"test_connection","arguments":{}}}' | node dist/server.js

# Send themed email
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"send_email","arguments":{"to":"test@example.com","theme":"birthday"}}}' | node dist/server.js
```

## Architecture

### Core Components

1. **server.ts**: Main MCP server with tool handlers
2. **client.ts**: Lever API client for candidate/requisition management
3. **gmail-client.ts**: Gmail API client with OAuth 2.0 support
4. **oauth-config.ts**: OAuth configuration and token management
5. **email-templates.ts**: Themed HTML email templates

### TypeScript Features

- **Strong typing**: Full type safety with interfaces and generics
- **ES Modules**: Modern JavaScript module system
- **Async/await**: Native promise handling
- **Error handling**: Comprehensive error management
- **OAuth 2.0**: Browser agent polling flow support

### Key Differences from Python Version

- Uses Google Auth Library for Node.js instead of google-auth-oauthlib
- Native Buffer support for base64 encoding
- TypeScript interfaces for type safety
- ESM module system with .js imports
- npm package management instead of pip

## Development

### Building
```bash
npm run build      # Compile TypeScript to JavaScript
npm run clean      # Remove dist directory
```

### Development Workflow
```bash
npm run dev        # Watch mode with auto-rebuild
```

### Dependencies

**Runtime:**
- `@modelcontextprotocol/sdk`: MCP protocol implementation
- `googleapis`: Google APIs client library
- `axios`: HTTP client for Lever API
- `uuid`: UUID generation for session IDs
- `express`: Web framework (for future HTTP endpoints)

**Development:**
- `typescript`: TypeScript compiler
- `tsx`: TypeScript execution environment
- `@types/*`: Type definitions

## Compatibility

The TypeScript server is 100% compatible with the Python version:
- Identical MCP tool definitions
- Same OAuth flow and browser agent polling
- Identical email templates and Gmail integration
- Same error handling and response formats
- Compatible with all existing MCP clients

## Performance

The TypeScript implementation offers several advantages:
- **Faster startup**: Node.js typically starts faster than Python
- **Lower memory usage**: More efficient for concurrent operations
- **Better async handling**: Native Promise support
- **Type safety**: Compile-time error checking

## Migration from Python

If migrating from the Python version:
1. Environment variables remain the same
2. OAuth tokens are compatible between versions
3. All tool names and schemas are identical
4. Response formats are unchanged

Both versions can run side by side during transition.
