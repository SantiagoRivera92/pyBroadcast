import sqlite3
from typing import List, List, Optional
from src.api.ibroadcast.models import Artist, Album, Track, Playlist, BaseModel

DB_PATH = "library.db"

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        with self.conn:
            self.conn.executescript('''
                PRAGMA foreign_keys = ON;
                CREATE TABLE IF NOT EXISTS Artists (artist_id INTEGER PRIMARY KEY, name TEXT, rating INTEGER, artwork_id INTEGER);
                CREATE TABLE IF NOT EXISTS Albums (album_id INTEGER PRIMARY KEY, name TEXT, rating INTEGER, disc INTEGER, year INTEGER);
                CREATE TABLE IF NOT EXISTS Tracks (track_id INTEGER PRIMARY KEY, album_id INTEGER, track_number INTEGER, year INTEGER, title TEXT, length INTEGER, artwork_id INTEGER, rating INTEGER, plays INTEGER, file TEXT, FOREIGN KEY(album_id) REFERENCES Albums(album_id) ON DELETE CASCADE);
                CREATE TABLE IF NOT EXISTS Playlists (playlist_id INTEGER PRIMARY KEY, name TEXT, description TEXT, artwork_id INTEGER);
                
                CREATE TABLE IF NOT EXISTS Track_Artists (ta_id INTEGER PRIMARY KEY AUTOINCREMENT, track_id INTEGER, artist_id INTEGER, UNIQUE(track_id, artist_id), FOREIGN KEY(track_id) REFERENCES Tracks(track_id) ON DELETE CASCADE, FOREIGN KEY(artist_id) REFERENCES Artists(artist_id) ON DELETE CASCADE);
                CREATE TABLE IF NOT EXISTS Album_Artists (aa_id INTEGER PRIMARY KEY AUTOINCREMENT, album_id INTEGER, artist_id INTEGER, UNIQUE(album_id, artist_id), FOREIGN KEY(album_id) REFERENCES Albums(album_id) ON DELETE CASCADE, FOREIGN KEY(artist_id) REFERENCES Artists(artist_id) ON DELETE CASCADE);
                CREATE TABLE IF NOT EXISTS Playlist_Tracks (pt_id INTEGER PRIMARY KEY AUTOINCREMENT, playlist_id INTEGER, track_id INTEGER, position INTEGER, FOREIGN KEY(playlist_id) REFERENCES Playlists(playlist_id) ON DELETE CASCADE, FOREIGN KEY(track_id) REFERENCES Tracks(track_id) ON DELETE CASCADE);
            ''')

    def clear_database(self):
        with self.conn:
            self.conn.execute("DELETE FROM Tracks")
            self.conn.execute("DELETE FROM Artists")
            self.conn.execute("DELETE FROM Albums")
            self.conn.execute("DELETE FROM Playlists")

    def sync_library(self, library_data: dict):
        """Processes the iBroadcast JSON and populates the DB."""
        self.clear_database()
        
        # 1. Insert Artists
        for aid, a in library_data.get('artists', {}).items():
            self.conn.execute(
                "INSERT INTO Artists (artist_id, name, rating, artwork_id) VALUES (?, ?, ?, ?)",
                (int(aid), a['name'], a.get('rating', 0), a.get('artwork_id'))
            )

        # 2. Insert Albums & Album_Artists
        for alid, al in library_data.get('albums', {}).items():
            self.conn.execute(
                "INSERT INTO Albums (album_id, name, rating, disc, year) VALUES (?, ?, ?, ?, ?)",
                (int(alid), al['name'], al.get('rating', 0), al.get('disc', 1), al.get('year', 0))
            )
            # Primary Album Artist
            self.conn.execute("INSERT INTO Album_Artists (album_id, artist_id) VALUES (?, ?)", (int(alid), al['artist_id']))
            # Additional Album Artists
            for extra in al.get('artists_additional', []):
                self.conn.execute("INSERT OR IGNORE INTO Album_Artists (album_id, artist_id) VALUES (?, ?)", 
                                  (int(alid), extra['artist_id']))

        # 3. Insert Tracks & Track_Artists
        for tid, t in library_data.get('tracks', {}).items():
            self.conn.execute(
                """INSERT INTO Tracks (track_id, album_id, track_number, year, title, length, artwork_id, rating, plays, file) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (int(tid), t['album_id'], t.get('track', 0), t.get('year', 0), t['title'], 
                 t.get('length', 0), t.get('artwork_id'), t.get('rating', 0), t.get('plays', 0), t.get('file', ""))
            )
            # Primary Track Artist
            self.conn.execute("INSERT INTO Track_Artists (track_id, artist_id) VALUES (?, ?)", (int(tid), t['artist_id']))
            # Additional Track Artists
            for extra in t.get('artists_additional', []):
                self.conn.execute("INSERT OR IGNORE INTO Track_Artists (track_id, artist_id) VALUES (?, ?)", 
                                  (int(tid), extra['artist_id']))

        # 4. Insert Playlists & Playlist_Tracks
        for pid, p in library_data.get('playlists', {}).items():
            self.conn.execute(
                "INSERT INTO Playlists (playlist_id, name, description, artwork_id) VALUES (?, ?, ?, ?)",
                (int(pid), p['name'], p.get('description'), p.get('artwork_id'))
            )
            for idx, track_id in enumerate(p.get('tracks', [])):
                self.conn.execute(
                    "INSERT INTO Playlist_Tracks (playlist_id, track_id, position) VALUES (?, ?, ?)",
                    (int(pid), track_id, idx)
                )
        
        self.conn.commit()

    def insert_artist(self, a: Artist):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO Artists VALUES (?, ?, ?, ?)", (a.id, a.name, a.rating, a.artwork_id))

    def insert_album(self, al: Album):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO Albums VALUES (?, ?, ?, ?, ?, ?)", (al.id, al.name, al.rating, al.disc, al.year))

    def insert_track(self, t: Track):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO Tracks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                (t.id, t.track_number, t.year, t.name, t.length, t.artwork_id, t.rating, t.plays, t.file))

    def insert_playlist(self, p: Playlist):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO Playlists VALUES (?, ?, ?, ?)", (p.id, p.name, p.description, p.artwork_id))

    # --- DELETE ---
    def delete_artist(self, artist_id: int):
        with self.conn: self.conn.execute("DELETE FROM Artists WHERE artist_id = ?", (artist_id,))

    def delete_album(self, album_id: int):
        with self.conn: self.conn.execute("DELETE FROM Albums WHERE album_id = ?", (album_id,))

    def delete_track(self, track_id: int):
        with self.conn: self.conn.execute("DELETE FROM Tracks WHERE track_id = ?", (track_id,))

    def delete_playlist(self, playlist_id: int):
        with self.conn: self.conn.execute("DELETE FROM Playlists WHERE playlist_id = ?", (playlist_id,))

    # --- GET EVERY ---
    def get_all_artists(self) -> List[Artist]:
        result = []
        for r in self.conn.execute("SELECT * FROM Artists ORDER BY name").fetchall():
            d = dict(r)
            result.append(Artist(d['artist_id'], d['name'], d['rating'], d['artwork_id']))
        return result

    def get_all_albums(self) -> List[Album]:
        result = []
        query = '''
            SELECT al.* FROM Albums al
            LEFT JOIN Album_Artists aa ON al.album_id = aa.album_id
            LEFT JOIN Artists a ON aa.artist_id = a.artist_id
            ORDER BY a.name COLLATE NOCASE, al.year
        '''
        for r in self.conn.execute(query).fetchall():
            d = dict(r)
            result.append(Album(d['album_id'], d['name'], d['rating'], d['disc'], d['year']))
        return result

    def get_all_tracks(self) -> List[Track]:
        result = []
        for r in self.conn.execute("SELECT * FROM Tracks").fetchall():
            d = dict(r)
            result.append(Track(d['track_id'], d['title'], d['track_number'], d['year'], d['length'], d['artwork_id'], d['rating'], d['plays'], d['file']))
        return result

    def get_all_playlists(self) -> List[Playlist]:
        result = []
        for r in self.conn.execute("SELECT * FROM Playlists").fetchall():
            d = dict(r)
            result.append(Playlist(d['playlist_id'], d['name'], d['description'], d['artwork_id']))
        return result
    
    # --- GET BY ID ---
    def get_artist_by_id(self, artist_id: int) -> Optional[Artist]:
        row = self.conn.execute("SELECT * FROM Artists WHERE artist_id = ?", (artist_id,)).fetchone()
        if row:
            d = dict(row)
            return Artist(d['artist_id'], d['name'], d['rating'], d['artwork_id'])
        return None
    
    def get_album_by_id(self, album_id: int) -> Optional[Album]:
        row = self.conn.execute("SELECT * FROM Albums WHERE album_id = ?", (album_id,)).fetchone()
        if row:
            d = dict(row)
            return Album(d['album_id'], d['name'], d['rating'], d['disc'], d['year'])
        return None
    
    def get_track_by_id(self, track_id: int) -> Optional[Track]:
        row = self.conn.execute("SELECT * FROM Tracks WHERE track_id = ?", (track_id,)).fetchone()
        if row:
            d = dict(row)
            return Track(d['track_id'], d['title'], d['track_number'], d['year'], d['length'], d['artwork_id'], d['rating'], d['plays'], d['file'])
        return None
    
    def get_playlist_by_id(self, playlist_id: int) -> Optional[Playlist]:
        row = self.conn.execute("SELECT * FROM Playlists WHERE playlist_id = ?", (playlist_id,)).fetchone()
        if row:
            d = dict(row)
            return Playlist(d['playlist_id'], d['name'], d['description'], d['artwork_id'])
        return None

    # --- FILTERED RETRIEVAL ---
    def get_tracks_by_artist(self, artist_id: int) -> List[Track]:
        result = []
        for r in self.conn.execute("SELECT t.* FROM Tracks t JOIN Track_Artists ta ON t.track_id = ta.track_id WHERE ta.artist_id = ?", (artist_id,)).fetchall():
            d = dict(r)
            result.append(Track(d['track_id'], d['title'], d['track_number'], d['year'], d['length'], d['artwork_id'], d['rating'], d['plays'], d['file']))
        return result

    def get_tracks_by_album(self, album_id: int) -> List[Track]:
        result = []
        for r in self.conn.execute("SELECT * FROM Tracks WHERE album_id = ? ORDER BY track_number", (album_id,)).fetchall():
            d = dict(r)
            result.append(Track(d['track_id'], d['title'], d['track_number'], d['year'], d['length'], d['artwork_id'], d['rating'], d['plays'], d['file']))
        return result

    def get_tracks_by_playlist(self, playlist_id: int) -> List[Track]:
        result = []
        for r in self.conn.execute("SELECT t.* FROM Tracks t JOIN Playlist_Tracks pt ON t.track_id = pt.track_id WHERE pt.playlist_id = ? ORDER BY pt.position", (playlist_id,)).fetchall():
            d = dict(r)
            result.append(Track(d['track_id'], d['title'], d['track_number'], d['year'], d['length'], d['artwork_id'], d['rating'], d['plays'], d['file']))
        return result

    def get_artists_by_album(self, album_id: int) -> List[Artist]:
        result = []
        for r in self.conn.execute("SELECT a.* FROM Artists a JOIN Album_Artists aa ON a.artist_id = aa.artist_id WHERE aa.album_id = ?", (album_id,)).fetchall():
            d = dict(r)
            result.append(Artist(d['artist_id'], d['name'], d['rating'], d['artwork_id']))
        return result

    def get_artists_with_albums(self) -> List[Artist]:
        result = []
        for r in self.conn.execute("""
            SELECT DISTINCT a.* FROM Artists a
            JOIN Album_Artists aa ON a.artist_id = aa.artist_id
            JOIN Albums al ON aa.album_id = al.album_id
            ORDER BY a.name COLLATE NOCASE
        """).fetchall():
            d = dict(r)
            result.append(Artist(d['artist_id'], d['name'], d['rating'], d['artwork_id']))
        return result
    
    def get_artists_by_track(self, track_id: int) -> List[Artist]:
        result = []
        for r in self.conn.execute("SELECT a.* FROM Artists a JOIN Track_Artists ta ON a.artist_id = ta.artist_id WHERE ta.track_id = ?", (track_id,)).fetchall():
            d = dict(r)
            result.append(Artist(d['artist_id'], d['name'], d['rating'], d['artwork_id']))
        return result

    def get_album_by_track(self, track_id: int) -> Optional[Album]:
        row = self.conn.execute("SELECT al.* FROM Albums al JOIN Tracks t ON al.album_id = t.album_id WHERE t.track_id = ?", (track_id,)).fetchone()
        if row:
            d = dict(row)
            return Album(d['album_id'], d['name'], d['rating'], d['disc'], d['year'])
        return None

    def get_albums_by_artist(self, artist_id: int) -> List[Album]:
        result = []
        for r in self.conn.execute("SELECT al.* FROM Albums al JOIN Album_Artists aa ON al.album_id = aa.album_id WHERE aa.artist_id = ? ORDER BY al.year", (artist_id,)).fetchall():
            d = dict(r)
            result.append(Album(d['album_id'], d['name'], d['rating'], d['disc'], d['year']))
        return result

    # --- Get all artwork ids ---
    def get_all_artwork_ids(self) -> List[int]:
        rows = self.conn.execute("""
            SELECT artwork_id FROM Artists
            UNION
            SELECT artwork_id FROM Tracks
            UNION
            SELECT artwork_id FROM Playlists
            WHERE artwork_id IS NOT NULL
        """).fetchall()
        return [row['artwork_id'] for row in rows if row['artwork_id'] is not None]

    # --- PLAYLIST MANIPULATION ---
    def add_track_to_playlist(self, playlist_id: int, track_id: int):
        with self.conn:
            pos = self.conn.execute("SELECT COALESCE(MAX(position), 0) + 1 FROM Playlist_Tracks WHERE playlist_id = ?", (playlist_id,)).fetchone()[0]
            self.conn.execute("INSERT INTO Playlist_Tracks (playlist_id, track_id, position) VALUES (?, ?, ?)", (playlist_id, track_id, pos))

    def remove_track_from_playlist(self, playlist_id: int, position: int):
        with self.conn:
            self.conn.execute("DELETE FROM Playlist_Tracks WHERE playlist_id = ? AND position = ?", (playlist_id, position))
            self.conn.execute("UPDATE Playlist_Tracks SET position = position - 1 WHERE playlist_id = ? AND position > ?", (playlist_id, position))

    def rearrange_playlist_track(self, playlist_id: int, old_pos: int, new_pos: int):
        with self.conn:
            target_id = self.conn.execute("SELECT pt_id FROM Playlist_Tracks WHERE playlist_id = ? AND position = ?", (playlist_id, old_pos)).fetchone()[0]
            self.conn.execute("UPDATE Playlist_Tracks SET position = -1 WHERE pt_id = ?", (target_id,))
            if old_pos > new_pos:
                self.conn.execute("UPDATE Playlist_Tracks SET position = position + 1 WHERE playlist_id = ? AND position >= ? AND position < ?", (playlist_id, new_pos, old_pos))
            else:
                self.conn.execute("UPDATE Playlist_Tracks SET position = position - 1 WHERE playlist_id = ? AND position > ? AND position <= ?", (playlist_id, old_pos, new_pos))
            self.conn.execute("UPDATE Playlist_Tracks SET position = ? WHERE pt_id = ?", (new_pos, target_id))
    
    def search_library(self, query: str) -> list[BaseModel]:
        """
        Searches across Tracks, Albums, Artists, and Playlists.
        Returns a dictionary of results sorted alphabetically.
        """
        search_term = f"%{query}%"
        results : List[BaseModel] = []

        with self.conn:
            # Search Tracks by Title
            track_rows = self.conn.execute(
                "SELECT * FROM Tracks WHERE title LIKE ? ORDER BY title COLLATE NOCASE",
                (search_term,)
            ).fetchall()
            for r in track_rows:
                track = Track(r['track_id'], r['title'], r['track_number'], r['year'], r['length'], r['artwork_id'], r['rating'], r['plays'], r['file'])
                results.append(track)

            # Search Albums by Name
            album_rows = self.conn.execute(
                "SELECT * FROM Albums WHERE name LIKE ? ORDER BY name COLLATE NOCASE",
                (search_term,)
            ).fetchall()
            for r in album_rows:
                album = Album(r['album_id'], r['name'], r['rating'], r['disc'], r['year'])
                results.append(album)

            # Search Artists by Name
            artist_rows = self.conn.execute(
                "SELECT * FROM Artists WHERE name LIKE ? ORDER BY name COLLATE NOCASE",
                (search_term,)
            ).fetchall()
            for r in artist_rows:
                artist = Artist(r['artist_id'], r['name'], r['rating'], r['artwork_id'])
                results.append(artist)

            # Search Playlists by Name
            playlist_rows = self.conn.execute(
                "SELECT * FROM Playlists WHERE name LIKE ? ORDER BY name COLLATE NOCASE",
                (search_term,)
            ).fetchall()
            for r in playlist_rows:
                playlist = Playlist(r['playlist_id'], r['name'], r['description'], r['artwork_id'])
                results.append(playlist)
                
        # Sort results by 'name' attribute (case-insensitive)
        return sorted(results, key=lambda x: getattr(x, 'name', '').lower())