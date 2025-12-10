# HTML Email Rendering Guide for Agents

## Problem: Gmail Shows Raw HTML Instead of Rendered Email

When agents send HTML emails via Gmail API, they often see raw HTML tags in the email instead of beautiful rendered HTML. This happens because **Gmail API requires RFC 2822 format with MIME headers**.

## Root Cause

Gmail API needs emails in this format:
```
To: recipient@example.com
Subject: Email Subject
MIME-Version: 1.0
Content-Type: text/html; charset=utf-8

<html>
  <body>
    <!-- Your HTML content -->
  </body>
</html>
```

**Without the `Content-Type: text/html` header**, Gmail treats the email as plain text and shows raw HTML tags.

## Solution: Use `gmail_payload.raw` Field

The `generate_email_content` tool now returns a response with clear instructions:

### ✅ CORRECT Way (Renders as HTML)

```python
# 1. Call the tool
response = generate_email_content(to="user@example.com", theme="birthday")

# 2. Extract gmail_payload.raw (already base64url encoded with MIME headers)
gmail_payload = response["gmail_payload"]["raw"]

# 3. Send via Gmail API
import requests
result = requests.post(
    'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
    headers={'Authorization': 'Bearer YOUR_ACCESS_TOKEN'},
    json={'raw': gmail_payload}  # ← This has Content-Type: text/html header
)
```

### ❌ WRONG Way (Shows Raw HTML)

```python
# DON'T DO THIS - Missing MIME headers
response = generate_email_content(to="user@example.com", theme="birthday")

# This will show raw HTML because it lacks Content-Type header
result = send_email(
    to=response["to"],
    subject=response["subject"],
    body=response["debug_info"]["html_body_preview"]  # ← Missing MIME headers!
)
```

## Response Structure

The tool now returns a response with these key fields:

```json
{
  "status": "content_generated",
  "message": "⚠️ CRITICAL: Send using gmail_payload.raw field...",
  
  "gmail_payload": {
    "raw": "VG86IHRlc3RAZXhhbXBsZS5jb20K..."  // ← USE THIS!
  },
  
  "AGENT_MUST_READ": {
    "CRITICAL_WARNING": "DO NOT send html_body directly! It will render as plain text!",
    "CORRECT_METHOD": "Use gmail_payload.raw field - it contains base64url encoded message with Content-Type: text/html header",
    "WHY": "Gmail API requires RFC 2822 format with MIME headers...",
    "ENDPOINT": "POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
    "MIME_TYPE": "text/html; charset=utf-8 (already set in gmail_payload.raw)"
  },
  
  "preview_url": "http://localhost:8000/preview/email/birthday",
  
  "example_correct_usage": {
    "description": "How to send this email correctly via Gmail API",
    "code": "..."
  }
}
```

## Preview URL

You can preview the rendered HTML by opening the `preview_url` in a browser:
- `http://localhost:8000/preview/email/birthday`
- `http://localhost:8000/preview/email/pirate`
- `http://localhost:8000/preview/email/space`
- etc.

## What's in `gmail_payload.raw`?

It's a **base64url encoded** RFC 2822 message that looks like this when decoded:

```
To: test@example.com
Subject: 🎉 Happy Birthday! Let's Celebrate! 🎂
MIME-Version: 1.0
Content-Type: text/html; charset=utf-8    ← THIS IS CRITICAL!


<html>
<body style="font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 20px; padding: 40px;">
        <h1 style="color: #667eea; text-align: center; font-size: 48px;">🎉 Happy Birthday! 🎉</h1>
        <!-- Beautiful HTML content -->
    </div>
</body>
</html>
```

The **`Content-Type: text/html; charset=utf-8`** header tells Gmail to render it as HTML, not plain text.

## Summary

1. **Always use `gmail_payload.raw`** when sending via Gmail API
2. **Never send HTML directly** without MIME headers
3. **Use the preview URL** to see how the email will look
4. The `gmail_payload.raw` field is **already properly formatted** with all necessary headers

This ensures your beautiful themed emails render correctly in Gmail! 🎉
