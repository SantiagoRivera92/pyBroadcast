from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSlider
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtCore import QUrl

class IconButton(QPushButton):
    def __init__(self, svg_data, size=24):
        super().__init__()
        self.svg_data = svg_data
        self.setFixedSize(size + 16, size + 16)
        self.setStyleSheet("""
            QPushButton {
                background: none; 
                border: none; 
                color: #b3b3b3;
                padding: 8px;
            }
            QPushButton:hover {
                color: white;
            }
        """)
        self.update_icon()
    
    def update_icon(self, color="#b3b3b3"):
        svg = self.svg_data.replace('currentColor', color)
        self.setText(svg)  # This won't work directly, we need a different approach

class PlayerControls(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(110)
        self.setStyleSheet("background-color: #181818; border-top: 1px solid #282828;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Left: Track Info
        left_layout = QHBoxLayout()
        
        self.artwork = QLabel()
        self.artwork.setFixedSize(70, 70)
        self.artwork.setStyleSheet("background-color: #282828; border-radius: 4px;")
        self.artwork.setScaledContents(True)
        left_layout.addWidget(self.artwork)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        self.track_name = QLabel("No track playing")
        self.track_name.setStyleSheet("color: white; font-weight: bold; font-size: 15px;")
        self.artist_name = QLabel("")
        self.artist_name.setStyleSheet("color: #b3b3b3; font-size: 13px;")
        info_layout.addWidget(self.track_name)
        info_layout.addWidget(self.artist_name)
        info_layout.addStretch()
        
        left_layout.addLayout(info_layout)
        left_layout.addStretch()
        
        # Center: Controls
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(8)
        
        # Button row
        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(15)
        
        self.shuffle_btn = QPushButton("⚯")
        self.prev_btn = QPushButton("⏮")
        self.play_btn = QPushButton("▶")
        self.next_btn = QPushButton("⏭")
        self.repeat_btn = QPushButton("⟳")
        
        button_style = """
            QPushButton {
                background: none; 
                border: none; 
                color: #b3b3b3; 
                font-size: 20px;
                padding: 5px;
                min-width: 32px;
            }
            QPushButton:hover { color: white; }
        """
        
        play_button_style = """
            QPushButton {
                background-color: white;
                border: none;
                color: black;
                font-size: 16px;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                transform: scale(1.05);
            }
        """
        
        self.shuffle_btn.setStyleSheet(button_style)
        self.prev_btn.setStyleSheet(button_style)
        self.play_btn.setStyleSheet(play_button_style)
        self.play_btn.setFixedSize(40, 40)
        self.next_btn.setStyleSheet(button_style)
        self.repeat_btn.setStyleSheet(button_style)
        
        btns_layout.addStretch()
        btns_layout.addWidget(self.shuffle_btn)
        btns_layout.addWidget(self.prev_btn)
        btns_layout.addWidget(self.play_btn)
        btns_layout.addWidget(self.next_btn)
        btns_layout.addWidget(self.repeat_btn)
        btns_layout.addStretch()
        
        # Progress bar with time labels
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(10)
        
        self.time_current = QLabel("0:00")
        self.time_current.setStyleSheet("color: #b3b3b3; font-size: 11px; min-width: 40px;")
        
        self.progress = QSlider(Qt.Orientation.Horizontal)
        self.progress.setStyleSheet("""
            QSlider::groove:horizontal { 
                height: 4px; 
                background: #4f4f4f; 
                border-radius: 2px;
            }
            QSlider::handle:horizontal { 
                background: white; 
                width: 12px; 
                height: 12px;
                margin: -4px 0; 
                border-radius: 6px; 
            }
            QSlider::sub-page:horizontal {
                background: #5DADE2;
                border-radius: 2px;
            }
        """)
        
        self.time_total = QLabel("0:00")
        self.time_total.setStyleSheet("color: #b3b3b3; font-size: 11px; min-width: 40px;")
        
        progress_layout.addWidget(self.time_current)
        progress_layout.addWidget(self.progress, 1)
        progress_layout.addWidget(self.time_total)
        
        controls_layout.addLayout(btns_layout)
        controls_layout.addLayout(progress_layout)
        
        # Right: Volume
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(10)
        
        volume_icon = QLabel("🔊")
        volume_icon.setStyleSheet("font-size: 18px;")
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal { 
                height: 4px; 
                background: #4f4f4f; 
                border-radius: 2px;
            }
            QSlider::handle:horizontal { 
                background: white; 
                width: 12px; 
                height: 12px;
                margin: -4px 0; 
                border-radius: 6px; 
            }
            QSlider::sub-page:horizontal {
                background: #5DADE2;
                border-radius: 2px;
            }
        """)
        
        volume_layout.addStretch()
        volume_layout.addWidget(volume_icon)
        volume_layout.addWidget(self.volume_slider)
        
        # Add all sections to main layout
        layout.addLayout(left_layout, 3)
        layout.addLayout(controls_layout, 4)
        layout.addLayout(volume_layout, 2)
        
        # Network manager for artwork loading
        self.network_manager = QNetworkAccessManager()
    
    def set_track_info(self, track_name, artist_name, artwork_url):
        self.track_name.setText(track_name)
        self.artist_name.setText(artist_name)
        
        if artwork_url:
            request = QNetworkRequest(QUrl(artwork_url))
            reply = self.network_manager.get(request)
            reply.finished.connect(lambda: self.on_artwork_loaded(reply))
        else:
            self.artwork.clear()
            self.artwork.setStyleSheet("background-color: #282828; border-radius: 4px;")
    
    def on_artwork_loaded(self, reply):
        if reply.error() == reply.NetworkError.NoError:
            data = reply.readAll()
            img = QImage()
            if img.loadFromData(data):
                pixmap = QPixmap.fromImage(img)
                self.artwork.setPixmap(pixmap.scaled(
                    70, 70,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                ))
        reply.deleteLater()
    
    def set_playing(self, is_playing):
        self.play_btn.setText("⏸" if is_playing else "▶")
    
    def set_shuffle(self, enabled):
        color = "#5DADE2" if enabled else "#b3b3b3"
        self.shuffle_btn.setStyleSheet(f"""
            QPushButton {{
                background: none; 
                border: none; 
                color: {color}; 
                font-size: 20px;
                padding: 5px;
                min-width: 32px;
            }}
            QPushButton:hover {{ color: white; }}
        """)
    
    def set_repeat(self, mode):
        # mode: "off", "all", "one"
        if mode == "off":
            self.repeat_btn.setText("⟳")
            color = "#b3b3b3"
        elif mode == "all":
            self.repeat_btn.setText("⟳")
            color = "#5DADE2"
        else:  # "one"
            self.repeat_btn.setText("🔂")
            color = "#5DADE2"
        
        self.repeat_btn.setStyleSheet(f"""
            QPushButton {{
                background: none; 
                border: none; 
                color: {color}; 
                font-size: 20px;
                padding: 5px;
                min-width: 32px;
            }}
            QPushButton:hover {{ color: white; }}
        """)
    
    def update_time_labels(self, current_seconds, total_seconds):
        def format_time(seconds):
            mins = seconds // 60
            secs = seconds % 60
            return f"{mins}:{secs:02d}"
        
        self.time_current.setText(format_time(current_seconds))
        self.time_total.setText(format_time(total_seconds))
    
    # Keep old interface for backwards compatibility
    @property
    def track_info(self):
        class TrackInfoProxy:
            def __init__(self, parent):
                self.parent = parent
            
            def setText(self, text):
                parts = text.split(' - ', 1)
                if len(parts) == 2:
                    self.parent.track_name.setText(parts[0])
                    self.parent.artist_name.setText(parts[1])
                else:
                    self.parent.track_name.setText(text)
                    self.parent.artist_name.setText("")
        
        return TrackInfoProxy(self)