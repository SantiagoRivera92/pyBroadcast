from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
from src.core.resource_path import resource_path

class SearchHeader(QFrame):
    searchTextChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self.setStyleSheet("background-color: #000000; border-bottom: 1px solid #282828;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tracks, artists, or albums...")
        self.search_input.setFixedWidth(450)
        self.search_input.setStyleSheet("""
            QLineEdit { 
                background-color: #242424; color: white; border-radius: 20px; 
                padding: 10px 20px; border: 1px solid transparent; font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #5DADE2; }
        """)
        self.search_input.textChanged.connect(self.searchTextChanged.emit)
        
        layout.addWidget(self.search_input)
        layout.addStretch()
        
        # Powered by Logo
        self.logo_label = QLabel()
        pixmap = QPixmap(resource_path("assets/powered.svg"))
        if not pixmap.isNull():
             pixmap = pixmap.scaledToHeight(40, Qt.TransformationMode.SmoothTransformation)
             self.logo_label.setPixmap(pixmap)
        layout.addWidget(self.logo_label)
    
    def clear(self):
        self.search_input.clear()