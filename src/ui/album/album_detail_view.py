from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PyQt6.QtCore import pyqtSignal, Qt
from src.ui.album.album_header import AlbumHeader
from src.ui.album.album_track_list import AlbumTrackList

class AlbumDetailView(QScrollArea):
    playTrackRequested = pyqtSignal(object)
    upButtonClicked = pyqtSignal(object)
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
        
        self.album_header = AlbumHeader()
        self.album_header.upButtonClicked.connect(self.upButtonClicked.emit)
        self.album_track_list = AlbumTrackList()
        # Disable track list's internal scrolling so it scrolls with the detail view
        self.album_track_list.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.album_track_list.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.album_track_list.playTrackRequested.connect(self.playTrackRequested.emit)
        self.album_track_list.artistClicked.connect(self.artistClicked.emit)
        
        layout.addWidget(self.album_header)
        layout.addWidget(self.album_track_list)
        layout.addStretch()
        
        self.setWidget(self.container)
    
    def set_album(self, album_name, artist_name, year, artwork_url=None):
        self.album_header.set_album(album_name, artist_name, year, artwork_url)
    
    def set_tracks(self, tracks):
        self.album_track_list.set_tracks(tracks)
        
    def set_artist_id(self, artist_id):
        self.album_header.set_artist_id(artist_id)