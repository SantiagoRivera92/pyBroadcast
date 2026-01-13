from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtSvgWidgets import QSvgWidget
from src.core.resource_path import resource_path

class LoginScreen(QWidget):
    loginRequested = pyqtSignal(str, str)  # client_id, client_secret
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        # Main layout with dark background (following app style)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setStyleSheet("background-color: #121212; color: white;")
        
        # Center container
        center_container = QWidget()
        center_container.setFixedWidth(450)
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(40, 40, 40, 40)
        center_layout.setSpacing(20)
        
        # Logo (Powered by iBroadcast)
        logo_path = resource_path("assets/powered.svg")
        self.logo = QSvgWidget(logo_path)
        self.logo.setFixedSize(300, 100)
        center_layout.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Title
        title = QLabel("pyBroadcast")
        title.setFont(QFont("Inter", 28, QFont.Weight.Bold))
        center_layout.addWidget(title, 0, Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Your premium iBroadcast Desktop Client")
        subtitle.setStyleSheet("color: #b3b3b3;")
        subtitle.setFont(QFont("Inter", 12))
        center_layout.addWidget(subtitle, 0, Qt.AlignmentFlag.AlignCenter)
        
        center_layout.addSpacing(20)
        
        # Credentials Group
        creds_frame = QFrame()
        creds_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 12px;
                border: 1px solid #333;
            }
        """)
        creds_layout = QVBoxLayout(creds_frame)
        creds_layout.setContentsMargins(20, 20, 20, 20)
        creds_layout.setSpacing(15)
        
        creds_title = QLabel("API Configuration")
        creds_title.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        creds_title.setStyleSheet("border: none; color: #b3b3b3;")
        creds_layout.addWidget(creds_title)
        
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("Client ID")
        self.client_id_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                border: none;
                border-radius: 6px;
                padding: 10px;
                color: white;
            }
        """)
        creds_layout.addWidget(self.client_id_input)
        
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setPlaceholderText("Client Secret")
        self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.client_secret_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                border: none;
                border-radius: 6px;
                padding: 10px;
                color: white;
            }
        """)
        creds_layout.addWidget(self.client_secret_input)
        
        # Helper link
        help_link = QPushButton("Where do I find my Client ID & Secret?")
        help_link.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #1DB954;
                text-align: left;
                border: none;
                font-size: 11px;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        help_link.setCursor(Qt.CursorShape.PointingHandCursor)
        help_link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.ibroadcast.com/apps/")))
        creds_layout.addWidget(help_link)
        
        center_layout.addWidget(creds_frame)
        
        # Login Button
        self.login_btn = QPushButton("Login with iBroadcast")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: white;
                border-radius: 25px;
                padding: 15px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1ed760;
            }
            QPushButton:disabled {
                background-color: #333;
                color: #777;
            }
        """)
        self.login_btn.clicked.connect(self._on_login_clicked)
        center_layout.addWidget(self.login_btn)
        
        # Status Label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #ff5555;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.status_label)
        
        # Add a spacer to center it vertically
        main_layout = QVBoxLayout()
        main_layout.addStretch()
        main_layout.addWidget(center_container, 0, Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch()
        
        layout.addLayout(main_layout)
        
    def _on_login_clicked(self):
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()
        
        if not client_id or not client_secret:
            self.set_error("Please enter both Client ID and Secret")
            return
            
        self.loginRequested.emit(client_id, client_secret)
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Connecting...")
        
    def set_error(self, message):
        self.status_label.setText(message)
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Login with iBroadcast")

    def set_credentials(self, client_id, client_secret):
        """Pre-fill fields if keys are already known but login is still required"""
        self.client_id_input.setText(client_id or "")
        self.client_secret_input.setText(client_secret or "")
