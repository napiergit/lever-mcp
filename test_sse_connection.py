#!/usr/bin/env python3
"""Test script to verify SSE connection to the Lever MCP server."""

import requests
import json

def test_sse_connection():
    """Test the SSE endpoint connection."""
    url = "http://localhost:8005/sse"
    
    print(f"Testing connection to {url}...")
    
    try:
        # Make a simple GET request to check if the endpoint is accessible
        response = requests.get(url, stream=True, timeout=5)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("\n✓ Server is responding correctly!")
            print("\nFirst few bytes of response:")
            # Read a small amount of data
            for i, chunk in enumerate(response.iter_content(chunk_size=100)):
                if i < 3:  # Only show first 3 chunks
                    print(f"Chunk {i}: {chunk[:100]}")
                else:
                    break
        else:
            print(f"\n✗ Unexpected status code: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("✗ Connection timed out")
    except requests.exceptions.ConnectionError as e:
        print(f"✗ Connection error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_sse_connection()
