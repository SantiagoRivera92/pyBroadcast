from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction

class TrackContextMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.play_action = QAction("Play Now", self)
        self.add_next_action = QAction("Add to Queue (Next)", self)
        self.add_end_action = QAction("Add to Queue (End)", self)
        
        self.addAction(self.play_action)
        self.addSeparator()
        self.addAction(self.add_next_action)
        self.addAction(self.add_end_action)
        
        self.setStyleSheet("""
            QMenu {
                background-color: #282828;
                color: white;
                border: 1px solid #404040;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px 8px 15px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #404040;
            }
            QMenu::separator {
                height: 1px;
                background-color: #404040;
                margin: 5px 10px;
            }
        """)

class AlbumContextMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.play_action = QAction("Play Now", self)
        self.add_queue_action = QAction("Add to Queue", self)
        
        self.addAction(self.play_action)
        self.addAction(self.add_queue_action)
        
        self.setStyleSheet("""
            QMenu {
                background-color: #282828;
                color: white;
                border: 1px solid #404040;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px 8px 15px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #404040;
            }
        """)

class PlaylistManagementMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.create_action = QAction("Create Playlist", self)
        self.edit_action = QAction("Edit Playlist", self)
        self.delete_action = QAction("Delete Playlist", self)
        
        self.addAction(self.create_action)
        self.addAction(self.edit_action)
        self.addAction(self.delete_action)
        
        self.setStyleSheet("""
            QMenu {
                background-color: #282828;
                color: white;
                border: 1px solid #404040;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px 8px 15px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #404040;
            }
        """)