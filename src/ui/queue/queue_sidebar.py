from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QListWidget, 
                             QListWidgetItem, QPushButton, QHBoxLayout, QWidget, QSizePolicy)
from PyQt6.QtCore import QSize, Qt, pyqtSignal

from src.ui.utils.scrolling_label import ScrollingLabel
from src.ui.utils.hoverable_widget import HoverableWidget

class QueueItem(HoverableWidget):
    removeRequested = pyqtSignal(int)
    itemClicked = pyqtSignal(int)
    
    def __init__(self, track_info, index, is_current=False):
        super().__init__(self.callback, index)
        self.index = index
        self.track_info = track_info
        self.is_current = is_current
        
        # Set fixed height for uniformity
        self.setFixedHeight(64)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(314)
        self.setMaximumWidth(314)  # Match QueueSidebar fixed width
                
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Subtle indicator for current track
        if is_current:
            indicator = QWidget()
            indicator.setFixedSize(3, 32)
            indicator.setStyleSheet("background-color: #5DADE2; border-radius: 1px;")
            layout.addWidget(indicator, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        # Text container
        text_container = QWidget(self)
        text_container.setStyleSheet("background: transparent;")
        text_container.setMinimumWidth(240)
        text_container.setMaximumWidth(240)
        text_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        
        # Title label with proper height
        title_label = ScrollingLabel(text_container)
        title_label.setText(track_info.get('title', 'Unknown'))
        title_label.setFixedHeight(20)
        title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {'#FFFFFF' if is_current else '#E0E0E0'};
                font-size: 14px;
                font-weight: {'500' if is_current else 'normal'};
                background: transparent;
                padding: 0px;
                border: none;
            }}
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title_label.setTextFormat(Qt.TextFormat.PlainText)
        
        # Artist label with proper height
        artist_label = ScrollingLabel(text_container)
        artist_label.setText(track_info.get('artist', 'Unknown Artist'))
        artist_label.setFixedHeight(18)
        artist_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        artist_label.setStyleSheet(f"""
            QLabel {{
                color: {'#B3B3B3' if is_current else '#808080'};
                font-size: 12px;
                background: transparent;
                padding: 0px;
                border: none;
            }}
        """)
        artist_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        artist_label.setTextFormat(Qt.TextFormat.PlainText)
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(artist_label)
        text_layout.addStretch()
        
        layout.addWidget(text_container, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        # Remove button
        if not is_current:
            remove_btn = QPushButton("×")
            remove_btn.setFixedSize(32, 32)
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            remove_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 16px;
                    color: #666666;
                    font-size: 24px;
                    font-weight: 300;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.08);
                    color: #FFFFFF;
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.12);
                }
            """)
            remove_btn.clicked.connect(lambda: self.removeRequested.emit(self.index - 1))
            layout.addWidget(remove_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        # Widget background styling
        self.setStyleSheet(f"""
            QueueItem {{
                background-color: {'rgba(93, 173, 226, 0.08)' if is_current else 'transparent'};
                border-left: {'3px solid #5DADE2' if is_current else 'none'};
                border-radius: 4px;
            }}
            QueueItem:hover {{
                background-color: rgba(255, 255, 255, 0.08);
            }}
        """)
        
    def callback(self, index):
        """Callback for when the item is clicked"""
        self.itemClicked.emit(index)
    
    def sizeHint(self) -> QSize:
        sizeHint = super().sizeHint()
        sizeHint.setHeight(64)
        return sizeHint

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
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet("background-color: #000000; border-bottom: 1px solid #282828;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 0, 0)
        
        title = QLabel("Play Queue")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-left: 4px;")
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
                margin-right: 10px;
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
                padding: 0px;
                margin: 0px;
            }
            QListWidget::item {
                border: none;
                padding: 0px;
                margin: 2px 10px;
            }
            QListWidget::item:selected {
                background: transparent;
            }
        """)
        self.queue_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.queue_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.queue_list.itemClicked.connect(self._on_item_clicked)
        model = self.queue_list.model()
        if model:
            model.rowsMoved.connect(self._on_rows_moved)
        self.queue_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.queue_list, stretch=1)
        
        self.tracks_data = []
        self.current_index = 0
    
    def _on_item_clicked(self, item):
        widget = self.queue_list.itemWidget(item)
        if isinstance(widget, QueueItem):
            self.playTrackRequested.emit(widget.index - 1)
    
    def _on_rows_moved(self, parent, start, end, destination, row):
        old_index = start
        new_index = row
        if new_index > old_index:
            new_index -= 1
        self.reorderRequested.emit(old_index, new_index)
    
    def set_queue(self, tracks_data, play_next_data=None, current_index=0, play_from='tracks'):
        """
        Set the queue display. 
        For the new system, tracks_data includes both current and upcoming tracks.
        """
        self.tracks_data = tracks_data
        self.current_index = current_index
        self.queue_list.clear()
        
        # Display all tracks, checking the 'is_current' flag in each track dict
        for i, track in enumerate(tracks_data):
            is_current = track.get('is_current', False)
            self._add_track_item(track, i, is_current)
        
        # Add a footer to provide spacing at the bottom
        footer = QListWidgetItem(self.queue_list)
        size_hint = QWidget().sizeHint()
        size_hint.setHeight(64)
        footer.setSizeHint(size_hint)
        self.queue_list.addItem(footer)
    
    def _add_track_item(self, track, index, is_current):
        item = QListWidgetItem(self.queue_list)
        
        widget = QueueItem(track, index, is_current)
        widget.removeRequested.connect(lambda idx: self.removeTrackRequested.emit(idx, False))
        
        item.setSizeHint(widget.sizeHint())
        self.queue_list.addItem(item)
        self.queue_list.setItemWidget(item, widget)
        
        if is_current:
            self.queue_list.scrollToItem(item)
    
    def get_track_count(self):
        return len(self.tracks_data)
    
    def update_current_track(self, index):
        """Update which track is highlighted as current"""
        self.current_index = index
        self.set_queue(self.tracks_data, [], self.current_index, 'tracks')