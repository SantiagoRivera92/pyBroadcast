import pytest
from src.api.ibroadcast.models import Artist, Album, Track, Playlist

def test_artist_creation():
    artist = Artist(1, "Test Artist", 5, 100)
    assert artist.id == 1
    assert artist.name == "Test Artist"
    assert artist.rating == 5
    assert artist.artwork_id == 100

def test_album_creation():
    album = Album(1, "Test Album", 4, 1, 2023)
    assert album.id == 1
    assert album.name == "Test Album"
    assert album.rating == 4
    assert album.disc == 1
    assert album.year == 2023

def test_track_creation():
    track = Track(1, "Test Track", 1, 2023, 300, 100, 5, 10, "file.mp3")
    assert track.id == 1
    assert track.name == "Test Track"
    assert track.length == 300
    assert track.file == "file.mp3"

def test_playlist_creation():
    playlist = Playlist(1, "Test Playlist", "Description", 100)
    assert playlist.id == 1
    assert playlist.name == "Test Playlist"
    assert playlist.description == "Description"
