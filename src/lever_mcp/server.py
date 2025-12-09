from fastmcp import FastMCP
from fastmcp.server.auth import OAuthProxy, StaticTokenVerifier
from lever_mcp.client import LeverClient
from lever_mcp.gmail_client import GmailClient
from lever_mcp.oauth_config import oauth_config, GMAIL_SCOPES
from typing import Optional, Dict, Any
import logging
import json
import base64
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("lever-mcp")

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
    from starlette.responses import JSONResponse, RedirectResponse
    from starlette.requests import Request
    
    # Add OAuth callback handler
    @mcp.custom_route("/oauth/callback", methods=["GET"])
    async def oauth_callback(request: Request):
        """Handle OAuth callback from Google."""
        from starlette.responses import HTMLResponse
        
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
                    .code-box {{
                        background: #f5f5f5;
                        border: 2px solid #e0e0e0;
                        border-radius: 8px;
                        padding: 15px;
                        margin: 20px 0;
                        word-break: break-all;
                        font-family: monospace;
                        font-size: 12px;
                        color: #333;
                    }}
                    .copy-btn {{
                        background: #667eea;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 14px;
                        margin-top: 10px;
                    }}
                    .copy-btn:hover {{
                        background: #5568d3;
                    }}
                    .copy-btn:active {{
                        background: #4451b8;
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
                    
                    <div class="code-box" id="codeBox">
                        <strong>Authorization Code:</strong><br>
                        {code}
                    </div>
                    
                    <button class="copy-btn" onclick="copyCode()">📋 Copy Code</button>
                    
                    <p class="status" id="status">
                        Checking if opened as popup...
                    </p>
                </div>
                <script>
                    const code = '{code}';
                    const state = '{state}';
                    
                    function copyCode() {{
                        navigator.clipboard.writeText(code).then(() => {{
                            const btn = document.querySelector('.copy-btn');
                            btn.textContent = '✅ Copied!';
                            setTimeout(() => {{
                                btn.textContent = '📋 Copy Code';
                            }}, 2000);
                        }});
                    }}
                    
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
                        document.getElementById('message').textContent = 'Copy the code above and paste it back in the chat.';
                        document.getElementById('status').textContent = 'You can close this window after copying the code.';
                    }}
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
        return JSONResponse({
            "issuer": str(auth_provider.base_url) + "/",
            "authorization_endpoint": f"{auth_provider.base_url}/authorize",
            "token_endpoint": f"{auth_provider.base_url}/token",
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
        return JSONResponse({
            "resource": str(auth_provider.base_url),
            "authorization_servers": [str(auth_provider.base_url)],
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
    
    AGENT INSTRUCTIONS:
    1. If you have OAuth capability (can open browser popups), try calling this tool first without access_token
    2. The response will include automation instructions (agent_action: "open_browser_popup")
    3. Follow the popup_instructions to get the authorization code automatically
    4. Use the exchange_oauth_code tool to get the access_token
    5. Call this tool again with the access_token parameter
    
    ALTERNATIVE: If you don't have OAuth capability, use the get_oauth_url tool to get a URL for the user.
    
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
    
    # Email templates based on themes
    email_templates = {
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
            "subject": "🚀 Greetings from the Cosmos! 🌌",
            "body": """
<html>
<body style="font-family: 'Arial', sans-serif; background: #000; padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%); border-radius: 20px; padding: 40px; box-shadow: 0 0 40px rgba(126, 34, 206, 0.5);">
        <h1 style="color: #fff; text-align: center; font-size: 42px; margin-bottom: 20px; text-shadow: 0 0 20px rgba(255,255,255,0.5);">🚀 Cosmic Greetings! 🌌</h1>
        <p style="font-size: 18px; color: #e0e0e0; line-height: 1.6;">
            Greetings, space explorer! 👨‍🚀
        </p>
        <p style="font-size: 16px; color: #d0d0d0; line-height: 1.6;">
            Your mission, should you choose to accept it, is to have an absolutely stellar day! 
            May your journey through the cosmos be filled with wonder and discovery!
        </p>
        <div style="text-align: center; margin: 30px 0; font-size: 50px;">
            🌟 🪐 🛸 🌙 ✨
        </div>
        <p style="font-size: 14px; color: #aaa; text-align: center;">
            Transmission complete.<br>
            - Mission Control
        </p>
    </div>
</body>
</html>
"""
        },
        "medieval": {
            "subject": "⚔️ A Royal Proclamation! 🏰",
            "body": """
<html>
<body style="font-family: 'Georgia', serif; background: #2c1810; padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: #f4e4c1; border: 5px solid #8b4513; border-radius: 10px; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.5);">
        <h1 style="color: #8b4513; text-align: center; font-size: 42px; margin-bottom: 20px; font-family: 'Georgia', serif;">⚔️ Royal Proclamation ⚔️</h1>
        <p style="font-size: 18px; color: #2c1810; line-height: 1.8; text-align: justify;">
            Hear ye, hear ye! By order of the realm, this message is delivered unto thee! 🏰
        </p>
        <p style="font-size: 16px; color: #3c2810; line-height: 1.8; text-align: justify; font-style: italic;">
            May thy days be filled with honor, thy quests be successful, and thy feasts be bountiful! 
            Long may thou prosper in this noble kingdom!
        </p>
        <div style="text-align: center; margin: 30px 0; font-size: 50px;">
            👑 ⚔️ 🏰 🛡️ 🐉
        </div>
        <p style="font-size: 14px; color: #5c4810; text-align: center;">
            By royal decree,<br>
            The Court Scribe
        </p>
    </div>
</body>
</html>
"""
        },
        "superhero": {
            "subject": "💥 URGENT: Superhero Alert! 🦸",
            "body": """
<html>
<body style="font-family: 'Impact', 'Arial Black', sans-serif; background: #ff0000; padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: #ffeb3b; border: 8px solid #000; border-radius: 15px; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.7);">
        <h1 style="color: #ff0000; text-align: center; font-size: 48px; margin-bottom: 20px; text-shadow: 3px 3px 0 #000; letter-spacing: 2px;">💥 SUPERHERO ALERT! 💥</h1>
        <p style="font-size: 20px; color: #000; line-height: 1.6; font-weight: bold;">
            ATTENTION HERO! 🦸
        </p>
        <p style="font-size: 16px; color: #333; line-height: 1.6;">
            Your incredible powers are needed! The city calls upon you to have an AMAZING day and 
            save the world with your awesome abilities! Remember: with great power comes great responsibility!
        </p>
        <div style="text-align: center; margin: 30px 0; font-size: 50px;">
            💪 ⚡ 🦸 🌟 💥
        </div>
        <p style="font-size: 14px; color: #666; text-align: center; font-weight: bold;">
            MISSION STATUS: ACTIVE<br>
            - Hero Command Center
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
<body style="font-family: 'Comic Sans MS', 'Arial', sans-serif; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: #fff; border-radius: 25px; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
        <h1 style="color: #f5576c; text-align: center; font-size: 42px; margin-bottom: 20px;">🌴 Aloha! 🌺</h1>
        <p style="font-size: 18px; color: #333; line-height: 1.6;">
            Sending you tropical vibes and sunny wishes! 🏝️
        </p>
        <p style="font-size: 16px; color: #555; line-height: 1.6;">
            May your day be as refreshing as a cool ocean breeze and as bright as the tropical sun! 
            Time to relax, unwind, and enjoy the paradise around you!
        </p>
        <div style="text-align: center; margin: 30px 0; font-size: 50px;">
            🌺 🥥 🍹 🏖️ 🌊
        </div>
        <p style="font-size: 14px; color: #999; text-align: center;">
            Mahalo!<br>
            - Your Island Friend
        </p>
    </div>
</body>
</html>
"""
        }
    }
    
    # Get the template or default to birthday
    template = email_templates.get(theme.lower(), email_templates["birthday"])
    
    # Use provided subject or template subject
    email_subject = subject if subject else template["subject"]
    email_body = template["body"]
    
    # Try to send email if we have OAuth token
    if access_token or oauth_config.is_configured():
        try:
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
                logger.warning("Gmail client not authenticated, falling back to payload generation")
        except Exception as e:
            logger.error(f"Error sending email via Gmail API: {e}")
            # Fall through to payload generation
            response_error = {
                "status": "error",
                "message": f"Failed to send email: {str(e)}",
                "fallback": "Generating payload for manual sending"
            }
    
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
    
    # Build OAuth authorization URL for the agent
    base_url = os.getenv('MCP_SERVER_BASE_URL', 'http://localhost:8000')
    from urllib.parse import urlencode
    oauth_params = {
        "response_type": "code",
        "scope": " ".join(GMAIL_SCOPES),
        "state": f"email_to_{user_id}"
    }
    oauth_url = f"{base_url}/authorize?{urlencode(oauth_params)}"
    
    # Prepare response with automation instructions for Toqan
    response = {
        "status": "authorization_required",
        "message": "OAuth authorization needed to send email. Please authorize Gmail access.",
        "theme": theme,
        "to": to,
        "subject": email_subject,
        
        # Toqan automation instructions - tells the agent to open a popup
        "agent_action": "open_browser_popup",
        "popup_url": oauth_url,
        "expected_result": "authorization_code",
        "automation_available": True,
        "action": "open_oauth_popup",
        "popup_instructions": {
            "url": oauth_url,
            "capture_callback": True,
            "auto_extract_code": True,
            "callback_url_pattern": f"{base_url}/oauth/callback*"
        },
        "browser_automation": {
            "supported": True,
            "method": "popup_window",
            "callback_handling": "automatic",
            "window_features": "width=500,height=600,popup=yes"
        },
        
        # After getting the code, agent should:
        "next_steps": {
            "1_exchange_code": {
                "description": "Exchange authorization code for access token",
                "endpoint": f"{base_url}/token",
                "method": "POST",
                "body": {
                    "code": "<code_from_callback>",
                    "grant_type": "authorization_code"
                }
            },
            "2_retry_send": {
                "description": "Call send_email again with the access_token",
                "tool": "send_email",
                "parameters": {
                    "to": to,
                    "theme": theme,
                    "subject": email_subject,
                    "cc": cc,
                    "bcc": bcc,
                    "access_token": "<token_from_step_1>",
                    "user_id": user_id
                }
            }
        },
        
        # Fallback for manual flow
        "manual_instructions": {
            "step_1": "User clicks the OAuth URL to authorize",
            "step_2": "User copies the authorization code from callback",
            "step_3": "Agent exchanges code for token",
            "step_4": "Agent retries send_email with access_token"
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
        
        params = {
            "response_type": "code",
            "state": f"user_{user_id}"
        }
        
        # Return our /authorize endpoint which will handle the redirect to Google
        auth_url = f"{base_url}/authorize?{urlencode(params)}"
        
        logger.info(f"Generated OAuth URL using MCP /authorize endpoint: {auth_url}")
        
        response = {
            "status": "success",
            "auth_url": auth_url,
            "discovery_endpoint": f"{base_url}/.well-known/oauth-authorization-server",
            "instructions": [
                "1. User should visit the auth_url in their browser",
                "2. They will be redirected to Google for authorization",
                "3. After granting permissions, they'll be redirected back with a code",
                "4. The code will be displayed in the callback page",
                "5. Call exchange_oauth_code tool with the code"
            ],
            "user_id": user_id,
            "note": "This URL uses the MCP server's /authorize endpoint for proper scope handling"
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
    
    Args:
        code: Authorization code from OAuth callback
        user_id: User identifier for token storage
        
    Returns:
        JSON with token information
    """
    logger.info(f"Exchanging OAuth code for user: {user_id}")
    
    try:
        gmail_client = GmailClient(user_id=user_id)
        token_data = gmail_client.exchange_code_for_token(code)
        
        response = {
            "status": "success",
            "message": "Token obtained and saved successfully",
            "user_id": user_id,
            "token_info": {
                "has_access_token": bool(token_data.get('access_token')),
                "has_refresh_token": bool(token_data.get('refresh_token')),
                "expires_in": token_data.get('expires_in')
            },
            "next_steps": [
                "Token is now saved and will be used automatically for send_email",
                "You can now call send_email without providing access_token parameter"
            ]
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error exchanging OAuth code: {e}")
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

mcp.tool(name="get_oauth_url")(_get_oauth_url)
mcp.tool(name="exchange_oauth_code")(_exchange_oauth_code)
mcp.tool(name="check_oauth_status")(_check_oauth_status)

if __name__ == "__main__":
    mcp.run()
