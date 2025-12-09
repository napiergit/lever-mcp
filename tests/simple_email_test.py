"""
Simple email test using stored OAuth token.
Run this after completing the OAuth flow with mock_toqan_client.py
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from lever_mcp.gmail_client import GmailClient
from lever_mcp.oauth_config import oauth_config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def send_test_email(to_email: str, theme: str = "space"):
    """Send a test email using stored OAuth token."""
    
    logger.info("🚀 Sending test email...")
    logger.info(f"   To: {to_email}")
    logger.info(f"   Theme: {theme}")
    
    # Check if OAuth is configured
    if not oauth_config.is_configured():
        logger.error("❌ OAuth not configured!")
        logger.error("   Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
        return False
    
    # Create Gmail client (will load stored token)
    client = GmailClient(user_id="default")
    
    if not client.is_authenticated():
        logger.error("❌ Not authenticated!")
        logger.error("   Please run the OAuth flow first:")
        logger.error("   python tests/mock_toqan_client.py")
        return False
    
    logger.info("✅ Authenticated with stored token")
    
    # Email themes
    themes = {
        "space": {
            "subject": "🚀 Test Email from Local OAuth Flow",
            "body": """
<html>
<body style="font-family: Arial, sans-serif; background: #000; padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%); border-radius: 20px; padding: 40px;">
        <h1 style="color: #fff; text-align: center; font-size: 42px;">🚀 Success! 🌌</h1>
        <p style="font-size: 18px; color: #e0e0e0; line-height: 1.6;">
            Your local OAuth flow is working perfectly! 🎉
        </p>
        <p style="font-size: 16px; color: #d0d0d0; line-height: 1.6;">
            This email was sent using:
        </p>
        <ul style="color: #d0d0d0; font-size: 16px;">
            <li>✅ Local MCP server (http://localhost:8000)</li>
            <li>✅ Google OAuth 2.0 authentication</li>
            <li>✅ Gmail API</li>
            <li>✅ On-behalf-of token flow</li>
        </ul>
        <div style="text-align: center; margin: 30px 0; font-size: 50px;">
            🌟 🪐 🛸 🌙 ✨
        </div>
        <p style="font-size: 14px; color: #aaa; text-align: center;">
            You're ready to deploy to production! 🚀
        </p>
    </div>
</body>
</html>
"""
        },
        "party": {
            "subject": "🎉 OAuth Test Successful!",
            "body": """
<html>
<body style="font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 20px; padding: 40px;">
        <h1 style="color: #667eea; text-align: center; font-size: 48px;">🎉 It Works! 🎉</h1>
        <p style="font-size: 18px; color: #333; line-height: 1.6; text-align: center;">
            Your OAuth integration is working perfectly!
        </p>
        <div style="text-align: center; margin: 30px 0; font-size: 60px;">
            🎊 🎈 🎁 🎂 🎉
        </div>
    </div>
</body>
</html>
"""
        }
    }
    
    template = themes.get(theme, themes["space"])
    
    try:
        result = await client.send_email(
            to=to_email,
            subject=template["subject"],
            body=template["body"],
            is_html=True
        )
        
        logger.info("✅ Email sent successfully!")
        logger.info(f"   Message ID: {result['message_id']}")
        logger.info(f"   To: {result['to']}")
        logger.info(f"   Subject: {result['subject']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        return False


async def main():
    """Main function."""
    # Load environment variables
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
    
    print("\n" + "="*80)
    print("📧 Simple Email Test")
    print("="*80 + "\n")
    
    # Get email address
    if len(sys.argv) > 1:
        to_email = sys.argv[1]
    else:
        to_email = input("Enter your email address: ").strip()
    
    # Get theme
    print("\nAvailable themes: space, party")
    theme = input("Enter theme (default: space): ").strip() or "space"
    
    print("\n" + "="*80)
    
    success = await send_test_email(to_email, theme)
    
    if success:
        print("\n" + "🎉 " * 20)
        print("SUCCESS! Check your email inbox!")
        print("🎉 " * 20 + "\n")
    else:
        print("\n" + "❌ " * 20)
        print("FAILED! Check the logs above for details.")
        print("❌ " * 20 + "\n")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
