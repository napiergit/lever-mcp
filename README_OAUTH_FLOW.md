# OAuth Email Flow Implementation

## Overview

This implementation provides a secure OAuth 2.0 flow for sending themed emails via Gmail API, specifically designed for browser-based LLM agents (like Toqan) that cannot open popup windows. The flow uses a session-based polling mechanism to handle asynchronous OAuth authorization.

## Architecture

### Core Components

1. **MCP Server** - FastAPI-based server handling OAuth flows and email generation
2. **Browser Agent** - LLM agent (Toqan) that polls for OAuth completion
3. **OAuth Session Store** - In-memory storage for temporary authorization codes
4. **Gmail Integration** - Direct Gmail API integration with proper HTML email rendering

### Key Features

- **Popup-free OAuth** - No popup windows required for browser agents
- **Session-based polling** - Asynchronous authorization code retrieval
- **Themed email templates** - Pre-built HTML email themes (birthday, pirate, space, medieval, superhero, tropical)
- **Scope normalization** - Handles Google Workspace extra scopes automatically
- **Proper HTML rendering** - Base64url encoding with MIME headers

## OAuth Flow Implementation

### 1. Flow Initiation
```python
# Agent calls send_email without access_token
send_email(to="user@example.com", theme="birthday")

# MCP generates session and returns OAuth URL
{
    "agent_action": "browser_agent_oauth_polling",
    "session_id": "abc123", 
    "oauth_url": "https://mcp-server.com/authorize?state=browser_agent_abc123",
    "polling_endpoint": "/oauth/poll/abc123"
}
```

### 2. User Authorization
- User clicks OAuth link in separate browser tab
- Google displays consent screen
- User grants permissions
- Google redirects to `/oauth/callback` with authorization code
- MCP stores code in session store keyed by session_id

### 3. Browser Agent Polling
```python
# Agent polls with exponential backoff
poll_oauth_code(session_id="abc123", attempt=1)  # 1s delay
poll_oauth_code(session_id="abc123", attempt=2)  # 2s delay  
poll_oauth_code(session_id="abc123", attempt=3)  # 4s delay
# ... continues until code received or timeout
```

### 4. Token Exchange & Email Sending
```python
# Exchange code for access token
exchange_oauth_code(code="auth_code_xyz")
# Returns: {"access_token": "token123"}

# Send email with token
send_email(to="user@example.com", theme="birthday", access_token="token123")
```

## Technical Implementation

### Session Management
```python
# In-memory session storage
oauth_sessions = {
    "session_id": {
        "code": "authorization_code",
        "timestamp": datetime.now(),
        "state": "browser_agent_session_id"
    }
}
```

### MCP Server Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/authorize` | GET | Redirects to Google OAuth with proper scopes |
| `/oauth/callback` | GET | Handles Google's redirect with auth code |
| `/token` | POST | Exchanges authorization code for access token |
| `/oauth/poll/{session_id}` | GET | Browser agent polling for auth code |
| `/oauth/status/{session_id}` | GET | Check session status without consuming code |

### Email Template System
```python
EMAIL_TEMPLATES = {
    "birthday": {
        "subject": "🎉 Happy Birthday! Let's Celebrate! 🎂",
        "body": "<html>...</html>"  # Styled HTML content
    },
    # ... other themes
}
```

### Gmail API Integration
- **MIME Headers**: Proper `Content-Type: text/html` for HTML rendering
- **Base64url Encoding**: RFC 2822 compliant message format
- **Scope Management**: Handles `https://www.googleapis.com/auth/gmail.send`

## Configuration

### Environment Variables
```bash
# Required for OAuth functionality
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
MCP_SERVER_BASE_URL=https://your-deployment-url.com

# Optional
LOG_LEVEL=INFO
```

### Google Cloud Console Setup
1. Create OAuth 2.0 credentials
2. Add authorized redirect URI: `https://your-domain.com/oauth/callback`
3. Configure OAuth consent screen
4. Enable Gmail API

## Usage Examples

### Basic Email Sending
```python
# Through MCP tools
result = await mcp_client.call_tool("send_email", {
    "to": "recipient@example.com",
    "theme": "pirate",
    "subject": "Custom Subject (optional)"
})
```

### With CC/BCC
```python
result = await mcp_client.call_tool("send_email", {
    "to": "recipient@example.com", 
    "theme": "space",
    "cc": "cc1@example.com,cc2@example.com",
    "bcc": "bcc@example.com"
})
```

## Security Concerns & Mitigations

### 🔴 Critical Security Issues

#### 1. **In-Memory Session Storage**
**Risk**: Authorization codes stored in server memory without persistence
- **Impact**: Server restart loses all pending OAuth sessions
- **Attack Vector**: Memory dumps could expose authorization codes
- **Mitigation**: 
  - Implement Redis/database storage with encryption
  - Set short session TTL (current: 10 minutes)
  - Clear sessions immediately after use

#### 2. **No Rate Limiting on Polling Endpoints**
**Risk**: Unlimited polling requests could enable DoS attacks
- **Impact**: Server resource exhaustion
- **Attack Vector**: Malicious agents could spam polling endpoints
- **Mitigation**:
  - Implement rate limiting (e.g., 10 requests/minute per session)
  - Add exponential backoff enforcement server-side
  - Monitor polling frequency patterns

#### 3. **Session ID Predictability**
**Risk**: Session IDs may be guessable if using weak random generation
- **Impact**: Session hijacking, unauthorized code access
- **Attack Vector**: Brute force session ID guessing
- **Mitigation**:
  - Use cryptographically secure random UUIDs
  - Implement session binding to client IP/user-agent
  - Add session invalidation on suspicious activity

### 🟡 Medium Security Issues

#### 4. **Access Token Exposure in Logs**
**Risk**: Access tokens logged in debug/error messages
- **Impact**: Token compromise if logs are accessible
- **Mitigation**: 
  - Implement token redaction in logging
  - Secure log storage and access controls
  - Use structured logging with token filtering

#### 5. **Cross-Origin Resource Sharing (CORS)**
**Risk**: Overly permissive CORS settings
- **Impact**: Unauthorized cross-origin requests
- **Mitigation**:
  - Restrict CORS to specific origins
  - Implement proper preflight handling
  - Validate origin headers

#### 6. **State Parameter Validation**
**Risk**: Insufficient state parameter validation in OAuth callback
- **Impact**: CSRF attacks, session confusion
- **Mitigation**:
  - Implement cryptographic state validation
  - Bind state to session context
  - Add timestamp validation

### 🟢 Low Risk Issues

#### 7. **Session Cleanup Timing**
**Risk**: Sessions may persist longer than necessary
- **Impact**: Extended attack window for session hijacking
- **Mitigation**: Implement aggressive session cleanup (current: 10min TTL)

#### 8. **Error Message Information Disclosure**
**Risk**: Detailed error messages may leak internal information
- **Impact**: Information disclosure for reconnaissance
- **Mitigation**: Use generic error messages in production

## Security Best Practices

### Recommended Implementations

1. **Secure Session Storage**
```python
# Replace in-memory storage with encrypted Redis
import redis
import cryptography.fernet

redis_client = redis.Redis(host='localhost', port=6379, db=0)
cipher = Fernet(encryption_key)

def store_session(session_id: str, data: dict):
    encrypted_data = cipher.encrypt(json.dumps(data).encode())
    redis_client.setex(session_id, 600, encrypted_data)  # 10min TTL
```

2. **Rate Limiting**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/oauth/poll/{session_id}")
@limiter.limit("10/minute")
async def oauth_poll_session(request: Request):
    # ... implementation
```

3. **Enhanced State Validation**
```python
import hmac
import hashlib

def generate_state(session_id: str) -> str:
    timestamp = str(int(time.time()))
    message = f"{session_id}:{timestamp}"
    signature = hmac.new(SECRET_KEY, message.encode(), hashlib.sha256).hexdigest()
    return f"browser_agent_{session_id}:{timestamp}:{signature}"

def validate_state(state: str) -> bool:
    # Validate HMAC signature and timestamp
    # ... implementation
```

## Monitoring & Alerting

### Key Metrics to Monitor
- **OAuth session creation rate**
- **Polling request frequency per session**
- **Failed authorization attempts**
- **Token exchange success/failure rates**
- **Session timeout frequency**

### Security Alerts
- Multiple failed OAuth attempts from same IP
- Unusually high polling frequency
- Session enumeration attempts
- Token exchange from unexpected locations

## Production Deployment

### Checklist
- [ ] Secure session storage implementation
- [ ] Rate limiting on all endpoints
- [ ] Comprehensive logging with token redaction
- [ ] HTTPS enforcement
- [ ] Security headers (HSTS, CSP, etc.)
- [ ] Regular security audits
- [ ] Monitoring and alerting setup
- [ ] Backup and disaster recovery procedures

---

**Note**: This implementation prioritizes functionality for browser-based LLM agents. For production use, implement all security mitigations outlined above.
