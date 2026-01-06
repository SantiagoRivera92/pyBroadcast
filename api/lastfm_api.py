import hashlib
import json
import time
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class LastFMAPI:
    """Handle Last.fm authentication and scrobbling"""
    
    API_KEY = os.getenv("LASTFM_API_KEY")
    API_SECRET = os.getenv("LASTFM_API_SECRET")
    if not API_KEY or not API_SECRET:
        raise ValueError("Last.fm API_KEY and API_SECRET must be set in environment variables.")
    API_URL = "http://ws.audioscrobbler.com/2.0/"
    
    def __init__(self):
        self.session_key = None
        self.username = None
        self.config_path = Path.home() / ".ibroadcast" / "lastfm_config.json"
        self.load_credentials()
    
    def load_credentials(self):
        """Load saved Last.fm credentials"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.session_key = data.get('session_key')
                    self.username = data.get('username')
            except Exception as e:
                print(f"Error loading Last.fm credentials: {e}")
    
    def save_credentials(self):
        """Save Last.fm credentials to disk"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_path, 'w') as f:
                json.dump({
                    'session_key': self.session_key,
                    'username': self.username
                }, f)
        except Exception as e:
            print(f"Error saving Last.fm credentials: {e}")
    
    def clear_credentials(self):
        """Clear saved credentials"""
        self.session_key = None
        self.username = None
        if self.config_path.exists():
            self.config_path.unlink()
    
    def generate_signature(self, params):
        """Generate API signature for authenticated calls"""
        # Create a copy and remove format and signature if present
        sig_params = {k: v for k, v in params.items() if k not in ['format', 'api_sig']}
        
        # Sort parameters and create signature string
        sig_string = ""
        for key in sorted(sig_params.keys()):
            sig_string += key + str(sig_params[key])
        if self.API_SECRET:
            sig_string += self.API_SECRET
        
        return hashlib.md5(sig_string.encode('utf-8')).hexdigest()
    
    def authenticate(self, username, password):
        """Authenticate with Last.fm using username and password"""
        # Build params for signature (without format)
        sig_params = {
            'method': 'auth.getMobileSession',
            'username': username,
            'password': password,
            'api_key': self.API_KEY
        }
        
        # Generate signature
        api_sig = self.generate_signature(sig_params)
        
        # Build full params for request (with format and signature)
        params = {
            **sig_params,
            'api_sig': api_sig,
            'format': 'json'
        }
        
        try:
            response = requests.post(self.API_URL, data=params)
            data = response.json()
            
            if 'session' in data:
                self.session_key = data['session']['key']
                self.username = data['session']['name']
                self.save_credentials()
                return {'success': True}
            else:
                error_msg = data.get('message', 'Unknown error')
                return {'success': False, 'message': error_msg}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def scrobble(self, artist, track, album=None, timestamp=None):
        """Scrobble a track to Last.fm"""
        if not self.session_key:
            return {'success': False, 'message': 'Not authenticated'}
        
        if timestamp is None:
            timestamp = int(time.time())
        
        # Build params for signature (without format)
        sig_params = {
            'method': 'track.scrobble',
            'artist': artist,
            'track': track,
            'timestamp': timestamp,
            'api_key': self.API_KEY,
            'sk': self.session_key
        }
        
        if album:
            sig_params['album'] = album
        
        # Generate signature
        api_sig = self.generate_signature(sig_params)
        
        # Build full params for request
        params = {
            **sig_params,
            'api_sig': api_sig,
            'format': 'json'
        }
        
        try:
            response = requests.post(self.API_URL, data=params)
            data = response.json()
            
            if 'scrobbles' in data:
                return {'success': True}
            else:
                error_msg = data.get('message', 'Unknown error')
                return {'success': False, 'message': error_msg}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def update_now_playing(self, artist, track, album=None):
        """Update Now Playing status on Last.fm"""
        if not self.session_key:
            return {'success': False, 'message': 'Not authenticated'}
        
        # Build params for signature (without format)
        sig_params = {
            'method': 'track.updateNowPlaying',
            'artist': artist,
            'track': track,
            'api_key': self.API_KEY,
            'sk': self.session_key
        }
        
        if album:
            sig_params['album'] = album
        
        # Generate signature
        api_sig = self.generate_signature(sig_params)
        
        # Build full params for request
        params = {
            **sig_params,
            'api_sig': api_sig,
            'format': 'json'
        }
        
        try:
            response = requests.post(self.API_URL, data=params)
            data = response.json()
            
            if 'nowplaying' in data:
                return {'success': True}
            else:
                error_msg = data.get('message', 'Unknown error')
                return {'success': False, 'message': error_msg}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return self.session_key is not None