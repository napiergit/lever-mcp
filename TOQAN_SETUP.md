# Toqan Integration Setup Guide

This guide shows you how to set up the Lever MCP server with OAuth for Toqan integration.

## Quick Setup

### 1. Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API" and click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Web application"
   - Add authorized redirect URI: `http://localhost:8080/auth/callback` (for local testing)
   - For production, add your server's public URL: `https://your-domain.com/auth/callback`
   - Download or copy Client ID and Client Secret

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Lever API (optional, only needed for Lever tools)
LEVER_API_KEY=your-lever-api-key-here

# Google OAuth (required for Gmail integration)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# MCP Server Base URL (required for OAuth proxy)
# For local testing:
MCP_SERVER_BASE_URL=http://localhost:8080

# For production (use your actual domain):
# MCP_SERVER_BASE_URL=https://your-domain.com
```

### 3. Start the MCP Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Start server (stdio mode for Toqan)
./run.sh

# OR start in HTTP mode for testing
./run_http.sh
```

### 4. Add to Toqan

In Toqan's MCP configuration, add:

```json
{
  "mcpServers": {
    "lever": {
      "command": "/bin/bash",
      "args": ["/absolute/path/to/lever-mcp/run.sh"],
      "env": {
        "GOOGLE_CLIENT_ID": "your-client-id.apps.googleusercontent.com",
        "GOOGLE_CLIENT_SECRET": "your-client-secret",
        "MCP_SERVER_BASE_URL": "http://localhost:8080"
      }
    }
  }
}
```

**Important:** Use absolute paths!

## How OAuth Works with Toqan

```
┌─────────┐         ┌─────────┐         ┌──────────────┐         ┌──────────┐
│  User   │────────▶│ Toqan   │────────▶│  MCP Server  │────────▶│  Google  │
│         │         │         │         │ (OAuth Proxy)│         │  OAuth   │
└─────────┘         └─────────┘         └──────────────┘         └──────────┘
    │                    │                      │                      │
    │ 1. "Send email"    │                      │                      │
    │───────────────────▶│                      │                      │
    │                    │                      │                      │
    │                    │ 2. Discover OAuth    │                      │
    │                    │    metadata          │                      │
    │                    │─────────────────────▶│                      │
    │                    │                      │                      │
    │                    │ 3. OAuth metadata    │                      │
    │                    │◀─────────────────────│                      │
    │                    │                      │                      │
    │                    │ 4. Start OAuth flow  │                      │
    │                    │─────────────────────▶│                      │
    │                    │                      │                      │
    │                    │                      │ 5. Redirect to Google│
    │                    │                      │─────────────────────▶│
    │                    │                      │                      │
    │ 6. Authorize       │                      │                      │
    │───────────────────────────────────────────────────────────────▶│
    │                    │                      │                      │
    │ 7. Auth code       │                      │                      │
    │◀───────────────────────────────────────────────────────────────│
    │                    │                      │                      │
    │                    │ 8. Exchange code     │                      │
    │                    │─────────────────────▶│                      │
    │                    │                      │                      │
    │                    │                      │ 9. Get token         │
    │                    │                      │─────────────────────▶│
    │                    │                      │                      │
    │                    │                      │ 10. Access token     │
    │                    │                      │◀─────────────────────│
    │                    │                      │                      │
    │                    │ 11. Token to Toqan   │                      │
    │                    │◀─────────────────────│                      │
    │                    │                      │                      │
    │                    │ 12. Call send_email  │                      │
    │                    │     with token       │                      │
    │                    │─────────────────────▶│                      │
    │                    │                      │                      │
    │                    │                      │ 13. Send via Gmail   │
    │                    │                      │─────────────────────▶│
    │                    │                      │                      │
    │ 14. "Email sent!"  │                      │                      │
    │◀───────────────────│                      │                      │
```

## Key Points

### OAuth Proxy
The MCP server acts as an **OAuth proxy** between Toqan and Google:
- Toqan discovers OAuth metadata from MCP server via `/.well-known/oauth-authorization-server`
- MCP server proxies the OAuth flow to Google
- User authorizes with Google
- MCP server receives and validates the token
- Token is passed to Toqan
- Toqan uses token to call MCP tools

### No Manual Token Management
- You don't need to manually obtain tokens
- Toqan handles the OAuth flow automatically
- The MCP server's OAuth proxy manages the flow
- Tokens are passed automatically with tool calls

### Required Configuration
1. **GOOGLE_CLIENT_ID** - Your Google OAuth client ID
2. **GOOGLE_CLIENT_SECRET** - Your Google OAuth client secret
3. **MCP_SERVER_BASE_URL** - Where your MCP server is accessible

### Redirect URI Configuration
In Google Cloud Console, add this redirect URI:
- Local: `http://localhost:8080/auth/callback`
- Production: `https://your-domain.com/auth/callback`

The redirect URI must match `{MCP_SERVER_BASE_URL}/auth/callback`

## Testing

### 1. Test OAuth Discovery

```bash
# Start server in HTTP mode
./run_http.sh

# In another terminal, test OAuth metadata endpoint
curl http://localhost:8080/.well-known/oauth-authorization-server
```

You should see OAuth metadata including:
- `authorization_endpoint`
- `token_endpoint`
- `scopes_supported`

### 2. Test with Toqan

1. Add MCP server to Toqan configuration
2. Ask Toqan: "Send a birthday email to test@example.com"
3. Toqan should:
   - Discover OAuth metadata
   - Start OAuth flow
   - Prompt you to authorize
   - Send the email after authorization

## Troubleshooting

### "could not discover MCP OAuth metadata"

**Causes:**
- MCP server not running
- OAuth not configured (missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET)
- MCP_SERVER_BASE_URL not set or incorrect

**Solution:**
1. Check `.env` file has all required variables
2. Restart MCP server
3. Check server logs for OAuth configuration messages

### "redirect_uri_mismatch"

**Cause:** Redirect URI in Google Cloud Console doesn't match server configuration

**Solution:**
1. Check `MCP_SERVER_BASE_URL` in `.env`
2. In Google Cloud Console, add redirect URI: `{MCP_SERVER_BASE_URL}/auth/callback`
3. Example: If `MCP_SERVER_BASE_URL=http://localhost:8080`, add `http://localhost:8080/auth/callback`

### "invalid_client"

**Cause:** Client ID or Secret incorrect

**Solution:**
1. Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
2. Check for extra spaces or quotes
3. Regenerate credentials in Google Cloud Console if needed

### Server won't start

**Check logs:**
```bash
# Run server and watch logs
./run.sh 2>&1 | tee server.log
```

**Common issues:**
- Port 8080 already in use (change `MCP_SERVER_BASE_URL`)
- Missing dependencies (run `pip install -e .`)
- Python version < 3.10 (upgrade Python)

## Production Deployment

### 1. Use HTTPS
```bash
MCP_SERVER_BASE_URL=https://your-domain.com
```

### 2. Update Google OAuth Redirect URI
Add in Google Cloud Console:
```
https://your-domain.com/auth/callback
```

### 3. Secure Environment Variables
- Use secrets management (AWS Secrets Manager, Azure Key Vault, etc.)
- Don't commit `.env` to git
- Rotate credentials regularly

### 4. Configure Firewall
- Allow inbound traffic on your server port
- Restrict access to trusted sources if possible

## Available Tools

Once OAuth is configured, these tools work automatically:

### `send_email`
Send themed emails via Gmail
```
Send a birthday email to friend@example.com
```

### `list_candidates` (requires LEVER_API_KEY)
List candidates from Lever
```
List candidates from Lever
```

### `get_candidate` (requires LEVER_API_KEY)
Get candidate details
```
Get candidate details for ID abc123
```

### `create_requisition` (requires LEVER_API_KEY)
Create job requisition
```
Create a requisition for Senior Engineer in SF
```

## Support

- **OAuth issues**: Check Google Cloud Console and server logs
- **Toqan integration**: Check Toqan's MCP configuration
- **Server issues**: Check `server.log` for errors

## Next Steps

1. ✅ Set up Google OAuth credentials
2. ✅ Configure `.env` file
3. ✅ Start MCP server
4. ✅ Add to Toqan
5. ✅ Test email sending
6. ✅ Deploy to production (optional)
