"""
OAuth configuration for Gmail integration.
Supports both FastMCP OAuth proxy and direct OAuth 2.0 on-behalf-of flows.
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Gmail API scopes
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
]

class OAuthConfig:
    """Configuration for OAuth authentication."""
    
    def __init__(self):
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        # Use dedicated OAUTH_CALLBACK_URL environment variable, fallback to MCP_SERVER_BASE_URL construction
        self.redirect_uri = os.getenv('OAUTH_CALLBACK_URL')
        if not self.redirect_uri:
            # Fallback to old behavior for backward compatibility
            base_url = os.getenv('MCP_SERVER_BASE_URL', 'https://isolated-coffee-reindeer.fastmcp.app')
            self.redirect_uri = f"{base_url}/oauth/callback"
        self.token_storage_path = Path(os.getenv('TOKEN_STORAGE_PATH', './.oauth_tokens'))
        
    def is_configured(self) -> bool:
        """Check if OAuth is properly configured."""
        return bool(self.client_id and self.client_secret)
    
    def get_client_config(self) -> Dict[str, Any]:
        """Get OAuth client configuration in Google's expected format."""
        if not self.is_configured():
            raise ValueError(
                "OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET "
                "environment variables."
            )
        
        return {
            "installed": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": [self.redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
            }
        }
    
    def save_token(self, token_data: Dict[str, Any], user_id: str = "default") -> None:
        """Save OAuth token to storage."""
        try:
            self.token_storage_path.mkdir(parents=True, exist_ok=True)
            token_file = self.token_storage_path / f"{user_id}_token.json"
            
            with open(token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            logger.info(f"Token saved for user: {user_id}")
        except (OSError, PermissionError) as e:
            # Read-only filesystem (common in serverless/cloud deployments)
            # This is OK - tokens should be managed by the MCP client (on-behalf-of flow)
            logger.warning(f"Cannot save token to filesystem (read-only): {e}")
            logger.info("Token storage skipped - using on-behalf-of flow where client manages tokens")
    
    def load_token(self, user_id: str = "default") -> Optional[Dict[str, Any]]:
        """Load OAuth token from storage."""
        try:
            token_file = self.token_storage_path / f"{user_id}_token.json"
            
            if not token_file.exists():
                return None
            
            with open(token_file, 'r') as f:
                return json.load(f)
        except (OSError, PermissionError) as e:
            # Read-only filesystem - no tokens stored locally
            logger.debug(f"Cannot load token from filesystem: {e}")
            return None
    
    def delete_token(self, user_id: str = "default") -> None:
        """Delete OAuth token from storage."""
        try:
            token_file = self.token_storage_path / f"{user_id}_token.json"
            
            if token_file.exists():
                token_file.unlink()
                logger.info(f"Token deleted for user: {user_id}")
        except (OSError, PermissionError) as e:
            # Read-only filesystem - nothing to delete
            logger.debug(f"Cannot delete token from filesystem: {e}")


# Global config instance
oauth_config = OAuthConfig()
