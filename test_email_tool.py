#!/usr/bin/env python3
"""
Test script for the send_email MCP tool
Demonstrates generating themed emails
"""
import asyncio
import json
from lever_mcp.server import _send_email


async def test_email_themes():
    """Test different email themes"""
    
    themes = ["birthday", "pirate", "space", "medieval", "superhero", "tropical"]
    
    print("=" * 80)
    print("Testing Fun Email MCP Tool")
    print("=" * 80)
    
    for theme in themes:
        print(f"\n🎨 Testing theme: {theme.upper()}")
        print("-" * 80)
        
        result = await _send_email(
            to="friend@example.com",
            theme=theme
        )
        
        result_data = json.loads(result)
        print(f"✅ Status: {result_data['status']}")
        print(f"📧 Subject: {result_data['subject']}")
        print(f"📬 To: {result_data['to']}")
        print(f"📦 Gmail API Payload Ready: Yes")
        print(f"📝 Instructions provided: {len(result_data['instructions'])} steps")
        
    print("\n" + "=" * 80)
    print("✨ All themes tested successfully!")
    print("=" * 80)
    
    # Test with custom subject and CC/BCC
    print("\n🎯 Testing custom parameters...")
    print("-" * 80)
    
    result = await _send_email(
        to="recipient@example.com",
        theme="birthday",
        subject="🎂 Custom Birthday Message!",
        cc="cc@example.com",
        bcc="bcc@example.com"
    )
    
    result_data = json.loads(result)
    print(f"✅ Custom subject: {result_data['subject']}")
    print(f"📧 To: {result_data['to']}")
    
    print("\n" + "=" * 80)
    print("Available themes:", ", ".join(result_data['available_themes']))
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_email_themes())
