"""
Secure credential management using keyring library.
Stores API keys and secrets securely in the system keychain.
"""
import keyring
from typing import Optional, Dict

class CredentialsManager:
    """Manages secure storage of API credentials using system keychain"""
    
    SERVICE_NAME = "pyBroadcast"
    
    # Credential keys
    IBROADCAST_CLIENT_ID = "ibroadcast_client_id"
    IBROADCAST_CLIENT_SECRET = "ibroadcast_client_secret"
    IBROADCAST_ACCESS_TOKEN = "ibroadcast_access_token"
    IBROADCAST_REFRESH_TOKEN = "ibroadcast_refresh_token"
    LASTFM_API_KEY = "lastfm_api_key"
    LASTFM_API_SECRET = "lastfm_api_secret"
    LASTFM_SESSION_KEY = "lastfm_session_key"
    LASTFM_USERNAME = "lastfm_username"
    
    @classmethod
    def set_credential(cls, key: str, value: str) -> bool:
        """
        Store a credential securely
        
        Args:
            key: The credential key
            value: The credential value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            keyring.set_password(cls.SERVICE_NAME, key, value)
            return True
        except Exception as e:
            print(f"Error storing credential {key}: {e}")
            return False
    
    @classmethod
    def get_credential(cls, key: str) -> Optional[str]:
        """
        Retrieve a credential
        
        Args:
            key: The credential key
            
        Returns:
            The credential value or None if not found
        """
        try:
            return keyring.get_password(cls.SERVICE_NAME, key)
        except Exception as e:
            print(f"Error retrieving credential {key}: {e}")
            return None
    
    @classmethod
    def delete_credential(cls, key: str) -> bool:
        """
        Delete a credential
        
        Args:
            key: The credential key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            keyring.delete_password(cls.SERVICE_NAME, key)
            return True
        except Exception as e:
            print(f"Error deleting credential {key}: {e}")
            return False
    
    @classmethod
    def has_ibroadcast_credentials(cls) -> bool:
        """Check if iBroadcast credentials are configured"""
        client_id = cls.get_credential(cls.IBROADCAST_CLIENT_ID)
        client_secret = cls.get_credential(cls.IBROADCAST_CLIENT_SECRET)
        return bool(client_id and client_secret)
    
    @classmethod
    def has_lastfm_credentials(cls) -> bool:
        """Check if Last.fm credentials are configured"""
        api_key = cls.get_credential(cls.LASTFM_API_KEY)
        api_secret = cls.get_credential(cls.LASTFM_API_SECRET)
        return bool(api_key and api_secret)
    
    @classmethod
    def get_ibroadcast_credentials(cls) -> Dict[str, Optional[str]]:
        """Get all iBroadcast credentials"""
        return {
            'client_id': cls.get_credential(cls.IBROADCAST_CLIENT_ID),
            'client_secret': cls.get_credential(cls.IBROADCAST_CLIENT_SECRET),
            'access_token': cls.get_credential(cls.IBROADCAST_ACCESS_TOKEN),
            'refresh_token': cls.get_credential(cls.IBROADCAST_REFRESH_TOKEN),
        }
    
    @classmethod
    def get_lastfm_credentials(cls) -> Dict[str, Optional[str]]:
        """Get all Last.fm credentials"""
        return {
            'api_key': cls.get_credential(cls.LASTFM_API_KEY),
            'api_secret': cls.get_credential(cls.LASTFM_API_SECRET),
            'session_key': cls.get_credential(cls.LASTFM_SESSION_KEY),
            'username': cls.get_credential(cls.LASTFM_USERNAME),
        }
    
    @classmethod
    def set_ibroadcast_tokens(cls, access_token: str, refresh_token: Optional[str] = None) -> bool:
        """Store iBroadcast OAuth tokens"""
        success = cls.set_credential(cls.IBROADCAST_ACCESS_TOKEN, access_token)
        if refresh_token:
            success = success and cls.set_credential(cls.IBROADCAST_REFRESH_TOKEN, refresh_token)
        return success
    
    @classmethod
    def set_lastfm_session(cls, session_key: str, username: str) -> bool:
        """Store Last.fm session information"""
        success = cls.set_credential(cls.LASTFM_SESSION_KEY, session_key)
        success = success and cls.set_credential(cls.LASTFM_USERNAME, username)
        return success
    
    @classmethod
    def clear_ibroadcast_credentials(cls) -> bool:
        """Clear all iBroadcast credentials"""
        keys = [
            cls.IBROADCAST_CLIENT_ID,
            cls.IBROADCAST_CLIENT_SECRET,
            cls.IBROADCAST_ACCESS_TOKEN,
            cls.IBROADCAST_REFRESH_TOKEN,
        ]
        return all(cls.delete_credential(key) for key in keys)
    
    @classmethod
    def clear_lastfm_credentials(cls) -> bool:
        """Clear all Last.fm credentials"""
        keys = [
            cls.LASTFM_API_KEY,
            cls.LASTFM_API_SECRET,
            cls.LASTFM_SESSION_KEY,
            cls.LASTFM_USERNAME,
        ]
        return all(cls.delete_credential(key) for key in keys)
    
    @classmethod
    def is_fully_configured(cls) -> bool:
        """Check if all required credentials are present"""
        return cls.has_ibroadcast_credentials()