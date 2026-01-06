import json
import time
import threading
import requests
from websocket import WebSocketApp
from typing import Dict, Callable, Optional, List

class PlayQueueWebSocket:
    def __init__(self, access_token: str, on_state_update: Optional[Callable] = None):
        self.access_token = access_token
        self.ws = None
        self.ws_thread = None
        self.session_uuid = None
        self.role = "player"
        self.on_state_update = on_state_update
        self.reconnect_delay = 5
        self.should_reconnect = True
        
        # Current state
        self.state = {
            'current_song': None,
            'data': {
                'play_from': 'tracks',
                'play_index': 0,
                'repeat_mode': 'none',
                'crossfade': False
            },
            'name': '',
            'pause': True,
            'tracks': [],
            'play_next': [],
            'shuffle': False,
            'start_position': 0.0,
            'start_time': 0.0,
            'volume': 0.8
        }
    
    def get_playqueue_token(self) -> Optional[str]:
        """Request a one-time-use token for connecting to the play queue server"""
        try:
            response = requests.post(
                'https://api.ibroadcast.com/s/JSON/playqueue_token',
                headers={'Authorization': f'Bearer {self.access_token}'},
                json={}
            )
            if response.status_code == 200:
                data = response.json()
                print(data)
                return data.get('token')
        except Exception as e:
            print(f"Failed to get playqueue token: {e}")
        return None
    
    def connect(self):
        """Connect to the play queue WebSocket server"""
        token = self.get_playqueue_token()
        if not token:
            print("Failed to get playqueue token")
            return False
        
        ws_url = f"wss://queue.ibroadcast.com?token={token}"
        
        self.ws = WebSocketApp(
            ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        
        self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.ws_thread.start()
        return True
    
    def _on_open(self, ws):
        """Called when WebSocket connection is opened"""
        print("Play Queue WebSocket connected")
        # Request current state
        self.send_command('get_state')
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            command = data.get('command')
            
            if command == 'set_state':
                self._handle_set_state(data)
            elif command == 'update_library':
                print("Library update notification received")
                # Trigger library reload if needed
            elif command == 'sessions':
                print("Sessions updated")
            elif command == 'end_session':
                print("Session ended - user logged out")
                self.should_reconnect = False
                
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def _handle_set_state(self, data):
        """Handle set_state command from server"""
        self.role = data.get('role', 'player')
        self.session_uuid = data.get('session_uuid')
        
        # Update state
        self.state.update({
            'current_song': data.get('current_song'),
            'data': data.get('data', self.state['data']),
            'name': data.get('name', ''),
            'pause': data.get('pause', True),
            'tracks': data.get('tracks', []),
            'play_next': data.get('play_next', []),
            'shuffle': data.get('shuffle', False),
            'start_position': data.get('start_position', 0.0),
            'start_time': data.get('start_time', 0.0),
            'volume': data.get('volume', 0.8)
        })
        
        print(f"State updated - Role: {self.role}, Current: {self.state['current_song']}")
        
        # Notify callback
        if self.on_state_update:
            self.on_state_update(self.state, self.role)
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        print(f"WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket closure"""
        print(f"WebSocket closed: {close_status_code} - {close_msg}")
        if self.should_reconnect:
            print(f"Reconnecting in {self.reconnect_delay} seconds...")
            time.sleep(self.reconnect_delay)
            self.connect()
    
    def send_command(self, command: str, value: Optional[Dict] = None):
        """Send a command to the play queue server"""
        if not self.ws:
            return
        
        message = {
            'session_uuid': self.session_uuid or '',
            'client': 'pyBroadcast',
            'version': '0.1',
            'device_name': 'Desktop',
            'command': command
        }
        
        if value:
            message['value'] = value
        
        try:
            self.ws.send(json.dumps(message))
        except Exception as e:
            print(f"Failed to send command: {e}")
    
    def update_state(self, updates: Dict):
        """Update the play queue state on the server"""
        self.state.update(updates)
        self.send_command('set_state', self.state)
    
    def set_current_track(self, track_id: int, track_name: str):
        """Set the currently playing track"""
        self.update_state({
            'current_song': track_id,
            'name': track_name,
            'pause': False,
            'start_position': 0.0,
            'start_time': time.time()
        })
    
    def set_pause(self, paused: bool):
        """Set pause state"""
        updates = {
            'pause': paused, 
            'start_position': self.state.get('start_position', 0.0), 
            'start_time': self.state.get('start_time', 0.0)
        }
        if paused:
            # When pausing, update start_position to current position
            current_pos = self.get_current_position()
            # Ensure start_position is set in the correct place (not in 'pause')
            updates['start_position'] = float(current_pos)
            updates['start_time'] = time.time()
        else:
            # When resuming, update start_time to now
            updates['start_time'] = time.time()
        self.update_state(updates)
    
    def set_queue(self, tracks: List[int], play_index: int = 0):
        """Set the main playback queue"""
        self.update_state({
            'tracks': tracks,
            'data': {
                **self.state['data'],
                'play_index': play_index,
                'play_from': 'tracks'
            }
        })
    
    def add_to_play_next(self, track_ids: List[int]):
        """Add tracks to the 'Up Next' queue"""
        play_next = self.state['play_next'] + track_ids
        self.update_state({'play_next': play_next})
    
    def remove_from_queue(self, index: int, from_play_next: bool = False):
        """Remove a track from the queue"""
        if from_play_next:
            play_next = self.state['play_next'].copy()
            if 0 <= index < len(play_next):
                play_next.pop(index)
                self.update_state({'play_next': play_next})
        else:
            tracks = self.state['tracks'].copy()
            if 0 <= index < len(tracks):
                tracks.pop(index)
                self.update_state({'tracks': tracks})
    
    def clear_queue(self):
        """Clear the entire queue"""
        self.update_state({
            'tracks': [],
            'play_next': [],
            'current_song': None,
            'pause': True
        })
    
    def set_shuffle(self, enabled: bool):
        """Set shuffle mode"""
        self.update_state({'shuffle': enabled})
    
    def set_repeat_mode(self, mode: str):
        """Set repeat mode: 'none', 'queue', or 'track'"""
        self.update_state({
            'data': {
                **self.state['data'],
                'repeat_mode': mode
            }
        })
    
    def set_volume(self, volume: float):
        """Set volume (0.0 - 1.0)"""
        self.update_state({'volume': max(0.0, min(1.0, volume))})
        
    def get_current_position(self) -> float:
        """Calculate current playback position"""
        if self.state['pause']:
            return self.state['start_position']
        
        return time.time() - (self.state['start_time'] - self.state['start_position'])
    
    def seek(self, position: float):
        """Seek to a position in the current track"""
        self.update_state({
            'start_position': position,
            'start_time': time.time()
        })
    
    def get_current_queue(self) -> List[int]:
        """Get the current playback queue (play_next + tracks)"""
        return self.state['play_next'] + self.state['tracks']
    
    def disconnect(self):
        """Disconnect from the WebSocket"""
        self.should_reconnect = False
        if self.ws:
            self.ws.close()