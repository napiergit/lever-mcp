# Quick Start: Gmail OAuth with Toqan

This guide shows you how to quickly set up Gmail OAuth for use with Toqan (your AI agent).

## 🚀 Quick Setup (5 minutes)

### Step 1: Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search "Gmail API" and click "Enable"
4. Create OAuth credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" or "Web application"
   - Download credentials or copy Client ID and Secret

### Step 2: Configure Environment

Copy the example environment file and add your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add:
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

### Step 3: Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install with OAuth support
pip install -e .
```

### Step 4: Test the Setup

```bash
python test_oauth.py
```

Follow the prompts to:
1. Get authorization URL
2. Authorize in browser
3. Paste redirect URL
4. Send test email

## 🤖 Using with Toqan (On-Behalf-Of Flow)

This is the recommended approach for production use with Toqan.

### How It Works

```
┌─────────┐         ┌─────────┐         ┌─────────────┐         ┌──────────┐
│  User   │────────▶│ Toqan   │────────▶│  MCP Server │────────▶│  Gmail   │
└─────────┘         └─────────┘         └─────────────┘         └──────────┘
    │                    │                      │                      │
    │ 1. "Send email"    │                      │                      │
    │───────────────────▶│                      │                      │
    │                    │                      │                      │
    │                    │ 2. Request OAuth     │                      │
    │                    │      (if needed)     │                      │
    │◀───────────────────│                      │                      │
    │                    │                      │                      │
    │ 3. Grant access    │                      │                      │
    │───────────────────▶│                      │                      │
    │                    │                      │                      │
    │                    │ 4. Call send_email   │                      │
    │                    │    with token        │                      │
    │                    │─────────────────────▶│                      │
    │                    │                      │                      │
    │                    │                      │ 5. Send email        │
    │                    │                      │─────────────────────▶│
    │                    │                      │                      │
    │                    │ 6. Confirmation      │ 7. Email sent        │
    │                    │◀─────────────────────│◀─────────────────────│
    │                    │                      │                      │
    │ 8. "Email sent!"   │                      │                      │
    │◀───────────────────│                      │                      │
```

### Implementation in Toqan

**Step 1: Toqan obtains OAuth token from user**

When user requests to send email, Toqan should:
1. Check if user has granted Gmail permissions
2. If not, initiate OAuth flow
3. Store the access token

**Step 2: Toqan calls MCP server with token**

```python
# Toqan calls the MCP send_email tool
result = await mcp_client.call_tool(
    "send_email",
    {
        "to": "recipient@example.com",
        "theme": "birthday",
        "access_token": user_oauth_token,  # Token from OAuth flow
        "user_id": toqan_user_id           # Unique user identifier
    }
)
```

**Step 3: MCP server sends email**

The MCP server will:
- Use the provided token to authenticate with Gmail
- Send the email immediately
- Return confirmation with message ID

### Token Management

**Access Token (Short-lived)**
- Valid for ~1 hour
- Passed with each request
- No storage needed on MCP server

**Refresh Token (Long-lived)**
- Optional but recommended
- Allows getting new access tokens
- Can be stored by MCP server for convenience

## 📋 MCP Tool Usage

### Send Email with Token (Recommended)

```json
{
  "tool": "send_email",
  "arguments": {
    "to": "friend@example.com",
    "theme": "birthday",
    "access_token": "ya29.a0AfH6SMBx...",
    "user_id": "user123"
  }
}
```

**Response when successful:**
```json
{
  "status": "sent",
  "message": "Email sent successfully via Gmail API",
  "message_id": "18c5f2e4a1b2c3d4",
  "to": "friend@example.com",
  "subject": "🎉 Happy Birthday! Let's Celebrate! 🎂"
}
```

### Send Email without Token (Fallback)

```json
{
  "tool": "send_email",
  "arguments": {
    "to": "friend@example.com",
    "theme": "birthday"
  }
}
```

**Response when not authenticated:**
```json
{
  "status": "payload_generated",
  "message": "Email payload generated. Provide access_token parameter to send automatically.",
  "gmail_api_payload": {
    "raw": "base64-encoded-email..."
  },
  "agent_instructions": {
    "step_1": "Agent should obtain OAuth token from user via Toqan",
    "step_2": "Call this tool again with access_token parameter",
    "step_3": "Email will be sent automatically via Gmail API"
  }
}
```

### Check OAuth Status

```json
{
  "tool": "check_oauth_status",
  "arguments": {
    "user_id": "user123"
  }
}
```

## 🔐 Security Best Practices

### For Toqan Integration

1. **Never log tokens**: Tokens are sensitive credentials
2. **Use HTTPS**: Always use HTTPS in production
3. **Token expiration**: Handle token expiration gracefully
4. **User consent**: Always get explicit user consent before accessing Gmail
5. **Scope limitation**: Only request necessary scopes

### Token Storage

**On Toqan side:**
- Store tokens securely (encrypted)
- Associate tokens with user accounts
- Implement token refresh logic

**On MCP server side:**
- Tokens stored in `.oauth_tokens/` directory
- Each user has separate token file
- Directory should be in `.gitignore`
- Set appropriate file permissions (600)

## 🎨 Available Email Themes

- **birthday** 🎉 - Colorful celebration
- **pirate** 🏴‍☠️ - High seas adventure
- **space** 🚀 - Cosmic greetings
- **medieval** ⚔️ - Royal proclamation
- **superhero** 🦸 - Bold and powerful
- **tropical** 🌴 - Paradise vibes

## 🐛 Troubleshooting

### "OAuth not configured"
**Solution:** Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`

### "Not authenticated"
**Solution:** Provide `access_token` parameter in the tool call

### "Token expired"
**Solution:** 
- If refresh token available: Token auto-refreshes
- Otherwise: Obtain new token from user

### "Insufficient permissions"
**Solution:** Ensure these scopes are granted:
- `https://www.googleapis.com/auth/gmail.send`
- `https://www.googleapis.com/auth/gmail.compose`

## 📚 Additional Resources

- [Full OAuth Setup Guide](./OAUTH_SETUP.md)
- [Google OAuth 2.0 Docs](https://developers.google.com/identity/protocols/oauth2)
- [Gmail API Docs](https://developers.google.com/gmail/api)

## 💡 Example: Complete Flow

```python
# 1. User asks Toqan to send email
user_request = "Send a birthday email to john@example.com"

# 2. Toqan checks if user has Gmail access
if not user_has_gmail_token:
    # Initiate OAuth flow
    oauth_token = await toqan.request_gmail_access(user)
else:
    oauth_token = user.gmail_token

# 3. Toqan calls MCP server
result = await mcp_client.call_tool("send_email", {
    "to": "john@example.com",
    "theme": "birthday",
    "access_token": oauth_token,
    "user_id": user.id
})

# 4. Check result
if result["status"] == "sent":
    await toqan.respond(f"✅ Birthday email sent to john@example.com!")
else:
    await toqan.respond(f"❌ Failed to send email: {result['message']}")
```

## 🎯 Next Steps

1. ✅ Set up Google OAuth credentials
2. ✅ Configure environment variables
3. ✅ Test with `test_oauth.py`
4. ✅ Integrate with Toqan
5. ✅ Test end-to-end flow
6. ✅ Deploy to production

Need help? Check [OAUTH_SETUP.md](./OAUTH_SETUP.md) for detailed documentation.
