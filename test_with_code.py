#!/usr/bin/env python3
"""
Complete OAuth flow with the authorization code.
"""
import httpx
import asyncio
import sys
import json

code = "4/0ATX87lNtNOVKv70CypqypCPSVugsfhTQLeabFdHhxKEil0nLixsi-7THij2eOaDeF_ebbw"

async def complete_flow():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("="*80)
        print("🔄 Exchanging authorization code for access token...")
        print("="*80)
        
        # Exchange code for token
        response = await client.post(
            "http://localhost:8000/token",
            data={
                'code': code,
                'grant_type': 'authorization_code'
            }
        )
        
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Token exchange failed!")
            print(f"Response: {response.text}")
            return False
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        
        print(f"✅ Got access token: {access_token[:30] if access_token else 'None'}...")
        print(f"✅ Got refresh token: {refresh_token[:30] if refresh_token else 'None'}...")
        
        # Step 2: Send test email
        print("\n" + "="*80)
        print("📧 Sending test email to andrew.napier@scrums.com...")
        print("="*80)
        
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
        
        # Parse result to check if sent
        try:
            result_data = json.loads(result)
            if result_data.get('status') == 'sent':
                print("\n" + "🎉 "*20)
                print("✅ EMAIL SENT SUCCESSFULLY!")
                print(f"Message ID: {result_data.get('message_id')}")
                print("Check your inbox at andrew.napier@scrums.com")
                print("🎉 "*20)
                return True
            else:
                print(f"\n⚠️  Status: {result_data.get('status')}")
                print(f"Message: {result_data.get('message')}")
                return False
        except:
            print("\n⚠️  Could not parse result")
            return False

success = asyncio.run(complete_flow())
sys.exit(0 if success else 1)
