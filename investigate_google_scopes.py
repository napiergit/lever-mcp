#!/usr/bin/env python3
"""
Deep investigation into Google OAuth scope behavior
"""
import webbrowser
import time

# Test different scope combinations to see what Google returns

test_cases = [
    {
        "name": "Test 1: Only gmail.send",
        "scopes": ["https://www.googleapis.com/auth/gmail.send"],
    },
    {
        "name": "Test 2: Only gmail.compose", 
        "scopes": ["https://www.googleapis.com/auth/gmail.compose"],
    },
    {
        "name": "Test 3: Both gmail.send and gmail.compose",
        "scopes": [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.compose"
        ],
    },
    {
        "name": "Test 4: Gmail full access (to see if this is what's being requested)",
        "scopes": ["https://mail.google.com/"],
    },
]

print("="*80)
print("🔬 GOOGLE OAUTH SCOPE INVESTIGATION")
print("="*80)
print("\nThis will help us understand what scopes Google is actually granting.")
print("\nWe'll test different scope combinations and see what Google returns.")
print("\n" + "="*80)

for i, test in enumerate(test_cases, 1):
    print(f"\n{test['name']}")
    print(f"Requesting: {test['scopes']}")
    
    from urllib.parse import urlencode
    scope_str = " ".join(test['scopes'])
    
    # Load env to get client ID
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    redirect_uri = os.getenv('MCP_SERVER_BASE_URL', 'http://localhost:8000') + '/oauth/callback'
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope_str,
        "access_type": "offline",
        "prompt": "consent",
        "state": f"test_{i}"
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
    
    print(f"\nURL: {auth_url[:120]}...")
    print("\nDo you want to test this? (y/n): ", end="")
    
    choice = input().strip().lower()
    if choice == 'y':
        print("Opening browser...")
        webbrowser.open(auth_url)
        print("\nAfter authorizing, check the callback URL.")
        print("Look at the 'scope' parameter in the URL.")
        print("\nCallback URL: ", end="")
        callback = input().strip()
        
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(callback)
        params = parse_qs(parsed.query)
        
        if 'scope' in params:
            returned_scopes = params['scope'][0]
            print(f"\n✅ Scopes Google returned:")
            for scope in returned_scopes.split():
                print(f"   - {scope}")
            
            requested_set = set(test['scopes'])
            returned_set = set(returned_scopes.split())
            
            extra = returned_set - requested_set
            if extra:
                print(f"\n⚠️  EXTRA SCOPES ADDED BY GOOGLE:")
                for scope in extra:
                    print(f"   - {scope}")
            else:
                print(f"\n✅ Exact match - no extra scopes!")
        
        print("\n" + "="*80)
        print("Press Enter to continue to next test...")
        input()
    else:
        print("Skipped.")

print("\n" + "="*80)
print("Investigation complete!")
print("="*80)
