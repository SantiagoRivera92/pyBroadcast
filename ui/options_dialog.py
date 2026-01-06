from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt

class OptionsDialog(QDialog):
    """Options dialog for app settings"""
    
    def __init__(self, lastfm_api, parent=None):
        super().__init__(parent)
        self.lastfm_api = lastfm_api
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Options")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Last.fm section
        lastfm_group = QGroupBox("Last.fm Integration")
        lastfm_layout = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel()
        self.update_status_label()
        lastfm_layout.addWidget(self.status_label)
        
        # Username field
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Last.fm username")
        username_layout.addWidget(self.username_input)
        lastfm_layout.addLayout(username_layout)
        
        # Password field
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Last.fm password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.password_input)
        lastfm_layout.addLayout(password_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.handle_login)
        button_layout.addWidget(self.login_btn)
        
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.clicked.connect(self.handle_logout)
        self.logout_btn.setEnabled(self.lastfm_api.is_authenticated())
        button_layout.addWidget(self.logout_btn)
        
        button_layout.addStretch()
        lastfm_layout.addLayout(button_layout)
        
        # Info label
        info_label = QLabel(
            "Note: To use Last.fm scrobbling, you need to create an API account at:\n"
            "https://www.last.fm/api/account/create"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 10px;")
        lastfm_layout.addWidget(info_label)
        
        lastfm_group.setLayout(lastfm_layout)
        layout.addWidget(lastfm_group)
        
        # Close button
        layout.addStretch()
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)
    
    def update_status_label(self):
        """Update the status label based on authentication state"""
        if self.lastfm_api.is_authenticated():
            self.status_label.setText(f"✓ Logged in as: {self.lastfm_api.username}")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText("Not connected to Last.fm")
            self.status_label.setStyleSheet("color: #666;")
    
    def handle_login(self):
        """Handle Last.fm login"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password")
            return
        
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Logging in...")
        
        result = self.lastfm_api.authenticate(username, password)
        
        if result['success']:
            QMessageBox.information(self, "Success", "Successfully logged in to Last.fm!")
            self.username_input.clear()
            self.password_input.clear()
            self.update_status_label()
            self.logout_btn.setEnabled(True)
        else:
            QMessageBox.warning(self, "Error", f"Login failed: {result.get('message', 'Unknown error')}")
        
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Login")
    
    def handle_logout(self):
        """Handle Last.fm logout"""
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout from Last.fm?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.lastfm_api.clear_credentials()
            self.update_status_label()
            self.logout_btn.setEnabled(False)
            QMessageBox.information(self, "Success", "Successfully logged out from Last.fm")