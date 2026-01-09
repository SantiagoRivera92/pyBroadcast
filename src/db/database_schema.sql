PRAGMA foreign_keys = ON;

CREATE TABLE Artists (
    artist_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    rating INTEGER,
    artwork_id INTEGER
);

CREATE TABLE Albums (
    album_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    rating INTEGER,
    disc INTEGER,
    year INTEGER
);

CREATE TABLE Tracks (
    track_id INTEGER PRIMARY KEY,
    album_id INTEGER NOT NULL,
    track_number INTEGER,
    year INTEGER,
    title TEXT NOT NULL,
    length INTEGER,
    artwork_id INTEGER,
    rating INTEGER,
    plays INTEGER,
    file TEXT,
    FOREIGN KEY (album_id) REFERENCES Albums(album_id) ON DELETE CASCADE
);

CREATE TABLE Playlists (
    playlist_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    artwork_id INTEGER
);

CREATE TABLE Track_Artists (
    ta_id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER,
    artist_id INTEGER,
    FOREIGN KEY (track_id) REFERENCES Tracks(track_id) ON DELETE CASCADE,
    FOREIGN KEY (artist_id) REFERENCES Artists(artist_id) ON DELETE CASCADE,
    UNIQUE(track_id, artist_id)
);

CREATE TABLE Album_Artists (
    aa_id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_id INTEGER,
    artist_id INTEGER,
    FOREIGN KEY (album_id) REFERENCES Albums(album_id) ON DELETE CASCADE,
    FOREIGN KEY (artist_id) REFERENCES Artists(artist_id) ON DELETE CASCADE,
    UNIQUE(album_id, artist_id)
);

CREATE TABLE Playlist_Tracks (
    pt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id INTEGER,
    track_id INTEGER,
    position INTEGER,
    FOREIGN KEY (playlist_id) REFERENCES Playlists(playlist_id) ON DELETE CASCADE,
    FOREIGN KEY (track_id) REFERENCES Tracks(track_id) ON DELETE CASCADE
);