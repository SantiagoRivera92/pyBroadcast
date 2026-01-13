from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PyQt6.QtCore import pyqtSignal, Qt

from src.ui.playlist.playlist_header import PlaylistHeader
from src.ui.album.album_track_list import AlbumTrackList

class PlaylistDetailView(QScrollArea):
    playTrackRequested = pyqtSignal(object)
    upButtonClicked = pyqtSignal()
    artistClicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setStyleSheet("background-color: #0f0f0f; border: none;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: #0f0f0f;")
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.playlist_header = PlaylistHeader()
        self.playlist_header.upButtonClicked.connect(self.upButtonClicked.emit)
        self.album_track_list = AlbumTrackList()
        # Disable track list's internal scrolling so it scrolls with the detail view
        self.album_track_list.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.album_track_list.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.album_track_list.playTrackRequested.connect(self.playTrackRequested.emit)
        self.album_track_list.artistClicked.connect(self.artistClicked.emit)
        
        layout.addWidget(self.playlist_header)
        layout.addWidget(self.album_track_list)
        layout.addStretch()
        
        self.setWidget(self.container)
    
    def set_playlist(self, playlist_name, track_count, artwork_url=None):
        self.playlist_header.set_playlist(playlist_name, track_count, artwork_url)
    
    def set_tracks(self, tracks):
        self.album_track_list.set_tracks(tracks)