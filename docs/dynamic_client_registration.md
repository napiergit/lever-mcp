# Dynamic Client Registration (DCR) Implementation

This document describes the Dynamic Client Registration implementation following RFC 7591 standards, allowing OAuth clients to register themselves at runtime.

## Overview

The implementation provides:
- **RFC 7591 compliant** dynamic client registration
- **Dual client support** - both static (environment-configured) and dynamic clients
- **Secure client storage** with hashed secrets and registration access tokens
- **Full CRUD operations** for client management
- **OAuth 2.0 integration** supporting dynamic clients in authorization flows

## Architecture

### Components

1. **`ClientRegistry`** (`src/client_registry.py`) - Core DCR logic
2. **Server endpoints** (`src/server.py`) - HTTP API implementation
3. **OAuth integration** - Updated OAuth flow to support dynamic clients
4. **Storage system** - File-based with fallback for read-only environments

### Client Types

The system supports two types of clients:

#### Static Clients (Legacy)
- Configured via environment variables (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`)
- Backward compatible with existing implementations
- Used when no `client_id` parameter is provided in OAuth requests

#### Dynamic Clients
- Registered at runtime via DCR endpoints
- Each client gets unique credentials and configuration
- Managed via registration access tokens

## API Endpoints

### 1. Client Registration
**`POST /clients`**

Register a new OAuth client dynamically.

**Request:**
```json
{
  "client_name": "My Application",
  "client_uri": "https://example.com",
  "logo_uri": "https://example.com/logo.png",
  "contacts": ["admin@example.com"],
  "redirect_uris": [
    "https://example.com/callback",
    "http://localhost:3000/callback"
  ],
  "response_types": ["code"],
  "grant_types": ["authorization_code", "refresh_token"],
  "application_type": "web",
  "token_endpoint_auth_method": "client_secret_post",
  "scope": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.compose",
  "tos_uri": "https://example.com/tos",
  "policy_uri": "https://example.com/privacy",
  "software_id": "my-app",
  "software_version": "1.0.0"
}
```

**Response (201 Created):**
```json
{
  "client_id": "dcr_abc123...",
  "client_secret": "secret123...",
  "client_id_issued_at": 1641024000,
  "registration_access_token": "token123...",
  "registration_client_uri": "https://server.com/clients/dcr_abc123...",
  "client_name": "My Application",
  "client_uri": "https://example.com",
  "redirect_uris": ["https://example.com/callback", "http://localhost:3000/callback"],
  "response_types": ["code"],
  "grant_types": ["authorization_code", "refresh_token"],
  "application_type": "web",
  "token_endpoint_auth_method": "client_secret_post",
  "scope": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.compose"
}
```

### 2. Client Retrieval
**`GET /clients/{client_id}`**

Retrieve client information. Requires registration access token.

**Headers:**
```
Authorization: Bearer {registration_access_token}
```

**Response (200 OK):**
```json
{
  "client_id": "dcr_abc123...",
  "client_name": "My Application",
  "client_uri": "https://example.com",
  "redirect_uris": ["https://example.com/callback"],
  "status": "active",
  "created_at": "2022-01-01T12:00:00Z",
  "updated_at": "2022-01-01T12:00:00Z"
}
```

### 3. Client Update
**`PUT /clients/{client_id}`**

Update client registration. Requires registration access token.

**Headers:**
```
Authorization: Bearer {registration_access_token}
Content-Type: application/json
```

**Request:**
```json
{
  "client_name": "My Updated Application",
  "redirect_uris": ["https://updated.example.com/callback"]
}
```

**Response (200 OK):**
Updated client information.

### 4. Client Deletion
**`DELETE /clients/{client_id}`**

Deactivate a client registration. Requires registration access token.

**Headers:**
```
Authorization: Bearer {registration_access_token}
```

**Response (204 No Content)**

### 5. Administrative Endpoints
**`GET /admin/clients`**

List all registered clients (for debugging/administration).

**Query Parameters:**
- `include_inactive=true` - Include inactive clients

**Response (200 OK):**
```json
{
  "clients": [...],
  "total": 5,
  "include_inactive": false
}
```

## OAuth 2.0 Integration

### Authorization Flow

#### For Dynamic Clients:
```
GET /authorize?client_id=dcr_abc123...&redirect_uri=https://example.com/callback&response_type=code&scope=...&state=...
```

#### For Static Clients (Legacy):
```
GET /authorize?response_type=code&scope=...&state=...
```

The system automatically detects client type based on presence of `client_id` parameter.

### Token Exchange

#### For Dynamic Clients:
```
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=abc123&client_id=dcr_abc123...&client_secret=secret123...&redirect_uri=https://example.com/callback
```

#### For Static Clients (Legacy):
```
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=abc123
```

## Security Features

### Client Authentication
- **Hashed storage** - Client secrets are stored as SHA-256 hashes
- **Secure comparison** - Uses `secrets.compare_digest()` for timing-safe comparison
- **Multiple auth methods** - Supports `client_secret_basic`, `client_secret_post`, and `none`

### Registration Access Tokens
- **Unique per client** - Each client gets a unique registration access token
- **Required for management** - All client management operations require the token
- **Secure generation** - Uses `secrets.token_urlsafe(32)` for token generation

### Validation
- **Redirect URI validation** - Strict validation of redirect URIs (HTTPS required, localhost allowed)
- **Client status checks** - Inactive clients are rejected
- **Scope validation** - Configurable scope validation
- **Request validation** - Comprehensive validation of all registration requests

## Storage System

### File-Based Storage
- **Location** - `./.client_registry/` (configurable via `CLIENT_REGISTRY_PATH`)
- **Format** - JSON files named `{client_id}.json`
- **Read-only fallback** - Gracefully handles read-only filesystems (serverless environments)

### Data Structure
```json
{
  "client_id": "dcr_abc123...",
  "client_secret": "hashed_secret",
  "registration_access_token": "hashed_token",
  "client_name": "My Application",
  "redirect_uris": ["https://example.com/callback"],
  "status": "active",
  "created_at": "2022-01-01T12:00:00Z",
  "updated_at": "2022-01-01T12:00:00Z"
}
```

## Discovery and Metadata

### Authorization Server Metadata
**`GET /.well-known/oauth-authorization-server`**

Advertises DCR capabilities:
```json
{
  "issuer": "https://server.com/",
  "authorization_endpoint": "https://server.com/authorize",
  "token_endpoint": "https://server.com/token",
  "registration_endpoint": "https://server.com/clients",
  "registration_endpoint_auth_methods_supported": ["none"],
  "client_metadata_supported": [
    "client_name", "client_uri", "logo_uri", "contacts",
    "redirect_uris", "response_types", "grant_types", "scope"
  ]
}
```

## Usage Examples

### 1. Basic Client Registration

```python
import httpx
import json

# Register a new client
registration_request = {
    "client_name": "My App",
    "redirect_uris": ["https://myapp.com/callback"],
    "response_types": ["code"],
    "grant_types": ["authorization_code"],
    "scope": "https://www.googleapis.com/auth/gmail.send"
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://server.com/clients",
        json=registration_request
    )
    
    if response.status_code == 201:
        client_data = response.json()
        client_id = client_data["client_id"]
        client_secret = client_data["client_secret"]
        registration_token = client_data["registration_access_token"]
        print(f"Client registered: {client_id}")
```

### 2. OAuth Authorization Flow

```python
# Build authorization URL
auth_url = f"https://server.com/authorize?client_id={client_id}&redirect_uri=https://myapp.com/callback&response_type=code&scope=https://www.googleapis.com/auth/gmail.send&state=xyz123"

# User visits auth_url, completes authorization
# Server redirects to: https://myapp.com/callback?code=abc123&state=xyz123

# Exchange code for token
token_request = {
    "grant_type": "authorization_code",
    "code": "abc123",
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": "https://myapp.com/callback"
}

token_response = await client.post(
    "https://server.com/token",
    data=token_request
)

if token_response.status_code == 200:
    token_data = token_response.json()
    access_token = token_data["access_token"]
    print(f"Access token obtained: {access_token[:20]}...")
```

### 3. Client Management

```python
# Update client
update_request = {
    "client_name": "My Updated App",
    "redirect_uris": ["https://updated.myapp.com/callback"]
}

headers = {"Authorization": f"Bearer {registration_token}"}
update_response = await client.put(
    f"https://server.com/clients/{client_id}",
    json=update_request,
    headers=headers
)

# Delete client
delete_response = await client.delete(
    f"https://server.com/clients/{client_id}",
    headers=headers
)
```

## Testing

A comprehensive test suite is provided in `test_dynamic_client_registration.py`:

```bash
# Run all DCR tests
python test_dynamic_client_registration.py

# Run with custom base URL
python test_dynamic_client_registration.py --base-url https://your-server.com

# Enable verbose logging
python test_dynamic_client_registration.py --verbose
```

The test suite covers:
- Authorization server metadata discovery
- Client registration, retrieval, update, and deletion
- OAuth authorization flow integration
- Client authentication at token endpoint
- Administrative endpoints

## Configuration

### Environment Variables

- **`CLIENT_REGISTRY_PATH`** - Path for client storage (default: `./.client_registry`)
- **`GOOGLE_CLIENT_ID`** - Google OAuth client ID (for upstream integration)
- **`GOOGLE_CLIENT_SECRET`** - Google OAuth client secret
- **`MCP_SERVER_BASE_URL`** - Base URL for the MCP server

### Supported Client Metadata

The implementation supports these RFC 7591 client metadata fields:

**Core Fields:**
- `client_name` - Human-readable client name
- `client_uri` - Client information URL
- `logo_uri` - Client logo URL
- `contacts` - Array of contact email addresses
- `tos_uri` - Terms of service URL
- `policy_uri` - Privacy policy URL

**OAuth 2.0 Fields:**
- `redirect_uris` - Array of valid redirect URIs (required)
- `response_types` - Supported response types (default: ["code"])
- `grant_types` - Supported grant types (default: ["authorization_code"])
- `application_type` - "web" or "native" (default: "web")
- `token_endpoint_auth_method` - Client authentication method
- `scope` - Requested OAuth scopes

**Extensions:**
- `jwks_uri` - JSON Web Key Set URI
- `software_id` - Software identifier
- `software_version` - Software version

## Limitations and Considerations

### Current Limitations
- **File-based storage** - Not suitable for high-scale deployments (consider database integration)
- **No client rotation** - Client secrets don't automatically expire (can be implemented)
- **Single tenant** - All clients share the same upstream Google OAuth app

### Security Considerations
- **HTTPS enforcement** - Redirect URIs must use HTTPS (except localhost for development)
- **Client validation** - Comprehensive validation of all client registration requests
- **Token security** - Registration access tokens should be treated as sensitive data

### Scaling Considerations
- **Storage backend** - Consider implementing database storage for production deployments
- **Caching** - Add caching layer for frequently accessed client data
- **Rate limiting** - Implement rate limiting for registration endpoints

## RFC 7591 Compliance

This implementation follows RFC 7591 "OAuth 2.0 Dynamic Client Registration Protocol" and includes:

✅ **REQUIRED Features:**
- Client registration endpoint (`POST /clients`)
- Client information endpoint (`GET /clients/{client_id}`)  
- Registration access token authentication
- Client metadata validation
- Error response format compliance

✅ **OPTIONAL Features:**
- Client configuration endpoint (`PUT /clients/{client_id}`)
- Client deletion endpoint (`DELETE /clients/{client_id}`)
- Authorization server metadata discovery
- Software statement support (basic)

The implementation is designed to be production-ready while maintaining RFC compliance and security best practices.
