# Local OAuth Testing Guide

This guide helps you test the complete OAuth flow locally before deploying to production.

## 🎯 Overview

The local testing setup includes:
- **Mock Toqan Client**: Simulates how Toqan will interact with your MCP server
- **E2E Tests**: Validates all OAuth endpoints and configurations
- **Local Server**: Runs on `http://localhost:8000` for testing

## 📋 Prerequisites

1. **Google OAuth Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Gmail API
   - Create OAuth 2.0 credentials (Desktop app type)
   - Download the credentials

2. **Python Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   pip install python-dotenv  # For testing
   ```

## 🔧 Setup

### Step 1: Configure Environment

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```bash
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   MCP_SERVER_BASE_URL=http://localhost:8000
   ```

### Step 2: Add Redirect URI to Google

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to: APIs & Services → Credentials
3. Click on your OAuth 2.0 Client ID
4. Under "Authorized redirect URIs", add:
   ```
   http://localhost:8000/oauth/callback
   ```
5. Save changes

### Step 3: Start the MCP Server

In one terminal, start the server:
```bash
./run_http.sh
```

Or manually:
```bash
python -m uvicorn lever_mcp.server:mcp.app --host 0.0.0.0 --port 8000
```

The server should start on `http://localhost:8000`

## 🧪 Running Tests

### Quick Test (Recommended)

Run the automated test suite:
```bash
./test_local_oauth.sh
```

This will:
- ✅ Check your environment configuration
- ✅ Verify the server is running
- ✅ Test all OAuth endpoints
- ✅ Validate OAuth discovery
- ✅ Test callback handling

### Manual E2E Tests

Run the end-to-end tests directly:
```bash
python tests/test_oauth_e2e.py
```

### Full OAuth Flow Test

Test the complete OAuth flow with the mock Toqan client:
```bash
python tests/mock_toqan_client.py
```

This will:
1. Discover OAuth endpoints from your server
2. Open your browser for Google authorization
3. Prompt you to paste the callback URL
4. Exchange the authorization code for an access token
5. Send a test email using the token

**Follow the prompts carefully!**

## 📊 What Gets Tested

### Automated Tests
- ✅ Server health check
- ✅ OAuth configuration validation
- ✅ OAuth endpoint discovery (`/.well-known/oauth-authorization-server`)
- ✅ Protected resource metadata (`/.well-known/oauth-protected-resource`)
- ✅ Authorization endpoint redirect
- ✅ Callback endpoint validation
- ✅ Gmail client initialization

### Manual Flow Test
- ✅ Complete OAuth authorization flow
- ✅ Code exchange for access token
- ✅ Token storage and retrieval
- ✅ Sending emails with OAuth token
- ✅ On-behalf-of flow (agent providing token)

## 🔍 Debugging

### Check Server Logs

The server logs will show:
- OAuth configuration status
- Redirect URIs
- Token exchange attempts
- Email sending attempts

### Common Issues

1. **"OAuth not configured"**
   - Check your `.env` file has `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
   - Restart the server after changing `.env`

2. **"Redirect URI mismatch"**
   - Ensure `http://localhost:8000/oauth/callback` is added to Google Cloud Console
   - Check `MCP_SERVER_BASE_URL` in `.env` is `http://localhost:8000`

3. **"Server not running"**
   - Start the server with `./run_http.sh`
   - Check port 8000 is not in use: `lsof -i :8000`

4. **"Token exchange failed"**
   - Check server logs for detailed error
   - Verify your Google OAuth credentials are correct
   - Ensure you're using the code from the callback URL immediately (codes expire quickly)

### Manual Testing

Test individual endpoints:

```bash
# Health check
curl http://localhost:8000/health

# OAuth discovery
curl http://localhost:8000/.well-known/oauth-authorization-server

# Protected resource metadata
curl http://localhost:8000/.well-known/oauth-protected-resource

# Authorization (will redirect to Google)
curl -L http://localhost:8000/authorize?state=test
```

## 🎯 Testing Workflow

### 1. First Time Setup
```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 2. Add redirect URI to Google Cloud Console
# http://localhost:8000/oauth/callback

# 3. Start server
./run_http.sh
```

### 2. Run Automated Tests
```bash
# In another terminal
./test_local_oauth.sh
```

### 3. Test Full OAuth Flow
```bash
# Test the complete flow
python tests/mock_toqan_client.py

# Follow the prompts:
# 1. Browser opens for authorization
# 2. Sign in to Google
# 3. Grant permissions
# 4. Copy the callback URL
# 5. Paste it when prompted
# 6. Enter your email for test
```

### 4. Verify Email Sent
- Check your Gmail inbox
- You should receive a test email with a space theme 🚀

## 🚀 After Local Testing

Once all tests pass locally:

1. **Update Production Configuration**
   ```bash
   # In your production .env or environment variables
   MCP_SERVER_BASE_URL=https://your-deployed-url.fastmcp.app
   ```

2. **Add Production Redirect URI**
   - Go to Google Cloud Console
   - Add: `https://your-deployed-url.fastmcp.app/oauth/callback`

3. **Deploy to FastMCP**
   ```bash
   fastmcp deploy
   ```

4. **Test in Toqan**
   - Configure the MCP server in Toqan
   - Test the OAuth flow
   - Send a test email

## 📝 Test Checklist

Before deploying to production, ensure:

- [ ] All automated tests pass (`./test_local_oauth.sh`)
- [ ] Mock Toqan client completes OAuth flow successfully
- [ ] Test email is received in Gmail
- [ ] Server logs show no errors
- [ ] OAuth endpoints return correct metadata
- [ ] Token exchange works correctly
- [ ] Email sending works with OAuth token

## 🔐 Security Notes

- Never commit `.env` file (it's in `.gitignore`)
- Keep your `GOOGLE_CLIENT_SECRET` secure
- Tokens are stored in `.oauth_tokens/` (also in `.gitignore`)
- Use different OAuth credentials for local testing and production

## 📚 Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Gmail API Send Email](https://developers.google.com/gmail/api/guides/sending)
- [FastMCP Documentation](https://docs.fastmcp.com/)
- [MCP OAuth Specification](https://spec.modelcontextprotocol.io/specification/2024-11-05/authentication/)

## 🆘 Getting Help

If you encounter issues:

1. Check the server logs for detailed error messages
2. Run tests with verbose logging: `python -v tests/test_oauth_e2e.py`
3. Verify your Google OAuth credentials are correct
4. Ensure all redirect URIs are properly configured
5. Check that the server is accessible at `http://localhost:8000`

## 🎉 Success Criteria

You're ready for production when:
- ✅ All automated tests pass
- ✅ Mock Toqan client successfully sends an email
- ✅ You receive the test email in your Gmail
- ✅ No errors in server logs
- ✅ OAuth flow completes without manual intervention
