#!/usr/bin/env python3
"""
Test to see what scopes Google actually returns
"""
import webbrowser
import httpx
import asyncio
from urllib.parse import urlparse, parse_qs

# Step 1: Open authorization URL
auth_url = "http://localhost:8000/authorize?response_type=code&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.send+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.compose&state=test_scope_check"

print("="*80)
print("🔍 SCOPE TESTING")
print("="*80)
print("\nStep 1: Opening browser for Google authorization...")
print(f"Requesting scopes:")
print("  - https://www.googleapis.com/auth/gmail.send")
print("  - https://www.googleapis.com/auth/gmail.compose")
print()

webbrowser.open(auth_url)

print("="*80)
print("After authorizing, paste the callback URL here:")
print("="*80)
callback_url = input("\nCallback URL: ").strip()

# Parse the code
parsed = urlparse(callback_url)
params = parse_qs(parsed.query)

if 'error' in params:
    print(f"\n❌ Error: {params['error'][0]}")
    exit(1)

if 'code' not in params:
    print("\n❌ No authorization code found!")
    exit(1)

code = params['code'][0]
print(f"\n✅ Got authorization code: {code[:30]}...")

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
        print(f"\n🔍 Scopes returned by Google:")
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
        returned = returned_scopes.split()
        
        print("\n" + "="*80)
        print("⚖️  SCOPE COMPARISON")
        print("="*80)
        print(f"\n✅ Requested scopes: {len(requested)}")
        for s in requested:
            print(f"   - {s}")
        
        print(f"\n📥 Returned scopes: {len(returned)}")
        for s in returned:
            print(f"   - {s}")
        
        extra_scopes = [s for s in returned if s not in requested]
        if extra_scopes:
            print(f"\n⚠️  EXTRA SCOPES ADDED BY GOOGLE: {len(extra_scopes)}")
            for s in extra_scopes:
                print(f"   - {s}")
        else:
            print(f"\n✅ No extra scopes - exact match!")

asyncio.run(exchange_code())
