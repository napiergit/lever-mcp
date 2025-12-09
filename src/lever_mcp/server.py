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
    
    # Get base URL from environment or use default
    base_url = os.getenv('MCP_SERVER_BASE_URL', 'http://localhost:8080')
    
    # Create OAuth proxy for Google
    # OAuthProxy validates its own issued tokens, so we pass it to itself as token_verifier
    # We need to create it in two steps to avoid circular reference
    auth_provider = OAuthProxy.__new__(OAuthProxy)
    # Initialize base attributes first
    auth_provider.base_url = base_url
    auth_provider.required_scopes = GMAIL_SCOPES
    # Now initialize the full proxy
    OAuthProxy.__init__(
        auth_provider,
        upstream_authorization_endpoint="https://accounts.google.com/o/oauth2/auth",
        upstream_token_endpoint="https://oauth2.googleapis.com/token",
        upstream_client_id=oauth_config.client_id,
        upstream_client_secret=oauth_config.client_secret,
        token_verifier=auth_provider,  # Proxy validates its own tokens
        base_url=base_url,
        redirect_path="/auth/callback",
        valid_scopes=GMAIL_SCOPES,
        forward_pkce=True,
        extra_authorize_params={
            "access_type": "offline",  # Request refresh token
            "prompt": "consent"  # Always show consent screen
        }
    )
    logger.info(f"OAuth proxy configured with base URL: {base_url}")
else:
    logger.warning("OAuth not configured - email sending will return payloads only")
    logger.warning("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to enable OAuth")

# Initialize FastMCP server with OAuth
# Pass auth_provider so Toqan can discover OAuth and authenticate users
mcp = FastMCP("lever", auth=auth_provider)

# Add a custom route for the root protected resource metadata
# Toqan looks for this at /.well-known/oauth-protected-resource (without /mcp suffix)
if auth_provider:
    from starlette.responses import JSONResponse
    from starlette.requests import Request
    
    @mcp.custom_route("/.well-known/oauth-protected-resource", methods=["GET"])
    async def oauth_protected_resource_root(request: Request):
        """Protected resource metadata at root level for Toqan compatibility."""
        return JSONResponse({
            "resource": str(auth_provider.base_url),
            "authorization_servers": [str(auth_provider.base_url)],
            "scopes_supported": GMAIL_SCOPES,
            "bearer_methods_supported": ["header"]
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
    
    Args:
        to: Recipient email address
        theme: Email theme (birthday, pirate, space, medieval, superhero, tropical)
        subject: Optional custom subject (uses theme default if not provided)
        cc: Optional CC recipients
        bcc: Optional BCC recipients
        access_token: OAuth access token from agent (on-behalf-of flow)
        user_id: User identifier for token storage
        
    Returns:
        JSON response with email status and details
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
    
    # Prepare response with instructions
    response = {
        "status": "payload_generated",
        "message": "Email payload generated. Provide access_token parameter to send automatically.",
        "theme": theme,
        "to": to,
        "subject": email_subject,
        "gmail_api_payload": gmail_payload,
        "oauth_setup": {
            "configured": oauth_config.is_configured(),
            "instructions": "To enable automatic sending, provide access_token parameter or set up OAuth credentials"
        },
        "agent_instructions": {
            "step_1": "Agent should obtain OAuth token from user via Toqan",
            "step_2": "Call this tool again with access_token parameter",
            "step_3": "Email will be sent automatically via Gmail API",
            "alternative": "Or make POST request to: https://gmail.googleapis.com/gmail/v1/users/me/messages/send with the payload"
        },
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
    User should visit this URL to grant permissions.
    
    Args:
        user_id: User identifier for token storage
        
    Returns:
        JSON with authorization URL
    """
    logger.info(f"Generating OAuth URL for user: {user_id}")
    
    try:
        if not oauth_config.is_configured():
            return json.dumps({
                "status": "error",
                "message": "OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
            }, indent=2)
        
        gmail_client = GmailClient(user_id=user_id)
        auth_url = gmail_client.get_auth_url()
        
        response = {
            "status": "success",
            "auth_url": auth_url,
            "instructions": [
                "1. User should visit the auth_url in their browser",
                "2. Grant permissions to the application",
                "3. User will be redirected with an authorization code",
                "4. Extract the 'code' parameter from the redirect URL",
                "5. Call exchange_oauth_code tool with the code"
            ],
            "user_id": user_id
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
