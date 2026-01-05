import sys
import webbrowser
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QListWidget, QStackedWidget, QFrame, QLineEdit, QLabel)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont

from api.ibroadcast_api import iBroadcastAPI

from ui.library_grid import LibraryGrid
from ui.player_controls import PlayerControls
from ui.artist_header import ArtistHeader

class iBroadcastNative(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api = iBroadcastAPI()
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self.current_queue = []
        self.current_index = 0
        self.shuffle_enabled = False
        self.repeat_mode = "off"  # "off", "all", "one"
        
        self.init_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        self.timer.start(1000)
        
        # Connect media player signals
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
        
        self.check_auth()

    def init_ui(self):
        self.setWindowTitle("iBroadcast Native")
        self.resize(1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Search Bar Header
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("background-color: #000000; border-bottom: 1px solid #282828;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tracks, artists, or albums...")
        self.search_input.setFixedWidth(450)
        self.search_input.setStyleSheet("""
            QLineEdit { 
                background-color: #242424; color: white; border-radius: 20px; 
                padding: 10px 20px; border: 1px solid transparent; font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #5DADE2; }
        """)
        self.search_input.textChanged.connect(self.handle_search)
        header_layout.addWidget(self.search_input)
        header_layout.addStretch()
        self.main_layout.addWidget(header)

        # Body
        top_layout = QHBoxLayout()
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(250)
        self.sidebar.addItems(["Home", "Artists", "Albums", "Playlists"])
        
        # Enhanced sidebar styling with larger text
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: #000000; 
                color: #b3b3b3; 
                border: none; 
                outline: none;
                font-size: 16px;
                font-weight: 600;
                padding: 10px;
            }
            QListWidget::item {
                padding: 15px 20px;
                border-radius: 6px;
                margin: 2px 0px;
            }
            QListWidget::item:hover {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #282828;
                color: #5DADE2;
            }
        """)
        self.sidebar.currentRowChanged.connect(self.switch_view)
        
        # Content area with artist header
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Artist header (hidden by default)
        self.artist_header = ArtistHeader()
        self.artist_header.setVisible(False)
        self.content_layout.addWidget(self.artist_header)
        
        # Stacked widget for different views
        from ui.album_header import AlbumHeader
        from ui.album_track_list import AlbumTrackList
        self.content_stack = QStackedWidget()
        self.home_view = LibraryGrid(self.show_album_detail)
        self.artists_view = LibraryGrid(self.show_artist_albums)
        self.albums_view = LibraryGrid(self.show_album_detail)
        self.playlists_view = LibraryGrid(self.play_playlist)

        # Album detail view (header + track list)
        self.album_detail_widget = QWidget()
        self.album_detail_layout = QVBoxLayout(self.album_detail_widget)
        self.album_detail_layout.setContentsMargins(0, 0, 0, 0)
        self.album_detail_layout.setSpacing(0)
        self.album_header = AlbumHeader()
        self.album_track_list = AlbumTrackList()
        self.album_track_list.playTrackRequested.connect(self.play_track_by_id)
        self.album_detail_layout.addWidget(self.album_header)
        self.album_detail_layout.addWidget(self.album_track_list)

        self.content_stack.addWidget(self.home_view)    # 0
        self.content_stack.addWidget(self.artists_view) # 1
        self.content_stack.addWidget(self.albums_view)  # 2
        self.content_stack.addWidget(self.playlists_view) # 3
        self.content_stack.addWidget(self.album_detail_widget) # 4

        self.content_layout.addWidget(self.content_stack)
        
        top_layout.addWidget(self.sidebar)
        top_layout.addWidget(self.content_container)
        self.main_layout.addLayout(top_layout)

        # Enhanced player controls
        self.controls = PlayerControls()
        self.main_layout.addWidget(self.controls)
        self.controls.play_btn.clicked.connect(self.toggle_play)
        self.controls.next_btn.clicked.connect(self.play_next)
        self.controls.prev_btn.clicked.connect(self.play_previous)
        self.controls.volume_slider.valueChanged.connect(self.set_volume)
        self.controls.shuffle_btn.clicked.connect(self.toggle_shuffle)
        self.controls.repeat_btn.clicked.connect(self.toggle_repeat)
        self.controls.progress.sliderPressed.connect(self.on_seek_start)
        self.controls.progress.sliderReleased.connect(self.on_seek_end)

    def handle_search(self, text):
        if len(text) < 2: 
            if self.sidebar.currentRow() == 0: self.load_home()
            return

        self.home_view.clear()
        self.artist_header.setVisible(False)
        self.sidebar.setCurrentRow(0)
        
        results = []
        query = text.lower()

        # Search artists
        for aid, artist in self.api.library['artists'].items():
            if query in str(artist.get('name', '')).lower():
                results.append((artist.get('name'), "Artist", artist.get('artwork_id'), aid))

        # Search albums
        for aid, album in self.api.library['albums'].items():
            if query in str(album.get('name', '')).lower():
                results.append((album.get('name'), "Album", album.get('artwork_id'), aid))

        # Search tracks (songs)
        for tid, track in self.api.library['tracks'].items():
            if query in str(track.get('title', '')).lower():
                results.append((track.get('title'), "Song", track.get('artwork_id') or '', tid))

        for i, res in enumerate(results[:30]):
            artwork = self.api.get_artwork_url(res[2])
            self.home_view.add_item(res[0], res[1], artwork, res[3], i // 5, i % 5)

    def check_auth(self):
        if self.api.access_token:
            res = self.api.load_library()
            if res.get('success'):
                self.load_home()
        else:
            self.controls.track_info.setText("Login Required...")
            auth_res = self.api.start_oauth_flow()
            if 'auth_url' in auth_res:
                webbrowser.open(auth_res['auth_url'])
                # Start polling for OAuth callback
                self.oauth_poll_timer = QTimer()
                self.oauth_poll_timer.setInterval(1000)
                self.oauth_poll_timer.timeout.connect(self.poll_oauth_callback)
                self.oauth_poll_timer.start()

    def poll_oauth_callback(self):
        status = self.api.check_callback_status()
        if status.get('success') and 'code' in status:
            self.oauth_poll_timer.stop()
            token_res = self.api.exchange_code_for_token(status['code'])
            if token_res.get('success'):
                lib_res = self.api.load_library()
                if lib_res.get('success'):
                    self.load_home()
                    self.controls.track_info.setText("")
                else:
                    self.controls.track_info.setText("Failed to load library after login.")
            else:
                self.controls.track_info.setText(f"Login failed: {token_res.get('message', 'Unknown error')}")
        elif not status.get('pending', False):
            self.oauth_poll_timer.stop()
            self.controls.track_info.setText(f"Login failed: {status.get('message', 'Unknown error')}")

    def switch_view(self, index):
        self.content_stack.setCurrentIndex(index)
        # Only hide artist header if not switching to albums for a specific artist
        if not (index == 2 and hasattr(self, '_showing_artist_albums') and self._showing_artist_albums):
            self.artist_header.setVisible(False)
        self._showing_artist_albums = False

        if index == 0:
            self.load_home()
        elif index == 1:
            self.load_artists()
        elif index == 2:
            self.load_albums()
        elif index == 3:
            self.load_playlists()

    def load_home(self):
        self.home_view.clear()
        albums = list(self.api.library['albums'].items())[:30]
        for i, (aid, album) in enumerate(albums):
            artwork = self.api.get_artwork_url(album.get('artwork_id'))
            self.home_view.add_item(album.get('name'), "Album", artwork, aid, i // 5, i % 5)

    def load_artists(self):
        self.artists_view.clear()
        artists = sorted(self.api.library['artists'].values(), key=lambda x: str(x.get('name', '')).lower())
        for i, artist in enumerate(artists):
            artwork = self.api.get_artwork_url(artist.get('artwork_id'))
            self.artists_view.add_item(artist.get('name', 'Unknown'), "Artist", artwork, artist.get('item_id'), i // 5, i % 5)

    def load_albums(self, artist_id=None):
        self.albums_view.clear()
        albums = self.api.library['albums'].values()
        if artist_id:
            albums = [a for a in albums if str(a.get('artist_id')) == str(artist_id)]
        albums_list = list(albums)
        for i, album in enumerate(albums_list):
            artwork = self.api.get_artwork_url(album.get('artwork_id'))
            self.albums_view.add_item(album.get('name'), "Album", artwork, album.get('item_id'), i // 5, i % 5)

    def show_album_detail(self, album_id):
        album = self.api.library['albums'].get(str(album_id)) or self.api.library['albums'].get(album_id)
        if not album:
            return
        artist = self.api.library['artists'].get(album.get('artist_id'))
        artist_name = artist.get('name', 'Unknown Artist') if artist else 'Unknown Artist'
        year = album.get('year', '') or album.get('release_date', '')
        artwork_url = self.api.get_artwork_url(album.get('artwork_id'))
        self.album_header.set_album(album.get('name', 'Unknown Album'), artist_name, year, artwork_url)

        # Get tracks for this album
        tracks = [t for t in self.api.library['tracks'].values() if str(t.get('album_id')) == str(album.get('item_id'))]
        tracks.sort(key=lambda x: x.get('track', 0))
        self.album_track_list.set_tracks(tracks)

        self.content_stack.setCurrentWidget(self.album_detail_widget)

    def load_playlists(self):
        self.playlists_view.clear()
        playlists = self.api.library.get('playlists', {})
        
        for i, (pid, pl) in enumerate(playlists.items()):
            # Get artwork from first track in playlist
            artwork_url = ""
            tracks = pl.get('tracks', [])
            if tracks:
                first_track_id = tracks[0]
                first_track = self.api.library['tracks'].get(str(first_track_id))
                if first_track and first_track.get('artwork_id'):
                    artwork_url = self.api.get_artwork_url(first_track['artwork_id'])
            
            self.playlists_view.add_item(
                pl.get('name', 'Untitled Playlist'), 
                f"{len(tracks)} tracks", 
                artwork_url, 
                pid, 
                i // 5, i % 5
            )

    def show_artist_albums(self, artist_id):
        artist = None
        for a in self.api.library['artists'].values():
            if str(a.get('item_id')) == str(artist_id):
                artist = a
                break

        if artist:
            self.artist_header.set_artist(
                artist.get('name', 'Unknown Artist'),
                self.api.get_artwork_url(artist.get('artwork_id'))
            )
            print("Showing albums for artist:", artist.get('name'))
            self.artist_header.setVisible(True)
        else:
            print("Artist not found")
            self.artist_header.setVisible(False)

        self._showing_artist_albums = True
        self.sidebar.setCurrentRow(2)
        self.load_albums(artist_id)

    def play_playlist(self, playlist_id):
        pl = self.api.library['playlists'].get(playlist_id)
        if pl and pl.get('tracks'):
            track_ids = pl['tracks']
            self.current_queue = track_ids
            self.current_index = 0
            self.play_track_by_id(track_ids[0])

    def play_album(self, album_id):
        # For compatibility, just show album detail
        self.show_album_detail(album_id)

    def play_track_by_id(self, track_id):
        print("Playing track ID:", track_id)
        track = None
        artist = None
        for tr in self.api.library['tracks'].values():
            if str(tr.get('item_id')) == str(track_id):
                track = tr
                break
        if track:
            for ar in self.api.library['artists'].values():
                if str(ar.get('item_id')) == str(track.get('artist_id')):
                    artist = ar
                    break

        if track:
            url = self.api.get_stream_url(track_id)
            print(url)
            self.media_player.setSource(QUrl(url))
            self.media_player.play()
            
            track_name = track.get('title', 'Unknown Track')

            artist_name = artist.get('name', 'Unknown Artist') if artist else 'Unknown Artist'
            artwork_url = self.api.get_artwork_url(track.get('artwork_id'))
            
            self.controls.set_track_info(track_name, artist_name, artwork_url)
            self.controls.set_playing(True)

    def toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.controls.set_playing(False)
        else:
            self.media_player.play()
            self.controls.set_playing(True)

    def play_next(self):
        if not self.current_queue:
            return
            
        if self.repeat_mode == "one":
            # Replay current track
            self.media_player.setPosition(0)
            self.media_player.play()
            return
        
        self.current_index += 1
        
        if self.current_index >= len(self.current_queue):
            if self.repeat_mode == "all":
                self.current_index = 0
            else:
                self.media_player.stop()
                self.controls.set_playing(False)
                return
        
        self.play_track_by_id(self.current_queue[self.current_index])

    def play_previous(self):
        if not self.current_queue:
            return
        
        # If more than 3 seconds into track, restart it
        if self.media_player.position() > 3000:
            self.media_player.setPosition(0)
            return
        
        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = len(self.current_queue) - 1 if self.repeat_mode == "all" else 0
        
        self.play_track_by_id(self.current_queue[self.current_index])

    def toggle_shuffle(self):
        self.shuffle_enabled = not self.shuffle_enabled
        self.controls.set_shuffle(self.shuffle_enabled)
        # TODO: Implement shuffle logic for queue

    def toggle_repeat(self):
        modes = ["off", "all", "one"]
        current_idx = modes.index(self.repeat_mode)
        self.repeat_mode = modes[(current_idx + 1) % len(modes)]
        self.controls.set_repeat(self.repeat_mode)

    def set_volume(self, value):
        self.audio_output.setVolume(value / 100)

    def on_seek_start(self):
        self.timer.stop()

    def on_seek_end(self):
        if self.media_player.duration() > 0:
            position = (self.controls.progress.value() / 100) * self.media_player.duration()
            self.media_player.setPosition(int(position))
        self.timer.start(1000)

    def update_position(self):
        if self.media_player.duration() > 0:
            pos = (self.media_player.position() / self.media_player.duration()) * 100
            self.controls.progress.setValue(int(pos))
            
            # Update time labels
            current = self.media_player.position() // 1000
            total = self.media_player.duration() // 1000
            self.controls.update_time_labels(current, total)

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.play_next()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = iBroadcastNative()
    window.show()
    sys.exit(app.exec())