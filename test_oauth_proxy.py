#!/usr/bin/env python3
"""Test OAuth proxy configuration."""
import os
import sys

# Set test environment variables BEFORE importing
os.environ['GOOGLE_CLIENT_ID'] = 'test-client-id.apps.googleusercontent.com'
os.environ['GOOGLE_CLIENT_SECRET'] = 'test-secret'
os.environ['MCP_SERVER_BASE_URL'] = 'http://localhost:8080'

# Now import
from lever_mcp.server import mcp, auth_provider

print("=" * 60)
print("OAuth Proxy Configuration Test")
print("=" * 60)

print(f"\nAuth provider: {auth_provider}")
print(f"Auth provider type: {type(auth_provider)}")

if auth_provider:
    print("\n✅ OAuth proxy is configured!")
    
    # Get well-known routes
    routes = auth_provider.get_well_known_routes('/mcp')
    print(f"\nWell-known routes ({len(routes)}):")
    for route in routes:
        print(f"  - {route.path}")
    
    # Get all routes
    all_routes = auth_provider.get_routes('/mcp')
    print(f"\nAll OAuth routes ({len(all_routes)}):")
    for route in all_routes:
        print(f"  - {route.path}")
else:
    print("\n❌ OAuth proxy is NOT configured")
    print("Make sure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set")

print("\n" + "=" * 60)
