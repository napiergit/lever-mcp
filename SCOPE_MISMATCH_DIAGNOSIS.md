# Google OAuth Scope Mismatch - Deep Diagnosis

## 🔍 The Mystery

**Toqan reports:**
- We request: `gmail.send` + `gmail.compose`
- Google grants: `gmail.send` + `gmail.compose` + `gmail.readonly` + `gmail.modify`

**Our local tests show:**
- We request: `gmail.send` + `gmail.compose`
- Google grants: `gmail.send` + `gmail.compose` (EXACT MATCH)

## 🤔 Why the Difference?

### Hypothesis 1: Google Cloud Console OAuth Consent Screen Settings

**MOST LIKELY CAUSE**: The OAuth consent screen in Google Cloud Console has **pre-approved scopes** configured.

#### How to Check:
1. Go to https://console.cloud.google.com/apis/credentials/consent
2. Look at "OAuth consent screen"
3. Check the "Scopes" section
4. **If you see scopes listed there**, Google will ALWAYS grant those scopes regardless of what the app requests

#### The Fix:
1. Go to OAuth consent screen settings
2. Remove ALL scopes from the consent screen configuration
3. Leave it empty - scopes should be requested dynamically by the app
4. Save changes
5. Revoke existing authorizations at https://myaccount.google.com/permissions
6. Re-authorize

### Hypothesis 2: Google Workspace Domain Policy

If you're using a Google Workspace account (not personal Gmail):
- Domain administrators can enforce additional scopes
- Check with your Google Workspace admin

### Hypothesis 3: OAuth Client Configuration

The OAuth client itself might have scope restrictions:

#### How to Check:
1. Go to https://console.cloud.google.com/apis/credentials
2. Click on your OAuth 2.0 Client ID
3. Look for any "Scopes" or "API scopes" configuration
4. Ensure nothing is pre-configured there

### Hypothesis 4: Incremental Authorization

Google might be combining scopes from previous authorizations:

#### The Fix:
1. Go to https://myaccount.google.com/permissions
2. Find your app
3. Click "Remove access"
4. Re-authorize fresh

## 🧪 How to Test

### Test 1: Check What Scopes Are Actually Requested

Look at the authorization URL that Toqan opens. It should look like:
```
https://accounts.google.com/o/oauth2/auth?
  client_id=YOUR_CLIENT_ID&
  redirect_uri=YOUR_REDIRECT_URI&
  response_type=code&
  scope=https://www.googleapis.com/auth/gmail.send%20https://www.googleapis.com/auth/gmail.compose&
  access_type=offline&
  prompt=consent&
  state=...
```

**Check the `scope` parameter** - does it only contain `gmail.send` and `gmail.compose`?

If it contains MORE scopes, then Toqan is requesting them (not our server).

### Test 2: Check the Callback URL

After authorization, look at the callback URL. It should contain:
```
http://your-server/oauth/callback?
  code=...&
  scope=https://www.googleapis.com/auth/gmail.send%20https://www.googleapis.com/auth/gmail.compose&
  state=...
```

**Check the `scope` parameter** - what does it contain?

If it has extra scopes HERE, then Google is adding them (not Toqan, not our server).

### Test 3: Check the Token Response

When we exchange the code for a token, Google returns:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "scope": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.compose",
  "expires_in": 3599
}
```

**Check the `scope` field** - what does it contain?

## 🎯 Action Items

### For You (Server Owner):

1. **Check OAuth Consent Screen:**
   ```
   https://console.cloud.google.com/apis/credentials/consent
   ```
   - Remove ALL pre-configured scopes
   - Save changes

2. **Check OAuth Client:**
   ```
   https://console.cloud.google.com/apis/credentials
   ```
   - Click your OAuth 2.0 Client ID
   - Ensure no scopes are pre-configured

3. **Revoke and Re-authorize:**
   ```
   https://myaccount.google.com/permissions
   ```
   - Remove your app
   - Re-authorize fresh

### For Toqan Team:

1. **Log the authorization URL** - What scopes are in the URL Toqan opens?

2. **Log the callback URL** - What scopes are in the callback from Google?

3. **Log the token response** - What scopes are in Google's token response?

4. **Share the logs** - This will tell us exactly where the extra scopes are coming from

## 💡 Most Likely Solution

Based on the evidence, the issue is almost certainly in the **Google Cloud Console OAuth Consent Screen configuration**.

The consent screen has pre-approved scopes that Google automatically grants regardless of what the app requests.

**Fix:** Remove all scopes from the OAuth consent screen configuration and let the app request them dynamically.

## 📊 Evidence

Our local testing proves:
- ✅ Server requests correct scopes
- ✅ Google returns correct scopes
- ✅ No extra scopes added
- ✅ Email sends successfully

The issue must be in:
1. Google Cloud Console configuration (most likely)
2. How Toqan is calling the endpoints
3. Cached authorization state

It is **NOT** an issue with our server code.
