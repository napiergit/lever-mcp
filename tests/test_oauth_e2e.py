"""
End-to-end OAuth flow testing.
Tests the complete OAuth integration without deploying to production.
"""
import asyncio
import httpx
import json
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from lever_mcp.oauth_config import oauth_config, GMAIL_SCOPES
from lever_mcp.gmail_client import GmailClient
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OAuthE2ETest:
    """End-to-end OAuth flow testing."""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def test_server_health(self) -> bool:
        """Test if the MCP server is running."""
        logger.info("🏥 Testing server health...")
        
        try:
            response = await self.client.get(f"{self.server_url}/health")
            if response.status_code == 404:
                # Try root endpoint
                response = await self.client.get(self.server_url)
            
            logger.info(f"✅ Server is running (status: {response.status_code})")
            return True
        except Exception as e:
            logger.error(f"❌ Server health check failed: {e}")
            return False
    
    async def test_oauth_discovery(self) -> bool:
        """Test OAuth endpoint discovery."""
        logger.info("🔍 Testing OAuth endpoint discovery...")
        
        try:
            response = await self.client.get(
                f"{self.server_url}/.well-known/oauth-authorization-server"
            )
            response.raise_for_status()
            metadata = response.json()
            
            required_fields = [
                'authorization_endpoint',
                'token_endpoint',
                'scopes_supported'
            ]
            
            for field in required_fields:
                if field not in metadata:
                    logger.error(f"❌ Missing required field: {field}")
                    return False
            
            logger.info(f"✅ OAuth discovery successful")
            logger.info(f"   Authorization endpoint: {metadata['authorization_endpoint']}")
            logger.info(f"   Token endpoint: {metadata['token_endpoint']}")
            logger.info(f"   Scopes: {metadata['scopes_supported']}")
            
            return True
        except Exception as e:
            logger.error(f"❌ OAuth discovery failed: {e}")
            return False
    
    async def test_protected_resource_discovery(self) -> bool:
        """Test protected resource metadata discovery."""
        logger.info("🔍 Testing protected resource discovery...")
        
        try:
            response = await self.client.get(
                f"{self.server_url}/.well-known/oauth-protected-resource"
            )
            response.raise_for_status()
            metadata = response.json()
            
            logger.info(f"✅ Protected resource discovery successful")
            logger.info(f"   Resource: {metadata.get('resource')}")
            logger.info(f"   Authorization servers: {metadata.get('authorization_servers')}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Protected resource discovery failed: {e}")
            return False
    
    async def test_authorization_redirect(self) -> bool:
        """Test that authorization endpoint redirects to Google."""
        logger.info("🔀 Testing authorization redirect...")
        
        try:
            # Don't follow redirects
            response = await self.client.get(
                f"{self.server_url}/authorize?state=test_state",
                follow_redirects=False
            )
            
            if response.status_code not in [301, 302, 303, 307, 308]:
                logger.error(f"❌ Expected redirect, got status {response.status_code}")
                return False
            
            location = response.headers.get('location', '')
            
            if 'accounts.google.com' not in location:
                logger.error(f"❌ Redirect not to Google: {location}")
                return False
            
            logger.info(f"✅ Authorization redirect successful")
            logger.info(f"   Redirects to: {location[:100]}...")
            
            return True
        except Exception as e:
            logger.error(f"❌ Authorization redirect test failed: {e}")
            return False
    
    async def test_oauth_config(self) -> bool:
        """Test OAuth configuration."""
        logger.info("⚙️  Testing OAuth configuration...")
        
        if not oauth_config.is_configured():
            logger.error("❌ OAuth not configured")
            logger.error("   Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")
            return False
        
        logger.info(f"✅ OAuth configured")
        logger.info(f"   Client ID: {oauth_config.client_id[:20]}...")
        logger.info(f"   Redirect URI: {oauth_config.redirect_uri}")
        
        return True
    
    async def test_gmail_client_init(self) -> bool:
        """Test Gmail client initialization."""
        logger.info("📧 Testing Gmail client initialization...")
        
        try:
            client = GmailClient(user_id="test_user")
            logger.info(f"✅ Gmail client initialized")
            logger.info(f"   Authenticated: {client.is_authenticated()}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Gmail client initialization failed: {e}")
            return False
    
    async def test_callback_endpoint(self) -> bool:
        """Test OAuth callback endpoint."""
        logger.info("🔙 Testing OAuth callback endpoint...")
        
        try:
            # Test with error
            response = await self.client.get(
                f"{self.server_url}/oauth/callback?error=access_denied"
            )
            
            if response.status_code != 400:
                logger.error(f"❌ Expected 400 for error, got {response.status_code}")
                return False
            
            # Test without code
            response = await self.client.get(
                f"{self.server_url}/oauth/callback"
            )
            
            if response.status_code != 400:
                logger.error(f"❌ Expected 400 for missing code, got {response.status_code}")
                return False
            
            logger.info(f"✅ Callback endpoint validation working")
            
            return True
        except Exception as e:
            logger.error(f"❌ Callback endpoint test failed: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all tests."""
        logger.info("\n" + "="*80)
        logger.info("🧪 RUNNING END-TO-END OAUTH TESTS")
        logger.info("="*80 + "\n")
        
        tests = [
            ("Server Health", self.test_server_health),
            ("OAuth Configuration", self.test_oauth_config),
            ("OAuth Discovery", self.test_oauth_discovery),
            ("Protected Resource Discovery", self.test_protected_resource_discovery),
            ("Authorization Redirect", self.test_authorization_redirect),
            ("Callback Endpoint", self.test_callback_endpoint),
            ("Gmail Client Init", self.test_gmail_client_init),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"\n{'─'*80}")
            logger.info(f"Running: {test_name}")
            logger.info(f"{'─'*80}")
            
            try:
                result = await test_func()
                results[test_name] = result
            except Exception as e:
                logger.error(f"❌ Test crashed: {e}")
                results[test_name] = False
            
            await asyncio.sleep(0.5)  # Brief pause between tests
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("📊 TEST SUMMARY")
        logger.info("="*80 + "\n")
        
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} - {test_name}")
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Results: {passed}/{total} tests passed")
        logger.info(f"{'='*80}\n")
        
        return all(results.values())


async def main():
    """Main test runner."""
    # Check if .env file exists
    env_file = Path(__file__).parent.parent / '.env'
    if not env_file.exists():
        logger.warning("⚠️  No .env file found. Please create one from .env.example")
        logger.warning("   Required variables: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET")
        logger.warning("   Set MCP_SERVER_BASE_URL=http://localhost:8000 for local testing")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    async with OAuthE2ETest() as tester:
        success = await tester.run_all_tests()
        
        if success:
            logger.info("\n" + "🎉 " * 20)
            logger.info("ALL TESTS PASSED!")
            logger.info("🎉 " * 20 + "\n")
            logger.info("Next step: Run the mock Toqan client to test the full OAuth flow:")
            logger.info("  python tests/mock_toqan_client.py")
        else:
            logger.error("\n" + "❌ " * 20)
            logger.error("SOME TESTS FAILED")
            logger.error("❌ " * 20 + "\n")
            logger.error("Please fix the issues above before proceeding.")
        
        return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
