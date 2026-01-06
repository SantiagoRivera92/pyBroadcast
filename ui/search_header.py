from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLineEdit
from PyQt6.QtCore import pyqtSignal

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
    
    def clear(self):
        self.search_input.clear()