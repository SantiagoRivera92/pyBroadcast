from PyQt6.QtWidgets import QListWidget
from PyQt6.QtCore import pyqtSignal

class SidebarNavigation(QListWidget):
    viewChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(250)
        self.addItems(["Artists", "Albums", "Playlists"])
        
        self.setStyleSheet("""
            QListWidget {
                background-color: #0f0f0f; 
                color: #b3b3b3; 
                border: none; 
                outline: none;
                font-size: 16px;
                font-weight: 600;
                padding: 10px;
            }
            QListWidget::item {
                padding: 15px 20px;
                border-radius: 8px;
                margin: 2px 0px;
            }
            QListWidget::item:hover {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #1a1a1a;
                color: #4DA6FF;
            }
        """)
        
        self.currentRowChanged.connect(self.viewChanged.emit)
