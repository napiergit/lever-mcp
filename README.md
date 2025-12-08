# Lever MCP Server

An MCP server for interacting with the [Lever.co](https://www.lever.co/) API. This server allows AI agents to list candidates, retrieve candidate details, create job requisitions, and send fun themed emails.

## Prerequisites

- Python 3.10 or higher
- A Lever API Key (generated from Lever Settings > Integrations and API > API Credentials)

## Installation

1.  Clone this repository.
2.  Create a virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -e .
    ```

## Configuration

The server requires the following environment variables:

- `LEVER_API_KEY`: Your Lever API key.
- `LEVER_API_BASE_URL` (Optional): The base URL for the API. Defaults to `https://api.lever.co/v1`.

### Sandbox Environment

To use the Lever Sandbox environment:
1.  Set `LEVER_API_BASE_URL` to `https://api.sandbox.lever.co/v1`.
2.  Use an API key generated from your Sandbox account.

## Usage

To run the server:

```bash
./run.sh
```


## Using with Antigravity

To connect this server to Antigravity, you need to add it to your MCP settings configuration.

1.  Open your Antigravity MCP settings (usually `~/.antigravity/mcp_settings.json` or via the UI).
2.  Add the following configuration. **Important:** Use absolute paths.

```json
{
  "mcpServers": {
    "lever": {
      "command": "/bin/bash",
      "args": ["/Users/andrew/focus/ai/apps/lever-mcp/run.sh"],
      "env": {
        "LEVER_API_KEY": "your_api_key_here",
        "LEVER_API_BASE_URL": "https://api.sandbox.lever.co/v1" 
      }
    }
  }
}
```

*Note: Replace `/Users/andrew/focus/ai/apps/lever-mcp/run.sh` with the actual absolute path to your `run.sh` file.*

### Verification and Logs

**Trigger Prompt:**
Once connected, you can ask Antigravity:
> "Can you list the current job candidates from Lever?"

**Viewing Logs:**
- **MCP Server Logs:** The server logs to `stderr`. In Antigravity, these logs are typically visible in the MCP Server logs panel or the application logs.
- **Application Logs:** Check `lever_mcp.log` if you configured file logging, otherwise they appear in the console output of the server.

## Running Manually (HTTP Transport)

If you prefer to run the server manually in your terminal and have Antigravity connect to it, you can use the HTTP transport.

### Streamable HTTP (Recommended)

The streamable-http transport is the modern, recommended approach for web deployments:

1.  Run the server in streamable HTTP mode:
    ```bash
    ./run_http.sh
    ```
    This will start the server on port 8005.

2.  Configure Antigravity to connect to the running server:

    ```json
    {
      "mcpServers": {
        "lever": {
          "url": "http://localhost:8005/mcp"
        }
      }
    }
    ```

### SSE (Legacy)

The SSE transport is deprecated but still supported:

1.  Run the server in SSE mode:
    ```bash
    ./run_sse.sh
    ```
    This will start the server on port 8005.

2.  Configure Antigravity to connect to the running server:

    ```json
    {
      "mcpServers": {
        "lever": {
          "url": "http://localhost:8005/sse"
        }
      }
    }
    ```

*Note: When running manually, you must ensure the `LEVER_API_KEY` environment variable is set in your terminal session before starting the server.*

## Available Tools

### Lever API Tools

#### `list_candidates`
Lists candidates from your Lever account.

**Parameters:**
- `limit` (optional): Maximum number of candidates to return (default: 10)
- `offset` (optional): Pagination offset token

**Example:**
```
List the first 20 candidates from Lever
```

#### `get_candidate`
Retrieves detailed information about a specific candidate.

**Parameters:**
- `candidateId` (required): The ID of the candidate to retrieve

**Example:**
```
Get candidate details for ID abc123
```

#### `create_requisition`
Creates a new job requisition in Lever.

**Parameters:**
- `title` (required): Job title
- `location` (required): Job location
- `team` (required): Team name

**Example:**
```
Create a requisition for Senior Software Engineer in San Francisco for the Engineering team
```

### Email Tool

#### `send_email`
Generates a fun themed email and returns a Gmail API payload ready to send.

**Parameters:**
- `to` (required): Recipient email address
- `theme` (required): Email theme - one of: `birthday`, `pirate`, `space`, `medieval`, `superhero`, `tropical`
- `subject` (optional): Custom subject line (uses theme default if not provided)
- `cc` (optional): CC email addresses (comma-separated)
- `bcc` (optional): BCC email addresses (comma-separated)

**Returns:**
- Gmail API payload (base64-encoded email ready to send)
- Step-by-step instructions for sending via Gmail API
- Email preview with subject and theme information

**Available Themes:**
- 🎉 **birthday**: Colorful birthday celebration email
- 🏴‍☠️ **pirate**: Pirate-themed message from the high seas
- 🚀 **space**: Cosmic greetings from outer space
- ⚔️ **medieval**: Royal proclamation in medieval style
- 🦸 **superhero**: Superhero alert with bold styling
- 🌴 **tropical**: Tropical paradise vibes

**Example:**
```
Send a birthday themed email to friend@example.com
```

**How it works:**
1. The tool generates a beautiful HTML email based on your chosen theme
2. Returns a Gmail API payload that can be used with OAuth credentials
3. If the AI agent has Gmail OAuth access, it can send the email directly
4. Otherwise, provides instructions for manual sending or integration

**Note:** This tool does not require Lever API credentials and can be used independently.

