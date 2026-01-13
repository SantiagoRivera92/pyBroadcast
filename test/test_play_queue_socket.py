import pytest
from unittest.mock import MagicMock, call
import json
from PyQt6.QtCore import QUrl
from src.api.ibroadcast.play_queue_socket import PlayQueueSocket

@pytest.fixture
def socket(qapp):
    sock = PlayQueueSocket()
    # Mock the internal QWebSocket
    sock.socket = MagicMock()
    return sock

def test_connect(socket):
    socket.connect_to_server("test_token")
    socket.socket.open.assert_called_with(QUrl("wss://queue.ibroadcast.com?token=test_token"))

def test_send_get_state(socket):
    socket.is_connected = True
    socket.send_get_state()
    
    expected_payload = {
        "command": "get_state",
        "version": "0.1",
        "client": "pyBroadcast",
        "device_name": "pyBroadcast Desktop"
    }
    socket.socket.sendTextMessage.assert_called()
    args, _ = socket.socket.sendTextMessage.call_args
    sent_json = json.loads(args[0])
    assert sent_json == expected_payload

def test_receive_set_state(socket):
    # Mock signal emission
    mock_emit = MagicMock()
    socket.stateUpdated.connect(mock_emit)
    
    payload = {
        "command": "set_state",
        "role": "player",
        "current_song": 123
    }
    
    socket._on_text_message(json.dumps(payload))
    mock_emit.assert_called_with(payload)

def test_receive_update_library(socket):
    mock_emit = MagicMock()
    socket.libraryUpdateRequested.connect(mock_emit)
    
    payload = {
        "command": "update_library",
        "lastmodified": "2025-01-01"
    }
    
    socket._on_text_message(json.dumps(payload))
    mock_emit.assert_called_with("2025-01-01")

def test_reconnect_logic(socket):
    socket.connect_to_server("token")
    
    # Simulate disconnect
    socket._on_disconnected()
    
    # Timer should start
    assert socket.reconnect_timer.isActive()
    assert socket.reconnect_timer.interval() == 5000
    
    # Simulate timeout -> reconnect
    socket._reconnect()
    assert socket.socket.open.call_count == 2 # Initial + reconnect
