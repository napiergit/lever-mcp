# Gmail OAuth Setup Guide

This guide explains how to set up OAuth 2.0 authentication for Gmail integration in the Lever MCP server.

## Overview

The MCP server supports two OAuth flows:

1. **On-Behalf-Of Flow**: Agent (Toqan) obtains OAuth token from user and passes it to MCP server
2. **Direct OAuth Flow**: MCP server handles OAuth flow directly with stored credentials

## Prerequisites

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

### 2. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Choose application type:
   - For desktop/CLI: Select "Desktop app"
   - For web: Select "Web application"
4. Configure OAuth consent screen if prompted
5. Add authorized redirect URIs:
   - For local development: `http://localhost:8080/oauth/callback`
   - For Toqan integration: Add Toqan's callback URL
6. Download the credentials JSON or copy the Client ID and Client Secret

### 3. Configure OAuth Scopes

The following Gmail API scopes are required:
- `https://www.googleapis.com/auth/gmail.send`
- `https://www.googleapis.com/auth/gmail.compose`

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required: Google OAuth credentials
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Optional: Custom redirect URI (defaults to http://localhost:8080/oauth/callback)
OAUTH_REDIRECT_URI=http://localhost:8080/oauth/callback

# Optional: Token storage path (defaults to ./.oauth_tokens)
TOKEN_STORAGE_PATH=./.oauth_tokens
```

### Load Environment Variables

Add to your shell profile or use a tool like `direnv`:

```bash
# Load .env file
export $(cat .env | xargs)
```

Or use Python's `python-dotenv`:

```bash
pip install python-dotenv
```

Then in your code:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Usage Flows

### Flow 1: On-Behalf-Of (Recommended for Toqan)

This is the recommended approach when using with an agent like Toqan.

#### Step 1: Agent Obtains Token

The agent (Toqan) should:
1. Direct user to Google OAuth consent screen
2. User grants permissions
3. Agent receives access token
4. Agent passes token to MCP server

#### Step 2: Send Email with Token

```python
# Agent calls MCP tool with access token
result = await mcp.call_tool(
    "send_email",
    {
        "to": "recipient@example.com",
        "theme": "birthday",
        "access_token": "ya29.a0AfH6SMBx...",  # Token from OAuth flow
        "user_id": "user123"  # Optional: for multi-user support
    }
)
```

The MCP server will:
- Use the provided token to authenticate with Gmail
- Send the email immediately
- Save the token for future use (if refresh token included)

### Flow 2: Direct OAuth (For Testing/Development)

#### Step 1: Get Authorization URL

```python
result = await mcp.call_tool("get_oauth_url", {"user_id": "testuser"})
# Returns: {"auth_url": "https://accounts.google.com/o/oauth2/auth?..."}
```

#### Step 2: User Authorizes

1. User visits the `auth_url` in browser
2. Grants permissions
3. Gets redirected to callback URL with authorization code
4. Extract the `code` parameter from URL

#### Step 3: Exchange Code for Token

```python
result = await mcp.call_tool(
    "exchange_oauth_code",
    {
        "code": "4/0AY0e-g7X...",  # From callback URL
        "user_id": "testuser"
    }
)
# Token is now saved and will be used automatically
```

#### Step 4: Send Email (No Token Needed)

```python
result = await mcp.call_tool(
    "send_email",
    {
        "to": "recipient@example.com",
        "theme": "birthday",
        "user_id": "testuser"  # Uses saved token
    }
)
```

### Flow 3: Check Authentication Status

```python
result = await mcp.call_tool("check_oauth_status", {"user_id": "testuser"})
# Returns authentication status and whether ready to send emails
```

## MCP Tools Reference

### `send_email`

Send a themed email via Gmail API.

**Parameters:**
- `to` (required): Recipient email address
- `theme` (required): Email theme (birthday, pirate, space, medieval, superhero, tropical)
- `subject` (optional): Custom subject line
- `cc` (optional): CC recipients (comma-separated)
- `bcc` (optional): BCC recipients (comma-separated)
- `access_token` (optional): OAuth access token for on-behalf-of flow
- `user_id` (optional): User identifier for token storage (default: "default")

**Returns:**
- If authenticated: Email sent status with message ID
- If not authenticated: Gmail API payload for manual sending

### `get_oauth_url`

Get OAuth authorization URL for user to grant permissions.

**Parameters:**
- `user_id` (optional): User identifier (default: "default")

**Returns:**
- Authorization URL and instructions

### `exchange_oauth_code`

Exchange authorization code for access token.

**Parameters:**
- `code` (required): Authorization code from OAuth callback
- `user_id` (optional): User identifier (default: "default")

**Returns:**
- Token information and confirmation

### `check_oauth_status`

Check OAuth authentication status.

**Parameters:**
- `user_id` (optional): User identifier (default: "default")

**Returns:**
- Authentication status and configuration info

## Integration with Toqan

### Recommended Workflow

1. **User initiates email sending in Toqan**
   ```
   User: "Send a birthday email to john@example.com"
   ```

2. **Toqan checks if user has granted Gmail permissions**
   - If yes: Use existing token
   - If no: Initiate OAuth flow

3. **Toqan calls MCP server with token**
   ```python
   await mcp.call_tool("send_email", {
       "to": "john@example.com",
       "theme": "birthday",
       "access_token": user_oauth_token,
       "user_id": toqan_user_id
   })
   ```

4. **MCP server sends email and returns confirmation**

### Token Management

- **Access tokens**: Short-lived (typically 1 hour)
- **Refresh tokens**: Long-lived, used to obtain new access tokens
- **Storage**: Tokens stored locally in `.oauth_tokens/` directory
- **Multi-user**: Each user has separate token file: `{user_id}_token.json`

### Security Best Practices

1. **Never log tokens**: Tokens are sensitive credentials
2. **Use HTTPS**: Always use HTTPS in production
3. **Secure storage**: Protect token storage directory
4. **Token rotation**: Implement token refresh logic
5. **Scope limitation**: Only request necessary Gmail scopes

## Troubleshooting

### "OAuth not configured" Error

**Solution:** Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` environment variables.

### "Not authenticated" Error

**Solution:** 
- For on-behalf-of flow: Provide `access_token` parameter
- For direct flow: Complete OAuth flow using `get_oauth_url` and `exchange_oauth_code`

### "Token expired" Error

**Solution:** 
- If refresh token available: Token will auto-refresh
- Otherwise: Re-authenticate using OAuth flow

### "Insufficient permissions" Error

**Solution:** Ensure Gmail API is enabled and correct scopes are granted:
- `https://www.googleapis.com/auth/gmail.send`
- `https://www.googleapis.com/auth/gmail.compose`

## Testing

### Test OAuth Flow

```bash
# Install dependencies
pip install -e .

# Set environment variables
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"

# Run server
python -m lever_mcp.server

# In another terminal, test with MCP client
# (Use your preferred MCP client to call tools)
```

### Test with Mock Token

For development, you can test the flow without real OAuth:

```python
# This will fail at Gmail API call but tests the flow
result = await mcp.call_tool("send_email", {
    "to": "test@example.com",
    "theme": "birthday",
    "access_token": "mock_token_for_testing"
})
```

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Google Cloud Console for API/OAuth errors
3. Check MCP server logs for detailed error messages
4. Ensure all environment variables are set correctly
