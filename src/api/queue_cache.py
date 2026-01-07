import json
import os
from typing import Optional, List

QUEUE_CACHE_FILE = 'cache/queue.json'

class QueueCache:
    def __init__(self):
        self.cache_dir = 'cache'
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        self.current_track: Optional[int] = None
        self.current_position: float = 0.0
        self.tracks: List[int] = []
        self.shuffle_enabled: bool = False
        self.repeat_mode: str = "off"
        
    def load(self) -> bool:
        """Load queue from cache file"""
        if not os.path.exists(QUEUE_CACHE_FILE):
            return False
        
        try:
            with open(QUEUE_CACHE_FILE, 'r') as f:
                data = json.load(f)
                
            self.current_track = data.get('current_track')
            self.current_position = data.get('current_position', 0.0)
            self.tracks = data.get('tracks', [])
            self.shuffle_enabled = data.get('shuffle_enabled', False)
            self.repeat_mode = data.get('repeat_mode', 'off')
            
            return True
        except Exception as e:
            print(f"Error loading queue cache: {e}")
            return False
    
    def save(self):
        """Save current queue to cache file"""
        try:
            data = {
                'current_track': self.current_track,
                'current_position': self.current_position,
                'tracks': self.tracks,
                'shuffle_enabled': self.shuffle_enabled,
                'repeat_mode': self.repeat_mode
            }
            
            with open(QUEUE_CACHE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving queue cache: {e}")
    
    def set_current_track(self, track_id: Optional[int], position: float = 0.0):
        """Set the current track and position"""
        self.current_track = track_id
        self.current_position = position
        self.save()
    
    def update_position(self, position: float):
        """Update just the position (called frequently)"""
        self.current_position = position
        self.save()
    
    def set_tracks(self, tracks: List[int]):
        """Set the queue tracks"""
        self.tracks = tracks
        self.save()
    
    def add_track(self, track_id: int, after_current: bool = False):
        """Add a track to the queue"""
        if after_current:
            self.tracks.insert(0, track_id)
        else:
            self.tracks.append(track_id)
        self.save()
    
    def remove_track(self, index: int):
        """Remove a track from the queue"""
        if 0 <= index < len(self.tracks):
            self.tracks.pop(index)
            self.save()
    
    def clear(self):
        """Clear the entire queue"""
        self.current_track = None
        self.current_position = 0.0
        self.tracks = []
        self.save()
    
    def reorder_tracks(self, old_index: int, new_index: int):
        """Reorder tracks in the queue"""
        if 0 <= old_index < len(self.tracks) and 0 <= new_index < len(self.tracks):
            track = self.tracks.pop(old_index)
            self.tracks.insert(new_index, track)
            self.save()
    
    def get_next_track(self) -> Optional[int]:
        """Get the next track in the queue"""
        if self.tracks:
            return self.tracks[0]
        return None
    
    def pop_next_track(self) -> Optional[int]:
        """Remove and return the next track"""
        if self.tracks:
            track = self.tracks.pop(0)
            self.save()
            return track
        return None
    
    def set_shuffle(self, enabled: bool):
        """Set shuffle mode"""
        self.shuffle_enabled = enabled
        self.save()
    
    def set_repeat_mode(self, mode: str):
        """Set repeat mode: 'off', 'all', or 'one'"""
        self.repeat_mode = mode
        self.save()
    
    def has_tracks(self) -> bool:
        """Check if there are any tracks in the queue"""
        return len(self.tracks) > 0 or self.current_track is not None