from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSlider, QSizePolicy
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QImage, QIcon
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtCore import QUrl
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QPainter
from ui.scrolling_label import ScrollingLabel

class SvgButton(QPushButton):
    def __init__(self, svg_path, size=24, parent=None):
        super().__init__(parent)
        self.svg_path = svg_path
        self.icon_size = size
        self.default_color = "#b3b3b3"
        self.hover_color = "#ffffff"
        self.active_color = "#5DADE2"
        self.current_color = self.default_color
        self.is_active = False
        
        self.setFixedSize(size + 16, size + 16)
        self.setStyleSheet("""
            QPushButton {
                background: none; 
                border: none;
                padding: 8px;
            }
        """)
        self.update_icon()
    
    def set_active(self, active):
        self.is_active = active
        self.update_icon()
    
    def update_icon(self):
        color = self.active_color if self.is_active else self.current_color
        icon = self.create_colored_icon(self.svg_path, color, self.icon_size)
        self.setIcon(icon)
        self.setIconSize(QSize(self.icon_size, self.icon_size))
    
    def create_colored_icon(self, svg_path, color, size):
        """Create a colored icon from SVG file"""
        # Read SVG file
        with open(svg_path, 'r') as f:
            svg_data = f.read()
        
        # Replace fill color
        svg_data = svg_data.replace('currentColor', color)
        svg_data = svg_data.replace('fill="black"', f'fill="{color}"')
        svg_data = svg_data.replace('fill="#000"', f'fill="{color}"')
        svg_data = svg_data.replace('fill="#000000"', f'fill="{color}"')
        svg_data = svg_data.replace('stroke="black"', f'stroke="{color}"')
        svg_data = svg_data.replace('stroke="#000"', f'stroke="{color}"')
        svg_data = svg_data.replace('stroke="#000000"', f'stroke="{color}"')
        
        # Render SVG to pixmap
        renderer = QSvgRenderer(svg_data.encode())
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return QIcon(pixmap)
    
    def enterEvent(self, event):
        self.current_color = self.hover_color
        self.update_icon()
        super().enterEvent(event)
    
    def leaveEvent(self, a0):
        self.current_color = self.default_color
        self.update_icon()
        super().leaveEvent(a0)

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
        self.artwork.setStyleSheet("background-color: #181818; background-color: #282828; border-radius: 4px;")
        self.artwork.setScaledContents(True)
        left_layout.addWidget(self.artwork)
        
        info_widget = QFrame(self)
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(2)
        self.track_name = ScrollingLabel(info_widget)
        self.track_name.setText("No track playing")
        self.track_name.setStyleSheet("color: white; font-weight: bold; font-size: 15px;")
        self.track_name.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.artist_name = ScrollingLabel(info_widget)
        self.artist_name.setText("")
        self.artist_name.setStyleSheet("color: #b3b3b3; font-size: 13px;")
        self.artist_name.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        info_layout.addWidget(self.track_name)
        info_layout.addWidget(self.artist_name)
        info_layout.addStretch()
        info_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self._info_widget = info_widget  # Store reference for resizeEvent
        left_layout.addWidget(info_widget)
        left_layout.addStretch()
        
        # Center: Controls
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(8)
        
        # Button row
        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(15)
        
        self.shuffle_btn = SvgButton("assets/shuffle_off.svg", 20)
        self.prev_btn = SvgButton("assets/fr.svg", 24)
        self.play_btn = SvgButton("assets/play.svg", 20)
        self.next_btn = SvgButton("assets/ff.svg", 24)
        self.repeat_btn = SvgButton("assets/repeat_off.svg", 20)
        
        # Special styling for play button
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: none;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        self.play_btn.default_color = "#000000"
        self.play_btn.hover_color = "#000000"
        self.play_btn.active_color = "#000000"
        self.play_btn.update_icon()
        
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
        
        self.volume_icon = SvgButton("assets/volume_up.svg", 20)
        self.volume_icon.setEnabled(False)  # Make it non-clickable
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        # Width will be set dynamically in resizeEvent
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
        
        # Update volume icon based on slider value
        self.volume_slider.valueChanged.connect(self.update_volume_icon)
        
        volume_layout.addStretch()
        volume_layout.addWidget(self.volume_icon)
        volume_layout.addWidget(self.volume_slider)
        
        # Add all sections to main layout with proportional stretch factors
        layout.addLayout(left_layout, 15)
        layout.addLayout(controls_layout, 75)
        layout.addLayout(volume_layout, 10)
        
        # Network manager for artwork loading
        self.network_manager = QNetworkAccessManager()
        
        # Track current state
        self.is_playing = False
        self.shuffle_enabled = False
        self.repeat_mode = "off"
    
    def update_volume_icon(self, value):
        """Update volume icon based on volume level"""
        if value == 0:
            self.volume_icon.svg_path = "assets/volume_down.svg"
        else:
            self.volume_icon.svg_path = "assets/volume_up.svg"
        self.volume_icon.update_icon()
    
    def set_track_info(self, track_name, artist_name, artwork_url):
        self.track_name.setText(track_name)
        self.artist_name.setText(artist_name)
        
        if artwork_url:
            request = QNetworkRequest(QUrl(artwork_url))
            reply = self.network_manager.get(request)
            if reply:
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
        self.is_playing = is_playing
        if is_playing:
            self.play_btn.svg_path = "assets/pause.svg"
        else:
            self.play_btn.svg_path = "assets/play.svg"
        self.play_btn.update_icon()
    
    def set_shuffle(self, enabled):
        self.shuffle_enabled = enabled
        if enabled:
            self.shuffle_btn.svg_path = "assets/shuffle_on.svg"
        else:
            self.shuffle_btn.svg_path = "assets/shuffle_off.svg"
        self.shuffle_btn.set_active(enabled)
    
    def set_repeat(self, mode):
        self.repeat_mode = mode
        if mode == "off":
            self.repeat_btn.svg_path = "assets/repeat_off.svg"
            self.repeat_btn.set_active(False)
        elif mode == "all":
            self.repeat_btn.svg_path = "assets/repeat_on.svg"
            self.repeat_btn.set_active(True)
        else:  # "one"
            self.repeat_btn.svg_path = "assets/repeat_one.svg"
            self.repeat_btn.set_active(True)
    
    def update_time_labels(self, current_seconds, total_seconds):
        def format_time(seconds):
            mins = seconds // 60
            secs = seconds % 60
            return f"{mins}:{secs:02d}"
        
        self.time_current.setText(format_time(current_seconds))
        self.time_total.setText(format_time(total_seconds))
    
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
    
    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        total_width = self.width()
        info_width = int(total_width * 0.20)
        self._info_widget.setMaximumWidth(info_width)
        volume_width = int(total_width * 0.20)
        self.volume_slider.setFixedWidth(max(60, volume_width))