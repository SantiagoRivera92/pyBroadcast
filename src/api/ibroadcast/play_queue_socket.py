from PyQt6.QtCore import QObject, pyqtSignal, QUrl, QTimer
from PyQt6.QtWebSockets import QWebSocket
import json
import traceback

class PlayQueueSocket(QObject):
    stateUpdated = pyqtSignal(dict)
    libraryUpdateRequested = pyqtSignal(str)
    sessionEnded = pyqtSignal()
    connected = pyqtSignal()
    disconnected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.socket = QWebSocket()
        self.socket.connected.connect(self._on_connected)
        self.socket.disconnected.connect(self._on_disconnected)
        self.socket.textMessageReceived.connect(self._on_text_message)
        self.socket.errorOccurred.connect(self._on_error)
        
        self.token = None
        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.timeout.connect(self._reconnect)
        
        self.is_connected = False
        self.manual_disconnect = False

    def connect_to_server(self, token: str, session_uuid: str = None):
        self.token = token
        if session_uuid:
            self.session_uuid = session_uuid
        self.manual_disconnect = False
        url = f"wss://queue.ibroadcast.com/ws?token={token}&onequeue=1"
        self.socket.open(QUrl(url))

    def disconnect_from_server(self):
        self.manual_disconnect = True
        self.socket.close()

    def send_command(self, cmd: str, value=None):
        if not self.is_connected:
            return
        
        payload = {
            "command": cmd,
            "version": "0.1",
            "client": "iBroadcast",
            "device_name": "pyBroadcast Desktop"
        }
        if value is not None:
            # If value is a dict, merge it or set it? 
            # Usually 'set_state' sends the state dict as 'value'
            payload["value"] = value
            
        if hasattr(self, 'session_uuid') and self.session_uuid:
             payload["session_uuid"] = self.session_uuid
        
        message = json.dumps(payload)
        self.socket.sendTextMessage(message)

    def send_get_state(self):
        self.send_command("get_state")

    def send_set_state(self, state_value: dict):
        self.send_command("set_state", state_value)

    def _on_connected(self):
        self.is_connected = True
        self.reconnect_timer.stop()
        self.connected.emit()
        
        # Immediate get_state to restore state
        self.send_get_state()

    def _on_disconnected(self):
        self.is_connected = False
        self.disconnected.emit()
        if not self.manual_disconnect:
            self.reconnect_timer.start(5000)

    def _on_error(self, error_code):
        pass

    def _reconnect(self):
        if self.token:
            self.connect_to_server(self.token)

    def _on_text_message(self, message):
        try:
            data = json.loads(message)
            
            # Capture session_uuid if present in any message
            if "session_uuid" in data:
                self.session_uuid = data["session_uuid"]
            
            cmd = data.get("command")
            
            if cmd == "set_state":
                self.stateUpdated.emit(data)
                
            elif cmd == "update_library":
                self.libraryUpdateRequested.emit(data.get("lastmodified", ""))
                
            elif cmd == "end_session":
                self.sessionEnded.emit()
                
            elif cmd == "sessions":
                pass 
                
        except Exception as e:
            traceback.print_exc()
