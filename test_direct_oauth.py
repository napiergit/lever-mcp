#!/usr/bin/env python3
"""
Direct OAuth flow test - opens browser and completes the flow.
"""
import webbrowser
import sys

# Step 1: Open authorization URL
auth_url = "http://localhost:8000/authorize?response_type=code&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.send+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.compose&state=test_state_12345"

print("="*80)
print("🚀 OAUTH FLOW TEST")
print("="*80)
print("\nStep 1: Opening browser for Google authorization...")
print(f"URL: {auth_url}\n")

webbrowser.open(auth_url)

print("="*80)
print("📋 INSTRUCTIONS")
print("="*80)
print("\n1. Your browser should have opened to Google's authorization page")
print("2. Sign in with your Google account")
print("3. Grant permissions to the application")
print("4. You'll be redirected to a callback URL")
print("5. Copy the ENTIRE callback URL from your browser address bar")
print("\nThe URL will look like:")
print("http://localhost:8000/oauth/callback?code=4/0A...&state=test_state_12345")
print("\n" + "="*80)

callback_url = input("\n📋 Paste the callback URL here: ").strip()

# Parse the code
from urllib.parse import urlparse, parse_qs
parsed = urlparse(callback_url)
params = parse_qs(parsed.query)

if 'error' in params:
    print(f"\n❌ Error: {params['error'][0]}")
    if 'error_description' in params:
        print(f"   {params['error_description'][0]}")
    sys.exit(1)

if 'code' not in params:
    print("\n❌ No authorization code found in URL!")
    sys.exit(1)

code = params['code'][0]
print(f"\n✅ Got authorization code: {code[:20]}...")

# Step 2: Exchange code for token
print("\nStep 2: Exchanging code for access token...")

import httpx
import asyncio

async def exchange_and_send():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Exchange code
        response = await client.post(
            "http://localhost:8000/token",
            data={
                'code': code,
                'grant_type': 'authorization_code'
            }
        )
        
        if response.status_code != 200:
            print(f"\n❌ Token exchange failed: {response.status_code}")
            print(response.text)
            return False
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        
        print(f"✅ Got access token: {access_token[:20] if access_token else 'None'}...")
        
        # Step 3: Send test email
        print(f"\nStep 3: Sending test email to andrew.napier@scrums.com...")
        
        # Import the send_email function
        sys.path.insert(0, 'src')
        from lever_mcp.server import _send_email
        
        result = await _send_email(
            to="andrew.napier@scrums.com",
            theme="space",
            subject="🚀 Local OAuth Test Success!",
            access_token=access_token,
            user_id="test_user"
        )
        
        print("\n" + "="*80)
        print("📧 EMAIL RESULT")
        print("="*80)
        print(result)
        print("="*80)
        
        return True

success = asyncio.run(exchange_and_send())

if success:
    print("\n" + "🎉 "*20)
    print("SUCCESS! Check your email at andrew.napier@scrums.com")
    print("🎉 "*20)
else:
    print("\n" + "❌ "*20)
    print("FAILED - See errors above")
    print("❌ "*20)
