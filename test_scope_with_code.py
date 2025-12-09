#!/usr/bin/env python3
"""
Test to see what scopes Google actually returns
"""
import httpx
import asyncio
from urllib.parse import urlparse, parse_qs

callback_url = "http://localhost:8000/oauth/callback?state=test_scope_check&code=4/0ATX87lNmtadqBwfWvuObXBDom0uyTvO8ox6Lffj8q4uE5lkW4R6hHnOXDysaXLYvNAkh8g&scope=https://www.googleapis.com/auth/gmail.send%20https://www.googleapis.com/auth/gmail.compose"

# Parse the code
parsed = urlparse(callback_url)
params = parse_qs(parsed.query)

code = params['code'][0]
callback_scope = params['scope'][0]

print("="*80)
print("🔍 SCOPE ANALYSIS")
print("="*80)
print(f"\n📥 Scope from callback URL:")
print(f"   {callback_scope}")
print(f"\n📝 Scopes in callback:")
for scope in callback_scope.split():
    print(f"   - {scope}")

print(f"\n✅ Authorization code: {code[:30]}...")

# Step 2: Exchange code for token and see what scopes Google returns
async def exchange_code():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n" + "="*80)
        print("🔄 Exchanging code for token...")
        print("="*80)
        
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
            return
        
        token_data = response.json()
        
        print("\n" + "="*80)
        print("📊 TOKEN RESPONSE FROM GOOGLE")
        print("="*80)
        
        # Check what scopes Google returned
        returned_scopes = token_data.get('scope', '')
        print(f"\n🔍 Scopes returned by Google in token response:")
        print(f"   {returned_scopes}")
        
        print(f"\n📝 Scopes breakdown:")
        for scope in returned_scopes.split():
            print(f"   - {scope}")
        
        print(f"\n✅ Access token: {token_data.get('access_token', 'None')[:30]}...")
        print(f"✅ Refresh token: {token_data.get('refresh_token', 'None')[:30]}...")
        print(f"✅ Expires in: {token_data.get('expires_in')} seconds")
        
        # Compare requested vs returned
        requested = [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.compose"
        ]
        callback_scopes = callback_scope.split()
        returned = returned_scopes.split()
        
        print("\n" + "="*80)
        print("⚖️  SCOPE COMPARISON")
        print("="*80)
        print(f"\n✅ Requested scopes: {len(requested)}")
        for s in requested:
            print(f"   - {s}")
        
        print(f"\n📥 Callback scopes: {len(callback_scopes)}")
        for s in callback_scopes:
            print(f"   - {s}")
        
        print(f"\n📥 Token response scopes: {len(returned)}")
        for s in returned:
            print(f"   - {s}")
        
        extra_in_callback = [s for s in callback_scopes if s not in requested]
        extra_in_token = [s for s in returned if s not in requested]
        
        if extra_in_callback:
            print(f"\n⚠️  EXTRA SCOPES IN CALLBACK: {len(extra_in_callback)}")
            for s in extra_in_callback:
                print(f"   - {s}")
        
        if extra_in_token:
            print(f"\n⚠️  EXTRA SCOPES IN TOKEN RESPONSE: {len(extra_in_token)}")
            for s in extra_in_token:
                print(f"   - {s}")
        
        if not extra_in_callback and not extra_in_token:
            print(f"\n✅ No extra scopes - exact match!")
        
        # Now test sending an email
        print("\n" + "="*80)
        print("📧 Testing email send with this token...")
        print("="*80)
        
        import sys
        sys.path.insert(0, 'src')
        from lever_mcp.server import _send_email
        
        result = await _send_email(
            to="andrew.napier@scrums.com",
            theme="space",
            subject="🔍 Scope Test Email",
            access_token=token_data.get('access_token'),
            user_id="scope_test"
        )
        
        print("\n📧 Email result:")
        print(result)

asyncio.run(exchange_code())
