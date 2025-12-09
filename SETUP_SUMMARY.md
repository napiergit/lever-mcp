# Setup Summary - OAuth Proxy for Toqan

## What Was Fixed

The error **"could not discover MCP OAuth metadata"** occurred because the MCP server wasn't exposing OAuth metadata that Toqan needs to discover and use OAuth.

## Solution Implemented

Added **FastMCP OAuth Proxy** to the server, which:
1. Exposes OAuth metadata at `/.well-known/oauth-authorization-server`
2. Acts as an OAuth proxy between Toqan and Google
3. Handles the complete OAuth flow automatically
4. Provides tokens to Toqan for calling MCP tools

## What You Need to Do

### Step 1: Get Google OAuth Credentials

1. Go to https://console.cloud.google.com/
2. Create/select a project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Web application type)
5. Add redirect URI: `http://localhost:8080/auth/callback`
6. Copy Client ID and Client Secret

### Step 2: Create `.env` File

```bash
# Copy template
cp .env.example .env

# Edit .env and add your credentials:
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
MCP_SERVER_BASE_URL=http://localhost:8080
```

### Step 3: Start Server

```bash
source .venv/bin/activate
./run.sh
```

### Step 4: Add to Toqan

Configure Toqan with your MCP server. The OAuth flow will now work automatically!

## How It Works Now

```
Toqan → Discovers OAuth metadata from MCP server
      → Starts OAuth flow via MCP OAuth proxy
      → MCP proxy redirects to Google
      → User authorizes
      → Token flows back through proxy to Toqan
      → Toqan calls send_email with token
      → Email sent via Gmail API ✅
```

## Files Changed

1. **`src/lever_mcp/server.py`** - Added OAuthProxy configuration
2. **`.env.example`** - Updated with OAuth proxy requirements
3. **`TOQAN_SETUP.md`** - Complete setup guide for Toqan integration

## Testing

Once configured, test with:

```bash
# Check OAuth metadata is exposed
curl http://localhost:8080/.well-known/oauth-authorization-server
```

Should return JSON with OAuth endpoints.

## Key Configuration

- **GOOGLE_CLIENT_ID**: Your Google OAuth client ID (required)
- **GOOGLE_CLIENT_SECRET**: Your Google OAuth client secret (required)
- **MCP_SERVER_BASE_URL**: Where your server is accessible (required)

The redirect URI in Google Console must be: `{MCP_SERVER_BASE_URL}/auth/callback`

## Next Steps

1. Provide your Google Client ID and Secret
2. I'll help you test the OAuth flow
3. Integrate with Toqan
4. Send emails! 🎉

See **TOQAN_SETUP.md** for detailed instructions.
