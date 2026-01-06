from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtCore import QUrl
from ui.scrolling_label import ScrollingLabel

class AlbumHeader(QFrame):
    upButtonClicked = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(280)
        self.setStyleSheet("""
            AlbumHeader {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1a1a, stop:1 #0f0f0f);
                border: none;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Album artwork
        self.artwork = QLabel()
        self.artwork.setFixedSize(180, 180)
        self.artwork.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a; AlbumHeader
                border-radius: 12px;
            }
        """)
        self.artwork.setScaledContents(True)
        self.artwork.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.artwork)

        # Album info container
        info_container = QFrame()
        info_container.setStyleSheet("QFrame { background: transparent; border: none; }")
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(10)

        # Album type label with fixed height
        album_type_label = QLabel("ALBUM")
        album_type_label.setFixedHeight(20)
        album_type_label.setStyleSheet("""
            QLabel {
                color: #4DA6FF; 
                font-size: 13px; 
                font-weight: bold;
                letter-spacing: 2px;
                background: none;
                padding: 0px;
                border: none;
            }
        """)
        album_type_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        album_type_label.setTextFormat(Qt.TextFormat.PlainText)

        # Album name with fixed height
        self.album_name = ScrollingLabel(info_container)
        self.album_name.setText("Album Name")
        self.album_name.setFixedHeight(60)
        self.album_name.setMaximumWidth(700)
        self.album_name.setMinimumWidth(200)
        self.album_name.setStyleSheet("""
            QLabel {
                color: white; 
                font-size: 48px; 
                font-weight: bold;
                background: none;
                padding: 0px;
                border: none;
            }
        """)
        self.album_name.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.album_name.setTextFormat(Qt.TextFormat.PlainText)
        self.album_name.setSizePolicy(self.album_name.sizePolicy().horizontalPolicy(), self.album_name.sizePolicy().verticalPolicy())

        # Artist name with fixed height
        self.artist_name = ScrollingLabel(info_container)
        self.artist_name.setText("Artist Name")
        self.artist_name.setFixedHeight(28)
        self.artist_name.setMaximumWidth(700)
        self.artist_name.setMinimumWidth(200)
        self.artist_name.setStyleSheet("""
            QLabel {
                color: #b3b3b3; 
                font-size: 20px;
                background: none;
                padding: 0px;
                border: none;
            }
        """)
        self.artist_name.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.artist_name.setTextFormat(Qt.TextFormat.PlainText)
        self.artist_name.setSizePolicy(self.artist_name.sizePolicy().horizontalPolicy(), self.artist_name.sizePolicy().verticalPolicy())

        # Year label with fixed height
        self.year_label = QLabel("")
        self.year_label.setFixedHeight(22)
        self.year_label.setStyleSheet("""
            QLabel {
                color: #b3b3b3; 
                font-size: 16px;
                background: none;
                padding: 0px;
                border: none;
            }
        """)
        self.year_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.year_label.setTextFormat(Qt.TextFormat.PlainText)

        info_layout.addWidget(album_type_label)
        info_layout.addWidget(self.album_name)
        info_layout.addWidget(self.artist_name)
        info_layout.addWidget(self.year_label)
        info_layout.addStretch()

        layout.addWidget(info_container)
        layout.addStretch()
        
        self.up_button = QPushButton("↑ Artist")
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
        layout.addWidget(self.up_button)

        self.network_manager = QNetworkAccessManager()
        
    def set_artist_id(self, artist_id):
        self.up_button.clicked.connect(lambda: self.upButtonClicked.emit(artist_id))

    def set_album(self, name, artist, year, artwork_url=None):
        self.album_name.setText(name)
        self.artist_name.setText(artist)
        self.year_label.setText(str(year) if year else "")
        
        if artwork_url:
            request = QNetworkRequest(QUrl(artwork_url))
            reply = self.network_manager.get(request)
            if reply:
                reply.finished.connect(lambda: self.on_artwork_loaded(reply))
        else:
            self.artwork.clear()
            self.artwork.setText("")

    def on_artwork_loaded(self, reply):
        if reply.error() == reply.NetworkError.NoError:
            data = reply.readAll()
            img = QImage()
            if img.loadFromData(data):
                pixmap = QPixmap.fromImage(img)
                scaled = pixmap.scaled(
                    180, 180, 
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.artwork.setPixmap(scaled)
                self.artwork.setStyleSheet("QLabel { background-color: transparent; border-radius: 12px; }")
        
        reply.deleteLater()
