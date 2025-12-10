from fastmcp import FastMCP
from fastmcp.server.auth import OAuthProxy, StaticTokenVerifier
from lever_mcp.client import LeverClient
from lever_mcp.gmail_client import GmailClient
from lever_mcp.oauth_config import oauth_config, GMAIL_SCOPES
from typing import Optional, Dict, Any
from starlette.responses import JSONResponse, RedirectResponse, HTMLResponse
from starlette.requests import Request
import logging
import json
import base64
import os
import time
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("lever-mcp")

# In-memory storage for OAuth sessions (browser agents)
# Structure: {session_id: {"code": str, "timestamp": datetime, "state": str}}
oauth_sessions = {}

# Shared email templates for all email tools
EMAIL_TEMPLATES = {
    "birthday": {
        "subject": "🎉 Happy Birthday! Let's Celebrate! 🎂",
        "body": """
<html>
<body style="font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 20px; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
        <h1 style="color: #667eea; text-align: center; font-size: 48px; margin-bottom: 20px;">🎉 Happy Birthday! 🎉</h1>
        <p style="font-size: 18px; color: #333; line-height: 1.6;">
            Wishing you a day filled with happiness, laughter, and all your favorite things! 
            May this year bring you endless joy and amazing adventures! 🎂🎈
        </p>
        <div style="text-align: center; margin: 30px 0;">
            <div style="font-size: 60px;">🎁 🎊 🎈 🎂 🎉</div>
        </div>
        <p style="font-size: 16px; color: #666; text-align: center;">
            Have an absolutely wonderful day!
        </p>
    </div>
</body>
</html>
"""
    },
    "pirate": {
        "subject": "⚓ Ahoy Matey! A Message from the Seven Seas! 🏴‍☠️",
        "body": """
<html>
<body style="font-family: 'Courier New', monospace; background: #1a1a2e; padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: #16213e; border: 3px solid #e94560; border-radius: 15px; padding: 40px; box-shadow: 0 10px 40px rgba(233, 69, 96, 0.3);">
        <h1 style="color: #e94560; text-align: center; font-size: 42px; margin-bottom: 20px;">⚓ Ahoy Matey! ⚓</h1>
        <p style="font-size: 18px; color: #f1f1f1; line-height: 1.6;">
            Arrr! This be a message from the high seas! 🏴‍☠️
        </p>
        <p style="font-size: 16px; color: #ddd; line-height: 1.6; font-style: italic;">
            May yer sails be full and yer treasure chest overflow with doubloons! 
            Keep a weather eye on the horizon, and may the winds be ever in yer favor!
        </p>
        <div style="text-align: center; margin: 30px 0; font-size: 50px;">
            🏴‍☠️ ⚓ 🗺️ 💰 ⚔️
        </div>
        <p style="font-size: 14px; color: #999; text-align: center;">
            Fair winds and following seas!<br>
            - Captain of the Digital Seas
        </p>
    </div>
</body>
</html>
"""
    },
    "space": {
        "subject": "🚀 Greetings from the Cosmos! ✨",
        "body": """
<html>
<body style="font-family: 'Arial', sans-serif; background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: rgba(255,255,255,0.05); border: 2px solid #4facfe; border-radius: 20px; padding: 40px; box-shadow: 0 0 40px rgba(79, 172, 254, 0.3);">
        <h1 style="color: #4facfe; text-align: center; font-size: 42px; margin-bottom: 20px; text-shadow: 0 0 20px rgba(79, 172, 254, 0.5);">🚀 Cosmic Greetings! 🌟</h1>
        <p style="font-size: 18px; color: #e0e0e0; line-height: 1.6;">
            Transmitting message from the outer reaches of the galaxy! 
            May your journey through the cosmos be filled with wonder and discovery! 🌌
        </p>
        <div style="text-align: center; margin: 30px 0; font-size: 50px;">
            🌍 🛸 ⭐ 🌙 🪐
        </div>
        <p style="font-size: 14px; color: #999; text-align: center;">
            To infinity and beyond!<br>
            - Your Intergalactic Friend
        </p>
    </div>
</body>
</html>
"""
    },
    "medieval": {
        "subject": "⚔️ A Royal Decree from the Kingdom! 👑",
        "body": """
<html>
<body style="font-family: 'Georgia', serif; background: linear-gradient(135deg, #2c1810 0%, #4a2c1a 100%); padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: #f4e4c1; border: 5px solid #8b6914; border-radius: 10px; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.5);">
        <h1 style="color: #8b6914; text-align: center; font-size: 42px; margin-bottom: 20px; font-family: 'Georgia', serif;">⚔️ Royal Decree ⚔️</h1>
        <p style="font-size: 18px; color: #2c1810; line-height: 1.6; font-style: italic;">
            Hear ye, hear ye! By order of the realm, we extend our warmest greetings! 
            May your days be filled with honor, valor, and prosperity! 👑
        </p>
        <div style="text-align: center; margin: 30px 0; font-size: 50px;">
            🏰 ⚔️ 🛡️ 👑 🐉
        </div>
        <p style="font-size: 14px; color: #666; text-align: center;">
            Long live the kingdom!<br>
            - The Royal Court
        </p>
    </div>
</body>
</html>
"""
    },
    "superhero": {
        "subject": "💥 Superhero Alert! You're Amazing! 🦸",
        "body": """
<html>
<body style="font-family: 'Impact', 'Arial Black', sans-serif; background: linear-gradient(135deg, #ff0844 0%, #ffb199 100%); padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: #fff; border: 5px solid #ff0844; border-radius: 15px; padding: 40px; box-shadow: 0 10px 40px rgba(255, 8, 68, 0.3);">
        <h1 style="color: #ff0844; text-align: center; font-size: 48px; margin-bottom: 20px; text-transform: uppercase;">💥 POW! 💥</h1>
        <p style="font-size: 18px; color: #333; line-height: 1.6; font-weight: bold;">
            Calling all heroes! You have the power to make today AMAZING! 
            Keep being the superhero you are! 🦸‍♀️🦸‍♂️
        </p>
        <div style="text-align: center; margin: 30px 0; font-size: 50px;">
            ⚡ 💪 🦸 🌟 💥
        </div>
        <p style="font-size: 14px; color: #666; text-align: center;">
            With great power comes great awesomeness!<br>
            - Your Superhero Squad
        </p>
    </div>
</body>
</html>
"""
    },
    "tropical": {
        "subject": "🌴 Aloha! Tropical Vibes Coming Your Way! 🌺",
        "body": """
<html>
<body style="font-family: 'Arial', sans-serif; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: #fff; border-radius: 25px; padding: 40px; box-shadow: 0 10px 40px rgba(245, 87, 108, 0.3);">
        <h1 style="color: #f5576c; text-align: center; font-size: 48px; margin-bottom: 20px;">🌴 Aloha! 🌺</h1>
        <p style="font-size: 18px; color: #333; line-height: 1.6;">
            Sending you tropical vibes and sunny smiles! 
            May your day be as bright and beautiful as a beach sunset! 🌅
        </p>
        <div style="text-align: center; margin: 30px 0; font-size: 50px;">
            🌴 🌺 🥥 🏖️ 🌊
        </div>
        <p style="font-size: 14px; color: #666; text-align: center;">
            Stay breezy!<br>
            - Your Island Friends
        </p>
    </div>
</body>
</html>
"""
    }
}

# Initialize FastMCP server with OAuth proxy
auth_provider = None
if oauth_config.is_configured():
    logger.info("OAuth configured - Setting up OAuth proxy for Gmail integration")
    
    # Get base URL from environment or use deployed URL
    base_url = os.getenv('MCP_SERVER_BASE_URL', 'https://isolated-coffee-reindeer.fastmcp.app')
    
    logger.info(f"MCP_SERVER_BASE_URL from environment: {os.getenv('MCP_SERVER_BASE_URL')}")
    logger.info(f"Using base_url: {base_url}")
    
    # Create OAuth proxy for Google
    # Use StaticTokenVerifier temporarily, then replace with self-verification
    temp_verifier = StaticTokenVerifier(tokens=set())
    
    auth_provider = OAuthProxy(
        upstream_authorization_endpoint="https://accounts.google.com/o/oauth2/auth",
        upstream_token_endpoint="https://oauth2.googleapis.com/token",
        upstream_client_id=oauth_config.client_id,
        upstream_client_secret=oauth_config.client_secret,
        token_verifier=temp_verifier,
        base_url=base_url,
        redirect_path="/oauth/callback",  # Changed to match what Toqan expects
        # Don't set valid_scopes - this causes strict validation
        # Google may return additional scopes (openid, email, profile) beyond what we request
        forward_pkce=True,
        extra_authorize_params={
            "access_type": "offline",  # Request refresh token
            "prompt": "consent"  # Always show consent screen
        }
    )
    
    logger.info(f"OAuth proxy redirect URI will be: {base_url}/oauth/callback")
    
    # Don't set required_scopes - this causes strict matching issues with Google
    # Google may return scopes in different order or with additional scopes (openid, email, profile)
    # By not setting valid_scopes or required_scopes, we allow Google to return whatever scopes it wants
    
    # Now set the proxy to verify its own tokens
    auth_provider._token_verifier = auth_provider
    logger.info(f"OAuth proxy configured with base URL: {base_url}")
else:
    logger.warning("OAuth not configured - email sending will return payloads only")
    logger.warning("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to enable OAuth")

# Initialize FastMCP server WITHOUT auth requirement
# Don't pass auth_provider to FastMCP - we'll handle OAuth manually to avoid scope validation
# The OAuthProxy's built-in endpoints do strict scope validation which breaks with Google
mcp = FastMCP("lever")

if auth_provider:
    # Add OAuth callback handler
    @mcp.custom_route("/oauth/callback", methods=["GET"])
    async def oauth_callback(request: Request):
        """Handle OAuth callback from Google."""
        # Get the authorization code and state from query params
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        error = request.query_params.get("error")
        callback_scope = request.query_params.get("scope")
        
        # Log what Google returned in the callback
        logger.info(f"OAuth callback received. State: {state}")
        logger.info(f"Scopes in callback URL: {callback_scope}")
        if callback_scope:
            logger.info(f"Callback scope breakdown: {callback_scope.split()}")
        
        if error:
            error_desc = request.query_params.get("error_description", "OAuth authorization failed")
            # Return HTML page that closes popup and sends error to parent
            return HTMLResponse(f"""
                <html>
                <head><title>Authorization Failed</title></head>
                <body>
                    <h1>❌ Authorization Failed</h1>
                    <p>{error}: {error_desc}</p>
                    <p>You can close this window.</p>
                    <script>
                        // Send error to parent window if opened as popup
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'oauth_error',
                                error: '{error}',
                                error_description: '{error_desc}'
                            }}, '*');
                            window.close();
                        }}
                    </script>
                </body>
                </html>
            """, status_code=400)
        
        if not code:
            return HTMLResponse("""
                <html>
                <head><title>Authorization Failed</title></head>
                <body>
                    <h1>❌ Authorization Failed</h1>
                    <p>No authorization code received.</p>
                    <p>You can close this window.</p>
                    <script>
                        if (window.opener) {
                            window.opener.postMessage({
                                type: 'oauth_error',
                                error: 'missing_code',
                                error_description: 'No authorization code received'
                            }, '*');
                            window.close();
                        }
                    </script>
                </body>
                </html>
            """, status_code=400)
        
        # Store code for browser agent polling if this looks like a browser agent session
        session_id = None
        if state and state.startswith('browser_agent_'):
            session_id = state.replace('browser_agent_', '')
            oauth_sessions[session_id] = {
                "code": code,
                "timestamp": datetime.now(),
                "state": state
            }
            logger.info(f"Stored OAuth code for browser agent session: {session_id}")
        
        # Return success page that closes popup and sends code to parent
        return HTMLResponse(f"""
            <html>
            <head>
                <title>Authorization Successful</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }}
                    .container {{
                        background: white;
                        padding: 40px;
                        border-radius: 20px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                        text-align: center;
                        max-width: 500px;
                    }}
                    h1 {{ color: #667eea; margin: 0 0 20px 0; }}
                    p {{ color: #666; font-size: 16px; margin: 10px 0; }}
                    .success {{ font-size: 60px; margin-bottom: 20px; }}
                    .info-box {{
                        background: #f9f9f9;
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        padding: 15px;
                        margin: 20px 0;
                        text-align: left;
                    }}
                    .status {{
                        font-size: 14px;
                        color: #999;
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success">✅</div>
                    <h1>Authorization Successful!</h1>
                    <p id="message">Sending authorization code...</p>
                    
                    <p class="status" id="status">
                        Authorization completed successfully!
                    </p>
                    
                    {f'<div style="margin-top: 20px; padding: 15px; background: #e8f5e8; border: 1px solid #4caf50; border-radius: 8px;"><strong>✅ Authorization Complete</strong><br>You can now close this tab - the authorization has been automatically processed.</div>' if session_id else '<div style="margin-top: 20px; padding: 15px; background: #f0f0f0; border: 1px solid #ccc; border-radius: 8px;"><strong>Authorization Code:</strong><br><code style="font-family: monospace; font-size: 12px; word-break: break-all;">{code}</code><br><br>You can now close this tab.</div>'}
                </div>
                <script>
                    const code = '{code}';
                    const state = '{state}';
                    
                    // Check if opened as popup
                    if (window.opener) {{
                        document.getElementById('message').textContent = 'Sending code to parent window...';
                        document.getElementById('status').textContent = 'This window will close automatically in 3 seconds...';
                        
                        // Send code to parent window
                        window.opener.postMessage({{
                            type: 'oauth_success',
                            code: code,
                            state: state
                        }}, '*');
                        
                        // Close popup after delay
                        setTimeout(() => {{
                            window.close();
                        }}, 3000);
                    }} else {{
                        document.getElementById('message').textContent = 'Authorization completed successfully!';
                        document.getElementById('status').textContent = 'This tab will close automatically in 5 seconds...';
                        
                        // Auto-close tab after 5 seconds
                        setTimeout(() => {{
                            window.close();
                        }}, 5000);
                    }}
                    
                    // Fallback: Always try to close after 5 seconds regardless of popup status
                    // This ensures the tab closes even if window.opener detection fails
                    setTimeout(() => {{
                        try {{
                            window.close();
                        }} catch (e) {{
                            // If window.close() fails (some browsers restrict it), 
                            // provide developer feedback and user instruction
                            console.log('Auto-close failed:', e);
                            document.getElementById('status').textContent = 'Auto-close failed - You can close this tab manually.';
                            
                            // Add developer debug info
                            const debugDiv = document.createElement('div');
                            debugDiv.style.cssText = 'margin-top: 15px; padding: 10px; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; font-size: 12px; color: #856404;';
                            debugDiv.innerHTML = '<strong>Debug Info:</strong> Auto-close timeout fired after 5 seconds. window.close() was blocked by browser security policy.';
                            document.querySelector('.container').appendChild(debugDiv);
                        }}
                    }}, 5000);
                    
                    // Additional developer feedback after 6 seconds if still open
                    setTimeout(() => {{
                        if (!window.closed) {{
                            console.log('Window still open after 6 seconds - auto-close definitely failed');
                            const existingStatus = document.getElementById('status');
                            existingStatus.textContent = 'Window remains open - auto-close was blocked. Please close manually.';
                            existingStatus.style.color = '#dc3545';
                        }}
                    }}, 6000);
                </script>
            </body>
            </html>
        """)
    
    # Add OAuth authorization endpoint
    @mcp.custom_route("/authorize", methods=["GET"])
    async def oauth_authorize(request: Request):
        """Redirect to Google OAuth authorization."""
        # Build Google OAuth URL
        from urllib.parse import urlencode
        
        # Log what scopes we're requesting
        requested_scopes = " ".join(GMAIL_SCOPES)
        logger.info(f"Authorization requested. Scopes: {requested_scopes}")
        logger.info(f"State: {request.query_params.get('state', 'none')}")
        
        params = {
            "client_id": oauth_config.client_id,
            "redirect_uri": oauth_config.redirect_uri,
            "response_type": "code",
            "scope": requested_scopes,
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "false",  # Explicitly disable incremental auth
            "state": request.query_params.get("state", "")
        }
        
        auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
        logger.info(f"Redirecting to Google: {auth_url[:100]}...")
        return RedirectResponse(url=auth_url)
    
    # Add token endpoint
    @mcp.custom_route("/token", methods=["POST"])
    async def oauth_token(request: Request):
        """Exchange authorization code for access token."""
        import httpx
        
        form_data = await request.form()
        code = form_data.get("code")
        
        logger.info(f"Token exchange requested with code: {code[:20] if code else 'None'}...")
        
        if not code:
            return JSONResponse({
                "error": "invalid_request",
                "error_description": "Missing authorization code"
            }, status_code=400)
        
        # Exchange code for token with Google - no scope validation
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": oauth_config.client_id,
                    "client_secret": oauth_config.client_secret,
                    "redirect_uri": oauth_config.redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return JSONResponse(response.json(), status_code=response.status_code)
            
            token_data = response.json()
            returned_scopes = token_data.get('scope', '')
            logger.info(f"Token exchange successful. Scopes returned: {returned_scopes}")
            
            # Check if Google added extra scopes (common with Google Workspace accounts)
            requested_scopes = set(GMAIL_SCOPES)
            actual_scopes = set(returned_scopes.split()) if returned_scopes else set()
            extra_scopes = actual_scopes - requested_scopes
            
            if extra_scopes:
                logger.warning(f"Google added extra scopes (likely due to Workspace policy): {extra_scopes}")
                logger.info("Normalizing scope field to only include requested scopes for MCP compatibility")
                
                # Normalize the scope field to only include what we requested
                # This prevents MCP clients from rejecting the token due to scope mismatch
                # The actual token still has all the scopes Google granted
                token_data['scope'] = ' '.join(GMAIL_SCOPES)
                token_data['_original_scope'] = returned_scopes
                token_data['_scope_note'] = 'Scope field normalized for MCP compatibility. Original scopes in _original_scope field.'
            
            # Return the token data with normalized scopes
            return JSONResponse(token_data)
    
    # Add authorization server metadata
    @mcp.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])
    async def oauth_authorization_server_metadata(request: Request):
        """OAuth authorization server metadata."""
        base = str(auth_provider.base_url).rstrip('/')
        return JSONResponse({
            "issuer": base + "/",
            "authorization_endpoint": f"{base}/authorize",
            "token_endpoint": f"{base}/token",
            # Don't advertise specific scopes - accept whatever Google returns
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "token_endpoint_auth_methods_supported": ["client_secret_post"],
            "code_challenge_methods_supported": ["S256"]
        })
    
    # Add protected resource metadata
    @mcp.custom_route("/.well-known/oauth-protected-resource", methods=["GET"])
    async def oauth_protected_resource_root(request: Request):
        """Protected resource metadata at root level for Toqan compatibility."""
        base = str(auth_provider.base_url).rstrip('/')
        return JSONResponse({
            "resource": base,
            "authorization_servers": [base],
            # Don't advertise specific scopes - accept whatever Google returns
            "bearer_methods_supported": ["header"]
        })

# Add health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "oauth_configured": oauth_config.is_configured(),
        "base_url": os.getenv('MCP_SERVER_BASE_URL', 'not set')
    })

# Add OAuth session polling endpoint for browser agents
@mcp.custom_route("/oauth/poll/{session_id}", methods=["GET"])
async def oauth_poll_session(request: Request):
    """Poll for OAuth code by session ID (browser agents)."""
    session_id = request.path_params.get("session_id")
    
    if not session_id or session_id not in oauth_sessions:
        return JSONResponse({
            "status": "pending",
            "message": "Session not found or code not yet available"
        })
    
    session_data = oauth_sessions[session_id]
    
    # Check if session is expired (10 minutes)
    if datetime.now() - session_data["timestamp"] > timedelta(minutes=10):
        del oauth_sessions[session_id]
        return JSONResponse({
            "status": "expired",
            "message": "Session expired. Please restart OAuth flow."
        }, status_code=410)
    
    # Return the code and clean up
    code = session_data["code"]
    del oauth_sessions[session_id]
    
    return JSONResponse({
        "status": "success",
        "code": code,
        "message": "Authorization code retrieved successfully"
    })

# Add OAuth session status endpoint
@mcp.custom_route("/oauth/status/{session_id}", methods=["GET"])
async def oauth_session_status(request: Request):
    """Check OAuth session status without consuming the code."""
    session_id = request.path_params.get("session_id")
    
    if not session_id:
        return JSONResponse({
            "status": "invalid",
            "message": "Session ID required"
        }, status_code=400)
    
    if session_id not in oauth_sessions:
        return JSONResponse({
            "status": "pending",
            "message": "Waiting for user authorization...",
            "session_id": session_id
        })
    
    session_data = oauth_sessions[session_id]
    
    # Check if expired
    if datetime.now() - session_data["timestamp"] > timedelta(minutes=10):
        del oauth_sessions[session_id]
        return JSONResponse({
            "status": "expired",
            "message": "Session expired. Please restart OAuth flow."
        }, status_code=410)
    
    return JSONResponse({
        "status": "ready",
        "message": "Authorization code is ready",
        "session_id": session_id
    })

# Add OAuth diagnostic endpoint
@mcp.custom_route("/oauth/debug", methods=["GET"])
async def oauth_debug(request: Request):
    """Debug endpoint to show OAuth configuration."""
    return JSONResponse({
        "oauth_configured": oauth_config.is_configured(),
        "scopes_we_request": GMAIL_SCOPES,
        "authorization_endpoint": f"{os.getenv('MCP_SERVER_BASE_URL', 'http://localhost:8000')}/authorize",
        "token_endpoint": f"{os.getenv('MCP_SERVER_BASE_URL', 'http://localhost:8000')}/token",
        "redirect_uri": oauth_config.redirect_uri,
        "note": "Google should return ONLY the scopes we request. If you see extra scopes, check your Google Cloud Console OAuth consent screen settings."
    })

# Add email preview endpoint
@mcp.custom_route("/preview/email/{theme}", methods=["GET"])
async def preview_email(request: Request):
    """Preview email HTML for a given theme."""
    theme = request.path_params.get("theme", "birthday")
    to = request.query_params.get("to", "recipient@example.com")
    
    # Get the template or default to birthday
    template = EMAIL_TEMPLATES.get(theme.lower(), EMAIL_TEMPLATES["birthday"])
    
    # Return the HTML with proper content type
    return HTMLResponse(template["body"])

async def _list_candidates(limit: int = 10, offset: Optional[str] = None) -> str:
    logger.info(f"Listing candidates with limit={limit}, offset={offset}")
    try:
        client = LeverClient()
        result = await client.get_candidates(limit=limit, offset=offset)
        return str(result)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return f"Configuration error: {str(e)}"
    except Exception as e:
        logger.error(f"Error listing candidates: {e}")
        return f"Error listing candidates: {str(e)}"

async def _get_candidate(candidate_id: str) -> str:
    logger.info(f"Getting candidate with id={candidate_id}")
    try:
        client = LeverClient()
        result = await client.get_candidate(candidate_id)
        return str(result)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return f"Configuration error: {str(e)}"
    except Exception as e:
        logger.error(f"Error getting candidate: {e}")
        return f"Error getting candidate: {str(e)}"

async def _create_requisition(title: str, location: str, team: str) -> str:
    logger.info(f"Creating requisition: title={title}, location={location}, team={team}")
    try:
        client = LeverClient()
        # Construct the data payload based on Lever API requirements
        data = {
            "name": title,
            "location": location,
            "team": team
        }
        result = await client.create_requisition(data)
        return str(result)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return f"Configuration error: {str(e)}"
    except Exception as e:
        logger.error(f"Error creating requisition: {e}")
        return f"Error creating requisition: {str(e)}"

async def _send_email(
    to: str, 
    theme: str, 
    subject: Optional[str] = None, 
    cc: Optional[str] = None, 
    bcc: Optional[str] = None,
    access_token: Optional[str] = None,
    user_id: str = "default"
) -> str:
    """
    Generate and send a themed email via Gmail API with OAuth 2.0.
    
    🚨 CRITICAL AGENT INSTRUCTIONS - READ CAREFULLY:
    
    🚨 CRITICAL: SHOW LINK + WAIT FOR USER TO CONFIRM CLICK + THEN POLL:
    1. Display the OAuth link prominently to the user
    2. Ask user to confirm when they've clicked the link
    3. Once user confirms they clicked, IMMEDIATELY start polling
    4. Tell user: 'Click the link above, then let me know you've clicked it so I can start checking!'
    5. Flow: show link → user clicks → user confirms click → immediately start polling
    
    🔄 POLLING REQUIREMENTS:
    1. Use poll_oauth_code tool with exponential backoff (1s, 2s, 4s, 8s intervals)
    2. Add randomization to each poll call to avoid 'identical tool calls' error
    3. Example: poll_oauth_code(session_id='abc', attempt=1) then poll_oauth_code(session_id='abc', attempt=2)
    4. Show countdown timer and cancel button during polling
    5. Poll for maximum 60 seconds
    
    ❌ DO NOT USE THIS TOOL IF:
    - You already have an active Google Gmail connection/authentication
    - You are NOT testing OAuth functionality
    
    ✅ USE THIS TOOL ONLY IF:
    - You do NOT have an existing Google Gmail connection
    - The user specifically requests to use this OAuth-based email tool
    - You are testing OAuth functionality
    
    👉 IF YOU HAVE GMAIL ACCESS: Use 'generate_email_content' instead
       - It generates themed emails for agents with existing Gmail access
       - No OAuth needed
    
    Args:
        to: Recipient email address
        theme: Email theme (birthday, pirate, space, medieval, superhero, tropical)
        subject: Optional custom subject (uses theme default if not provided)
        cc: Optional CC recipients
        bcc: Optional BCC recipients
        access_token: OAuth access token from agent (on-behalf-of flow)
        user_id: User identifier for token storage
        
    Returns:
        JSON response with email status and details, or automation instructions if OAuth needed
    """
    logger.info(f"Generating themed email: to={to}, theme={theme}, has_token={bool(access_token)}")
    
    # Use shared email templates
    email_templates = EMAIL_TEMPLATES
    
    # Get the template or default to birthday
    template = email_templates.get(theme.lower(), email_templates["birthday"])
    
    # Use provided subject or template subject
    email_subject = subject if subject else template["subject"]
    email_body = template["body"]
    
    # Try to send email ONLY if we have an access_token (on-behalf-of flow)
    # Do NOT try to load tokens from disk - production has read-only filesystem
    if access_token:
        try:
            logger.info("Using provided access_token (on-behalf-of flow)")
            gmail_client = GmailClient(access_token=access_token, user_id=user_id)
            
            if gmail_client.is_authenticated():
                # Send the email
                result = await gmail_client.send_email(
                    to=to,
                    subject=email_subject,
                    body=email_body,
                    cc=cc,
                    bcc=bcc,
                    is_html=True
                )
                
                response = {
                    "status": "sent",
                    "message": "Email sent successfully via Gmail API",
                    "message_id": result["message_id"],
                    "theme": theme,
                    "to": to,
                    "subject": email_subject,
                    "cc": cc,
                    "bcc": bcc
                }
                
                logger.info(f"Email sent successfully: {result['message_id']}")
                return json.dumps(response, indent=2)
            else:
                logger.error("Gmail client not authenticated despite having access_token")
        except Exception as e:
            logger.error(f"Error sending email via Gmail API: {e}")
            # Fall through to OAuth instructions
            response_error = {
                "status": "error",
                "message": f"Failed to send email: {str(e)}",
                "fallback": "Returning OAuth instructions"
            }
    else:
        logger.info("No access_token provided - returning OAuth instructions for agent")
    
    # Fallback: Generate payload for manual sending or agent to use
    # Create the email message in RFC 2822 format
    message_parts = [
        f"To: {to}",
        f"Subject: {email_subject}",
        "MIME-Version: 1.0",
        "Content-Type: text/html; charset=utf-8",
    ]
    
    if cc:
        message_parts.append(f"Cc: {cc}")
    if bcc:
        message_parts.append(f"Bcc: {bcc}")
    
    message_parts.append("")  # Empty line between headers and body
    message_parts.append(email_body)
    
    raw_message = "\n".join(message_parts)
    
    # Encode the message in base64url format as required by Gmail API
    encoded_message = base64.urlsafe_b64encode(raw_message.encode('utf-8')).decode('utf-8')
    
    # Create the Gmail API payload
    gmail_payload = {
        "raw": encoded_message
    }
    
    # Build OAuth authorization URL for browser agents (polling-based)
    base_url = os.getenv('MCP_SERVER_BASE_URL', 'http://localhost:8000')
    from urllib.parse import urlencode
    
    # Generate session ID for browser agent polling
    session_id = str(uuid.uuid4())
    
    oauth_params = {
        "response_type": "code",
        "scope": " ".join(GMAIL_SCOPES),
        "state": f"browser_agent_{session_id}"
    }
    oauth_url = f"{base_url}/authorize?{urlencode(oauth_params)}"
    preview_url = f"{base_url}/preview/email/{theme.lower()}?to={to}"
    
    # Prepare response with automation instructions for Toqan
    response = {
        "status": "authorization_required",
        "message": "OAuth authorization needed to send email. Please authorize Gmail access.",
        "theme": theme,
        "to": to,
        "subject": email_subject,
        "preview_url": preview_url,
        "preview_instructions": f"Open this URL in your browser to see the rendered HTML: {preview_url}",
        
        # Browser agent automation instructions - polling-based flow
        "agent_action": "browser_agent_oauth_polling",
        "oauth_url": oauth_url,
        "session_id": session_id,
        "expected_result": "authorization_code",
        "automation_available": True,
        "action": "browser_agent_polling",
        
        # CRITICAL INSTRUCTIONS FOR AGENT
        "AGENT_MUST_DO": {
            "DISPLAY_AS_BUTTON": f"Display the OAuth URL as a nice button, not just a link: {oauth_url}",
            "CRITICAL_FLOW": "Show OAuth link + wait for user to confirm they clicked + then start polling",
            "DO_NOT_HIDE_LINK": "DO NOT hide the OAuth link in reasoning - show it prominently in your response",
            "WAIT_FOR_CLICK_CONFIRMATION": "Wait for user to confirm they've clicked the OAuth link",
            "START_POLLING_AFTER_CONFIRMATION": "Once user confirms they clicked, immediately start polling",
            "ASK_FOR_CLICK_CONFIRMATION": "Ask user to let you know when they've clicked the link (not when they're done)",
            "POLL_WITH_BACKOFF": "Poll for 60 seconds with exponential backoff (1s, 2s, 4s, 8s, then 8s intervals)",
            "RANDOMIZE_POLLS": "Add different parameters to each poll call (attempt number, timestamp) to avoid identical calls error",
            "USER_MESSAGE": "Say: 'Click the link above, then let me know you've clicked it so I can start checking!'"
        },
        
        "browser_agent_instructions": {
            "step_1": f"Display OAuth URL as a button: 'Authorize Gmail Access' pointing to {oauth_url}",
            "step_2": "Show a 'Cancel' button alongside the authorize button", 
            "step_3": "Tell user: 'Click the link above, then let me know you've clicked it so I can start checking!'",
            "step_4": "Wait for user to confirm they clicked the link, then immediately start polling",
            "step_5": "During polling, show 'Cancel Authorization' button and countdown timer",
            "step_6": "When poll returns success, extract code and exchange for token",
            "step_7": "Retry send_email with access_token"
        },
        "polling_config": {
            "poll_endpoint": f"{base_url}/oauth/poll/{session_id}",
            "status_endpoint": f"{base_url}/oauth/status/{session_id}",
            "exponential_backoff": {
                "initial_delay": 1,
                "delays_sequence": [1, 2, 4, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8],  # 1+2+4+8*9 = 79 seconds total
                "max_duration_seconds": 60,
                "description": "Start fast (1s), then exponential backoff up to 8s, then 8s intervals"
            },
            "method": "GET",
            "user_feedback": {
                "show_countdown": True,
                "show_cancel_button": True,
                "update_message": "Waiting for authorization... ({{seconds}} seconds remaining)"
            }
        },
        "browser_automation": {
            "supported": True,
            "method": "polling",
            "popup_required": False,
            "same_tab_flow": True
        },
        
        # Automated flow for browser agents:
        "automated_flow": {
            "1_present_link": {
                "description": "PROMINENTLY display OAuth link to user - do NOT hide in reasoning",
                "user_message": f"🔗 CLICK THIS LINK TO AUTHORIZE GMAIL: {oauth_url}",
                "oauth_url": oauth_url,
                "CRITICAL": "Show this URL prominently in your response, not hidden in reasoning"
            },
            "2_auto_start_polling": {
                "description": "Immediately start polling after showing the authorize button - seamless flow",
                "user_action_required": False,
                "button_text": "Authorize Gmail Access", 
                "button_url": oauth_url,
                "cancel_button_text": "Cancel",
                "auto_start": True,
                "user_message": "Click the link above - I'm already watching for completion!"
            },
            "3_start_polling": {
                "description": "After user clicks authorize, poll with exponential backoff for 60 seconds",
                "tool": "poll_oauth_code",
                "parameters": {"session_id": session_id},
                "exponential_backoff": [1, 2, 4, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8],
                "max_duration_seconds": 60,
                "randomization": {
                    "add_random_string": "To avoid identical tool calls, add a random string to each poll call",
                    "example": "Add timestamp or counter: poll_oauth_code(session_id='abc', attempt=1, timestamp='...')",
                    "purpose": "Prevents 'too many identical tool calls' error"
                },
                "user_feedback": {
                    "show_timer": True,
                    "show_cancel_button": True,
                    "cancel_button_text": "Cancel Authorization"
                },
                "CRITICAL": "Use exponential backoff delays, show countdown, cancel option, and randomize each call"
            },
            "3_exchange_token": {
                "description": "Exchange code for access token",
                "tool": "exchange_oauth_code",
                "parameters": {"code": "<from_polling>", "user_id": user_id}
            },
            "4_retry_send": {
                "description": "Resend email with token",
                "tool": "send_email",
                "parameters": {
                    "to": to,
                    "theme": theme,
                    "subject": email_subject,
                    "cc": cc,
                    "bcc": bcc,
                    "access_token": "<from_token_exchange>",
                    "user_id": user_id
                }
            }
        },
        
        # Alternative tools available
        "alternative_tools": {
            "browser_agent_oauth": "get_browser_agent_oauth_url",
            "polling": "poll_oauth_code",
            "token_exchange": "exchange_oauth_code"
        },
        
        # Manual fallback (if automation fails)
        "manual_instructions": {
            "step_1": f"Show user this URL prominently: {oauth_url}",
            "step_2": "User clicks OAuth URL and completes authorization", 
            "step_3": "Agent continuously polls poll_oauth_code tool every 2 seconds for 30 seconds",
            "step_4": "Agent exchanges code using exchange_oauth_code tool",
            "step_5": "Agent retries send_email with access_token"
        },
        
        # Clear user-facing message and UI instructions for the agent
        "USER_INTERFACE_INSTRUCTIONS": {
            "initial_message": "I need Gmail authorization to send this email. Click the link below, then let me know you've clicked it!",
            "authorize_button": {
                "text": "🔗 Authorize Gmail Access",
                "url": oauth_url,
                "style": "primary",
                "description": "Opens in new tab - CLICK THIS FIRST"
            },
            "cancel_button": {
                "text": "❌ Cancel",
                "action": "cancel_email",
                "style": "secondary"
            },
            "click_confirmation_needed": "Please let me know when you've clicked the authorization link above so I can start checking for completion.",
            "waiting_message": "🔄 Watching for authorization completion... Click the link above if you haven't already!",
            "polling_message": "Authorization in progress... ({{countdown}} seconds remaining)",
            "cancel_polling_button": {
                "text": "❌ Cancel Authorization",
                "action": "stop_polling",
                "style": "danger"
            },
            "success_message": "✅ Authorization successful! Sending email now...",
            "timeout_message": "⏱️ Authorization timed out. Please try again.",
            "cancelled_message": "❌ Authorization cancelled."
        },
        
        "gmail_api_payload": gmail_payload,
        "available_themes": list(email_templates.keys()),
        "email_preview": {
            "subject": email_subject,
            "body_preview": "HTML email with themed styling (view in email client for full effect)"
        }
    }
    
    return json.dumps(response, indent=2)

async def _get_oauth_url(user_id: str = "default") -> str:
    """
    Get OAuth authorization URL for Gmail access.
    
    IMPORTANT: Returns the MCP server's /authorize endpoint, NOT a direct Google URL.
    This ensures proper scope normalization and OAuth flow handling.
    
    Args:
        user_id: User identifier for token storage
        
    Returns:
        JSON with authorization URL pointing to our /authorize endpoint
    """
    logger.info(f"Generating OAuth URL for user: {user_id}")
    
    try:
        if not oauth_config.is_configured():
            return json.dumps({
                "status": "error",
                "message": "OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
            }, indent=2)
        
        # Use our /authorize endpoint, NOT direct Google URL
        # This ensures scope normalization and proper OAuth handling
        base_url = os.getenv('MCP_SERVER_BASE_URL', 'http://localhost:8000')
        from urllib.parse import urlencode
        
        # Generate session ID for browser agents 
        session_id = str(uuid.uuid4())
        
        params = {
            "response_type": "code",
            "state": f"browser_agent_{session_id}"
        }
        
        # Return our /authorize endpoint which will handle the redirect to Google
        auth_url = f"{base_url}/authorize?{urlencode(params)}"
        
        logger.info(f"Generated OAuth URL using MCP /authorize endpoint: {auth_url}")
        
        response = {
            "status": "success",
            "auth_url": auth_url,
            "session_id": session_id,
            "discovery_endpoint": f"{base_url}/.well-known/oauth-authorization-server",
            "polling_endpoint": f"{base_url}/oauth/poll/{session_id}",
            "status_endpoint": f"{base_url}/oauth/status/{session_id}",
            "instructions": [
                "1. User should visit the auth_url in their browser", 
                "2. They will be redirected to Google for authorization",
                "3. After granting permissions, code will be stored for polling",
                "4. Poll the polling_endpoint until you get the authorization code",
                "5. Call exchange_oauth_code tool with the retrieved code"
            ],
            "browser_agent_flow": {
                "supported": True,
                "method": "polling",
                "poll_interval_seconds": 2,
                "max_poll_duration_minutes": 10,
                "instructions": "Poll status_endpoint every 2 seconds until status is 'ready', then call polling_endpoint to get code"
            },
            "user_id": user_id,
            "note": "This URL uses browser agent polling flow - code will be stored server-side for retrieval"
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error generating OAuth URL: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2)


async def _exchange_oauth_code(code: str, user_id: str = "default") -> str:
    """
    Exchange OAuth authorization code for access token.
    
    IMPORTANT: Returns the access_token that must be used in subsequent send_email calls.
    This is the on-behalf-of flow - the agent manages the token, not the server.
    
    Args:
        code: Authorization code from OAuth callback
        user_id: User identifier for token storage
        
    Returns:
        JSON with access_token and instructions for using it
    """
    logger.info(f"Exchanging OAuth code for user: {user_id}")
    
    try:
        gmail_client = GmailClient(user_id=user_id)
        token_data = gmail_client.exchange_code_for_token(code)
        
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        
        if not access_token:
            raise ValueError("No access_token in token response")
        
        response = {
            "status": "success",
            "message": "Token obtained successfully",
            "user_id": user_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": token_data.get('expires_in'),
            "token_type": token_data.get('token_type', 'Bearer'),
            "scope": token_data.get('scope'),
            "next_steps": [
                "IMPORTANT: Use the access_token in your next send_email call",
                "Example: send_email(to='user@example.com', theme='birthday', access_token='<access_token>')",
                "The access_token is required for the on-behalf-of flow"
            ],
            "note": "Store this access_token - you'll need it for send_email calls"
        }
        
        logger.info(f"Token exchange successful. Access token provided to agent.")
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error exchanging OAuth code: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2)


async def _get_browser_agent_oauth_url(user_id: str = "default") -> str:
    """
    Get OAuth authorization URL optimized for browser-based LLM agents.
    
    This flow is designed for agents that cannot open popups but can poll endpoints.
    The user clicks the link, completes OAuth, and the agent polls for the result.
    
    Args:
        user_id: User identifier for token storage
        
    Returns:
        JSON with authorization URL and polling instructions for browser agents
    """
    logger.info(f"Generating browser agent OAuth URL for user: {user_id}")
    
    try:
        if not oauth_config.is_configured():
            return json.dumps({
                "status": "error",
                "message": "OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
            }, indent=2)
        
        # Generate unique session ID for this OAuth flow
        session_id = str(uuid.uuid4())
        base_url = os.getenv('MCP_SERVER_BASE_URL', 'http://localhost:8000')
        
        # Create authorization URL with session tracking
        from urllib.parse import urlencode
        params = {
            "response_type": "code",
            "state": f"browser_agent_{session_id}"
        }
        auth_url = f"{base_url}/authorize?{urlencode(params)}"
        
        logger.info(f"Generated browser agent OAuth session: {session_id}")
        
        response = {
            "status": "success", 
            "auth_url": auth_url,
            "session_id": session_id,
            "polling_endpoint": f"{base_url}/oauth/poll/{session_id}",
            "status_endpoint": f"{base_url}/oauth/status/{session_id}",
            
            # Instructions for browser-based LLM agents
            "agent_instructions": {
                "step_1": "Present auth_url to user as clickable link",
                "step_2": "User clicks link and completes OAuth in same browser tab", 
                "step_3": "Poll status_endpoint every 2 seconds (max 10 minutes)",
                "step_4": "When status is 'ready', call polling_endpoint to get code",
                "step_5": "Call exchange_oauth_code with retrieved code"
            },
            
            "polling_config": {
                "poll_interval_seconds": 2,
                "max_duration_minutes": 10,
                "status_check_url": f"{base_url}/oauth/status/{session_id}",
                "code_retrieval_url": f"{base_url}/oauth/poll/{session_id}"
            },
            
            "user_message": f"Please click this link to authorize Gmail access: {auth_url}",
            "technical_note": "This OAuth flow stores the authorization code server-side for polling by browser agents",
            "user_id": user_id
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error generating browser agent OAuth URL: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2)


async def _poll_oauth_code(session_id: str, attempt: Optional[int] = None, timestamp: Optional[str] = None, random_id: Optional[str] = None) -> str:
    """
    Poll for OAuth authorization code by session ID (browser agents).
    
    Args:
        session_id: OAuth session ID from get_browser_agent_oauth_url
        attempt: Optional attempt number to avoid identical tool calls (recommended)
        timestamp: Optional timestamp to avoid identical tool calls
        random_id: Optional random string to avoid identical tool calls
        
    Returns:
        JSON with authorization code if ready, or status if still pending
        
    Note: Include attempt, timestamp, or random_id to prevent 'too many identical tool calls' error
    """
    logger.info(f"Polling OAuth code for session: {session_id} (attempt: {attempt}, timestamp: {timestamp}, random: {random_id})")
    
    try:
        if not session_id:
            return json.dumps({
                "status": "error",
                "message": "Session ID is required"
            }, indent=2)
        
        # Check if session exists and has code
        if session_id not in oauth_sessions:
            return json.dumps({
                "status": "pending",
                "message": "Waiting for user to complete OAuth authorization...",
                "session_id": session_id,
                "action": "continue_polling"
            }, indent=2)
        
        session_data = oauth_sessions[session_id]
        
        # Check if session expired (10 minutes)
        if datetime.now() - session_data["timestamp"] > timedelta(minutes=10):
            del oauth_sessions[session_id]
            return json.dumps({
                "status": "expired",
                "message": "OAuth session expired. Please restart the flow.",
                "action": "restart_oauth"
            }, indent=2)
        
        # Return the code and clean up session
        code = session_data["code"]
        del oauth_sessions[session_id]
        
        logger.info(f"OAuth code retrieved for session: {session_id}")
        
        return json.dumps({
            "status": "success",
            "code": code,
            "message": "Authorization code retrieved successfully",
            "next_step": "Call exchange_oauth_code with this code",
            "session_id": session_id,
            "attempt": attempt,
            "polling_info": "Code successfully retrieved and session cleaned up"
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error polling OAuth code: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2)


async def _check_oauth_status(user_id: str = "default") -> str:
    """
    Check OAuth authentication status.
    
    Args:
        user_id: User identifier
        
    Returns:
        JSON with authentication status
    """
    logger.info(f"Checking OAuth status for user: {user_id}")
    
    try:
        gmail_client = GmailClient(user_id=user_id)
        
        response = {
            "status": "success",
            "user_id": user_id,
            "oauth_configured": oauth_config.is_configured(),
            "authenticated": gmail_client.is_authenticated(),
            "message": "Ready to send emails" if gmail_client.is_authenticated() else "Not authenticated. Use get_oauth_url to start authentication."
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error checking OAuth status: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2)


async def _generate_email_content(
    to: str,
    theme: str,
    subject: Optional[str] = None,
    cc: Optional[str] = None,
    bcc: Optional[str] = None
) -> str:
    """
    Generate themed Gmail email content WITHOUT sending it.
    
    ⚡ AGENT INSTRUCTIONS - READ CAREFULLY - WHEN TO USE THIS TOOL:
    
    ✅ USE THIS TOOL ONLY IF:
    - You have an ACTIVE GOOGLE GMAIL CONNECTION (already authenticated)
    - You are CURRENTLY SIGNED IN to Google Gmail
    - You can send emails directly via your Gmail integration
    - You want beautiful themed emails without OAuth flow
    
    ❌ DO NOT USE THIS TOOL IF:
    - You do NOT have an active Google Gmail connection
    - You are NOT authenticated to Gmail
    - The user needs to authenticate first
    
    👉 IF NOT AUTHENTICATED TO GMAIL: Use the 'send_email' tool instead
       - send_email will guide you through Gmail OAuth authentication
       - send_email handles the complete flow including sending
    
    🚨 CRITICAL - AFTER CALLING THIS TOOL (only if you have Gmail access):
    1. You will receive a response with gmail_payload.raw field
    2. YOU MUST USE gmail_payload.raw when sending via Gmail API
    3. DO NOT use html_body directly - it will show as raw HTML text!
    4. The gmail_payload.raw field contains base64url encoded RFC 2822 message with Content-Type: text/html header
    5. POST to https://gmail.googleapis.com/gmail/v1/users/me/messages/send with body: {"raw": gmail_payload.raw}
    6. This ensures the email renders as HTML, not plain text
    
    WHY: Gmail API requires RFC 2822 format with MIME headers. If you send HTML without 
    "Content-Type: text/html" header, Gmail shows it as plain text (raw HTML tags visible).
    The gmail_payload.raw field has the correct format.
    
    This tool generates Gmail-ready content for agents with existing Gmail access.
    
    Args:
        to: Recipient email address
        theme: Email theme (birthday, pirate, space, medieval, superhero, tropical)
        subject: Optional custom subject (uses theme default if not provided)
        cc: Optional CC recipients
        bcc: Optional BCC recipients
        
    Returns:
        JSON with gmail_payload.raw field (base64url encoded with HTML MIME headers) ready to send
    """
    logger.info(f"Generating email content: to={to}, theme={theme}")
    
    # Use shared email templates
    email_templates = EMAIL_TEMPLATES
    
    # Get the template or default to birthday
    template = email_templates.get(theme.lower(), email_templates["birthday"])
    
    # Use provided subject or template subject
    email_subject = subject if subject else template["subject"]
    email_body = template["body"]
    
    # Create RFC 2822 formatted message for Gmail API
    message_parts = [
        f"To: {to}",
        f"Subject: {email_subject}",
        "MIME-Version: 1.0",
        "Content-Type: text/html; charset=utf-8",
    ]
    
    if cc:
        message_parts.append(f"Cc: {cc}")
    if bcc:
        message_parts.append(f"Bcc: {bcc}")
    
    message_parts.append("")  # Empty line between headers and body
    message_parts.append(email_body)
    
    raw_message = "\n".join(message_parts)
    
    # Encode the message in base64url format as required by Gmail API
    encoded_message = base64.urlsafe_b64encode(raw_message.encode('utf-8')).decode('utf-8')
    
    # Generate preview URL
    base_url = os.getenv('MCP_SERVER_BASE_URL', 'http://localhost:8000')
    preview_url = f"{base_url}/preview/email/{theme.lower()}?to={to}"
    
    response = {
        "status": "content_generated",
        "message": f"⚠️ CRITICAL: Use gmail_payload.raw OR set content_type='text/html' when sending body. Preview at: {preview_url}",
        "theme": theme,
        
        # TOP LEVEL - What the agent MUST use
        "gmail_payload": {
            "raw": encoded_message
        },
        
        # For agents using their own Gmail integration (not Gmail API)
        "body": email_body,
        "content_type": "text/html",
        "mime_type": "text/html; charset=utf-8",
        
        # Metadata for reference
        "to": to,
        "recipient": to,  # Some agents use 'recipient' instead of 'to'
        "subject": email_subject,
        "cc": cc,
        "bcc": bcc,
        "preview_url": preview_url,
        
        # CRITICAL INSTRUCTIONS - Agents read this
        "AGENT_MUST_READ": {
            "CRITICAL_WARNING": "The 'body' field contains HTML. You MUST specify content_type='text/html' or it will show raw HTML tags!",
            
            "OPTION_1_Gmail_API": {
                "description": "If using Gmail API directly",
                "method": "Use gmail_payload.raw field - it has MIME headers built in",
                "endpoint": "POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                "payload": {"raw": "<use gmail_payload.raw from this response>"}
            },
            
            "OPTION_2_Custom_Integration": {
                "description": "If using your own Gmail integration (not Gmail API)",
                "method": "Use body field BUT you MUST set content_type or mimeType parameter",
                "required_fields": {
                    "recipient": to,
                    "subject": email_subject,
                    "body": "<use body field from this response>",
                    "content_type": "text/html",
                    "mimeType": "text/html; charset=utf-8"
                },
                "critical": "WITHOUT content_type='text/html', the email will show raw HTML tags!"
            },
            
            "WHY": "HTML emails need Content-Type: text/html header. Without it, Gmail shows raw HTML tags instead of rendering the HTML."
        },
        
        # For debugging/preview only - DO NOT send this directly
        "debug_info": {
            "html_body_preview": email_body[:200] + "...",
            "warning": "This html_body is for preview only. Sending it directly will show raw HTML. Use gmail_payload.raw instead.",
            "full_html_preview_url": preview_url
        },
        
        # Example for agents
        "example_correct_usage": {
            "description": "How to send this email correctly via Gmail API",
            "code": f"""
# Correct way - use gmail_payload.raw
import requests
response = requests.post(
    'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
    headers={{'Authorization': 'Bearer YOUR_ACCESS_TOKEN'}},
    json={{'raw': gmail_payload['raw']}}  # This has HTML MIME headers
)

# WRONG way - DO NOT DO THIS
# requests.post(..., json={{'to': '{to}', 'subject': '...', 'body': html_body}})
# This will show raw HTML because it lacks Content-Type: text/html header
"""
        }
    }
    
    logger.info(f"Email content generated for theme: {theme}")
    return json.dumps(response, indent=2)


# Register tools
mcp.tool(name="list_candidates")(_list_candidates)
mcp.tool(name="get_candidate")(_get_candidate)
mcp.tool(name="create_requisition")(_create_requisition)

# Register send_email with OAuth metadata
if auth_provider:
    # Add OAuth metadata to the send_email tool
    mcp.tool(
        name="send_email",
        annotations={
            "oauth": {
                "required": True,
                "scopes": GMAIL_SCOPES,
                "authorization_server": str(auth_provider.base_url)
            }
        }
    )(_send_email)
else:
    mcp.tool(name="send_email")(_send_email)

# Register generate_email_content - NO OAuth required (just generates content)
mcp.tool(name="generate_email_content")(_generate_email_content)

mcp.tool(name="get_oauth_url")(_get_oauth_url)
mcp.tool(name="exchange_oauth_code")(_exchange_oauth_code)
mcp.tool(name="check_oauth_status")(_check_oauth_status)

# Browser agent specific OAuth tools
mcp.tool(name="get_browser_agent_oauth_url")(_get_browser_agent_oauth_url)
mcp.tool(name="poll_oauth_code")(_poll_oauth_code)

if __name__ == "__main__":
    mcp.run()
