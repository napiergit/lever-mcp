# Send Email OAuth Flow Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant Toqan as Toqan (Browser Agent)
    participant MCP as MCP Server
    participant Callback as OAuth Callback Handler
    participant Google as Gmail/Google OAuth
    participant Gmail as Gmail API
    
    Note over User,Gmail: Initial Email Send Request
    User->>Toqan: "Send themed email to recipient@example.com"
    Toqan->>MCP: send_email(to, theme, no access_token)
    
    Note over MCP: Check if access_token provided
    Note over MCP: No token → Need OAuth flow
    
    Note over User,Gmail: OAuth Flow Initiation
    MCP->>MCP: Generate session_id (browser_agent_*)
    MCP-->>Toqan: Return OAuth URL + session_id + polling config
    Note right of MCP: agent_action: "browser_agent_oauth_polling"<br/>session_id: "abc123"<br/>polling_endpoint: "/oauth/poll/abc123"
    
    Toqan->>User: Display OAuth link + "Click to authorize"
    Toqan->>MCP: poll_oauth_code(session_id, attempt=1)
    MCP-->>Toqan: {"status": "pending", "message": "waiting..."}
    
    Note over User,Gmail: User Authorization
    User->>Google: Click OAuth link → /authorize?state=browser_agent_abc123
    MCP->>Google: Redirect with client_id, scopes, redirect_uri
    Google->>User: Show consent screen
    User->>Google: Grant permissions
    
    Note over User,Gmail: OAuth Callback
    Google->>Callback: GET /oauth/callback?code=xyz&state=browser_agent_abc123
    Callback->>Callback: Extract session_id from state
    Callback->>Callback: Store code in oauth_sessions[session_id]
    Callback-->>User: HTML success page (auto-closes tab)
    
    Note over User,Gmail: Polling Detection
    Toqan->>MCP: poll_oauth_code(session_id, attempt=2) 
    MCP->>MCP: Check oauth_sessions[session_id]
    Note right of MCP: Code found! Remove from session store
    MCP-->>Toqan: {"status": "success", "code": "xyz"}
    
    Note over User,Gmail: Token Exchange
    Toqan->>MCP: exchange_oauth_code(code="xyz")
    MCP->>Google: POST /token (code, client_secret, redirect_uri)
    Google-->>MCP: {"access_token": "token123", "scope": "gmail.send"}
    MCP->>MCP: Normalize scopes for MCP compatibility
    MCP-->>Toqan: {"access_token": "token123"}
    
    Note over User,Gmail: Email Sending
    Toqan->>MCP: send_email(to, theme, access_token="token123")
    MCP->>MCP: Generate themed HTML email
    MCP->>MCP: Create Gmail API payload (base64url + MIME headers)
    MCP->>Gmail: POST /gmail/v1/users/me/messages/send
    Note right of MCP: Authorization: Bearer token123
    Gmail-->>MCP: {"id": "msg456", "labelIds": ["SENT"]}
    MCP-->>Toqan: {"status": "sent", "message_id": "msg456"}
    Toqan-->>User: "✅ Email sent successfully!"
    
    Note over User,Gmail: Alternative Polling Scenarios
    
    rect rgb(255, 240, 240)
        Note over Toqan,MCP: Polling While User Still Authorizing
        Toqan->>MCP: poll_oauth_code(session_id, attempt=3)
        MCP-->>Toqan: {"status": "pending", "message": "waiting..."}
        Note right of Toqan: Continue polling with backoff:<br/>1s, 2s, 4s, 8s intervals
    end
    
    rect rgb(240, 240, 255)  
        Note over Toqan,MCP: Session Timeout Scenario
        Toqan->>MCP: poll_oauth_code(session_id, attempt=N)
        Note right of MCP: Session > 10 minutes old
        MCP->>MCP: Delete expired session
        MCP-->>Toqan: {"status": "expired", "message": "restart flow"}
        Toqan-->>User: "❌ Authorization expired, please try again"
    end
    
    Note over User,Gmail: Key Design Points
    Note right of MCP: • Browser agent can't open popups<br/>• Polling avoids "identical tool calls" with attempt counter<br/>• Session storage enables async callback handling<br/>• Scope normalization fixes Google Workspace extra scopes<br/>• Base64url encoding ensures HTML renders properly
```

## Key Components

### 1. **MCP Server Endpoints**
- `/authorize` - Redirects to Google OAuth
- `/oauth/callback` - Handles Google's redirect with auth code  
- `/token` - Exchanges auth code for access token
- `/oauth/poll/{session_id}` - Browser agent polling endpoint

### 2. **Browser Agent Flow**
- Cannot open popup windows
- Uses polling mechanism with exponential backoff
- Session-based code retrieval prevents race conditions

### 3. **OAuth Session Storage**
```python
oauth_sessions = {
    "abc123": {
        "code": "auth_code_xyz", 
        "timestamp": datetime.now(),
        "state": "browser_agent_abc123"
    }
}
```

### 4. **Polling Strategy**
- Exponential backoff: 1s, 2s, 4s, 8s intervals
- Maximum 60 second timeout
- Attempt counter prevents "identical tool calls" error
- Session cleanup after 10 minutes

### 5. **Gmail Integration**
- Scope normalization for Google Workspace compatibility
- Base64url encoding with MIME headers
- HTML email rendering via `Content-Type: text/html`
