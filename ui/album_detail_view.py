from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal
from ui.album_header import AlbumHeader
from ui.album_track_list import AlbumTrackList

class AlbumDetailView(QWidget):
    playTrackRequested = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.album_header = AlbumHeader()
        self.album_track_list = AlbumTrackList()
        self.album_track_list.playTrackRequested.connect(self.playTrackRequested.emit)
        
        layout.addWidget(self.album_header)
        layout.addWidget(self.album_track_list)
    
    def set_album(self, album_name, artist_name, year, artwork_url=None):
        self.album_header.set_album(album_name, artist_name, year, artwork_url)
    
    def set_tracks(self, tracks):
        self.album_track_list.set_tracks(tracks)