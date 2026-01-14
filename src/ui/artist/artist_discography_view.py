from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QLabel, QGridLayout
from PyQt6.QtCore import Qt, pyqtSignal
from src.ui.album.album_header import AlbumHeader
from src.ui.album.album_track_list import AlbumTrackList
from src.ui.artist.artist_header import ArtistHeader
from src.ui.grid.library_grid import LibraryGrid
from src.api.ibroadcast.ibroadcast_api import iBroadcastAPI
from src.api.ibroadcast.models import BaseModel, ExtraData, Track
from src.ui.utils.hoverable_widget import HoverableWidget
from src.ui.utils.rounded_image import RoundedImage
from src.ui.utils.scrolling_label import ScrollingLabel
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QImage, QPixmap

class ArtistDiscographyView(QScrollArea):
    playTrackRequested = pyqtSignal(object)
    playAlbumRequested = pyqtSignal(object)
    upButtonClicked = pyqtSignal()
    artistClicked = pyqtSignal(str)
    
    def __init__(self, api: iBroadcastAPI, parent=None):
        super().__init__(parent)
        self.api = api
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setStyleSheet("background-color: #0f0f0f; border: none;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: #0f0f0f;")
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 40)
        self.main_layout.setSpacing(20)
        
        self.setWidget(self.container)

    def clear(self):
        # Clear the layout
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                    
    def set_selected_track(self, track_id):
        for i in range(self.main_layout.count()):
            item = self.main_layout.itemAt(i)
            if item:
                widget = item.widget()
                if isinstance(widget, AlbumTrackList):
                    widget.set_selected_track(track_id)

    def set_artist_discography(self, artist, albums):
        self.clear()
        
        if not albums:
            # Show ArtistHeader and a list of all tracks by this artist
            header = ArtistHeader()
            header.set_artist(artist.name, self.api.get_artwork_url(artist.artwork_id))
            self.main_layout.addWidget(header)
            
            tracks = self.api.get_tracks_by_artist(artist.id)
            if tracks:
                # Filter for starred tracks (rating == 5) if any exist
                starred_tracks = [t for t in tracks if t.rating == 5]
                header_text = "ALL TRACKS"
                if starred_tracks:
                    tracks = starred_tracks
                    header_text = "STARRED TRACKS"
                
                header.artist_name.setText(f"{artist.name} - {header_text}")
                
                grid_container = QWidget()
                grid_layout = QVBoxLayout(grid_container)
                grid_layout.setContentsMargins(10, 0, 10, 0)
                
                self.tracks_grid = QGridLayout()
                self.tracks_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
                self.tracks_grid.setSpacing(10)
                grid_layout.addLayout(self.tracks_grid)
                
                cols = 5
                for i, track in enumerate(tracks):
                    row = i // cols
                    col = i % cols
                    
                    item_widget = HoverableWidget(lambda t: self.playTrackRequested.emit(t.id), track)
                    layout = QVBoxLayout(item_widget)
                    layout.setContentsMargins(5, 5, 5, 5)
                    
                    img_label = RoundedImage()
                    img_label.setFixedSize(160, 160)
                    img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    artwork_url = self.api.get_artwork_url(track.artwork_id)
                    if artwork_url:
                        manager = QNetworkAccessManager(item_widget)
                        def set_img(reply, lbl=img_label):
                            if reply.error() == reply.NetworkError.NoError:
                                data = reply.readAll()
                                img = QImage()
                                if img.loadFromData(data):
                                    lbl.setPixmap(QPixmap.fromImage(img).scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
                            reply.deleteLater()
                        
                        request = QNetworkRequest(QUrl(artwork_url))
                        reply = manager.get(request)
                        if reply:
                            reply.finished.connect(lambda r=reply: set_img(r))

                    t_label = ScrollingLabel(item_widget)
                    t_label.setText(track.name)
                    t_label.setStyleSheet("color: white; font-weight: bold; margin-top: 5px; font-size: 16px;")
                    t_label.setFixedHeight(24)
                    t_label.setFixedWidth(160)
                    
                    album = self.api.get_album_by_track(track.id)
                    s_label = QLabel(album.name if album else "Unknown Album")
                    s_label.setStyleSheet("color: #b3b3b3; font-size: 13px;")
                    s_label.setWordWrap(True)
                    s_label.setFixedWidth(160)
                    
                    layout.addWidget(img_label)
                    layout.addWidget(t_label)
                    layout.addWidget(s_label)
                    
                    self.tracks_grid.addWidget(item_widget, row, col)
                
                self.main_layout.addWidget(grid_container)
            else:
                no_tracks = QLabel("No tracks found for this artist.")
                no_tracks.setStyleSheet("color: #b3b3b3; font-size: 16px; margin: 40px;")
                no_tracks.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.main_layout.addWidget(no_tracks)
        else:
            for album in albums:
                # Add Album Header
                album_header = AlbumHeader(show_up_button=False)
                artists = self.api.get_artists_by_album(album.id)
                artist_name = ", ".join([a.name for a in artists]) if artists else "Unknown Artist"
                
                tracks = self.api.get_tracks_by_album(album.id)
                artwork_url = None
                for t in tracks:
                    if t.artwork_id != 0:
                        artwork_url = self.api.get_artwork_url(t.artwork_id)
                        break
                
                album_header.set_album(album.name, artist_name, album.year, artwork_url)
                album_header.playButtonClicked.connect(lambda a_id=album.id: self.playAlbumRequested.emit(a_id))
                
                self.main_layout.addWidget(album_header)
                
                # Add Tracks
                track_list = AlbumTrackList()
                track_list.artistClicked.connect(self.artistClicked.emit)
                tracks.sort(key=lambda x: x.track_number if x.track_number is not None else 0)
                
                # Pre-populate artist name and full artist objects for the table
                for track in tracks:
                    track_artists = self.api.get_artists_by_track(track.id)
                    extraData = ExtraData()
                    extraData.artists = track_artists
                    extraData.artist_name = ", ".join([a.name for a in track_artists]) if track_artists else "Unknown Artist"
                    track.extra_data = extraData
                
                track_list.set_tracks(tracks)
                track_list.playTrackRequested.connect(self.playTrackRequested.emit)
                
                self.main_layout.addWidget(track_list)
        
        self.main_layout.addStretch()
