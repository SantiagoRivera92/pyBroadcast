import requests
import json
import os
import secrets
import base64
import hashlib
import threading
import socket
import time
from http.server import HTTPServer
from urllib.parse import urlencode, quote
from typing import Dict, Optional
from api.oauth_callback_handler import OAuthCallbackHandler
from dotenv import load_dotenv

load_dotenv()

OAUTH_CONFIG = {
    'client_id': os.getenv('IBROADCAST_CLIENT_ID', ''),
    'client_secret': os.getenv('IBROADCAST_CLIENT_SECRET', ''),
    'redirect_uri': 'http://localhost:8888/callback',
    'authorization_url': 'https://oauth.ibroadcast.com/authorize',
    'token_url': 'https://oauth.ibroadcast.com/token',
    'device_code_url': 'https://oauth.ibroadcast.com/device/code',
    'scopes': 'user.library:read user.queue:read user.queue:write'
}

TOKEN_FILE = 'token.json'

class iBroadcastAPI:
    def __init__(self):
        self.base_url = "https://api.ibroadcast.com"
        self.library_url = "https://library.ibroadcast.com"
        self.streaming_server = "https://streaming.ibroadcast.com"
        self.access_token = None
        self.refresh_token = None
        self.session = requests.Session()
        self.library = {'artists': {}, 'albums': {}, 'tracks': {}, 'playlists': {}}
        self.load_cached_token()

    def load_cached_token(self):
        """Load token from local file on startup"""
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r') as f:
                    data = json.load(f)
                    self.access_token = data.get('access_token')
                    self.refresh_token = data.get('refresh_token')
            except Exception as e:
                print(f"Error loading cache: {e}")

    def save_token(self):
        """Save current tokens to local file"""
        with open(TOKEN_FILE, 'w') as f:
            json.dump({
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
            }, f)

    def logout(self):
        """Delete cached token and reset state"""
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        self.access_token = None
        self.refresh_token = None
        self.library = {'artists': {}, 'albums': {}, 'tracks': {}, 'playlists': {}}

    def load_library(self) -> Dict:
        """Load library using the API's index mapping system"""
        try:
            url = f"{self.library_url}/s/JSON/library"
            headers = {'Authorization': f'Bearer {self.access_token}', 'Content-Type': 'application/json'}
            response = self.session.post(url, json={'mode': 'library'}, headers=headers)
            data = response.json()
            
            if not data.get('authenticated', True):
                if self.refresh_access_token():
                    return self.load_library()
                return {'success': False, 'message': 'Auth expired'}

            if 'settings' in data:
                streaming_server = data['settings'].get('streaming_server')
                if streaming_server:
                    self.streaming_server = streaming_server

            if 'library' in data:
                lib = data['library']
                
                def process_section(section_name):
                    section = lib.get(section_name, {})
                    index_map = section.get('map', {})
                    processed = {}
                    
                    for item_id, item_data in section.items():
                        if item_id == 'map': continue
                        
                        # Convert array to dict using the map
                        if isinstance(item_data, list):
                            obj = {}
                            for key, index in index_map.items():
                                if isinstance(index, int):
                                    if index < len(item_data):
                                        obj[key] = item_data[index]
                            obj['item_id'] = item_id
                            processed[int(item_id)] = obj
                        elif isinstance(item_data, dict):
                            processed[int(item_id)] = item_data
                    return processed

                self.library['artists'] = process_section('artists')
                self.library['albums'] = process_section('albums')
                self.library['tracks'] = process_section('tracks')
                self.library['playlists'] = process_section('playlists')

                # Fill in missing artwork for albums
                for album_id, album in self.library['albums'].items():
                    if not isinstance(album, dict):
                        continue
                    if not album.get('artwork_id'):
                        for track in self.library['tracks'].values():
                            if isinstance(track, dict) and track.get('album_id') == album_id and track.get('artwork_id'):
                                album['artwork_id'] = track['artwork_id']
                                break

                # Remove artists with no albums assigned
                album_artist_ids = set()
                for album in self.library['albums'].values():
                    if isinstance(album, dict) and 'artist_id' in album:
                        album_artist_ids.add(album['artist_id'])
                self.library['artists'] = {aid: artist for aid, artist in self.library['artists'].items() if aid in album_artist_ids}

                # Sort albums by artist and release date
                self.library['albums'] = dict(sorted(
                    self.library['albums'].items(),
                    key=lambda x: (
                        self.library['artists'].get(self.library['albums'][x[0]].get('artist_id', -1), {}).get('name', ''),
                        self.library['albums'][x[0]].get('release_date', '')
                    )
                ))

                self.save_token()
                return {'success': True}
            return {'success': False}
        except Exception as e:
            return {'success': False, 'message': str(e)}
        
    def generate_pkce_pair(self):
        """Generate PKCE code_verifier and code_challenge"""
        self.code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        challenge_bytes = hashlib.sha256(self.code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
        return code_challenge
    
    def start_oauth_flow(self) -> Dict:
        """Start OAuth authorization flow using authorization_code grant"""
        try:
            code_challenge = self.generate_pkce_pair()
            self.oauth_state = secrets.token_urlsafe(32)
            
            params = {
                'client_id': OAUTH_CONFIG['client_id'],
                'state': self.oauth_state,
                'response_type': 'code',
                'code_challenge': code_challenge,
                'code_challenge_method': 'S256',
                'scope': OAUTH_CONFIG['scopes'],
                'redirect_uri': OAUTH_CONFIG['redirect_uri']
            }
            
            auth_url = f"{OAUTH_CONFIG['authorization_url']}?{urlencode(params)}"
            self.start_callback_server()
            
            return {'success': True, 'auth_url': auth_url}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def start_callback_server(self):
        """Start HTTP server to handle OAuth callback"""
        def run_server():
            try:
                server = HTTPServer(('localhost', 8888), OAuthCallbackHandler)
                server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.timeout = 300
                server.handle_request()
                server.server_close()
            except Exception as e:
                print(f"Callback server error: {e}")
        
        OAuthCallbackHandler.auth_code = None
        OAuthCallbackHandler.auth_state = None
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
    
    def check_callback_status(self) -> Dict:
        """Check if OAuth callback has been received"""
        if OAuthCallbackHandler.auth_code is not None:
            if OAuthCallbackHandler.auth_state != self.oauth_state:
                return {'success': False, 'message': 'State mismatch - possible CSRF attack'}
            
            auth_code = OAuthCallbackHandler.auth_code
            OAuthCallbackHandler.auth_code = None
            OAuthCallbackHandler.auth_state = None
            
            return {'success': True, 'code': auth_code}
        
        return {'success': False, 'pending': True}
    
    def exchange_code_for_token(self, auth_code: str) -> Dict:
        """Exchange authorization code for access token"""
        try:
            data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'client_id': OAUTH_CONFIG['client_id'],
                'redirect_uri': OAUTH_CONFIG['redirect_uri'],
                'code_verifier': self.code_verifier
            }
            
            response = requests.post(
                OAUTH_CONFIG['token_url'],
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.refresh_token = token_data['refresh_token']
                self.save_token()
                return {'success': True, 'authenticated': True}
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                return {'success': False, 'message': error_data.get('error_description', f'HTTP {response.status_code}')}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def refresh_access_token(self) -> bool:
        """Refresh the access token"""
        try:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': OAUTH_CONFIG['client_id'],
                'redirect_uri': OAUTH_CONFIG['redirect_uri']
            }
            
            response = requests.post(
                OAUTH_CONFIG['token_url'],
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.refresh_token = token_data['refresh_token']
                self.save_token()
                return True
            return False
        except Exception as e:
            return False

    def get_stream_url(self, track_id: int) -> str:
        """
        Get streaming URL for a track following iBroadcast's streaming format.
        
        Format: [streaming_server]/[bitrate]/[url]?Expires=[now]&Signature=[token]&file_id=[file_id]&user_id=[user_id]&platform=native&version=1.0
        
        Args:
            track_id: The track ID
            bitrate: Desired bitrate (96, 128, 192, 256, 320, orig)
        
        Returns:
            Complete streaming URL
        """

        track = None
        for tr in self.library['tracks'].values():
            if str(tr.get('item_id')) == str(track_id):
                track = tr
                break

        if not track:
            return ""

        # Get track URL and file_id from library
        file_id = track.get('file', '')
        
        if not file_id:
            print("Missing data for streaming URL")
            return ""
        
        # Current timestamp in milliseconds
        expires = int(time.time() * 1000)
        
        # Build query parameters
        params = {
            'Expires': expires,
            'Signature': self.access_token,
            'file_id': file_id,
            'platform': 'pyBroadcast',
            'version': '0.1'
        }
        
        # Construct final URL
        stream_url = f"{self.streaming_server}{file_id}?{urlencode(params)}"
        
        return stream_url
    
    def get_artwork_url(self, artwork_id: Optional[str]) -> str:
        """Get artwork URL"""
        if not artwork_id:
            return ""
        return f"https://artwork.ibroadcast.com/artwork/{artwork_id}"