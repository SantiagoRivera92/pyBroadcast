import pytest
import os
import sys
from PyQt6.QtWidgets import QApplication

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.ibroadcast.database import DatabaseManager

@pytest.fixture(scope="session")
def qapp():
    """Fixture for QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

@pytest.fixture
def db():
    """Fixture for a temporary in-memory database or test-file database."""
    # Use a test file to avoid messing with real DB, but easier than in-memory for some concurrent things?
    # Actually in-memory is best for speed and isolation.
    # However, DatabaseManager hardcodes DB_PATH.
    # We need to patch it.
    
    import src.api.ibroadcast.database
    original_path = src.api.ibroadcast.database.DB_PATH
    src.api.ibroadcast.database.DB_PATH = ":memory:" # Or a temp file
    
    manager = DatabaseManager()
    yield manager
    
    manager.conn.close()
    src.api.ibroadcast.database.DB_PATH = original_path
