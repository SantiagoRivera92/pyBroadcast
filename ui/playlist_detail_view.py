from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal
from ui.playlist_header import PlaylistHeader
from ui.album_track_list import AlbumTrackList

class PlaylistDetailView(QWidget):
    playTrackRequested = pyqtSignal(object)
    upButtonClicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.playlist_header = PlaylistHeader()
        self.playlist_header.upButtonClicked.connect(self.upButtonClicked.emit)
        self.track_list = AlbumTrackList()
        self.track_list.playTrackRequested.connect(self.playTrackRequested.emit)

        
        layout.addWidget(self.playlist_header)
        layout.addWidget(self.track_list)
    
    def set_playlist(self, playlist_name, track_count, artwork_url=None):
        self.playlist_header.set_playlist(playlist_name, track_count, artwork_url)
    
    def set_tracks(self, tracks):
        self.track_list.set_tracks(tracks)