#!/usr/bin/env python3
"""
Test the generate_email_content response to verify it has clear instructions
for agents on how to send HTML emails properly.
"""
import json
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from lever_mcp.server import _generate_email_content

async def test_response():
    """Test that the response has clear HTML rendering instructions."""
    
    print("=" * 80)
    print("Testing generate_email_content response structure")
    print("=" * 80)
    
    # Generate email content
    result = await _generate_email_content(
        to="test@example.com",
        theme="birthday",
        subject=None,
        cc=None,
        bcc=None
    )
    
    # Parse the JSON response
    response = json.loads(result)
    
    # Check critical fields
    print("\n✅ CRITICAL FIELDS CHECK:")
    print("-" * 80)
    
    if "gmail_payload" in response:
        print("✓ gmail_payload field present")
        if "raw" in response["gmail_payload"]:
            print("✓ gmail_payload.raw field present (base64url encoded)")
            raw_length = len(response["gmail_payload"]["raw"])
            print(f"  Length: {raw_length} characters")
    else:
        print("✗ MISSING gmail_payload field!")
    
    if "AGENT_MUST_READ" in response:
        print("✓ AGENT_MUST_READ instructions present")
        agent_instructions = response["AGENT_MUST_READ"]
        print(f"  - CRITICAL_WARNING: {agent_instructions.get('CRITICAL_WARNING', 'N/A')}")
        print(f"  - CORRECT_METHOD: {agent_instructions.get('CORRECT_METHOD', 'N/A')[:80]}...")
        print(f"  - MIME_TYPE: {agent_instructions.get('MIME_TYPE', 'N/A')}")
    else:
        print("✗ MISSING AGENT_MUST_READ field!")
    
    if "preview_url" in response:
        print(f"✓ preview_url present: {response['preview_url']}")
    
    print("\n📋 FULL RESPONSE STRUCTURE:")
    print("-" * 80)
    print(json.dumps(response, indent=2))
    
    print("\n" + "=" * 80)
    print("SUMMARY: Agent should use gmail_payload.raw field to send HTML email")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_response())
