from fastmcp import FastMCP
from lever_mcp.client import LeverClient
from typing import Optional, Dict, Any
import logging
import json
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("lever-mcp")

# Initialize FastMCP server
mcp = FastMCP("lever")

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

async def _send_email(to: str, theme: str, subject: Optional[str] = None, cc: Optional[str] = None, bcc: Optional[str] = None) -> str:
    """
    Generate a cool email and return the Gmail API payload.
    No authentication required - returns the payload that can be used with a valid OAuth token.
    """
    logger.info(f"Generating themed email: to={to}, theme={theme}")
    
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
        "status": "success",
        "theme": theme,
        "to": to,
        "subject": email_subject,
        "gmail_api_payload": gmail_payload,
        "instructions": {
            "step_1": "If you have Gmail OAuth credentials, use the Gmail API to send this email",
            "step_2": "Make a POST request to: https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            "step_3": "Include your OAuth token in the Authorization header: 'Bearer YOUR_ACCESS_TOKEN'",
            "step_4": "Send the 'gmail_api_payload' as the request body",
            "step_5": "If you don't have credentials, inform the user that the email template has been generated and they need to provide OAuth credentials",
            "alternative": "You can also copy the email body and send it manually through your email client"
        },
        "available_themes": list(email_templates.keys()),
        "email_preview": {
            "subject": email_subject,
            "body_preview": "HTML email with themed styling (view in email client for full effect)"
        }
    }
    
    return json.dumps(response, indent=2)

# Register tools
mcp.tool(name="list_candidates")(_list_candidates)
mcp.tool(name="get_candidate")(_get_candidate)
mcp.tool(name="create_requisition")(_create_requisition)
mcp.tool(name="send_email")(_send_email)

if __name__ == "__main__":
    mcp.run()
