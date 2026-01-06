from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtCore import QUrl

from ui.utils.scrolling_label import ScrollingLabel

class PlaylistHeader(QFrame):
    upButtonClicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(280)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1a1a, stop:1 #0f0f0f);
                border: none;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Playlist artwork
        self.artwork = QLabel()
        self.artwork.setFixedSize(180, 180)
        self.artwork.setStyleSheet("""
            background-color: #1a1a1a; 
            border-radius: 12px;
        """)
        self.artwork.setScaledContents(True)
        self.artwork.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.artwork)

        # Playlist info
        info_container = QFrame()
        info_container.setStyleSheet("QFrame { background: transparent; border: none; }")
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(10)

        playlist_type_label = QLabel("PLAYLIST")
        playlist_type_label.setStyleSheet("""
            color: #4DA6FF; 
            font-size: 13px; 
            font-weight: bold;
            letter-spacing: 2px;
            background: none;
        """)

        self.playlist_name = ScrollingLabel(info_container)
        self.playlist_name.setText("Playlist Name")
        self.playlist_name.setStyleSheet("""
            color: white; 
            font-size: 48px; 
            font-weight: bold;
            background: none;
        """)
        self.playlist_name.setWordWrap(True)

        self.track_count_label = QLabel("")
        self.track_count_label.setStyleSheet("color: #b3b3b3; font-size: 16px; background: none;")

        info_layout.addWidget(playlist_type_label)
        info_layout.addWidget(self.playlist_name)
        info_layout.addWidget(self.track_count_label)
        info_layout.addStretch()

        layout.addWidget(info_container)
        layout.addStretch()
        
        self.up_button = QPushButton("↑ Playlists")
        self.up_button.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #4DA6FF;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #252525;
                border: 1px solid #4DA6FF;
            }
        """)
        self.up_button.setFixedHeight(40)
        self.up_button.clicked.connect(self.upButtonClicked.emit)
        layout.addWidget(self.up_button)

        self.network_manager = QNetworkAccessManager()

    def set_playlist(self, name, track_count, artwork_url=None):
        self.playlist_name.setText(name)
        self.track_count_label.setText(f"{track_count} tracks")
        if artwork_url:
            request = QNetworkRequest(QUrl(artwork_url))
            reply = self.network_manager.get(request)
            if reply:
                reply.finished.connect(lambda: self.on_artwork_loaded(reply))
        else:
            self.artwork.clear()
            self.artwork.setText("♪")
            self.artwork.setStyleSheet("""
                background-color: #4DA6FF; 
                border-radius: 12px;
                color: white;
                font-size: 72px;
            """)

    def on_artwork_loaded(self, reply):
        if reply.error() == reply.NetworkError.NoError:
            data = reply.readAll()
            img = QImage()
            if img.loadFromData(data):
                pixmap = QPixmap.fromImage(img)
                scaled = pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                self.artwork.setPixmap(scaled)
                self.artwork.setStyleSheet("background-color: transparent; border-radius: 12px;")
        reply.deleteLater()
