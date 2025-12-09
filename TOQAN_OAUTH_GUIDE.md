# Toqan OAuth Integration Guide

## Understanding the OAuth Architecture

### The Three Players

```
┌─────────┐         ┌─────────┐         ┌──────────────┐         ┌──────────┐
│  User   │────────▶│ Toqan   │────────▶│  MCP Server  │────────▶│  Google  │
│         │         │ (Agent) │         │ (OAuth Proxy)│         │  OAuth   │
└─────────┘         └─────────┘         └──────────────┘         └──────────┘
```

1. **User**: The person using Toqan
2. **Toqan**: The AI agent (MCP client)
3. **MCP Server**: Your Lever MCP server with OAuth proxy
4. **Google**: OAuth authorization server

### How OAuth Works Here

The MCP server uses **FastMCP's OAuthProxy** which implements the MCP OAuth specification. This is specifically designed for MCP clients like Toqan.

#### What the OAuth Proxy Does

The OAuth Proxy:
- ✅ Exposes OAuth metadata at `/.well-known/oauth-authorization-server`
- ✅ Implements Dynamic Client Registration (DCR) for MCP clients
- ✅ Proxies OAuth flows between Toqan and Google
- ✅ Handles redirect URI translation (Toqan's dynamic URIs → Google's fixed URI)
- ✅ Manages PKCE end-to-end
- ✅ Returns tokens to Toqan for tool calls

#### What the OAuth Proxy Does NOT Do

- ❌ Does NOT replace Toqan's OAuth management
- ❌ Does NOT store user credentials
- ❌ Does NOT directly authenticate users

## The Complete OAuth Flow

### Step 1: Discovery
```
Toqan → GET /.well-known/oauth-authorization-server → MCP Server
```
Toqan discovers that the MCP server requires OAuth and what scopes are needed.

### Step 2: Client Registration (DCR)
```
Toqan → POST /register → MCP Server
```
Toqan registers itself as an OAuth client with the MCP server.

### Step 3: Authorization
```
User → Toqan → MCP Server → Google → User authorizes → Google → MCP Server → Toqan
```
1. User wants to send email via Toqan
2. Toqan starts OAuth flow with MCP server
3. MCP server redirects to Google OAuth
4. User authorizes in browser
5. Google redirects back to MCP server
6. MCP server exchanges code for token
7. MCP server returns token to Toqan

### Step 4: Tool Call with Token
```
Toqan → send_email(access_token=...) → MCP Server → Gmail API → Email sent
```
Toqan calls MCP tools with the access token, and the MCP server uses it to call Gmail API.

## Setup Instructions

### 1. Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable Gmail API
4. Create OAuth 2.0 Client ID:
   - **Type**: Web application
   - **Name**: Lever MCP Server (or any name)
   - **Authorized redirect URIs**: Add `http://localhost:8080/auth/callback`
     - For production: `https://your-domain.com/auth/callback`
5. Copy Client ID and Client Secret

### 2. Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# Google OAuth (REQUIRED)
GOOGLE_CLIENT_ID=your-actual-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-actual-client-secret

# Server Base URL (REQUIRED)
# Must match the redirect URI in Google Console
MCP_SERVER_BASE_URL=http://localhost:8080

# Lever API (optional, only for Lever tools)
LEVER_API_KEY=your-lever-api-key
```

**IMPORTANT**: The redirect URI in Google Console must be:
```
{MCP_SERVER_BASE_URL}/auth/callback
```

### 3. Start the Server

```bash
./run.sh
```

The server will:
- Load environment variables from `.env`
- Configure OAuth proxy with Google
- Expose OAuth metadata endpoints
- Be ready for Toqan to connect

### 4. Add to Toqan

Configure Toqan to use your MCP server. Toqan will automatically:
- Discover OAuth metadata
- Register as a client
- Handle the OAuth flow
- Pass tokens with tool calls

## Verification

### Check OAuth Metadata

```bash
# Start server
./run_http.sh

# In another terminal, check OAuth metadata
curl http://localhost:8080/.well-known/oauth-authorization-server
```

Expected response:
```json
{
  "issuer": "http://localhost:8080",
  "authorization_endpoint": "http://localhost:8080/authorize",
  "token_endpoint": "http://localhost:8080/token",
  "registration_endpoint": "http://localhost:8080/register",
  "scopes_supported": [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose"
  ],
  ...
}
```

### Check Protected Resource Metadata

```bash
curl http://localhost:8080/.well-known/oauth-protected-resource/mcp
```

This tells Toqan what OAuth scopes are needed for the MCP server.

## Troubleshooting

### "could not discover MCP OAuth metadata"

**Causes:**
1. Environment variables not set
2. Server not running
3. OAuth proxy not configured

**Solutions:**

1. **Check environment variables:**
```bash
# Verify .env file exists and has correct values
cat .env

# Test with environment variables set
GOOGLE_CLIENT_ID=your-id GOOGLE_CLIENT_SECRET=your-secret ./run.sh
```

2. **Check server logs:**
```bash
./run.sh 2>&1 | tee server.log
```

Look for:
```
INFO - OAuth configured - Setting up OAuth proxy for Gmail integration
INFO - OAuth proxy configured with base URL: http://localhost:8080
```

3. **Test OAuth endpoints:**
```bash
# Start server in HTTP mode
./run_http.sh

# Test metadata endpoint
curl http://localhost:8080/.well-known/oauth-authorization-server

# Should return JSON, not 404
```

### "redirect_uri_mismatch"

**Cause:** Redirect URI mismatch between Google Console and server config

**Solution:**
1. Check `MCP_SERVER_BASE_URL` in `.env`
2. In Google Console, ensure redirect URI is: `{MCP_SERVER_BASE_URL}/auth/callback`
3. Example: If `MCP_SERVER_BASE_URL=http://localhost:8080`, add `http://localhost:8080/auth/callback`

### "invalid_client"

**Cause:** Wrong Client ID or Secret

**Solution:**
1. Verify credentials in `.env` match Google Console
2. Check for extra spaces or quotes
3. Regenerate credentials if needed

### Server starts but Toqan can't connect

**Possible causes:**
1. Toqan configured for wrong transport (stdio vs HTTP)
2. Port mismatch
3. Firewall blocking connection

**Solutions:**
1. Check Toqan's MCP configuration
2. Ensure server is running on expected port
3. Check firewall settings

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_CLIENT_ID` | Yes | - | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Yes | - | Google OAuth client secret |
| `MCP_SERVER_BASE_URL` | Yes | `http://localhost:8080` | Public URL of MCP server |
| `LEVER_API_KEY` | No | - | Lever API key (for Lever tools) |
| `LOG_LEVEL` | No | `INFO` | Logging level |

## OAuth Endpoints

The OAuth proxy exposes these endpoints:

| Endpoint | Purpose |
|----------|---------|
| `/.well-known/oauth-authorization-server` | OAuth server metadata |
| `/.well-known/oauth-protected-resource/mcp` | Protected resource metadata |
| `/register` | Dynamic Client Registration |
| `/authorize` | Authorization endpoint |
| `/token` | Token endpoint |
| `/auth/callback` | OAuth callback (for Google) |
| `/consent` | User consent page |

## Security Notes

1. **HTTPS in Production**: Always use HTTPS in production
2. **Secure Credentials**: Never commit `.env` to git
3. **Redirect URI**: Must match exactly in Google Console
4. **Token Handling**: Tokens are managed by OAuth proxy, not stored long-term
5. **PKCE**: Enforced end-to-end for security

## Testing the Flow

### Manual OAuth Flow Test

1. Start server in HTTP mode:
```bash
./run_http.sh
```

2. Visit authorization URL:
```
http://localhost:8080/authorize?
  response_type=code&
  client_id=test-client&
  redirect_uri=http://localhost:3000/callback&
  scope=https://www.googleapis.com/auth/gmail.send&
  state=test-state
```

3. You should be redirected to Google OAuth
4. After authorization, you'll be redirected back with a code
5. Exchange code for token at `/token` endpoint

### With Toqan

Just add the MCP server to Toqan and ask it to send an email. Toqan will handle the OAuth flow automatically.

## Next Steps

1. ✅ Set up Google OAuth credentials
2. ✅ Configure `.env` file
3. ✅ Start server and verify OAuth metadata
4. ✅ Add to Toqan
5. ✅ Test email sending
6. ✅ Deploy to production (optional)

## Support

- **OAuth setup**: See Google Cloud Console documentation
- **MCP integration**: See Toqan documentation
- **Server issues**: Check server logs with `./run.sh 2>&1 | tee server.log`
- **FastMCP**: See [FastMCP documentation](https://github.com/jlowin/fastmcp)
