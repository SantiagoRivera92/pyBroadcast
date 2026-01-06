from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QListWidget, 
                             QListWidgetItem, QPushButton, QHBoxLayout, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QDrag
from PyQt6.QtCore import QMimeData

class QueueItem(QWidget):
    removeRequested = pyqtSignal(int)
    
    def __init__(self, track_info, index, is_current=False, is_play_next=False):
        super().__init__()
        print("Creating QueueItem for index", index, "is_current:", is_current, "is_play_next:", is_play_next)
        self.index = index
        self.track_info = track_info
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        title_label = QLabel(track_info.get('title', 'Unknown'))
        title_label.setStyleSheet(f"""
            color: {'#5DADE2' if is_current else 'white'};
            font-weight: {'bold' if is_current else 'normal'};
            font-size: 14px;
        """)
        title_label.setWordWrap(True)
        
        artist_label = QLabel(track_info.get('artist', 'Unknown Artist'))
        artist_label.setStyleSheet("color: #b3b3b3; font-size: 12px;")
        artist_label.setWordWrap(True)
        
        info_layout.addWidget(title_label)
        info_layout.addWidget(artist_label)
        
        if is_play_next:
            badge = QLabel("UP NEXT")
            badge.setStyleSheet("""
                background-color: #5DADE2;
                color: black;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
            """)
            badge.setFixedHeight(20)
            info_layout.addWidget(badge)
        
        layout.addLayout(info_layout, 1)
        
        remove_btn = QPushButton("X")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                color: #b3b3b3;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ff4444;
            }
        """)
        remove_btn.clicked.connect(lambda: self.removeRequested.emit(self.index))
        layout.addWidget(remove_btn)
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {'#282828' if is_current else '#181818'};
                border-radius: 4px;
            }}
            QWidget:hover {{
                background-color: #202020;
            }}
        """)

class QueueSidebar(QFrame):
    playTrackRequested = pyqtSignal(int)
    removeTrackRequested = pyqtSignal(int, bool)
    clearQueueRequested = pyqtSignal()
    reorderRequested = pyqtSignal(int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(350)
        self.setStyleSheet("""
            QFrame {
                background-color: #000000;
                border-left: 1px solid #282828;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: #000000; border-bottom: 1px solid #282828;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        title = QLabel("Play Queue")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: none;
                border: 1px solid #5DADE2;
                color: #5DADE2;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5DADE2;
                color: black;
            }
        """)
        clear_btn.clicked.connect(self.clearQueueRequested.emit)
        header_layout.addWidget(clear_btn)
        
        layout.addWidget(header)
        
        self.queue_list = QListWidget()
        self.queue_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.queue_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.queue_list.setStyleSheet("""
            QListWidget {
                background-color: #000000;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border: none;
                padding: 0px;
                margin: 5px 10px;
            }
            QListWidget::item:selected {
                background: transparent;
            }
        """)
        self.queue_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.queue_list.itemClicked.connect(self._on_item_clicked)
        model = self.queue_list.model()
        if model:
            model.rowsMoved.connect(self._on_rows_moved)
        
        layout.addWidget(self.queue_list)
        
        self.tracks_data = []
        self.play_next_data = []
        self.current_index = 0
        self.play_from = 'tracks'
    
    def _on_item_clicked(self, item):
        widget = self.queue_list.itemWidget(item)
        if isinstance(widget, QueueItem):
            self.playTrackRequested.emit(widget.index)
    
    def _on_rows_moved(self, parent, start, end, destination, row):
        play_next_count = len(self.play_next_data)
        
        if start >= play_next_count and row >= play_next_count:
            old_index = start - play_next_count
            new_index = row - play_next_count
            if new_index > old_index:
                new_index -= 1
            self.reorderRequested.emit(old_index, new_index)
    
    def set_queue(self, tracks_data, play_next_data, current_index, play_from='tracks'):
        print("Setting queue with", len(tracks_data), "tracks and", len(play_next_data), "play next")
        self.tracks_data = tracks_data
        self.play_next_data = play_next_data
        self.current_index = current_index
        self.play_from = play_from
        
        self.queue_list.clear()
        
        for i, track in enumerate(play_next_data):
            is_current = (play_from == 'play_next' and i == 0)
            self._add_track_item(track, i, is_current, is_play_next=True)
        
        for i, track in enumerate(tracks_data):
            is_current = (play_from == 'tracks' and i == current_index)
            self._add_track_item(track, i, is_current, is_play_next=False)
    
    def _add_track_item(self, track, index, is_current, is_play_next):
        print("Adding track item:", track.get('title', 'Unknown'), "Index:", index, "Is current:", is_current, "Is play next:", is_play_next)
        item = QListWidgetItem(self.queue_list)
        
        widget = QueueItem(track, index, is_current, is_play_next)
        widget.removeRequested.connect(lambda idx: self.removeTrackRequested.emit(idx, is_play_next))
        
        item.setSizeHint(widget.sizeHint())
        self.queue_list.addItem(item)
        self.queue_list.setItemWidget(item, widget)
        
        if is_current:
            self.queue_list.scrollToItem(item)
    
    def get_track_count(self):
        return len(self.tracks_data) + len(self.play_next_data)
    
    def update_current_track(self, index, play_from='tracks'):
        print("Updating current track to index", index, "from", play_from)
        self.current_index = index
        self.play_from = play_from
        self.set_queue(self.tracks_data, self.play_next_data, self.current_index, self.play_from)