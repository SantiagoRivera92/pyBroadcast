from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QPushButton, QCheckBox)
from PyQt6.QtCore import Qt

class CreatePlaylistDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Playlist")
        self.setModal(True)
        self.setFixedSize(400, 250)
        self.setStyleSheet("""
            QDialog {
                background-color: #181818;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QLineEdit, QTextEdit {
                background-color: #282828;
                color: white;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #5DADE2;
            }
            QPushButton {
                background-color: #5DADE2;
                color: black;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4A9DD1;
            }
            QPushButton:pressed {
                background-color: #3A8DC1;
            }
            QPushButton#cancelBtn {
                background-color: #404040;
                color: white;
            }
            QPushButton#cancelBtn:hover {
                background-color: #505050;
            }
            QCheckBox {
                color: white;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #5DADE2;
                border-radius: 3px;
                background-color: #282828;
            }
            QCheckBox::indicator:checked {
                background-color: #5DADE2;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Name
        name_label = QLabel("Playlist Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter playlist name...")
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        
        # Description
        desc_label = QLabel("Description (optional):")
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Enter description...")
        self.desc_input.setMaximumHeight(60)
        layout.addWidget(desc_label)
        layout.addWidget(self.desc_input)
        
        # Public checkbox
        self.public_checkbox = QCheckBox("Make playlist public")
        layout.addWidget(self.public_checkbox)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(create_btn)
        
        layout.addLayout(btn_layout)
    
    def get_playlist_data(self):
        return {
            'name': self.name_input.text(),
            'description': self.desc_input.toPlainText(),
            'make_public': self.public_checkbox.isChecked()
        }

class EditPlaylistDialog(QDialog):
    def __init__(self, playlist_name, playlist_desc="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Playlist")
        self.setModal(True)
        self.setFixedSize(400, 200)
        self.setStyleSheet("""
            QDialog {
                background-color: #181818;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QLineEdit, QTextEdit {
                background-color: #282828;
                color: white;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #5DADE2;
            }
            QPushButton {
                background-color: #5DADE2;
                color: black;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4A9DD1;
            }
            QPushButton#cancelBtn {
                background-color: #404040;
                color: white;
            }
            QPushButton#cancelBtn:hover {
                background-color: #505050;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Name
        name_label = QLabel("Playlist Name:")
        self.name_input = QLineEdit()
        self.name_input.setText(playlist_name)
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        
        # Description
        desc_label = QLabel("Description (optional):")
        self.desc_input = QTextEdit()
        self.desc_input.setPlainText(playlist_desc)
        self.desc_input.setMaximumHeight(60)
        layout.addWidget(desc_label)
        layout.addWidget(self.desc_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def get_playlist_data(self):
        return {
            'name': self.name_input.text(),
            'description': self.desc_input.toPlainText()
        }