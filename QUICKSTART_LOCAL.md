# 🚀 Quick Start: Local OAuth Testing

Get your OAuth flow working locally in 5 minutes!

## Step 1: Setup (2 minutes)

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and add your Google OAuth credentials
# Get these from: https://console.cloud.google.com/
nano .env  # or use your favorite editor
```

Add to `.env`:
```bash
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
MCP_SERVER_BASE_URL=http://localhost:8000
```

## Step 2: Google Cloud Console (1 minute)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to: **APIs & Services → Credentials**
3. Click your OAuth 2.0 Client ID
4. Under **Authorized redirect URIs**, add:
   ```
   http://localhost:8000/oauth/callback
   ```
5. Click **Save**

## Step 3: Start Server (30 seconds)

```bash
# Install dependencies (first time only)
pip install -e .

# Start the server
./run_http.sh
```

Server should start at `http://localhost:8000`

## Step 4: Run Tests (1 minute)

In a **new terminal**:

```bash
# Run automated tests
./test_local_oauth.sh
```

You should see:
```
✅ All tests passed!
```

## Step 5: Test Full OAuth Flow (30 seconds)

```bash
# Run the mock Toqan client
python tests/mock_toqan_client.py
```

This will:
1. 🌐 Open your browser for Google authorization
2. 📋 Ask you to paste the callback URL
3. 🔄 Exchange code for access token
4. 📧 Send a test email

**Follow the prompts!**

## ✅ Success!

If you received the test email, you're done! 🎉

Your OAuth flow is working perfectly. Now you can:

1. **Deploy to production**:
   ```bash
   # Update .env with production URL
   MCP_SERVER_BASE_URL=https://your-app.fastmcp.app
   
   # Add production redirect URI to Google Cloud Console
   # https://your-app.fastmcp.app/oauth/callback
   
   # Deploy
   fastmcp deploy
   ```

2. **Test in Toqan**:
   - Add your MCP server to Toqan
   - Test the OAuth flow
   - Send emails!

## 🆘 Troubleshooting

### "OAuth not configured"
- Check `.env` has `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- Restart the server after editing `.env`

### "Server not running"
- Run `./run_http.sh` in another terminal
- Check port 8000 is free: `lsof -i :8000`

### "Redirect URI mismatch"
- Verify `http://localhost:8000/oauth/callback` is in Google Cloud Console
- Check `MCP_SERVER_BASE_URL=http://localhost:8000` in `.env`

### "Token exchange failed"
- Use the callback URL immediately (codes expire in ~10 minutes)
- Check server logs for detailed errors
- Verify Google OAuth credentials are correct

## 📚 More Details

See [LOCAL_TESTING.md](LOCAL_TESTING.md) for comprehensive documentation.

## 🎯 What You Just Tested

- ✅ OAuth endpoint discovery
- ✅ Authorization flow
- ✅ Token exchange
- ✅ Gmail API integration
- ✅ Email sending with OAuth
- ✅ On-behalf-of token flow

Everything Toqan will do in production! 🚀
