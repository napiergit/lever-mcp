# Google_SendEmail Tool - HTML Email Issue

## Problem

The `Google_SendEmail` tool only accepts these parameters:
- `body`
- `recipient`
- `subject`
- `cc`
- `bcc`

**It does NOT have a parameter to specify that the body is HTML**, which means:
- When you send HTML content via the `body` parameter, Gmail treats it as plain text
- The email shows raw HTML tags like `<html>`, `<div>`, `<h1>`, etc. instead of rendering them

## Why This Happens

Gmail needs to know the content type of the email body. Without a `Content-Type: text/html` header, Gmail assumes the body is plain text and displays it literally.

## Solutions

### Solution 1: Check if Google_SendEmail Has Hidden HTML Parameters

The tool might support HTML through one of these parameter names:
- `isHtml` (boolean)
- `is_html` (boolean)
- `html` (boolean)
- `contentType` (string: "text/html")
- `mimeType` (string: "text/html")
- `content_type` (string: "text/html")

**Try calling it with one of these:**
```json
{
  "recipient": "user@example.com",
  "subject": "Test",
  "body": "<html><body><h1>Hello</h1></body></html>",
  "isHtml": true
}
```

### Solution 2: Use Gmail API Directly with `raw` Field (Recommended)

Instead of using `Google_SendEmail`, call the Gmail API directly:

```
POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "raw": "<base64url_encoded_message_from_gmail_payload.raw>"
}
```

The `generate_email_content` tool returns a `gmail_payload.raw` field that contains the properly formatted message with HTML headers.

### Solution 3: Use the Preview URL

If you can't send HTML emails, provide the user with the preview URL:
```
http://localhost:8000/preview/email/birthday?to=user@example.com
```

The user can open this in their browser to see the rendered HTML email.

### Solution 4: Request a Different Tool

Ask the user if they have access to a different email-sending tool that supports HTML, such as:
- A tool that accepts `mimeType` or `contentType` parameters
- Direct Gmail API access
- A custom MCP tool that supports HTML

## What Our Tool Returns

The `generate_email_content` tool now returns multiple fields to support different scenarios:

```json
{
  "body": "<html>...</html>",
  "recipient": "user@example.com",
  "subject": "Email Subject",
  
  // HTML indicators (try passing these to Google_SendEmail)
  "isHtml": true,
  "is_html": true,
  "html": true,
  "contentType": "text/html",
  "mimeType": "text/html",
  
  // Gmail API format (guaranteed to work)
  "gmail_payload": {
    "raw": "VG86IHVzZXJAZXhhbXBsZS5jb20K..."
  },
  
  // Preview URL
  "preview_url": "http://localhost:8000/preview/email/birthday"
}
```

## Recommendation

**If `Google_SendEmail` doesn't support any HTML parameters**, you should:

1. Tell the user that their `Google_SendEmail` tool doesn't support HTML emails
2. Provide them with the preview URL so they can see the rendered email
3. Suggest they use a tool that supports HTML or give you direct Gmail API access

## Testing

To test if `Google_SendEmail` supports HTML, try sending a simple HTML email:

```json
{
  "recipient": "test@example.com",
  "subject": "HTML Test",
  "body": "<h1 style='color: red;'>This should be red and large</h1>",
  "isHtml": true
}
```

If the email shows "This should be red and large" in large red text, it works!
If it shows the raw HTML tags, the tool doesn't support HTML.
