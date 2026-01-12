import pytest
from unittest.mock import MagicMock, patch
from src.api.ibroadcast.ibroadcast_api import iBroadcastAPI

@pytest.fixture
def api(db):
    """Fixture for API client with mocked session and database."""
    # Patch DatabaseManager instantiation in iBroadcastAPI to return our test db fixture
    with patch('src.api.ibroadcast.ibroadcast_api.DatabaseManager', return_value=db):
        client = iBroadcastAPI()
        client.session = MagicMock()
        yield client

def test_api_initialization(api):
    assert api.base_url == "https://api.ibroadcast.com"
    assert api.library_url == "https://library.ibroadcast.com"

def test_load_library_success(api, db):
    # Mock OAuth config
    with patch('src.api.ibroadcast.ibroadcast_api.get_oauth_config', return_value={'client_id': 'id', 'client_secret': 'secret'}):
        api.access_token = "fake_token"
        
        # Mock API Response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'authenticated': True,
            'library': {
                'artists': {
                    'map': {'id': 0, 'name': 1},
                    '100': [100, 'Test Artist']
                },
                'albums': {},
                'tracks': {},
                'playlists': {}
            }
        }
        api.session.post.return_value = mock_response
        
        result = api.load_library()
        
        assert result['success'] is True
        
        # Verify DB was populated
        artist = db.get_artist_by_id(100)
        assert artist is not None
        assert artist.name == 'Test Artist'

def test_load_library_auth_fail(api):
    with patch('src.api.ibroadcast.ibroadcast_api.get_oauth_config', return_value={'client_id': 'id', 'client_secret': 'secret'}):
        api.access_token = "fake_token"
        
        # Mock API Response for detailed failure
        mock_response = MagicMock()
        mock_response.json.return_value = {'authenticated': False}
        api.session.post.return_value = mock_response
        
        # Mock refresh failing
        with patch.object(api, 'refresh_access_token', return_value=False):
            result = api.load_library()
            assert result['success'] is False
            assert result['message'] == 'Auth expired'
