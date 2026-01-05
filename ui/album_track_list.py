from PyQt6.QtWidgets import QFrame, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView
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
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["#", "Title", "Duration", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #181818; color: #fff; font-size: 16px; }
            QHeaderView::section { background-color: #181818; color: #b3b3b3; font-size: 14px; border: none; }
            QTableWidget::item:selected { background-color: #282828; }
        """)
        layout.addWidget(self.table)

    def set_tracks(self, tracks):
        self.table.setRowCount(len(tracks))
        for i, track in enumerate(tracks):
            num_item = QTableWidgetItem(str(track.get('track', i+1)))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            title_item = QTableWidgetItem(track.get('title', 'Unknown'))
            duration_item = QTableWidgetItem(self.format_duration(track.get('length', 0)))
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            play_btn = QPushButton("▶")
            play_btn.setStyleSheet("background: none; color: #5DADE2; font-size: 18px; border: none;")
            play_btn.clicked.connect(lambda _, tid=track.get('item_id'): self.play_track(tid))
            self.table.setItem(i, 0, num_item)
            self.table.setItem(i, 1, title_item)
            self.table.setItem(i, 2, duration_item)
            self.table.setCellWidget(i, 3, play_btn)

    def format_duration(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m}:{s:02d}"

    def play_track(self, track_id):
        self.playTrackRequested.emit(track_id)
