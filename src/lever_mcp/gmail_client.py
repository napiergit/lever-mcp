"""
Gmail client with OAuth 2.0 support.
Handles authentication and email sending via Gmail API.
"""
import logging
import base64
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from lever_mcp.oauth_config import oauth_config, GMAIL_SCOPES

logger = logging.getLogger(__name__)


class GmailClient:
    """Client for interacting with Gmail API using OAuth 2.0."""
    
    def __init__(self, access_token: Optional[str] = None, user_id: str = "default"):
        """
        Initialize Gmail client.
        
        Args:
            access_token: OAuth access token from the agent (on-behalf-of flow)
            user_id: User identifier for token storage
        """
        self.user_id = user_id
        self.credentials = None
        
        if access_token:
            # Use token provided by agent (on-behalf-of flow)
            self.credentials = Credentials(
                token=access_token,
                scopes=GMAIL_SCOPES
            )
        else:
            # Try to load stored token
            self._load_credentials()
    
    def _load_credentials(self) -> None:
        """Load credentials from storage."""
        token_data = oauth_config.load_token(self.user_id)
        
        if token_data:
            self.credentials = Credentials.from_authorized_user_info(
                token_data,
                GMAIL_SCOPES
            )
            
            # Refresh token if expired
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                try:
                    self.credentials.refresh(Request())
                    # Save refreshed token
                    self._save_credentials()
                    logger.info("Token refreshed successfully")
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}")
                    self.credentials = None
    
    def _save_credentials(self) -> None:
        """Save credentials to storage."""
        if self.credentials:
            token_data = {
                'token': self.credentials.token,
                'refresh_token': self.credentials.refresh_token,
                'token_uri': self.credentials.token_uri,
                'client_id': self.credentials.client_id,
                'client_secret': self.credentials.client_secret,
                'scopes': self.credentials.scopes
            }
            oauth_config.save_token(token_data, self.user_id)
    
    def is_authenticated(self) -> bool:
        """Check if client has valid credentials."""
        return self.credentials is not None and self.credentials.valid
    
    def set_token(self, token_data: Dict[str, Any]) -> None:
        """
        Set OAuth token from agent.
        
        Args:
            token_data: Token data containing access_token and optionally refresh_token
        """
        if isinstance(token_data, str):
            # Simple access token string
            self.credentials = Credentials(
                token=token_data,
                scopes=GMAIL_SCOPES
            )
        elif isinstance(token_data, dict):
            # Full token data
            if 'access_token' in token_data:
                self.credentials = Credentials(
                    token=token_data['access_token'],
                    refresh_token=token_data.get('refresh_token'),
                    token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    client_id=token_data.get('client_id', oauth_config.client_id),
                    client_secret=token_data.get('client_secret', oauth_config.client_secret),
                    scopes=GMAIL_SCOPES
                )
                # Save for future use
                self._save_credentials()
            else:
                raise ValueError("Token data must contain 'access_token'")
        else:
            raise ValueError("Token must be a string or dictionary")
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        is_html: bool = True
    ) -> Dict[str, Any]:
        """
        Send an email via Gmail API.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (HTML or plain text)
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            is_html: Whether body is HTML
            
        Returns:
            Response from Gmail API
            
        Raises:
            ValueError: If not authenticated
            HttpError: If Gmail API request fails
        """
        if not self.is_authenticated():
            raise ValueError(
                "Not authenticated. Please provide an OAuth token or complete authentication flow."
            )
        
        try:
            # Build Gmail service
            service = build('gmail', 'v1', credentials=self.credentials)
            
            # Create message
            message_parts = [
                f"To: {to}",
                f"Subject: {subject}",
                "MIME-Version: 1.0",
            ]
            
            if is_html:
                message_parts.append("Content-Type: text/html; charset=utf-8")
            else:
                message_parts.append("Content-Type: text/plain; charset=utf-8")
            
            if cc:
                message_parts.append(f"Cc: {cc}")
            if bcc:
                message_parts.append(f"Bcc: {bcc}")
            
            message_parts.append("")  # Empty line between headers and body
            message_parts.append(body)
            
            raw_message = "\n".join(message_parts)
            
            # Encode message
            encoded_message = base64.urlsafe_b64encode(
                raw_message.encode('utf-8')
            ).decode('utf-8')
            
            # Send message
            message = service.users().messages().send(
                userId='me',
                body={'raw': encoded_message}
            ).execute()
            
            logger.info(f"Email sent successfully. Message ID: {message['id']}")
            
            return {
                "status": "success",
                "message_id": message['id'],
                "to": to,
                "subject": subject
            }
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            raise
        except Exception as error:
            logger.error(f"Error sending email: {error}")
            raise
    
    def get_auth_url(self) -> str:
        """
        Get OAuth authorization URL for user to authenticate.
        
        Returns:
            Authorization URL
        """
        from google_auth_oauthlib.flow import Flow
        
        if not oauth_config.is_configured():
            raise ValueError("OAuth not configured")
        
        flow = Flow.from_client_config(
            oauth_config.get_client_config(),
            scopes=GMAIL_SCOPES,
            redirect_uri=oauth_config.redirect_uri
        )
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return auth_url
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Token data
        """
        from google_auth_oauthlib.flow import Flow
        
        if not oauth_config.is_configured():
            raise ValueError("OAuth not configured")
        
        flow = Flow.from_client_config(
            oauth_config.get_client_config(),
            scopes=GMAIL_SCOPES,
            redirect_uri=oauth_config.redirect_uri
        )
        
        flow.fetch_token(code=code)
        
        self.credentials = flow.credentials
        self._save_credentials()
        
        return {
            'access_token': self.credentials.token,
            'refresh_token': self.credentials.refresh_token,
            'expires_in': self.credentials.expiry.timestamp() if self.credentials.expiry else None
        }
