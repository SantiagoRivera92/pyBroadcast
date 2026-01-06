from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtCore import QUrl
from ui.scrolling_label import ScrollingLabel

class ArtistHeader(QFrame):
    upButtonClicked = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(280)
        self.setStyleSheet("""
            ArtistHeader {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1a1a, stop:1 #0f0f0f);
                border: none;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # Artist artwork
        self.artwork = QLabel()
        self.artwork.setFixedSize(180, 180)
        self.artwork.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a; 
                border-radius: 90px;
            }
        """)
        self.artwork.setScaledContents(True)
        self.artwork.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.artwork)
        
        # Artist info container
        info_container = QFrame()
        info_container.setStyleSheet("QFrame { background: transparent; border: none; }")
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(10)
        
        # Artist type label with fixed height
        artist_type_label = QLabel("ARTIST")
        artist_type_label.setFixedHeight(20)
        artist_type_label.setStyleSheet("""
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
        artist_type_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        artist_type_label.setTextFormat(Qt.TextFormat.PlainText)
        
        # Artist name with fixed height
        self.artist_name = ScrollingLabel(info_container)
        self.artist_name.setText("Artist Name")
        self.artist_name.setFixedHeight(70)
        self.artist_name.setStyleSheet("""
            QLabel {
                color: white; 
                font-size: 56px; 
                font-weight: bold;
                background: none;
                padding: 0px;
                border: none;
            }
        """)
        self.artist_name.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.artist_name.setTextFormat(Qt.TextFormat.PlainText)
        
        info_layout.addWidget(artist_type_label)
        info_layout.addWidget(self.artist_name)
        info_layout.addStretch()
        
        layout.addWidget(info_container)
        layout.addStretch()
        
        self.up_button = QPushButton("↑ Artists")
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
        
        # Network manager for loading artwork
        self.network_manager = QNetworkAccessManager()
    
    def set_artist(self, name, artwork_url=None):
        self.artist_name.setText(name)
        
        if artwork_url:
            request = QNetworkRequest(QUrl(artwork_url))
            reply = self.network_manager.get(request)
            if reply:
                reply.finished.connect(lambda: self.on_artwork_loaded(reply))
        else:
            self.artwork.clear()
            # Show first letter of artist name as placeholder
            first_letter = name[0].upper() if name else "?"
            self.artwork.setText(first_letter)
            self.artwork.setStyleSheet("""
                QLabel {
                    background-color: #4DA6FF; 
                    border-radius: 90px;
                    color: white;
                    font-size: 72px;
                    font-weight: bold;
                }
            """)
            self.artwork.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def on_artwork_loaded(self, reply):
        if reply.error() == reply.NetworkError.NoError:
            data = reply.readAll()
            img = QImage()
            if img.loadFromData(data):
                pixmap = QPixmap.fromImage(img)
                
                # Create circular mask
                rounded = QPixmap(180, 180)
                rounded.fill(Qt.GlobalColor.transparent)
                
                from PyQt6.QtGui import QPainter, QBrush, QPainterPath
                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                path = QPainterPath()
                path.addEllipse(0, 0, 180, 180)
                painter.setClipPath(path)
                
                scaled = pixmap.scaled(
                    180, 180,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                painter.drawPixmap(0, 0, scaled)
                painter.end()
                
                self.artwork.setPixmap(rounded)
                self.artwork.setStyleSheet("QLabel { background-color: transparent; border-radius: 90px; }")
        
        reply.deleteLater()
