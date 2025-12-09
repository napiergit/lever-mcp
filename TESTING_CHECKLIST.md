# ✅ OAuth Testing Checklist

Use this checklist to ensure everything is working before deploying to production.

## 📋 Pre-Testing Setup

- [ ] **Get Google OAuth Credentials**
  - [ ] Go to [Google Cloud Console](https://console.cloud.google.com/)
  - [ ] Create/select a project
  - [ ] Enable Gmail API
  - [ ] Create OAuth 2.0 credentials (Desktop app type)
  - [ ] Download credentials

- [ ] **Configure Environment**
  - [ ] Copy `.env.example` to `.env`
  - [ ] Add `GOOGLE_CLIENT_ID` to `.env`
  - [ ] Add `GOOGLE_CLIENT_SECRET` to `.env`
  - [ ] Set `MCP_SERVER_BASE_URL=http://localhost:8000` in `.env`

- [ ] **Add Redirect URI to Google**
  - [ ] Go to Google Cloud Console → APIs & Services → Credentials
  - [ ] Click your OAuth 2.0 Client ID
  - [ ] Add redirect URI: `http://localhost:8000/oauth/callback`
  - [ ] Save changes

- [ ] **Install Dependencies**
  - [ ] Run `pip install -e .`
  - [ ] Verify installation: `python -c "import lever_mcp"`

## 🧪 Testing Phase

### Step 1: Start Server
- [ ] Open terminal
- [ ] Run `./run_http.sh`
- [ ] Verify server starts on `http://localhost:8000`
- [ ] Check logs show "OAuth configured"

### Step 2: Run Automated Tests
- [ ] Open new terminal
- [ ] Run `./test_local_oauth.sh`
- [ ] Verify all tests pass ✅
- [ ] Check for any warnings or errors

### Step 3: Test Full OAuth Flow
- [ ] Run `python tests/mock_toqan_client.py`
- [ ] Browser opens for Google authorization
- [ ] Sign in to Google
- [ ] Grant permissions
- [ ] Copy callback URL from browser
- [ ] Paste callback URL when prompted
- [ ] Enter your email address
- [ ] Verify no errors in console

### Step 4: Verify Email Received
- [ ] Check your Gmail inbox
- [ ] Verify you received the test email
- [ ] Email has space theme 🚀
- [ ] Email is properly formatted (HTML)

### Step 5: Test Token Persistence
- [ ] Run `python tests/simple_email_test.py`
- [ ] Enter your email address
- [ ] Choose theme (or press Enter for default)
- [ ] Verify email is sent without re-authorizing
- [ ] Check you received the second email

## 🔍 Verification

- [ ] **Server Logs**
  - [ ] No errors in server terminal
  - [ ] OAuth configuration logged correctly
  - [ ] Token exchange logged successfully
  - [ ] Email sending logged successfully

- [ ] **Token Storage**
  - [ ] Check `.oauth_tokens/` directory exists
  - [ ] Check `default_token.json` file exists
  - [ ] Verify token has `access_token` and `refresh_token`

- [ ] **Endpoints**
  - [ ] Health check works: `curl http://localhost:8000/health`
  - [ ] OAuth discovery works: `curl http://localhost:8000/.well-known/oauth-authorization-server`
  - [ ] Protected resource works: `curl http://localhost:8000/.well-known/oauth-protected-resource`

## 🚀 Pre-Deployment

- [ ] **All Tests Pass**
  - [ ] Automated tests: ✅
  - [ ] OAuth flow test: ✅
  - [ ] Email received: ✅
  - [ ] Token persistence: ✅

- [ ] **Update for Production**
  - [ ] Set `MCP_SERVER_BASE_URL` to production URL
  - [ ] Add production redirect URI to Google Cloud Console
  - [ ] Verify production credentials are correct

- [ ] **Deploy**
  - [ ] Run `fastmcp deploy`
  - [ ] Wait for deployment to complete
  - [ ] Verify deployment URL

## 🎯 Post-Deployment

- [ ] **Test in Toqan**
  - [ ] Add MCP server to Toqan
  - [ ] Initiate OAuth flow
  - [ ] Grant permissions
  - [ ] Send test email
  - [ ] Verify email received

- [ ] **Verify Production**
  - [ ] Check production logs
  - [ ] Verify OAuth endpoints work
  - [ ] Test email sending
  - [ ] Confirm no errors

## ❌ Troubleshooting

If any step fails, check:

- [ ] `.env` file has correct credentials
- [ ] Server is running on port 8000
- [ ] Redirect URI matches exactly
- [ ] Google OAuth credentials are valid
- [ ] No firewall blocking localhost:8000
- [ ] Browser allows popups
- [ ] Using callback URL immediately (codes expire)

## 📝 Notes

**Date Tested**: _______________

**Tested By**: _______________

**Issues Found**: 
- 
- 
- 

**Resolution**: 
- 
- 
- 

**Production Deployment Date**: _______________

**Production URL**: _______________

**Status**: 
- [ ] ✅ Ready for production
- [ ] ⚠️ Issues to resolve
- [ ] ❌ Not ready

---

**Remember**: Local testing success = Production confidence! 🎉
