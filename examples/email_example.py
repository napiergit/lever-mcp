#!/usr/bin/env python3
"""
Example: How to use the send_email MCP tool

This demonstrates how an AI agent would interact with the send_email tool
to generate and send themed emails.
"""
import asyncio
import json
from lever_mcp.server import _send_email


async def example_birthday_email():
    """Example: Send a birthday email"""
    print("=" * 80)
    print("Example 1: Birthday Email")
    print("=" * 80)
    
    result = await _send_email(
        to="friend@example.com",
        theme="birthday"
    )
    
    data = json.loads(result)
    
    print(f"\n✅ Email generated successfully!")
    print(f"📧 Subject: {data['subject']}")
    print(f"📬 To: {data['to']}")
    print(f"\n📋 Instructions for AI Agent:")
    for key, instruction in data['instructions'].items():
        print(f"  {key}: {instruction}")
    
    print(f"\n🎨 Available themes: {', '.join(data['available_themes'])}")
    
    # The Gmail API payload is ready to use
    print(f"\n📦 Gmail API Payload (truncated):")
    print(f"  {{")
    print(f"    'raw': '{data['gmail_api_payload']['raw'][:50]}...'")
    print(f"  }}")


async def example_pirate_email_with_cc():
    """Example: Send a pirate-themed email with CC"""
    print("\n\n" + "=" * 80)
    print("Example 2: Pirate Email with CC and Custom Subject")
    print("=" * 80)
    
    result = await _send_email(
        to="matey@example.com",
        theme="pirate",
        subject="⚓ Treasure Map Enclosed! ⚓",
        cc="crew@example.com"
    )
    
    data = json.loads(result)
    
    print(f"\n✅ Email generated successfully!")
    print(f"📧 Subject: {data['subject']}")
    print(f"📬 To: {data['to']}")
    print(f"\n💡 Agent Workflow:")
    print(f"  1. Check if Gmail OAuth credentials are available")
    print(f"  2. If yes: POST to Gmail API with the payload")
    print(f"  3. If no: Inform user that email template is ready")


async def example_space_email():
    """Example: Send a space-themed email"""
    print("\n\n" + "=" * 80)
    print("Example 3: Space-Themed Email")
    print("=" * 80)
    
    result = await _send_email(
        to="astronaut@example.com",
        theme="space"
    )
    
    data = json.loads(result)
    
    print(f"\n✅ Email generated successfully!")
    print(f"📧 Subject: {data['subject']}")
    print(f"🚀 Theme: {data['theme']}")
    
    print(f"\n📝 What the AI Agent receives:")
    print(f"  - status: {data['status']}")
    print(f"  - theme: {data['theme']}")
    print(f"  - to: {data['to']}")
    print(f"  - subject: {data['subject']}")
    print(f"  - gmail_api_payload: <base64 encoded email>")
    print(f"  - instructions: <step-by-step guide>")
    print(f"  - available_themes: <list of all themes>")
    print(f"  - email_preview: <preview information>")


async def main():
    """Run all examples"""
    await example_birthday_email()
    await example_pirate_email_with_cc()
    await example_space_email()
    
    print("\n\n" + "=" * 80)
    print("🎯 Key Points for AI Agents")
    print("=" * 80)
    print("""
1. The tool returns a complete Gmail API payload ready to send
2. No authentication is required to generate the email
3. The agent should check if it has Gmail OAuth credentials
4. If credentials exist, send via: POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send
5. If no credentials, inform the user the template is ready
6. All emails are HTML formatted with beautiful styling
7. Six themes available: birthday, pirate, space, medieval, superhero, tropical
8. Optional parameters: subject, cc, bcc for customization
    """)


if __name__ == "__main__":
    asyncio.run(main())
