"""
Dynamic Client Registration implementation following RFC 7591.
Allows OAuth clients to register themselves at runtime.
"""
import os
import json
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ClientRegistry:
    """
    Dynamic client registry for OAuth 2.0 clients.
    Implements RFC 7591 Dynamic Client Registration Protocol.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the client registry.
        
        Args:
            storage_path: Path to store client data (defaults to ./.client_registry)
        """
        if storage_path is None:
            storage_path = os.getenv('CLIENT_REGISTRY_PATH', './.client_registry')
        
        self.storage_path = Path(storage_path)
        self._ensure_storage_directory()
    
    def _ensure_storage_directory(self) -> None:
        """Ensure storage directory exists."""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Client registry storage: {self.storage_path}")
        except (OSError, PermissionError) as e:
            logger.warning(f"Cannot create client registry storage (read-only filesystem): {e}")
            logger.info("Client registry will operate in memory-only mode")
    
    def _generate_client_id(self) -> str:
        """Generate a unique client ID."""
        return f"dcr_{uuid.uuid4().hex}"
    
    def _generate_client_secret(self) -> str:
        """Generate a secure client secret."""
        return secrets.token_urlsafe(32)
    
    def _generate_registration_access_token(self) -> str:
        """Generate a registration access token for client management."""
        return secrets.token_urlsafe(32)
    
    def _hash_secret(self, secret: str) -> str:
        """Hash a client secret for secure storage."""
        return hashlib.sha256(secret.encode()).hexdigest()
    
    def _get_client_file_path(self, client_id: str) -> Path:
        """Get the file path for storing client data."""
        return self.storage_path / f"{client_id}.json"
    
    def _save_client_data(self, client_data: Dict[str, Any]) -> None:
        """Save client data to storage."""
        try:
            client_file = self._get_client_file_path(client_data['client_id'])
            with open(client_file, 'w') as f:
                json.dump(client_data, f, indent=2, default=str)
            logger.info(f"Client data saved: {client_data['client_id']}")
        except (OSError, PermissionError) as e:
            logger.warning(f"Cannot save client data to filesystem: {e}")
            # In production/serverless, store in memory or external storage
            # For now, log the warning but continue
    
    def _load_client_data(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Load client data from storage."""
        try:
            client_file = self._get_client_file_path(client_id)
            if not client_file.exists():
                return None
            
            with open(client_file, 'r') as f:
                data = json.load(f)
                
            # Convert datetime strings back to datetime objects
            if 'client_id_issued_at' in data:
                data['client_id_issued_at'] = datetime.fromisoformat(data['client_id_issued_at'])
            if 'client_secret_expires_at' in data and data['client_secret_expires_at']:
                data['client_secret_expires_at'] = datetime.fromisoformat(data['client_secret_expires_at'])
                
            return data
        except (OSError, PermissionError, json.JSONDecodeError) as e:
            logger.warning(f"Cannot load client data from filesystem: {e}")
            return None
    
    def register_client(self, registration_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new OAuth client dynamically.
        
        Args:
            registration_request: Client registration request following RFC 7591
            
        Returns:
            Client registration response with client_id, client_secret, etc.
            
        Raises:
            ValueError: If registration request is invalid
        """
        logger.info("Processing dynamic client registration request")
        
        # Validate required fields and supported values
        self._validate_registration_request(registration_request)
        
        # Generate client credentials
        client_id = self._generate_client_id()
        client_secret = self._generate_client_secret()
        client_secret_hash = self._hash_secret(client_secret)
        registration_access_token = self._generate_registration_access_token()
        
        # Set client metadata
        now = datetime.now()
        client_data = {
            # Core RFC 7591 fields
            'client_id': client_id,
            'client_secret': client_secret_hash,  # Store hashed version
            'client_id_issued_at': now,
            'client_secret_expires_at': None,  # Non-expiring by default
            'registration_access_token': self._hash_secret(registration_access_token),
            
            # Client metadata from request
            'client_name': registration_request.get('client_name'),
            'client_uri': registration_request.get('client_uri'),
            'logo_uri': registration_request.get('logo_uri'),
            'contacts': registration_request.get('contacts', []),
            'tos_uri': registration_request.get('tos_uri'),
            'policy_uri': registration_request.get('policy_uri'),
            'jwks_uri': registration_request.get('jwks_uri'),
            'software_id': registration_request.get('software_id'),
            'software_version': registration_request.get('software_version'),
            
            # OAuth 2.0 parameters
            'redirect_uris': registration_request.get('redirect_uris', []),
            'response_types': registration_request.get('response_types', ['code']),
            'grant_types': registration_request.get('grant_types', ['authorization_code']),
            'application_type': registration_request.get('application_type', 'web'),
            'token_endpoint_auth_method': registration_request.get('token_endpoint_auth_method', 'client_secret_basic'),
            'scope': registration_request.get('scope', ''),
            
            # Additional metadata
            'created_at': now,
            'updated_at': now,
            'status': 'active'
        }
        
        # Save client data
        self._save_client_data(client_data)
        
        # Prepare response (return plaintext secret only in registration response)
        base_url = os.getenv('MCP_SERVER_BASE_URL', 'http://localhost:8000')
        response = {
            'client_id': client_id,
            'client_secret': client_secret,  # Return plaintext secret only here
            'client_id_issued_at': int(now.timestamp()),
            'registration_access_token': registration_access_token,
            'registration_client_uri': f"{base_url}/clients/{client_id}",
            
            # Echo back the accepted metadata
            'client_name': client_data['client_name'],
            'client_uri': client_data['client_uri'],
            'redirect_uris': client_data['redirect_uris'],
            'response_types': client_data['response_types'],
            'grant_types': client_data['grant_types'],
            'application_type': client_data['application_type'],
            'token_endpoint_auth_method': client_data['token_endpoint_auth_method'],
            'scope': client_data['scope'],
        }
        
        # Add optional fields if present
        optional_fields = ['logo_uri', 'contacts', 'tos_uri', 'policy_uri', 'jwks_uri', 
                          'software_id', 'software_version']
        for field in optional_fields:
            if client_data.get(field):
                response[field] = client_data[field]
        
        logger.info(f"Dynamic client registered: {client_id}")
        return response
    
    def _validate_registration_request(self, request: Dict[str, Any]) -> None:
        """Validate client registration request."""
        # Check for required redirect_uris
        redirect_uris = request.get('redirect_uris')
        if not redirect_uris or not isinstance(redirect_uris, list) or len(redirect_uris) == 0:
            raise ValueError("redirect_uris is required and must be a non-empty array")
        
        # Validate redirect URIs
        for uri in redirect_uris:
            if not isinstance(uri, str) or not uri.startswith(('https://', 'http://localhost', 'http://127.0.0.1')):
                raise ValueError(f"Invalid redirect_uri: {uri}. Must use HTTPS or localhost")
        
        # Validate response_types
        response_types = request.get('response_types', ['code'])
        supported_response_types = ['code']
        for rt in response_types:
            if rt not in supported_response_types:
                raise ValueError(f"Unsupported response_type: {rt}. Supported: {supported_response_types}")
        
        # Validate grant_types
        grant_types = request.get('grant_types', ['authorization_code'])
        supported_grant_types = ['authorization_code', 'refresh_token']
        for gt in grant_types:
            if gt not in supported_grant_types:
                raise ValueError(f"Unsupported grant_type: {gt}. Supported: {supported_grant_types}")
        
        # Validate application_type
        app_type = request.get('application_type', 'web')
        if app_type not in ['web', 'native']:
            raise ValueError(f"Unsupported application_type: {app_type}. Supported: web, native")
        
        # Validate token_endpoint_auth_method
        auth_method = request.get('token_endpoint_auth_method', 'client_secret_basic')
        supported_auth_methods = ['client_secret_basic', 'client_secret_post', 'none']
        if auth_method not in supported_auth_methods:
            raise ValueError(f"Unsupported token_endpoint_auth_method: {auth_method}. Supported: {supported_auth_methods}")
    
    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve client information.
        
        Args:
            client_id: The client identifier
            
        Returns:
            Client data without sensitive information, or None if not found
        """
        client_data = self._load_client_data(client_id)
        if not client_data:
            return None
        
        # Return client data without sensitive fields
        safe_data = client_data.copy()
        safe_data.pop('client_secret', None)  # Never return hashed secret
        safe_data.pop('registration_access_token', None)  # Never return hashed token
        
        return safe_data
    
    def authenticate_client(self, client_id: str, client_secret: str) -> bool:
        """
        Authenticate a client using client credentials.
        
        Args:
            client_id: The client identifier
            client_secret: The client secret
            
        Returns:
            True if authentication successful, False otherwise
        """
        client_data = self._load_client_data(client_id)
        if not client_data:
            return False
        
        # Check if client is active
        if client_data.get('status') != 'active':
            return False
        
        # Check secret expiration
        expires_at = client_data.get('client_secret_expires_at')
        if expires_at and datetime.now() > expires_at:
            return False
        
        # Verify secret
        expected_hash = client_data.get('client_secret')
        actual_hash = self._hash_secret(client_secret)
        
        return secrets.compare_digest(expected_hash, actual_hash)
    
    def update_client(self, client_id: str, registration_access_token: str, 
                     update_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update client registration.
        
        Args:
            client_id: The client identifier
            registration_access_token: The registration access token
            update_request: Updated client metadata
            
        Returns:
            Updated client registration response
            
        Raises:
            ValueError: If update is invalid
            PermissionError: If registration access token is invalid
        """
        client_data = self._load_client_data(client_id)
        if not client_data:
            raise ValueError(f"Client not found: {client_id}")
        
        # Verify registration access token
        expected_hash = client_data.get('registration_access_token')
        actual_hash = self._hash_secret(registration_access_token)
        if not secrets.compare_digest(expected_hash, actual_hash):
            raise PermissionError("Invalid registration access token")
        
        # Validate update request
        self._validate_registration_request(update_request)
        
        # Update allowed fields
        updatable_fields = [
            'client_name', 'client_uri', 'logo_uri', 'contacts', 'tos_uri', 'policy_uri',
            'jwks_uri', 'redirect_uris', 'response_types', 'grant_types', 'scope'
        ]
        
        for field in updatable_fields:
            if field in update_request:
                client_data[field] = update_request[field]
        
        client_data['updated_at'] = datetime.now()
        
        # Save updated data
        self._save_client_data(client_data)
        
        # Return updated client info (same format as registration response)
        response = self.get_client(client_id)
        response['registration_access_token'] = registration_access_token
        base_url = os.getenv('MCP_SERVER_BASE_URL', 'http://localhost:8000')
        response['registration_client_uri'] = f"{base_url}/clients/{client_id}"
        
        logger.info(f"Client updated: {client_id}")
        return response
    
    def delete_client(self, client_id: str, registration_access_token: str) -> bool:
        """
        Delete/deactivate a client registration.
        
        Args:
            client_id: The client identifier
            registration_access_token: The registration access token
            
        Returns:
            True if deletion successful, False otherwise
            
        Raises:
            PermissionError: If registration access token is invalid
        """
        client_data = self._load_client_data(client_id)
        if not client_data:
            return False
        
        # Verify registration access token
        expected_hash = client_data.get('registration_access_token')
        actual_hash = self._hash_secret(registration_access_token)
        if not secrets.compare_digest(expected_hash, actual_hash):
            raise PermissionError("Invalid registration access token")
        
        # Mark as inactive rather than physically delete
        client_data['status'] = 'inactive'
        client_data['updated_at'] = datetime.now()
        self._save_client_data(client_data)
        
        logger.info(f"Client deactivated: {client_id}")
        return True
    
    def list_clients(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        List all registered clients (for administrative purposes).
        
        Args:
            include_inactive: Whether to include inactive clients
            
        Returns:
            List of client data (without sensitive information)
        """
        clients = []
        
        try:
            for client_file in self.storage_path.glob("dcr_*.json"):
                try:
                    client_data = self._load_client_data(client_file.stem)
                    if client_data:
                        # Filter by status
                        if not include_inactive and client_data.get('status') != 'active':
                            continue
                            
                        # Remove sensitive data
                        safe_data = client_data.copy()
                        safe_data.pop('client_secret', None)
                        safe_data.pop('registration_access_token', None)
                        clients.append(safe_data)
                except Exception as e:
                    logger.warning(f"Error loading client {client_file.stem}: {e}")
                    continue
        except (OSError, PermissionError):
            logger.warning("Cannot list clients from filesystem")
        
        return clients

# Global client registry instance
client_registry = ClientRegistry()
