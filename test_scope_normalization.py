#!/usr/bin/env python3
"""
Test scope normalization for Google Workspace accounts
"""
import json

# Simulate what Google returns for a Workspace account
google_response = {
    "access_token": "ya29.test_token",
    "refresh_token": "1//test_refresh",
    "expires_in": 3599,
    "scope": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.compose https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.modify",
    "token_type": "Bearer"
}

GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
]

print("="*80)
print("🧪 SCOPE NORMALIZATION TEST")
print("="*80)

print("\n📥 Google's response (Workspace account with extra scopes):")
print(json.dumps(google_response, indent=2))

# Apply normalization logic
token_data = google_response.copy()
returned_scopes = token_data.get('scope', '')

requested_scopes = set(GMAIL_SCOPES)
actual_scopes = set(returned_scopes.split()) if returned_scopes else set()
extra_scopes = actual_scopes - requested_scopes

print(f"\n📊 Scope Analysis:")
print(f"   Requested: {requested_scopes}")
print(f"   Received: {actual_scopes}")
print(f"   Extra: {extra_scopes}")

if extra_scopes:
    print(f"\n⚠️  Google added extra scopes (Workspace policy)")
    print(f"   Normalizing for MCP compatibility...")
    
    # Normalize
    token_data['scope'] = ' '.join(GMAIL_SCOPES)
    token_data['_original_scope'] = returned_scopes
    token_data['_scope_note'] = 'Scope field normalized for MCP compatibility. Original scopes in _original_scope field.'

print("\n📤 Normalized response sent to Toqan:")
print(json.dumps(token_data, indent=2))

print("\n" + "="*80)
print("✅ RESULT")
print("="*80)
print("\nToqan will see:")
print(f"   scope: {token_data['scope']}")
print("\nThis matches what was requested, so no scope mismatch error!")
print("\nThe actual token still has all the scopes Google granted.")
print("="*80)
