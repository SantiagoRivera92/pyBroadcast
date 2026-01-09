from typing import Optional
from PyQt6.QtWidgets import QWidget,QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSlider, QSizePolicy
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QIcon
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtCore import QUrl, QTimer

from src.api.ibroadcast.models import Album, Artist, Track
from src.ui.utils.scrolling_label import ScrollingLabel
from src.ui.utils.scrolling_artists_label import ScrollingArtistsLabel
from src.core.resource_path import resource_path


from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QPixmap, QIcon, QPainter


class SvgButton(QPushButton):
    def __init__(self, svg_path, size=24, parent=None):
        super().__init__(parent)
        self.svg_path = svg_path
        self.base_icon_size = size
        self._icon_size = size
        self.target_icon_size = size
        self.setFixedSize(size + 16, size + 16)
        self.setStyleSheet("""
            QPushButton {
                background: none; 
                border: none;
                padding: 8px;
            }
        """)
        self._animation_timer = QTimer(self)
        self._animation_timer.setInterval(16)  # ~60 FPS
        self._animation_timer.timeout.connect(self._animate_icon_size)
        self._animation_duration = 500  # ms
        self._animation_elapsed = 0
        self._animation_start_size = size
        self.update_icon()

    def enterEvent(self, event):
        self._start_icon_size_animation(int(self.base_icon_size * 1.2))
        super().enterEvent(event)

    def leaveEvent(self, a0):
        self._start_icon_size_animation(self.base_icon_size)
        super().leaveEvent(a0)

    def _start_icon_size_animation(self, target_size):
        self.target_icon_size = target_size
        self._animation_start_size = self._icon_size
        self._animation_elapsed = 0
        self._animation_timer.start()

    def _animate_icon_size(self):
        self._animation_elapsed += self._animation_timer.interval()
        progress = min(self._animation_elapsed / self._animation_duration, 1.0)
        new_size = int(self._animation_start_size + (self.target_icon_size - self._animation_start_size) * progress)
        if new_size != self._icon_size:
            self._icon_size = new_size
            self.update_icon()
        if progress >= 1.0:
            self._animation_timer.stop()

    @property
    def icon_size(self):
        return self._icon_size

    @icon_size.setter
    def icon_size(self, value):
        self._icon_size = int(value)
        self.update_icon()

    def update_icon(self):
        try:
            with open(self.svg_path, "r") as f:
                svg_data = f.read()
            renderer = QSvgRenderer(bytearray(svg_data, encoding='utf-8'))
            pixmap = QPixmap(self._icon_size, self._icon_size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            self.setIcon(QIcon(pixmap))
            self.setIconSize(QSize(self._icon_size, self._icon_size))
        except Exception as e:
            self.setIcon(QIcon())  # Clear icon if error

    @property
    def svg_path(self):
        return self._svg_path

    @svg_path.setter
    def svg_path(self, value):
        self._svg_path = value
        self.update_icon()
        
class PlayerControls(QFrame):
    
    albumClicked = pyqtSignal(object)
    artistClicked = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(110)
        self.setStyleSheet("background: none; border-top: 1px solid #282828;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Left: Track Info
        left_layout = QHBoxLayout()
        
        self.artwork = QLabel()
        self.artwork.setFixedSize(70, 70)
        self.artwork.setStyleSheet("background: none; background-color: #282828; border-radius: 4px;")
        self.artwork.setScaledContents(True)
        left_layout.addWidget(self.artwork)
        
        info_widget = QFrame(self)
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(2)
        self.track_name = ScrollingLabel(info_widget)
        self.track_name.setText("No track playing")
        self.track_name.setStyleSheet("background: transparent; color: white; font-weight: bold; font-size: 15px; border: none; padding: 0;")
        self.track_name.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.album_name = ScrollingLabel(info_widget)
        self.album_name.setText("")
        self.album_name.setStyleSheet("background: transparent; color: #b3b3b3; font-size: 13px; border: none; padding: 0; text-decoration: underline;")
        self.album_name.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.album_name.onClickCallback = self._on_album_clicked
        self.artist_name = ScrollingArtistsLabel(info_widget, self._on_artist_clicked)
        self.artist_name.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        info_layout.addWidget(self.track_name)
        info_layout.addWidget(self.album_name)
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
        
        self.shuffle_btn = SvgButton(resource_path("assets/shuffle_off.svg"), 20)
        self.prev_btn = SvgButton(resource_path("assets/fr.svg"), 24)
        self.play_btn = SvgButton(resource_path("assets/play.svg"), 20)
        self.next_btn = SvgButton(resource_path("assets/ff.svg"), 24)
        self.repeat_btn = SvgButton(resource_path("assets/repeat_off.svg"), 20)
        
        # Special styling for play button
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: none;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #a6a6d6;
            }
        """)
        
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
        self.time_current.setStyleSheet("background: transparent; color: #b3b3b3; font-size: 11px; min-width: 40px; border: none; padding: 0;")
        
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
        self.time_total.setStyleSheet("background: transparent; color: #b3b3b3; font-size: 11px; min-width: 40px; border: none; padding: 0;")
        
        progress_layout.addWidget(self.time_current)
        progress_layout.addWidget(self.progress, 1)
        progress_layout.addWidget(self.time_total)
        
        controls_layout.addLayout(btns_layout)
        controls_layout.addLayout(progress_layout)
        
        # Right: Volume
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(10)
        
        self.volume_icon = SvgButton(resource_path("assets/volume_up.svg"), 20)
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
            self.volume_icon.svg_path = resource_path("assets/volume_down.svg")
        else:
            self.volume_icon.svg_path = resource_path("assets/volume_up.svg")
    
    def set_track_info(self, track:Track, album:Optional[Album], artists: list[Artist], album_artists: list[Artist], artwork_url):
        self.track_name.setText(track.name)
        self.album_name.setText(album.name if album else "Unknown Album")
        self.album_id = album.id if album else None
        self.artist_ids = [artist.id for artist in artists]
        self.are_albumartists = [artist.id in [a.id for a in album_artists] for artist in artists]

        # Build artist label with clickable segments, underline on hover, no HTML
        class ArtistSegment(QLabel):
            def __init__(self, name, artist_id=None, is_albumartist=False, parent=None):
                super().__init__(name, parent)
                self.artist_id = artist_id
                self.is_albumartist = is_albumartist
                self.setStyleSheet("color: #b3b3b3; font-size: 13px; border: none; padding: 0;")
                if is_albumartist:
                    self.setCursor(Qt.CursorShape.PointingHandCursor)
                self.installEventFilter(self)

            def eventFilter(self, a0, a1):
                from PyQt6.QtCore import QEvent
                if self.is_albumartist:
                    if a1 and a1.type() == QEvent.Type.Enter:
                        self.setStyleSheet("color: #b3b3b3; font-size: 13px; border: none; padding: 0; text-decoration: underline;")
                    elif a1 and a1.type() == QEvent.Type.Leave:
                        self.setStyleSheet("color: #b3b3b3; font-size: 13px; border: none; padding: 0;")
                return super().eventFilter(a0, a1)


        self.artist_name.setArtists(artists)

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
            self.play_btn.svg_path = resource_path("assets/pause.svg")
        else:
            self.play_btn.svg_path = resource_path("assets/play.svg")
    
    def set_shuffle(self, enabled):
        self.shuffle_enabled = enabled
        if enabled:
            self.shuffle_btn.svg_path = resource_path("assets/shuffle_on.svg")
        else:
            self.shuffle_btn.svg_path = resource_path("assets/shuffle_off.svg")
    
    def set_repeat(self, mode):
        self.repeat_mode = mode
        if mode == "off":
            self.repeat_btn.svg_path = resource_path("assets/repeat_off.svg")
        elif mode == "all":
            self.repeat_btn.svg_path = resource_path("assets/repeat_on.svg")
        else:  # "one"
            self.repeat_btn.svg_path = resource_path("assets/repeat_one.svg")
    
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
    
    def _on_album_clicked(self):
        self.albumClicked.emit(self.album_id)
            
    def _on_artist_clicked(self, artist_id):
        self.artistClicked.emit(artist_id)