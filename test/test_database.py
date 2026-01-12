import pytest
from src.api.ibroadcast.models import Artist, Album, Track

def test_database_init(db):
    """Test that tables are created."""
    cursor = db.conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    assert "Artists" in tables
    assert "Albums" in tables
    assert "Tracks" in tables
    assert "Playlists" in tables

def test_insert_and_get_artist(db):
    artist = Artist(1, "Test Artist", 0, 0)
    db.insert_artist(artist)
    fetched = db.get_artist_by_id(1)
    assert fetched is not None
    assert fetched.name == "Test Artist"

def test_artist_filtering(db):
    """Verify criteria: Hide artists with no solo albums who only appear on split albums with major artists."""
    
    # 1. Major Artist (Solo Album)
    db.insert_artist(Artist(1, "Major1", 0, 0))
    db.insert_album(Album(101, "Solo Major1", 0, 1, 2020))
    db.conn.execute("INSERT INTO Album_Artists (album_id, artist_id) VALUES (101, 1)")
    
    # 2. Major Artist 2 (Solo Album)
    db.insert_artist(Artist(2, "Major2", 0, 0))
    db.insert_album(Album(102, "Solo Major2", 0, 1, 2020))
    db.conn.execute("INSERT INTO Album_Artists (album_id, artist_id) VALUES (102, 2)")
    
    # 3. Minor Artist (Only on split with Major1 & Major2) -> SHOULD BE HIDDEN
    db.insert_artist(Artist(3, "Minor1", 0, 0))
    
    # Split Album 1: Major1 & Minor1
    db.insert_album(Album(103, "Split1", 0, 1, 2020))
    db.conn.execute("INSERT INTO Album_Artists (album_id, artist_id) VALUES (103, 1)")
    db.conn.execute("INSERT INTO Album_Artists (album_id, artist_id) VALUES (103, 3)")
    
    # Split Album 2: Major2 & Minor1
    db.insert_album(Album(104, "Split2", 0, 1, 2020))
    db.conn.execute("INSERT INTO Album_Artists (album_id, artist_id) VALUES (104, 2)")
    db.conn.execute("INSERT INTO Album_Artists (album_id, artist_id) VALUES (104, 3)")
    
    # 4. Minor Artist 2 (With Minor Artist 3) -> SHOULD BE SHOWN (because they are not with majors only)
    db.insert_artist(Artist(4, "Minor2", 0, 0))
    db.insert_artist(Artist(5, "Minor3", 0, 0))
    
    db.insert_album(Album(105, "Split3", 0, 1, 2020))
    db.conn.execute("INSERT INTO Album_Artists (album_id, artist_id) VALUES (105, 4)")
    db.conn.execute("INSERT INTO Album_Artists (album_id, artist_id) VALUES (105, 5)")
    
    filtered_artists = db.get_artists_with_albums()
    filtered_ids = sorted([a.id for a in filtered_artists])
    
    assert 1 in filtered_ids
    assert 2 in filtered_ids
    assert 3 not in filtered_ids # HIDDEN
    assert 4 in filtered_ids
    assert 5 in filtered_ids

def test_clear_database(db):
    db.insert_artist(Artist(1, "Test", 0,0))
    db.clear_database()
    assert len(db.get_all_artists()) == 0
    
    # Verify link tables are cleared
    count = db.conn.execute("SELECT COUNT(*) FROM Album_Artists").fetchone()[0]
    assert count == 0
