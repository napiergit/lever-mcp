#!/usr/bin/env python3
"""
Test script for Gmail OAuth integration.
This script helps test the OAuth flow and email sending.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lever_mcp.gmail_client import GmailClient
from lever_mcp.oauth_config import oauth_config


async def test_oauth_flow():
    """Test the complete OAuth flow."""
    print("=" * 60)
    print("Gmail OAuth Integration Test")
    print("=" * 60)
    
    # Check configuration
    print("\n1. Checking OAuth configuration...")
    if not oauth_config.is_configured():
        print("❌ OAuth not configured!")
        print("\nPlease set the following environment variables:")
        print("  - GOOGLE_CLIENT_ID")
        print("  - GOOGLE_CLIENT_SECRET")
        print("\nYou can copy .env.example to .env and fill in your credentials.")
        return False
    
    print("✅ OAuth configured")
    print(f"   Client ID: {oauth_config.client_id[:20]}...")
    print(f"   Redirect URI: {oauth_config.redirect_uri}")
    
    # Check existing authentication
    print("\n2. Checking existing authentication...")
    client = GmailClient(user_id="test_user")
    
    if client.is_authenticated():
        print("✅ Already authenticated!")
        print("   You can send emails without re-authenticating.")
        
        # Test email sending
        choice = input("\nWould you like to send a test email? (y/n): ")
        if choice.lower() == 'y':
            to_email = input("Enter recipient email: ")
            await send_test_email(client, to_email)
        return True
    
    print("⚠️  Not authenticated yet")
    
    # Start OAuth flow
    print("\n3. Starting OAuth flow...")
    print("\nGenerating authorization URL...")
    
    try:
        auth_url = client.get_auth_url()
        print("\n" + "=" * 60)
        print("AUTHORIZATION URL:")
        print("=" * 60)
        print(auth_url)
        print("=" * 60)
        
        print("\nInstructions:")
        print("1. Copy the URL above and open it in your browser")
        print("2. Sign in with your Google account")
        print("3. Grant the requested permissions")
        print("4. You'll be redirected to a URL with a 'code' parameter")
        print("5. Copy the entire redirect URL and paste it below")
        
        redirect_url = input("\nPaste the redirect URL here: ").strip()
        
        # Extract code from URL
        if "code=" in redirect_url:
            code = redirect_url.split("code=")[1].split("&")[0]
        else:
            print("❌ Could not find authorization code in URL")
            return False
        
        print("\n4. Exchanging code for token...")
        token_data = client.exchange_code_for_token(code)
        
        print("✅ Token obtained successfully!")
        print(f"   Access token: {token_data['access_token'][:20]}...")
        print(f"   Has refresh token: {bool(token_data.get('refresh_token'))}")
        
        # Test email sending
        choice = input("\nWould you like to send a test email? (y/n): ")
        if choice.lower() == 'y':
            to_email = input("Enter recipient email: ")
            await send_test_email(client, to_email)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during OAuth flow: {e}")
        return False


async def send_test_email(client: GmailClient, to_email: str):
    """Send a test email."""
    print("\n5. Sending test email...")
    
    themes = ["birthday", "pirate", "space", "medieval", "superhero", "tropical"]
    print("\nAvailable themes:")
    for i, theme in enumerate(themes, 1):
        print(f"  {i}. {theme}")
    
    theme_choice = input(f"\nSelect theme (1-{len(themes)}) or press Enter for 'birthday': ").strip()
    
    if theme_choice and theme_choice.isdigit():
        theme_idx = int(theme_choice) - 1
        if 0 <= theme_idx < len(themes):
            theme = themes[theme_idx]
        else:
            theme = "birthday"
    else:
        theme = "birthday"
    
    subject = f"Test Email - {theme.title()} Theme"
    
    # Get theme body
    email_templates = {
        "birthday": "🎉 Happy Birthday! This is a test email with birthday theme! 🎂",
        "pirate": "⚓ Ahoy Matey! This be a test email from the high seas! 🏴‍☠️",
        "space": "🚀 Greetings from space! This is a cosmic test email! 🌌",
        "medieval": "⚔️ Hear ye! This is a royal test proclamation! 🏰",
        "superhero": "💥 SUPERHERO ALERT! This is a super test email! 🦸",
        "tropical": "🌴 Aloha! This is a tropical test email! 🌺"
    }
    
    body = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h1>Test Email - {theme.title()} Theme</h1>
    <p>{email_templates.get(theme, 'Test email')}</p>
    <p>This email was sent via the Lever MCP Gmail OAuth integration.</p>
    <hr>
    <p style="color: #666; font-size: 12px;">
        Sent from Lever MCP Server<br>
        Theme: {theme}<br>
        Test Mode
    </p>
</body>
</html>
"""
    
    try:
        result = await client.send_email(
            to=to_email,
            subject=subject,
            body=body,
            is_html=True
        )
        
        print("\n✅ Email sent successfully!")
        print(f"   Message ID: {result['message_id']}")
        print(f"   To: {result['to']}")
        print(f"   Subject: {result['subject']}")
        
    except Exception as e:
        print(f"\n❌ Error sending email: {e}")


async def test_with_token():
    """Test with an existing access token."""
    print("=" * 60)
    print("Test with Existing Access Token")
    print("=" * 60)
    
    print("\nThis mode is for testing the on-behalf-of flow.")
    print("Paste your OAuth access token below:")
    
    access_token = input("Access token: ").strip()
    
    if not access_token:
        print("❌ No token provided")
        return
    
    print("\nCreating Gmail client with provided token...")
    client = GmailClient(access_token=access_token, user_id="token_test")
    
    if not client.is_authenticated():
        print("❌ Token is invalid or expired")
        return
    
    print("✅ Token is valid!")
    
    to_email = input("\nEnter recipient email: ")
    await send_test_email(client, to_email)


def main():
    """Main entry point."""
    print("\nGmail OAuth Test Script")
    print("\nSelect test mode:")
    print("1. Complete OAuth flow (recommended for first time)")
    print("2. Test with existing access token (for on-behalf-of flow)")
    print("3. Check authentication status")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(test_oauth_flow())
    elif choice == "2":
        asyncio.run(test_with_token())
    elif choice == "3":
        client = GmailClient(user_id="test_user")
        print(f"\nAuthentication status: {'✅ Authenticated' if client.is_authenticated() else '❌ Not authenticated'}")
        print(f"OAuth configured: {'✅ Yes' if oauth_config.is_configured() else '❌ No'}")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
