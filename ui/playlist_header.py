from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtCore import QUrl

class PlaylistHeader(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(280)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1a1a, stop:1 #121212);
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
            background-color: #282828; 
            border-radius: 16px;
        """)
        self.artwork.setScaledContents(True)
        self.artwork.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.artwork)

        # Playlist info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)

        playlist_type_label = QLabel("PLAYLIST")
        playlist_type_label.setStyleSheet("""
            color: white; 
            font-size: 13px; 
            font-weight: bold;
            letter-spacing: 2px;
        """)

        self.playlist_name = QLabel("Playlist Name")
        self.playlist_name.setStyleSheet("""
            color: white; 
            font-size: 48px; 
            font-weight: bold;
        """)
        self.playlist_name.setWordWrap(True)

        self.track_count_label = QLabel("")
        self.track_count_label.setStyleSheet("color: #b3b3b3; font-size: 16px;")

        info_layout.addWidget(playlist_type_label)
        info_layout.addWidget(self.playlist_name)
        info_layout.addWidget(self.track_count_label)
        info_layout.addStretch()

        layout.addLayout(info_layout)
        layout.addStretch()

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
                background-color: #5DADE2; 
                border-radius: 16px;
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
                self.artwork.setStyleSheet("background-color: transparent; border-radius: 16px;")
        reply.deleteLater()