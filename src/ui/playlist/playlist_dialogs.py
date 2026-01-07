from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QPushButton, QCheckBox)

class CreatePlaylistDialog(QDialog):
    """Dialog for creating a new playlist"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Playlist")
        self.setModal(True)
        self.setFixedSize(450, 280)
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel("Create New Playlist")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        # Name
        name_label = QLabel("Playlist Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter playlist name...")
        self.name_input.textChanged.connect(self.validate_input)
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        
        # Description
        desc_label = QLabel("Description (optional):")
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Enter description...")
        self.desc_input.setMaximumHeight(80)
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
        
        self.create_btn = QPushButton("Create")
        self.create_btn.setEnabled(False)
        self.create_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.create_btn)
        
        layout.addLayout(btn_layout)
        
        # Focus on name input
        self.name_input.setFocus()
    
    def validate_input(self):
        """Validate input and enable/disable create button"""
        has_name = bool(self.name_input.text().strip())
        self.create_btn.setEnabled(has_name)
    
    def apply_styles(self):
        """Apply stylesheet"""
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
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
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
    
    def get_playlist_data(self):
        """Get the playlist data from the form"""
        return {
            'name': self.name_input.text().strip(),
            'description': self.desc_input.toPlainText().strip(),
            'make_public': self.public_checkbox.isChecked()
        }


class EditPlaylistDialog(QDialog):
    """Dialog for editing an existing playlist"""
    
    def __init__(self, playlist_name, playlist_desc="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Playlist")
        self.setModal(True)
        self.setFixedSize(450, 250)
        self.original_name = playlist_name
        self.init_ui(playlist_name, playlist_desc)
        self.apply_styles()
    
    def init_ui(self, playlist_name, playlist_desc):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel("Edit Playlist")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        # Name
        name_label = QLabel("Playlist Name:")
        self.name_input = QLineEdit()
        self.name_input.setText(playlist_name)
        self.name_input.textChanged.connect(self.validate_input)
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        
        # Description
        desc_label = QLabel("Description (optional):")
        self.desc_input = QTextEdit()
        self.desc_input.setPlainText(playlist_desc)
        self.desc_input.setMaximumHeight(80)
        layout.addWidget(desc_label)
        layout.addWidget(self.desc_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
        
        # Focus on name input
        self.name_input.setFocus()
        self.name_input.selectAll()
    
    def validate_input(self):
        """Validate input and enable/disable save button"""
        has_name = bool(self.name_input.text().strip())
        self.save_btn.setEnabled(has_name)
    
    def apply_styles(self):
        """Apply stylesheet"""
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
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
            }
            QPushButton#cancelBtn {
                background-color: #404040;
                color: white;
            }
            QPushButton#cancelBtn:hover {
                background-color: #505050;
            }
        """)
    
    def get_playlist_data(self):
        """Get the playlist data from the form"""
        return {
            'name': self.name_input.text().strip(),
            'description': self.desc_input.toPlainText().strip()
        }
    
    def has_changes(self):
        """Check if any changes were made"""
        return self.name_input.text().strip() != self.original_name


class DeletePlaylistDialog(QDialog):
    """Dialog for confirming playlist deletion"""
    
    def __init__(self, playlist_name, track_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Delete Playlist")
        self.setModal(True)
        self.setFixedSize(400, 200)
        self.init_ui(playlist_name, track_count)
        self.apply_styles()
    
    def init_ui(self, playlist_name, track_count):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Warning icon and title
        header_layout = QHBoxLayout()
        warning_label = QLabel("⚠")
        warning_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(warning_label)
        
        title = QLabel("Delete Playlist?")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Message
        message = QLabel(
            f"Are you sure you want to delete the playlist <b>{playlist_name}</b>?<br><br>"
            f"This playlist contains <b>{track_count}</b> track{'s' if track_count != 1 else ''}. "
            f"This action cannot be undone."
        )
        message.setWordWrap(True)
        layout.addWidget(message)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        
        delete_btn = QPushButton("Delete Playlist")
        delete_btn.setObjectName("deleteBtn")
        delete_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
    
    def apply_styles(self):
        """Apply stylesheet"""
        self.setStyleSheet("""
            QDialog {
                background-color: #181818;
            }
            QLabel {
                color: white;
                font-size: 14px;
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
            QPushButton#deleteBtn {
                background-color: #E53E3E;
                color: white;
            }
            QPushButton#deleteBtn:hover {
                background-color: #C53030;
            }
        """)