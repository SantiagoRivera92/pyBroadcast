"""
Updated options dialog with tabbed interface for API credentials.
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QGroupBox, QMessageBox,
                             QTabWidget, QWidget)

from src.api.ibroadcast.ibroadcast_api import iBroadcastAPI
from src.core.credentials_manager import CredentialsManager


class APICredentialsTab(QWidget):
    """Tab for managing API credentials"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        
        # iBroadcast section
        ibroadcast_group = QGroupBox("iBroadcast API Credentials")
        ibroadcast_layout = QVBoxLayout()
        
        # Status
        self.ibroadcast_status = QLabel()
        self.update_ibroadcast_status()
        ibroadcast_layout.addWidget(self.ibroadcast_status)
        
        # Client ID
        client_id_layout = QHBoxLayout()
        client_id_layout.addWidget(QLabel("Client ID:"))
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("iBroadcast Client ID")
        client_id_layout.addWidget(self.client_id_input)
        ibroadcast_layout.addLayout(client_id_layout)
        
        # Client Secret
        secret_layout = QHBoxLayout()
        secret_layout.addWidget(QLabel("Client Secret:"))
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setPlaceholderText("iBroadcast Client Secret")
        self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        secret_layout.addWidget(self.client_secret_input)
        ibroadcast_layout.addLayout(secret_layout)
        
        # Show/hide button
        self.show_secret_btn = QPushButton("Show Secret")
        self.show_secret_btn.setCheckable(True)
        self.show_secret_btn.toggled.connect(self.toggle_secret_visibility)
        ibroadcast_layout.addWidget(self.show_secret_btn)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.save_ibroadcast_btn = QPushButton("Save Credentials")
        self.save_ibroadcast_btn.clicked.connect(self.save_ibroadcast_credentials)
        btn_layout.addWidget(self.save_ibroadcast_btn)
        
        self.clear_ibroadcast_btn = QPushButton("Clear Credentials")
        self.clear_ibroadcast_btn.clicked.connect(self.clear_ibroadcast_credentials)
        btn_layout.addWidget(self.clear_ibroadcast_btn)
        btn_layout.addStretch()
        ibroadcast_layout.addLayout(btn_layout)
        
        # Info
        info_label = QLabel(
            "To get your iBroadcast API credentials:\n"
            "1. Visit https://ibroadcast.com/developer\n"
            "2. Create or log into your account\n"
            "3. Register a new application\n"
            "4. Copy the Client ID and Client Secret here\n\n"
            "You need an iBroadcast account to use this application."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 10px;")
        ibroadcast_layout.addWidget(info_label)
        
        ibroadcast_group.setLayout(ibroadcast_layout)
        layout.addWidget(ibroadcast_group)
        
        layout.addStretch()
    
    def toggle_secret_visibility(self, checked):
        """Toggle secret visibility"""
        if checked:
            self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_secret_btn.setText("Hide Secret")
        else:
            self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_secret_btn.setText("Show Secret")
    
    def update_ibroadcast_status(self):
        """Update iBroadcast status label"""
        if CredentialsManager.has_ibroadcast_credentials():
            self.ibroadcast_status.setText("✓ Credentials configured")
            self.ibroadcast_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.ibroadcast_status.setText("⚠ No credentials configured")
            self.ibroadcast_status.setStyleSheet("color: orange; font-weight: bold;")
    
    def save_ibroadcast_credentials(self):
        """Save iBroadcast credentials"""
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()
        
        if not client_id or not client_secret:
            QMessageBox.warning(self, "Error", "Please enter both Client ID and Client Secret")
            return
        
        success = CredentialsManager.set_credential(
            CredentialsManager.IBROADCAST_CLIENT_ID,
            client_id
        )
        success = success and CredentialsManager.set_credential(
            CredentialsManager.IBROADCAST_CLIENT_SECRET,
            client_secret
        )
        
        if success:
            QMessageBox.information(self, "Success", "iBroadcast credentials saved successfully!")
            self.client_id_input.clear()
            self.client_secret_input.clear()
            self.update_ibroadcast_status()
        else:
            QMessageBox.critical(self, "Error", "Failed to save credentials")
    
    def clear_ibroadcast_credentials(self):
        """Clear iBroadcast credentials"""
        reply = QMessageBox.question(
            self,
            "Clear Credentials",
            "Are you sure you want to clear your iBroadcast credentials?\n"
            "You will need to re-authenticate.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if CredentialsManager.clear_ibroadcast_credentials():
                QMessageBox.information(self, "Success", "Credentials cleared")
                self.update_ibroadcast_status()
            else:
                QMessageBox.critical(self, "Error", "Failed to clear credentials")

class IBroadcastTab(QWidget):
    """Tab for iBroadcast actions like reloading the library."""
    def __init__(self, ibroadcast_api, parent=None):
        super().__init__(parent)
        self.ibroadcast_api = ibroadcast_api
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        reload_btn = QPushButton("Reload Library")
        reload_btn.clicked.connect(self.reload_library)
        layout.addWidget(reload_btn)
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        layout.addStretch()

    def reload_library(self):
        from PyQt6.QtCore import QThread, pyqtSignal, QObject

        class ReloadWorker(QObject):
            finished = pyqtSignal(dict)

            def __init__(self, ibroadcast_api: iBroadcastAPI):
                super().__init__()
                self.ibroadcast_api = ibroadcast_api

            def run(self):
                result = self.ibroadcast_api.load_library()
                self.finished.emit(result)

        self.status_label.setText("Reloading library...")
        self.reload_thread = QThread()
        self.worker = ReloadWorker(self.ibroadcast_api)
        self.worker.moveToThread(self.reload_thread)
        self.reload_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_reload_finished)
        self.worker.finished.connect(self.reload_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.reload_thread.finished.connect(self.reload_thread.deleteLater)
        self.reload_thread.start()

    def on_reload_finished(self, result):
        if result.get('success'):
            self.status_label.setText("Library reloaded successfully!")
        else:
            self.status_label.setText(f"Failed to reload library: {result.get('message', 'Unknown error')}")

class OptionsDialog(QDialog):
    """Main options dialog with tabbed interface"""
    
    def __init__(self, ibroadcast_api: iBroadcastAPI, parent=None, on_close_callback=None):
        super().__init__(parent)
        self.ibroadcast_api = ibroadcast_api
        self.on_close_callback = on_close_callback
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Options")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tabs = QTabWidget()

        # API Credentials tab
        self.api_tab = APICredentialsTab()
        self.tabs.addTab(self.api_tab, "API Credentials")

        # iBroadcast tab (library reload)
        self.ibroadcast_tab = IBroadcastTab(self.ibroadcast_api)
        self.tabs.addTab(self.ibroadcast_tab, "Refresh Library")
        
        layout.addWidget(self.tabs)
        
        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        if self.on_close_callback:
            self.finished.connect(self.on_close_callback)
            
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)