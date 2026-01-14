from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QSpacerItem,
    QSizePolicy,
    QTextEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtSvgWidgets import QSvgWidget
from src.core.resource_path import resource_path
from src.core.credentials_manager import CredentialsManager


class LoginScreen(QWidget):
    loginRequested = pyqtSignal()  # No args, since credentials are already set

    def __init__(self, parent=None):
        super().__init__(parent)
        self.editing = False
        self.init_ui()

    def init_ui(self):
        # Main layout with dark background (following app style)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setStyleSheet("background-color: #121212; color: white;")

        # Center container
        center_container = QWidget()
        center_container.setFixedWidth(500)
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(40, 40, 40, 40)
        center_layout.setSpacing(20)

        # Logo (Powered by iBroadcast)
        logo_path = resource_path("assets/powered.svg")
        self.logo = QSvgWidget(logo_path)
        self.logo.setMaximumWidth(300)
        center_layout.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("pyBroadcast")
        title.setFont(QFont("Inter", 28, QFont.Weight.Bold))
        center_layout.addWidget(title, 0, Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("A Python-based iBroadcast desktop client for Linux")
        subtitle.setStyleSheet("color: #b3b3b3;")
        subtitle.setFont(QFont("Inter", 12))
        center_layout.addWidget(subtitle, 0, Qt.AlignmentFlag.AlignCenter)

        center_layout.addSpacing(20)

        # Instructions
        instructions = QLabel(
            "To use pyBroadcast, you need to create an iBroadcast Developer App:\n\n"
            "1. Create an iBroadcast profile if you don't have one.\n"
            "2. Go to your username (on the top right) => Apps => Click on \"Developer\".\n"
            "3. Set the callback URL to: http://localhost:8888/callback\n"
            "4. Enter your Client ID and Client Secret below.\n"
            "5. Click 'Save Credentials' and then 'Login with iBroadcast'.\n"
            "6. Follow the login process in your web browser."            
        )
        instructions.setStyleSheet("color: #b3b3b3; font-size: 12px;")
        instructions.setWordWrap(True)
        center_layout.addWidget(instructions)

        # Credentials Group
        self.creds_frame = QFrame()
        self.creds_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 12px;
                border: 1px solid #333;
            }
        """)
        creds_layout = QVBoxLayout(self.creds_frame)
        creds_layout.setContentsMargins(20, 20, 20, 20)
        creds_layout.setSpacing(15)

        creds_title = QLabel("API Configuration")
        creds_title.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        creds_title.setStyleSheet("border: none; color: #b3b3b3;")
        creds_layout.addWidget(creds_title)

        client_id_label = QLabel("Client ID:")
        client_id_label.setStyleSheet("color: #b3b3b3; font-size: 14px; background-color: transparent; border: none;")
        creds_layout.addWidget(client_id_label)

        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("Enter your Client ID")
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

        client_secret_label = QLabel("Client Secret:")
        client_secret_label.setStyleSheet("color: #b3b3b3; font-size: 14px; background-color: transparent; border: none;")
        creds_layout.addWidget(client_secret_label)

        self.client_secret_input = QLineEdit()
        self.client_secret_input.setPlaceholderText("Enter your Client Secret")
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

        center_layout.addWidget(self.creds_frame)

        # Save/Edit Credentials Button
        self.save_btn = QPushButton("Save Credentials")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border-radius: 25px;
                padding: 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.save_btn.clicked.connect(self._on_save_or_edit_clicked)
        center_layout.addWidget(self.save_btn)

        # Login Button
        self.login_btn = QPushButton("Login with iBroadcast")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setEnabled(False)
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

    def _on_save_or_edit_clicked(self):
        if self.editing:
            # Save mode
            client_id = self.client_id_input.text().strip()
            client_secret = self.client_secret_input.text().strip()

            if not client_id or not client_secret:
                self.set_error("Please enter both Client ID and Secret")
                return

            CredentialsManager.set_credential(
                CredentialsManager.IBROADCAST_CLIENT_ID, client_id
            )
            CredentialsManager.set_credential(
                CredentialsManager.IBROADCAST_CLIENT_SECRET, client_secret
            )
            self.editing = False
            self._update_ui_for_credentials()
            self.status_label.setText("Credentials saved successfully.")
            self.status_label.setStyleSheet("color: #1DB954;")
        else:
            # Edit mode
            self.editing = True
            self._update_ui_for_editing()

    def _on_login_clicked(self):
        self.loginRequested.emit()
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Connecting...")

    def _update_ui_for_credentials(self):
        client_id = CredentialsManager.get_credential(
            CredentialsManager.IBROADCAST_CLIENT_ID
        )
        client_secret = CredentialsManager.get_credential(
            CredentialsManager.IBROADCAST_CLIENT_SECRET
        )
        if client_id and client_secret:
            self.creds_frame.setVisible(False)
            self.save_btn.setText("Edit Existing Credentials")
            self.login_btn.setEnabled(True)
        else:
            self.creds_frame.setVisible(True)
            self.save_btn.setText("Save Credentials")
            self.login_btn.setEnabled(False)
        self.editing = False

    def _update_ui_for_editing(self):
        self.creds_frame.setVisible(True)
        client_id = CredentialsManager.get_credential(
            CredentialsManager.IBROADCAST_CLIENT_ID
        )
        client_secret = CredentialsManager.get_credential(
            CredentialsManager.IBROADCAST_CLIENT_SECRET
        )
        self.client_id_input.setText(client_id or "")
        self.client_secret_input.setText(client_secret or "")
        self.save_btn.setText("Save Credentials")
        self.login_btn.setEnabled(False)

    def set_error(self, message):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #ff5555;")
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Login with iBroadcast")

    def set_credentials(self, client_id, client_secret):
        """Pre-fill fields if keys are already known but login is still required"""
        # Don't pre-fill here, handle in _update_ui_for_credentials
        self._update_ui_for_credentials()
