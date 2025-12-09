# Why Local vs Production Scopes Differ (Same OAuth Client)

## 🔍 The Mystery

**Same OAuth Client ID, but:**
- Local: Returns only `gmail.send` + `gmail.compose` ✅
- Production: Returns `gmail.send` + `gmail.compose` + `gmail.readonly` + `gmail.modify` ❌

## 🎯 Possible Causes

### 1. **Different Google Account Types**

**Local testing:**
- You're using a personal Gmail account?
- Personal accounts don't have Workspace policies

**Production (Toqan):**
- User is using a company Google Workspace account
- Workspace admin has enforced additional scopes for ALL apps

**Test this:**
- Try local OAuth with the SAME Google Workspace account that Toqan is using
- See if you get extra scopes locally too

### 2. **Incremental Authorization / Cached Consent**

**Local:**
- Fresh authorization every time
- Google grants exactly what's requested

**Production:**
- User previously authorized the app with different scopes
- Google is combining old + new scopes
- Cached consent is adding extra scopes

**Test this:**
1. Go to https://myaccount.google.com/permissions
2. Find your app
3. Check what scopes are listed
4. Remove access
5. Re-authorize fresh

### 3. **OAuth Consent Screen Configuration**

Even with the same Client ID, the consent screen might have:
- Scopes added AFTER you tested locally
- Scopes that only apply to certain account types

**Check this:**
1. Go to https://console.cloud.google.com/apis/credentials/consent
2. Look at "Scopes for Google APIs"
3. Are there ANY scopes listed?
4. If yes, REMOVE THEM ALL

### 4. **Google Workspace Domain-Wide Delegation**

If the OAuth client has domain-wide delegation enabled:
- Workspace admins can enforce additional scopes
- These only apply to Workspace accounts, not personal Gmail

**Check this:**
1. Go to https://console.cloud.google.com/apis/credentials
2. Click your OAuth Client ID
3. Look for "Domain-wide delegation"
4. If enabled, check what scopes are configured

### 5. **Different Authorization Flow**

**Local:**
- You're using `/authorize` endpoint
- Direct authorization code flow

**Production (Toqan):**
- Might be using a different endpoint
- Might be using PKCE with different parameters
- Might be requesting scopes differently

**Check the authorization URL Toqan is opening:**
```
https://accounts.google.com/o/oauth2/auth?
  client_id=...&
  scope=WHAT_IS_HERE?  <-- Check this!
```

## 🧪 Diagnostic Steps

### Step 1: Test with Same Account
Use the EXACT same Google Workspace account locally that Toqan is using:
```bash
python test_scope_with_code.py
```

If you get extra scopes locally too → It's the account, not the environment

### Step 2: Check Authorization URL
Ask Toqan to log the FULL authorization URL they're opening. Compare it to:
```
http://localhost:8000/authorize?response_type=code&scope=...
```

Are the scopes in the URL the same?

### Step 3: Check Callback URL
Ask Toqan to log the callback URL from Google. What scopes are in it?
```
?code=...&scope=WHAT_IS_HERE?&state=...
```

If extra scopes are HERE → Google is adding them, not Toqan

### Step 4: Check Token Response
Our server now logs this! Check the production logs for:
```
Token exchange successful. Scopes returned: ...
Google added extra scopes (likely due to Workspace policy): ...
```

## 💡 Most Likely Answer

Since you're using the same OAuth Client ID, the difference is almost certainly:

**The Google Account Type:**
- Local: Personal Gmail account → No extra scopes
- Production: Google Workspace account → Domain admin enforces extra scopes

**The Fix:** The scope normalization I just implemented handles this! ✅

## 🔬 Let's Verify

Can you:
1. Check what type of Google account you used locally (personal vs Workspace)
2. Check what type of account Toqan is using in production
3. Try local OAuth with a Workspace account and see if you get extra scopes

This will confirm the hypothesis!
