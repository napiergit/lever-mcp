#!/usr/bin/env python3
"""
Test script for Dynamic Client Registration (RFC 7591) implementation.
Tests the complete DCR flow including registration, authentication, and OAuth.
"""
import asyncio
import json
import aiohttp
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DCRTester:
    """Test harness for Dynamic Client Registration implementation."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.registered_client = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_authorization_server_metadata(self) -> bool:
        """Test /.well-known/oauth-authorization-server endpoint."""
        logger.info("Testing authorization server metadata...")
        
        try:
            url = f"{self.base_url}/.well-known/oauth-authorization-server"
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Metadata endpoint failed: {response.status}")
                    return False
                
                metadata = await response.json()
                
                # Check required fields
                required_fields = ['issuer', 'authorization_endpoint', 'token_endpoint', 'registration_endpoint']
                for field in required_fields:
                    if field not in metadata:
                        logger.error(f"Missing required field: {field}")
                        return False
                
                # Check DCR-specific fields
                dcr_fields = ['client_metadata_supported', 'registration_endpoint']
                for field in dcr_fields:
                    if field not in metadata:
                        logger.error(f"Missing DCR field: {field}")
                        return False
                
                logger.info("✅ Authorization server metadata is valid")
                logger.info(f"Registration endpoint: {metadata['registration_endpoint']}")
                return True
                
        except Exception as e:
            logger.error(f"Error testing metadata: {e}")
            return False
    
    async def test_client_registration(self) -> bool:
        """Test dynamic client registration."""
        logger.info("Testing dynamic client registration...")
        
        # Prepare registration request
        registration_request = {
            "client_name": "DCR Test Client",
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
            "software_id": "dcr-test-client",
            "software_version": "1.0.0"
        }
        
        try:
            url = f"{self.base_url}/clients"
            async with self.session.post(
                url, 
                json=registration_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status != 201:
                    error_text = await response.text()
                    logger.error(f"Registration failed: {response.status} - {error_text}")
                    return False
                
                self.registered_client = await response.json()
                
                # Validate response fields
                required_fields = ['client_id', 'client_secret', 'registration_access_token', 'registration_client_uri']
                for field in required_fields:
                    if field not in self.registered_client:
                        logger.error(f"Missing field in registration response: {field}")
                        return False
                
                logger.info("✅ Client registration successful")
                logger.info(f"Client ID: {self.registered_client['client_id']}")
                logger.info(f"Client Name: {self.registered_client.get('client_name')}")
                return True
                
        except Exception as e:
            logger.error(f"Error during client registration: {e}")
            return False
    
    async def test_client_retrieval(self) -> bool:
        """Test retrieving client information."""
        if not self.registered_client:
            logger.error("No registered client to retrieve")
            return False
        
        logger.info("Testing client information retrieval...")
        
        try:
            client_id = self.registered_client['client_id']
            registration_token = self.registered_client['registration_access_token']
            
            url = f"{self.base_url}/clients/{client_id}"
            headers = {"Authorization": f"Bearer {registration_token}"}
            
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Client retrieval failed: {response.status} - {error_text}")
                    return False
                
                client_data = await response.json()
                
                # Verify client data
                if client_data.get('client_id') != client_id:
                    logger.error("Retrieved client ID doesn't match")
                    return False
                
                if 'client_secret' in client_data:
                    logger.error("Client secret should not be returned in GET response")
                    return False
                
                logger.info("✅ Client retrieval successful")
                return True
                
        except Exception as e:
            logger.error(f"Error retrieving client: {e}")
            return False
    
    async def test_client_update(self) -> bool:
        """Test updating client registration."""
        if not self.registered_client:
            logger.error("No registered client to update")
            return False
        
        logger.info("Testing client registration update...")
        
        try:
            client_id = self.registered_client['client_id']
            registration_token = self.registered_client['registration_access_token']
            
            # Update request
            update_request = {
                "client_name": "DCR Test Client (Updated)",
                "client_uri": "https://updated.example.com",
                "redirect_uris": [
                    "https://updated.example.com/callback",
                    "http://localhost:3000/callback"
                ],
                "contacts": ["updated@example.com"],
                "response_types": ["code"],
                "grant_types": ["authorization_code"],
                "application_type": "web",
                "token_endpoint_auth_method": "client_secret_post",
                "scope": "https://www.googleapis.com/auth/gmail.send"
            }
            
            url = f"{self.base_url}/clients/{client_id}"
            headers = {
                "Authorization": f"Bearer {registration_token}",
                "Content-Type": "application/json"
            }
            
            async with self.session.put(url, json=update_request, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Client update failed: {response.status} - {error_text}")
                    return False
                
                updated_client = await response.json()
                
                # Verify updates
                if updated_client.get('client_name') != "DCR Test Client (Updated)":
                    logger.error("Client name was not updated")
                    return False
                
                if updated_client.get('client_uri') != "https://updated.example.com":
                    logger.error("Client URI was not updated")
                    return False
                
                logger.info("✅ Client update successful")
                return True
                
        except Exception as e:
            logger.error(f"Error updating client: {e}")
            return False
    
    async def test_oauth_authorization_flow(self) -> bool:
        """Test OAuth authorization flow with dynamic client."""
        if not self.registered_client:
            logger.error("No registered client for OAuth test")
            return False
        
        logger.info("Testing OAuth authorization flow...")
        
        try:
            client_id = self.registered_client['client_id']
            redirect_uri = self.registered_client['redirect_uris'][0]
            
            # Test authorization endpoint
            url = f"{self.base_url}/authorize"
            params = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "https://www.googleapis.com/auth/gmail.send",
                "state": "test_state_123"
            }
            
            async with self.session.get(url, params=params, allow_redirects=False) as response:
                if response.status != 302:  # Should redirect to Google
                    error_text = await response.text()
                    logger.error(f"Authorization failed: {response.status} - {error_text}")
                    return False
                
                location = response.headers.get('Location', '')
                if not location.startswith('https://accounts.google.com/o/oauth2/auth'):
                    logger.error(f"Invalid redirect location: {location}")
                    return False
                
                logger.info("✅ OAuth authorization flow initiated successfully")
                logger.info(f"Redirect location: {location[:100]}...")
                return True
                
        except Exception as e:
            logger.error(f"Error testing OAuth flow: {e}")
            return False
    
    async def test_token_endpoint_authentication(self) -> bool:
        """Test token endpoint client authentication."""
        if not self.registered_client:
            logger.error("No registered client for token test")
            return False
        
        logger.info("Testing token endpoint client authentication...")
        
        try:
            client_id = self.registered_client['client_id']
            client_secret = self.registered_client['client_secret']
            redirect_uri = self.registered_client['redirect_uris'][0]
            
            # Test with invalid code (should fail gracefully)
            url = f"{self.base_url}/token"
            data = {
                "grant_type": "authorization_code",
                "code": "invalid_test_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri
            }
            
            async with self.session.post(url, data=data) as response:
                # Should authenticate client but fail on invalid code
                if response.status == 401:
                    logger.error("Client authentication failed")
                    return False
                
                # Expect 400 or other error due to invalid code, but not 401 (auth failure)
                if response.status == 401:
                    error_data = await response.json()
                    if error_data.get('error') == 'invalid_client':
                        logger.error("Client authentication failed")
                        return False
                
                logger.info("✅ Token endpoint client authentication working")
                return True
                
        except Exception as e:
            logger.error(f"Error testing token endpoint: {e}")
            return False
    
    async def test_client_deletion(self) -> bool:
        """Test client deletion/deactivation."""
        if not self.registered_client:
            logger.error("No registered client to delete")
            return False
        
        logger.info("Testing client deletion...")
        
        try:
            client_id = self.registered_client['client_id']
            registration_token = self.registered_client['registration_access_token']
            
            url = f"{self.base_url}/clients/{client_id}"
            headers = {"Authorization": f"Bearer {registration_token}"}
            
            async with self.session.delete(url, headers=headers) as response:
                if response.status != 204:
                    error_text = await response.text()
                    logger.error(f"Client deletion failed: {response.status} - {error_text}")
                    return False
                
                logger.info("✅ Client deletion successful")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting client: {e}")
            return False
    
    async def test_admin_endpoints(self) -> bool:
        """Test administrative endpoints."""
        logger.info("Testing administrative endpoints...")
        
        try:
            url = f"{self.base_url}/admin/clients"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Admin endpoint failed: {response.status} - {error_text}")
                    return False
                
                clients_data = await response.json()
                
                if 'clients' not in clients_data:
                    logger.error("Missing 'clients' field in admin response")
                    return False
                
                logger.info(f"✅ Admin endpoint working - {clients_data['total']} clients found")
                return True
                
        except Exception as e:
            logger.error(f"Error testing admin endpoints: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all DCR tests."""
        logger.info("🚀 Starting Dynamic Client Registration tests...")
        
        tests = [
            ("Authorization Server Metadata", self.test_authorization_server_metadata),
            ("Client Registration", self.test_client_registration),
            ("Client Retrieval", self.test_client_retrieval),
            ("Client Update", self.test_client_update),
            ("OAuth Authorization Flow", self.test_oauth_authorization_flow),
            ("Token Endpoint Authentication", self.test_token_endpoint_authentication),
            ("Admin Endpoints", self.test_admin_endpoints),
            ("Client Deletion", self.test_client_deletion),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n--- Running: {test_name} ---")
            try:
                if await test_func():
                    passed += 1
                    logger.info(f"✅ {test_name} PASSED")
                else:
                    logger.error(f"❌ {test_name} FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name} ERROR: {e}")
        
        logger.info(f"\n🏁 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All Dynamic Client Registration tests passed!")
            return True
        else:
            logger.error(f"💥 {total - passed} tests failed")
            return False

async def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Dynamic Client Registration implementation')
    parser.add_argument('--base-url', default='http://localhost:8000', 
                       help='Base URL of the MCP server (default: http://localhost:8000)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    async with DCRTester(args.base_url) as tester:
        success = await tester.run_all_tests()
        return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
