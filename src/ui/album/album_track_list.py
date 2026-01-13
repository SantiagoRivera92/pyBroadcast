from PyQt6.QtWidgets import QFrame, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QWidget, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QSize

from src.api.ibroadcast.models import Track, Artist
from src.ui.utils.artist_links_label import ArtistLinksLabel

class AlbumTrackList(QFrame):
    playTrackRequested = pyqtSignal(object)
    artistClicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #181818; border: none;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 0, 40, 40)
        layout.setSpacing(0)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["#", "Title", "Duration"])
        horizontalHeader = self.table.horizontalHeader()
        if horizontalHeader is not None:
            horizontalHeader.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            horizontalHeader.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            horizontalHeader.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        verticalHeader = self.table.verticalHeader()
        if verticalHeader is not None:
            verticalHeader.setVisible(False)

        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget { 
                background-color: #181818; 
                color: #fff; 
                font-size: 16px; 
            }
            QTableView::focus { outline: none; }
            QHeaderView::section { 
                background-color: #181818; 
                color: #b3b3b3; 
                font-size: 14px; 
                border: none; 
                padding: 10px;
            }
            QTableWidget::item { 
                padding: 12px 8px;
            }
            QTableWidget::focus { outline: none; }
            QTableWidget::item:selected { 
                background-color: #313a4d; 
            }
            QTableWidget::item:hover {
                background-color: #313a4d;
            }
            QTableWidget::item:focus {
                outline: none;
            }
        """)
        
        # Connect double-click signal
        self.table.cellDoubleClicked.connect(self.on_row_double_clicked)
        
        layout.addWidget(self.table)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        
        # Store track data for retrieval
        self.tracks_data : list[Track] = []

    def set_tracks(self, tracks):
        self.tracks_data = tracks
        self.table.setRowCount(len(tracks))
        
        for i, track in enumerate(tracks):
            # Number column
            num_item = QTableWidgetItem(str(track.track_number))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 0, num_item)
            
            # Title + Artist column
            info_container = QWidget()
            info_container.setStyleSheet("background: transparent; border: none;")
            info_layout = QVBoxLayout(info_container)
            info_layout.setContentsMargins(10, 8, 10, 8)
            info_layout.setSpacing(2)
            
            title_label = QLabel(track.name)
            title_label.setStyleSheet("color: white; font-weight: bold; font-size: 15px; border: none; background: transparent;")
            
            artist_label = ArtistLinksLabel()
            # If we have full artist objects in extra_data, use them
            artists = track.extra_data.get('artists', []) if hasattr(track, 'extra_data') and track.extra_data else []
            if not artists and 'artist_name' in (track.extra_data or {}):
                # Fallback to plain text if objects aren't available (though they should be now)
                artist_label.setText(track.extra_data['artist_name'])
                artist_label.setCursor(Qt.CursorShape.ArrowCursor)
            else:
                artist_label.set_artists(artists)
                artist_label.artistClicked.connect(self.artistClicked.emit)
                
            info_layout.addWidget(title_label)
            info_layout.addWidget(artist_label)
            
            self.table.setCellWidget(i, 1, info_container)
            
            # Duration column
            duration_item = QTableWidgetItem(self.format_duration(track.length))
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 2, duration_item)
            
            self.table.setRowHeight(i, 80)
            
        # Adjust table height to fit all rows
        self.update_table_height()

    def update_table_height(self):
        height = self.table.horizontalHeader().height()
        for i in range(self.table.rowCount()):
            height += self.table.rowHeight(i)
        self.table.setFixedHeight(height + 2)

    def format_duration(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m}:{s:02d}"

    def on_row_double_clicked(self, row, column):
        if 0 <= row < len(self.tracks_data):
            track_id = self.tracks_data[row].id
            if track_id:
                self.playTrackRequested.emit(track_id)