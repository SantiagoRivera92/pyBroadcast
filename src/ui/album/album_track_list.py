from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint

from src.api.ibroadcast.models import Track
from src.ui.utils.artist_links_label import ArtistLinksLabel


class TrackRow(QFrame):
    """A custom widget representing a single row in the track list."""

    contextMenuRequested = pyqtSignal(object, QPoint)

    def __init__(self, track, parent_list):
        super().__init__()
        self.track = track
        self.parent_list = parent_list
        self.setObjectName("TrackRow")
        self.setFixedHeight(60)  # Slightly slimmer than 80 for a tighter list feel
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(15)

        # 1. Number Column
        self.num_label = QLabel(str(track.track_number))
        self.num_label.setFixedWidth(30)
        self.num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.num_label.setStyleSheet(
            "color: #b3b3b3; background-color:transparent; font-size: 14px;"
        )

        # 2. Title & Artist Column
        info_widget = QWidget()
        info_widget.setStyleSheet("background-color: transparent; border: none;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 8, 0, 8)
        info_layout.setSpacing(2)

        self.title_label = QLabel(track.name)
        self.title_label.setStyleSheet("""
            color: white; 
            font-weight: 500; 
            font-size: 15px; 
            background-color: transparent;
        """)

        self.artist_label = ArtistLinksLabel()
        if track.extra_data:
            artists = track.extra_data.artists
            if not artists and track.extra_data.artist_name:
                self.artist_label.setText(track.extra_data.artist_name)
            else:
                self.artist_label.set_artists(artists)
                # Forward the click signal
                self.artist_label.artistClicked.connect(
                    self.parent_list.artistClicked.emit
                )

        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.artist_label)

        # 3. Duration Column
        duration_str = self.parent_list.format_duration(track.length)
        self.duration_label = QLabel(duration_str)
        self.duration_label.setFixedWidth(50)
        self.duration_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.duration_label.setStyleSheet(
            "color: #b3b3b3; background-color: transparent; font-size: 14px;"
        )

        # Add to main layout
        layout.addWidget(self.num_label)
        layout.addWidget(info_widget, 1)  # Stretch factor 1
        layout.addWidget(self.duration_label)

        self.is_selected = False
        self.update_style()

    def update_style(self):
        bg = "#232a38" if self.is_selected else "transparent"
        self.setStyleSheet(f"""
            #TrackRow {{
                background-color: {bg};
                border-radius: 4px;
            }}
            #TrackRow:hover {{
                background-color: #313a4d;
            }}
            QLabel {{
                background-color: transparent;
            }}
            ArtistLinksLabel {{
                background-color: transparent;
            }}
        """)
        self.update()

    def set_selected(self, selected):
        self.is_selected = selected
        self.update_style()

    def mouseDoubleClickEvent(self, a0):
        """Handle double click to play track."""
        if self.track.id:
            self.parent_list.playTrackRequested.emit(self.track.id)
        super().mouseDoubleClickEvent(a0)

    def on_context_menu(self, pos):
        # Map the local click position to global screen coordinates
        global_pos = self.mapToGlobal(pos)
        # Emit the track object and the position
        self.contextMenuRequested.emit(self.track, global_pos)


class AlbumTrackList(QFrame):
    playTrackRequested = pyqtSignal(object)
    artistClicked = pyqtSignal(str)
    trackContextMenuRequested = pyqtSignal(object, QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #181818; border: none;")

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 0, 40, 40)
        self.main_layout.setSpacing(0)

        # Header Row
        self.setup_header()

        # Tracks Container
        self.tracks_container = QWidget()
        self.tracks_layout = QVBoxLayout(self.tracks_container)
        self.tracks_layout.setContentsMargins(0, 0, 0, 0)
        self.tracks_layout.setSpacing(4)

        self.main_layout.addWidget(self.tracks_container)

        # Add a stretch at the bottom to keep items at the top
        self.main_layout.addStretch()

        self.tracks_data: list[Track] = []
        self.selected_track_id = None
        self.track_rows: list[TrackRow] = []

    def setup_header(self):
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)
        header_layout.setSpacing(15)

        h_num = QLabel("#")
        h_num.setFixedWidth(30)
        h_num.setAlignment(Qt.AlignmentFlag.AlignCenter)

        h_title = QLabel("Title")

        h_duration = QLabel("Duration")
        h_duration.setFixedWidth(50)
        h_duration.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Style headers
        header_style = "color: #b3b3b3; font-size: 13px; font-weight: bold; text-transform: uppercase;"
        for lbl in [h_num, h_title, h_duration]:
            lbl.setStyleSheet(header_style)

        header_layout.addWidget(h_num)
        header_layout.addWidget(h_title, 1)
        header_layout.addWidget(h_duration)

        # Bottom border for header
        header_widget.setStyleSheet(
            "border-bottom: 1px solid #282828; margin-bottom: 10px;"
        )

        self.main_layout.addWidget(header_widget)

    def set_tracks(self, tracks):
        self.tracks_data = tracks

        # Clear existing track widgets
        while self.tracks_layout.count():
            item = self.tracks_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        self.track_rows = []
        # Add new tracks
        for track in tracks:
            row = TrackRow(track, self)
            self.track_rows.append(row)
            row.contextMenuRequested.connect(self.trackContextMenuRequested.emit)
            self.tracks_layout.addWidget(row)

    def set_selected_track(self, track_id):
        self.selected_track_id = track_id
        for row in self.track_rows:
            row.set_selected(row.track.id == track_id)

    def format_duration(self, seconds):
        if not seconds:
            return "0:00"
        m, s = divmod(int(seconds), 60)
        return f"{m}:{s:02d}"
