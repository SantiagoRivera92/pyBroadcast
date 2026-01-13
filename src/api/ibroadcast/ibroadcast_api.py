import requests
import json
import os
import secrets
import base64
import hashlib
import threading
import time
from src.core.credentials_manager import CredentialsManager

from typing import List

from http.server import HTTPServer
from urllib.parse import urlencode
from typing import Dict, Optional

from src.api.ibroadcast.oauth_callback_handler import OAuthCallbackHandler
from src.api.artwork_cache import ArtworkCache
from src.api.ibroadcast.database import DatabaseManager
from src.api.ibroadcast.models import Artist, Album, Track, Playlist, BaseModel

def get_oauth_config():
    return {
        'client_id': CredentialsManager.get_credential(CredentialsManager.IBROADCAST_CLIENT_ID) or '',
        'client_secret': CredentialsManager.get_credential(CredentialsManager.IBROADCAST_CLIENT_SECRET) or '',
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
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.session = requests.Session()
        
        # Initialize database and artwork cache
        self.db = DatabaseManager()
        self.artwork_cache = ArtworkCache()
        
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
                pass

    def save_token(self):
        """Save current tokens to local file"""
        with open(TOKEN_FILE, 'w') as f:
            json.dump({
                'access_token': self.access_token,
                'refresh_token': self.refresh_token
            }, f)

    def logout(self):
        """Delete cached token and reset state"""
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        self.access_token = None
        self.refresh_token = None
        self.db.clear_database()

    def _process_section(self, lib_data, section_name):
        """Helper to decode iBroadcast map-based JSON response"""
        section = lib_data.get(section_name, {})
        index_map = section.get('map', {})
        processed = {}
        
        for item_id, item_data in section.items():
            if item_id == 'map': continue
            if isinstance(item_data, list):
                obj = {}
                for key, index in index_map.items():
                    if key != "artists_additional":
                        if isinstance(index, int) and index < len(item_data):
                            val = item_data[index]
                            # Force ID types
                            if (key.endswith("_id") or key == "artwork_id") and isinstance(val, str) and val.isdigit():
                                val = int(val)
                            obj[key] = val
                    else:
                        additional = []
                        add_map = index_map.get('artists_additional_map', {})
                        if item_data is not None and index < len(item_data) and item_data[index] is not None:
                            for item in item_data[index]:
                                add_obj = {k: item[i] for k, i in add_map.items() if isinstance(i, int) and i < len(item)}
                                additional.append(add_obj)
                        obj[key] = additional
                
                final_id = int(item_id) if str(item_id).isdigit() else item_id
                obj['item_id'] = final_id
                processed[final_id] = obj
        return processed

    def load_library(self) -> Dict:
        """Load library from API and sync to SQLite"""
        oauth_config = get_oauth_config()
        if not oauth_config['client_id'] or not oauth_config['client_secret']:
            return {'success': False, 'message': 'Missing iBroadcast OAuth credentials'}
        try:
            url = f"{self.library_url}/s/JSON/library"
            headers = {'Authorization': f'Bearer {self.access_token}', 'Content-Type': 'application/json'}
            response = self.session.post(url, json={'mode': 'library'}, headers=headers)
            try:
                data = response.json()
            except ValueError:
                return {'success': False, 'message': 'Invalid API response'}

            if not data.get('authenticated', True):
                if self.refresh_access_token():
                    return self.load_library()
                return {'success': False, 'message': 'Auth expired'}

            if 'settings' in data:
                self.streaming_server = data['settings'].get('streaming_server', self.streaming_server)

            if 'library' in data:
                lib = data['library']
                processed_lib = {
                    'artists': self._process_section(lib, 'artists'),
                    'albums': self._process_section(lib, 'albums'),
                    'tracks': self._process_section(lib, 'tracks'),
                    'playlists': self._process_section(lib, 'playlists')
                }

                # Backfill missing Album artwork from its children tracks
                for al_id, al in processed_lib['albums'].items():
                    if not al.get('artwork_id'):
                        for t_id in al.get('tracks', []):
                            track_data = processed_lib['tracks'].get(t_id)
                            if track_data and track_data.get('artwork_id'):
                                al['artwork_id'] = track_data['artwork_id']
                                break
                
                # Remove "Recently Played" and "Most Recently Uploaded" playlists
                processed_lib['playlists'] = {k: v for k, v in processed_lib['playlists'].items() if v.get('name') not in ['Recently Played', 'Most Recent Uploads']}
                
                # Save to DB
                self.db.sync_library(processed_lib)
                self.save_token()

                # Start background caching
                threading.Thread(target=self._precache_artworks, daemon=True).start()

                return {'success': True}
            return {'success': False}
        except Exception as e:
            raise e
            return {'success': False, 'message': str(e)}
    
    def _precache_artworks(self):
        """Background task to pre-cache all artworks from DB references"""
        artwork_ids = self.db.get_all_artwork_ids()
        
        for artwork_id in artwork_ids:
            if not self.artwork_cache.is_cached(artwork_id):
                artwork_url = f"https://artwork.ibroadcast.com/artwork/{artwork_id}"
                self.artwork_cache.download_and_cache(artwork_url, artwork_id)
        

    def get_stream_url(self, track_id: int) -> str:
        """Get streaming URL by querying the database"""
        track = self.db.get_track_by_id(track_id)
        if not track or not track.file:
            return ""
        
        expires = int(time.time() * 1000)
        params = {
            'Expires': expires,
            'Signature': self.access_token,
            'file_id': track.file,
            'platform': 'pyBroadcast',
            'version': '0.1'
        }
        return f"{self.streaming_server}{track.file}?{urlencode(params)}"

    def get_artwork_url(self, artwork_id: Optional[int], use_cache: bool = True) -> str:
        if not artwork_id or artwork_id == 0:
            return ""
        if use_cache:
            cached_url = self.artwork_cache.get_cached_url(artwork_id)
            if cached_url:
                return cached_url
        return f"https://artwork.ibroadcast.com/artwork/{artwork_id}"

    # --- Playlist Operations ---
    # These call the API and then trigger a reload of the library to keep the DB in sync.

    def create_playlist(self, name: str, **kwargs) -> Dict:
        url = f"{self.base_url}/s/JSON/playlists"
        data = {'mode': 'createplaylist', 'name': name, **kwargs}
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        response = self.session.post(url, json=data, headers=headers)
        if response.status_code == 200:
            self.load_library() # Update local DB
            return {'success': True, **response.json()}
        return {'success': False, 'message': 'API Error'}

    def append_to_playlist(self, playlist_id: int, tracks: list) -> Dict:
        url = f"{self.base_url}/s/JSON/playlists"
        data = {'mode': 'appendplaylist', 'playlist_id': playlist_id, 'tracks': tracks}
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        if self.session.post(url, json=data, headers=headers).status_code == 200:
            self.load_library()
            return {'success': True}
        return {'success': False}

    # --- OAuth Logic ---

    def generate_pkce_pair(self):
        self.code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        challenge_bytes = hashlib.sha256(self.code_verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')

    def start_oauth_flow(self) -> Dict:
        try:
            oauth_config = get_oauth_config()
            code_challenge = self.generate_pkce_pair()
            self.oauth_state = secrets.token_urlsafe(32)
            params = {
                'client_id': oauth_config['client_id'],
                'state': self.oauth_state,
                'response_type': 'code',
                'code_challenge': code_challenge,
                'code_challenge_method': 'S256',
                'scope': oauth_config['scopes'],
                'redirect_uri': oauth_config['redirect_uri']
            }
            auth_url = f"{oauth_config['authorization_url']}?{urlencode(params)}"
            self.start_callback_server()
            return {'success': True, 'auth_url': auth_url}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def start_callback_server(self):
        def run_server():
            server = HTTPServer(('localhost', 8888), OAuthCallbackHandler)
            server.handle_request()
        threading.Thread(target=run_server, daemon=True).start()
        
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
        oauth_config = get_oauth_config()
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'client_id': oauth_config['client_id'],
            'redirect_uri': oauth_config['redirect_uri'],
            'code_verifier': self.code_verifier
        }
        resp = requests.post(oauth_config['token_url'], data=data)
        if resp.status_code == 200:
            token_data = resp.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data['refresh_token']
            self.save_token()
            return {'success': True}
        return {'success': False}

    def refresh_access_token(self) -> bool:
        oauth_config = get_oauth_config()
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': oauth_config['client_id']
        }
        resp = requests.post(oauth_config['token_url'], data=data)
        if resp.status_code == 200:
            token_data = resp.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data['refresh_token']
            self.save_token()
            return True
        return False

    def get_artists(self) -> List[Artist]:
        """Returns all artists sorted by name."""
        return self.db.get_all_artists()

    def get_artist_albums(self, artist_id: int) -> List[Album]:
        """Returns all albums for a specific artist (including featured)."""
        return self.db.get_albums_by_artist(artist_id)

    def get_album_tracks(self, album_id: int) -> List[Track]:
        """Returns all tracks in an album, ordered by track number."""
        return self.db.get_tracks_by_album(album_id)

    def get_playlist_tracks(self, playlist_id: int) -> List[Track]:
        """Returns all tracks in a playlist in order."""
        return self.db.get_tracks_by_playlist(playlist_id)

    def get_track_artists(self, track_id: int) -> List[Artist]:
        """Returns all artists associated with a specific track."""
        return self.db.get_artists_by_track(track_id)

    def search(self, query: str) -> List[BaseModel]:
        """Search the library for tracks matching the query."""
        return self.db.search_library(query)
    
    def get_track_details(self, track_id: int) -> Optional[Track]:
        """Fetch a single track's metadata."""
        return self.db.get_track_by_id(track_id)
    
    def get_album_by_track(self, track_id: int) -> Optional[Album]:
        """Fetch the album for a given track."""
        return self.db.get_album_by_track(track_id)
        
    def get_artist_by_id(self, artist_id: int) -> Optional[Artist]:
        """Fetch a single artist by ID."""
        return self.db.get_artist_by_id(artist_id)
    
    def get_albums(self) -> List[Album]:
        """Returns all albums sorted by artist name and year."""
        return self.db.get_all_albums()
    
    def get_album_by_id(self, album_id: int) -> Optional[Album]:
        """Fetch a single album by ID."""
        return self.db.get_album_by_id(album_id)
    
    def get_artists_by_album(self, album_id: int) -> List[Artist]:
        """Get all artists associated with a specific album."""
        return self.db.get_artists_by_album(album_id)
    
    def get_tracks_by_album(self, album_id: int) -> List[Track]:
        """Get all tracks for a specific album."""
        return self.db.get_tracks_by_album(album_id)
    
    def get_playlist_by_id(self, playlist_id: int) -> Optional[Playlist]:
        """Fetch a single playlist by ID."""
        return self.db.get_playlist_by_id(playlist_id)
    
    def get_playlists(self) -> List[Playlist]:
        """Returns all playlists sorted by name."""
        return self.db.get_all_playlists()
    
    def get_track_by_id(self, track_id: int) -> Optional[Track]:
        """Fetch a single track by ID."""
        return self.db.get_track_by_id(track_id)
    
    def get_artists_by_track(self, track_id: int) -> List[Artist]:
        """Get all artists associated with a specific track."""
        return self.db.get_artists_by_track(track_id)
    
    def get_artists_with_albums(self) -> List[Artist]:
        """Get all artists that have albums."""
        return self.db.get_artists_with_albums()
    
    def get_tracks_by_artist(self, artist_id: int) -> List[Track]:
        """Get all tracks associated with a specific artist."""
        return self.db.get_tracks_by_artist(artist_id)

    def get_play_queue_token(self) -> Optional[dict]:
        """Fetch a one-time token for the Play Queue WebSocket."""

        url = f"{self.base_url}/s/JSON/status"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "mode": "playqueue_token"
        }
        
        try:
            response = self.session.post(url, json=payload, headers=headers)
            data = response.json()
            
            if data.get('result'):
                user_data = data.get('user', {})
                session_uuid = None
                
                # Try multiple possible locations for session_uuid
                if isinstance(user_data, dict):
                    session_uuid = user_data.get('session_uuid')
                    if not session_uuid:
                        session_obj = user_data.get('session')
                        if isinstance(session_obj, dict):
                            session_uuid = session_obj.get('session_uuid')
                        elif isinstance(session_obj, str):
                            session_uuid = session_obj
                
                result = {
                    'token': data.get('token'),
                    'session_uuid': session_uuid
                }
                
                return result
            
            return None
        except Exception as e:
            return None