from PyQt6.QtWidgets import QFrame, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt, pyqtSignal

class AlbumTrackList(QFrame):
    playTrackRequested = pyqtSignal(object)

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
            QTableWidget::item:selected { 
                background-color: #282828; 
            }
            QTableWidget::item:hover {
                background-color: #202020;
            }
        """)
        
        # Connect double-click signal
        self.table.cellDoubleClicked.connect(self.on_row_double_clicked)
        
        layout.addWidget(self.table)
        
        # Store track data for retrieval
        self.tracks_data = []

    def set_tracks(self, tracks):
        self.tracks_data = tracks
        self.table.setRowCount(len(tracks))
        
        for i, track in enumerate(tracks):
            num_item = QTableWidgetItem(str(track.get('track', i+1)))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            title_item = QTableWidgetItem(track.get('title', 'Unknown'))
            
            duration_item = QTableWidgetItem(self.format_duration(track.get('length', 0)))
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.table.setItem(i, 0, num_item)
            self.table.setItem(i, 1, title_item)
            self.table.setItem(i, 2, duration_item)

    def format_duration(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m}:{s:02d}"

    def on_row_double_clicked(self, row, column):
        if 0 <= row < len(self.tracks_data):
            track_id = self.tracks_data[row].get('item_id')
            if track_id:
                self.playTrackRequested.emit(track_id)