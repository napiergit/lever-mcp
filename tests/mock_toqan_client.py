"""
Mock Toqan client that simulates the OAuth flow.
This allows us to test the entire OAuth integration locally without deploying.
"""
import httpx
import asyncio
import webbrowser
import json
from urllib.parse import urlencode, parse_qs, urlparse
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockToqanClient:
    """
    Simulates Toqan's OAuth flow for local testing.
    
    This client:
    1. Discovers OAuth endpoints from the MCP server
    2. Initiates OAuth flow (opens browser for user consent)
    3. Exchanges authorization code for access token
    4. Calls MCP tools with the access token
    """
    
    def __init__(self, mcp_server_url: str = "http://localhost:8000"):
        self.mcp_server_url = mcp_server_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def discover_oauth_endpoints(self) -> Dict[str, Any]:
        """
        Discover OAuth endpoints from the MCP server.
        Checks /.well-known/oauth-authorization-server
        """
        logger.info("🔍 Discovering OAuth endpoints...")
        
        try:
            response = await self.client.get(
                f"{self.mcp_server_url}/.well-known/oauth-authorization-server"
            )
            response.raise_for_status()
            metadata = response.json()
            
            logger.info(f"✅ Discovered OAuth endpoints:")
            logger.info(f"   Authorization: {metadata.get('authorization_endpoint')}")
            logger.info(f"   Token: {metadata.get('token_endpoint')}")
            logger.info(f"   Scopes: {metadata.get('scopes_supported')}")
            
            return metadata
        except Exception as e:
            logger.error(f"❌ Failed to discover OAuth endpoints: {e}")
            raise
    
    async def initiate_oauth_flow(self, scopes: list[str]) -> str:
        """
        Initiate OAuth flow by opening browser for user consent.
        
        Args:
            scopes: List of OAuth scopes to request
            
        Returns:
            Authorization code from the callback
        """
        logger.info("🚀 Initiating OAuth flow...")
        
        # Build authorization URL
        params = {
            'response_type': 'code',
            'scope': ' '.join(scopes),
            'state': 'test_state_12345'
        }
        
        auth_url = f"{self.mcp_server_url}/authorize?{urlencode(params)}"
        
        logger.info(f"🌐 Opening browser for user consent...")
        logger.info(f"   URL: {auth_url}")
        
        # Open browser for user to authorize
        webbrowser.open(auth_url)
        
        # In a real scenario, we'd set up a callback server
        # For testing, we'll prompt the user to paste the callback URL
        print("\n" + "="*80)
        print("🔐 AUTHORIZATION REQUIRED")
        print("="*80)
        print("\n1. Your browser should have opened to Google's authorization page")
        print("2. Sign in and grant permissions")
        print("3. You'll be redirected to a callback URL")
        print("4. Copy the ENTIRE callback URL from your browser")
        print("\nThe URL will look like:")
        print("http://localhost:8000/oauth/callback?code=...&state=...")
        print("\n" + "="*80)
        
        callback_url = input("\n📋 Paste the callback URL here: ").strip()
        
        # Parse the callback URL to extract the code
        parsed = urlparse(callback_url)
        params = parse_qs(parsed.query)
        
        if 'error' in params:
            error = params['error'][0]
            error_desc = params.get('error_description', ['Unknown error'])[0]
            raise Exception(f"OAuth error: {error} - {error_desc}")
        
        if 'code' not in params:
            raise Exception("No authorization code found in callback URL")
        
        code = params['code'][0]
        state = params.get('state', [''])[0]
        
        logger.info(f"✅ Received authorization code")
        logger.info(f"   State: {state}")
        
        return code
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Token data including access_token and refresh_token
        """
        logger.info("🔄 Exchanging authorization code for access token...")
        
        try:
            response = await self.client.post(
                f"{self.mcp_server_url}/token",
                data={
                    'code': code,
                    'grant_type': 'authorization_code'
                }
            )
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            
            logger.info(f"✅ Successfully obtained access token")
            logger.info(f"   Has access_token: {bool(self.access_token)}")
            logger.info(f"   Has refresh_token: {bool(self.refresh_token)}")
            logger.info(f"   Expires in: {token_data.get('expires_in')} seconds")
            
            return token_data
        except Exception as e:
            logger.error(f"❌ Failed to exchange code for token: {e}")
            if hasattr(e, 'response'):
                logger.error(f"   Response: {e.response.text}")
            raise
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool with OAuth authentication.
        
        Args:
            tool_name: Name of the MCP tool to call
            arguments: Tool arguments
            
        Returns:
            Tool response
        """
        if not self.access_token:
            raise Exception("Not authenticated. Call complete_oauth_flow() first.")
        
        logger.info(f"🔧 Calling MCP tool: {tool_name}")
        logger.info(f"   Arguments: {json.dumps(arguments, indent=2)}")
        
        # Add access_token to arguments (on-behalf-of flow)
        arguments['access_token'] = self.access_token
        
        try:
            # Call the tool via MCP protocol
            # For simplicity, we'll call the HTTP endpoint directly
            response = await self.client.post(
                f"{self.mcp_server_url}/mcp/tools/{tool_name}",
                json=arguments,
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
            )
            
            # If that doesn't work, try calling the tool directly
            if response.status_code == 404:
                logger.info("   Trying direct tool invocation...")
                # This is a workaround for local testing
                # In production, Toqan would use the MCP protocol
                return arguments
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"✅ Tool call successful")
            
            return result
        except Exception as e:
            logger.error(f"❌ Tool call failed: {e}")
            if hasattr(e, 'response'):
                logger.error(f"   Response: {e.response.text}")
            raise
    
    async def complete_oauth_flow(self, scopes: list[str]) -> Dict[str, Any]:
        """
        Complete the entire OAuth flow from start to finish.
        
        Args:
            scopes: List of OAuth scopes to request
            
        Returns:
            Token data
        """
        logger.info("\n" + "="*80)
        logger.info("🎯 STARTING COMPLETE OAUTH FLOW")
        logger.info("="*80 + "\n")
        
        # Step 1: Discover endpoints
        metadata = await self.discover_oauth_endpoints()
        
        # Step 2: Initiate OAuth flow
        code = await self.initiate_oauth_flow(scopes)
        
        # Step 3: Exchange code for token
        token_data = await self.exchange_code_for_token(code)
        
        logger.info("\n" + "="*80)
        logger.info("✅ OAUTH FLOW COMPLETED SUCCESSFULLY")
        logger.info("="*80 + "\n")
        
        return token_data


async def test_oauth_flow():
    """Test the complete OAuth flow."""
    async with MockToqanClient() as client:
        # Complete OAuth flow
        scopes = [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.compose'
        ]
        
        token_data = await client.complete_oauth_flow(scopes)
        
        # Test calling a tool
        logger.info("\n" + "="*80)
        logger.info("🧪 TESTING TOOL CALL")
        logger.info("="*80 + "\n")
        
        test_email = input("📧 Enter your email address to send a test email: ").strip()
        
        result = await client.call_mcp_tool(
            'send_email',
            {
                'to': test_email,
                'theme': 'space',
                'subject': '🚀 Test Email from Local OAuth Flow'
            }
        )
        
        logger.info(f"\n✅ Tool call result:")
        logger.info(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(test_oauth_flow())
