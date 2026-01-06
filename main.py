import sys
import webbrowser
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QStackedWidget, QMessageBox)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, QTimer, Qt

from api.ibroadcast_api import iBroadcastAPI

from ui.search_header import SearchHeader
from ui.sidebar_navigation import SidebarNavigation
from ui.library_grid import LibraryGrid
from ui.player_controls import PlayerControls
from ui.artist_header import ArtistHeader
from ui.album_detail_view import AlbumDetailView
from ui.playlist_detail_view import PlaylistDetailView
from ui.queue_sidebar import QueueSidebar
from ui.context_menus import TrackContextMenu
from api.play_queue_websocket import PlayQueueWebSocket

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
        self.repeat_mode = "off"
        
        self.current_album_id = None
        self.current_playlist_id = None
        
        self.play_queue_ws = None
        
        self.init_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        self.timer.start(1000)
        
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
        
        self.check_auth()

    def init_ui(self):
        self.setWindowTitle("iBroadcast Native")
        self.resize(1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.search_header = SearchHeader()
        self.search_header.searchTextChanged.connect(self.handle_search)
        main_layout.addWidget(self.search_header)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(0)
        body_layout.setContentsMargins(0, 0, 0, 0)
        
        self.sidebar = SidebarNavigation()
        self.sidebar.viewChanged.connect(self.switch_view)
        body_layout.addWidget(self.sidebar)
        
        self.content_container = QWidget()
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        self.artist_header = ArtistHeader()
        self.artist_header.setVisible(False)
        content_layout.addWidget(self.artist_header)
        
        self.content_stack = QStackedWidget()
        self.home_view = LibraryGrid(self.show_album_detail)
        self.artists_view = LibraryGrid(self.show_artist_albums)
        self.albums_view = LibraryGrid(self.show_album_detail)
        self.playlists_view = LibraryGrid(self.show_playlist_detail)
        self.album_detail_view = AlbumDetailView()
        self.album_detail_view.playTrackRequested.connect(self.play_track_from_album)
        self.playlist_detail_view = PlaylistDetailView()
        self.playlist_detail_view.playTrackRequested.connect(self.play_track_from_playlist)

        self.content_stack.addWidget(self.home_view)
        self.content_stack.addWidget(self.artists_view)
        self.content_stack.addWidget(self.albums_view)
        self.content_stack.addWidget(self.playlists_view)
        self.content_stack.addWidget(self.album_detail_view)
        self.content_stack.addWidget(self.playlist_detail_view)

        content_layout.addWidget(self.content_stack)
        
        self.album_detail_view.album_track_list.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.album_detail_view.album_track_list.table.customContextMenuRequested.connect(
            self.show_track_context_menu_album
        )
        
        self.playlist_detail_view.track_list.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlist_detail_view.track_list.table.customContextMenuRequested.connect(
            self.show_track_context_menu_playlist
        )
        
        body_layout.addWidget(self.content_container)
        
        self.queue_sidebar = QueueSidebar()
        self.queue_sidebar.playTrackRequested.connect(self.play_track_from_queue)
        self.queue_sidebar.removeTrackRequested.connect(self.remove_from_queue)
        self.queue_sidebar.clearQueueRequested.connect(self.clear_queue)
        self.queue_sidebar.reorderRequested.connect(self.reorder_queue)
        body_layout.addWidget(self.queue_sidebar)
        
        main_layout.addLayout(body_layout)

        self.controls = PlayerControls()
        main_layout.addWidget(self.controls)
        
        self.controls.play_btn.clicked.connect(self.toggle_play)
        self.controls.next_btn.clicked.connect(self.play_next)
        self.controls.prev_btn.clicked.connect(self.play_previous)
        self.controls.volume_slider.valueChanged.connect(self.set_volume)
        self.controls.shuffle_btn.clicked.connect(self.toggle_shuffle)
        self.controls.repeat_btn.clicked.connect(self.toggle_repeat)
        self.controls.progress.sliderPressed.connect(self.on_seek_start)
        self.controls.progress.sliderReleased.connect(self.on_seek_end)

    def show_track_context_menu_album(self, pos):
        table = self.album_detail_view.album_track_list.table
        row = table.rowAt(pos.y())
        if row < 0:
            return
        
        menu = TrackContextMenu(self)
        menu.play_action.triggered.connect(lambda: self.play_track_from_album_at_row(row))
        menu.add_next_action.triggered.connect(lambda: self.add_track_to_queue_from_album(row, after_current=True))
        menu.add_end_action.triggered.connect(lambda: self.add_track_to_queue_from_album(row, after_current=False))
        
        viewport = table.viewport()
        if viewport:
            menu.exec(viewport.mapToGlobal(pos))
    
    def show_track_context_menu_playlist(self, pos):
        table = self.playlist_detail_view.track_list.table
        row = table.rowAt(pos.y())
        if row < 0:
            return
        
        menu = TrackContextMenu(self)
        menu.play_action.triggered.connect(lambda: self.play_track_from_playlist_at_row(row))
        menu.add_next_action.triggered.connect(lambda: self.add_track_to_queue_from_playlist(row, after_current=True))
        menu.add_end_action.triggered.connect(lambda: self.add_track_to_queue_from_playlist(row, after_current=False))
        
        viewport = table.viewport()
        if viewport:
            menu.exec(viewport.mapToGlobal(pos))
    
    def handle_search(self, text):
        if len(text) < 2: 
            if self.sidebar.currentRow() == 0:
                self.load_home()
            return

        self.home_view.clear()
        self.artist_header.setVisible(False)
        self.sidebar.setCurrentRow(0)
        
        results = []
        query = text.lower()

        for aid, artist in self.api.library['artists'].items():
            if query in str(artist.get('name', '')).lower():
                results.append((artist.get('name'), "Artist", artist.get('artwork_id'), aid))

        for aid, album in self.api.library['albums'].items():
            if query in str(album.get('name', '')).lower():
                results.append((album.get('name'), "Album", album.get('artwork_id'), aid))

        for tid, track in self.api.library['tracks'].items():
            if query in str(track.get('title', '')).lower():
                results.append((track.get('title'), "Song", track.get('artwork_id') or '', tid))

        for i, res in enumerate(results[:50]):
            artwork = self.api.get_artwork_url(res[2])
            self.home_view.add_item(res[0], res[1], artwork, res[3])

    def check_auth(self):
        if self.api.access_token:
            res = self.api.load_library()
            if res.get('success'):
                self.load_home()
                self.connect_play_queue()
        else:
            self.controls.track_info.setText("Login Required...")
            auth_res = self.api.start_oauth_flow()
            if 'auth_url' in auth_res:
                webbrowser.open(auth_res['auth_url'])
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
                    self.connect_play_queue()
                else:
                    self.controls.track_info.setText("Failed to load library after login.")
            else:
                self.controls.track_info.setText(f"Login failed: {token_res.get('message', 'Unknown error')}")
        elif not status.get('pending', False):
            self.oauth_poll_timer.stop()
            self.controls.track_info.setText(f"Login failed: {status.get('message', 'Unknown error')}")

    def switch_view(self, index):
        self.content_stack.setCurrentIndex(index)
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
        albums = list(self.api.library['albums'].items())[:50]
        for i, (aid, album) in enumerate(albums):
            artwork = self.api.get_artwork_url(album.get('artwork_id'))
            self.home_view.add_item(album.get('name'), "Album", artwork, aid)

    def load_artists(self):
        self.artists_view.clear()
        artists = sorted(self.api.library['artists'].values(), key=lambda x: str(x.get('name', '')).lower())
        for artist in artists:
            artwork = self.api.get_artwork_url(artist.get('artwork_id'))
            self.artists_view.add_item(artist.get('name', 'Unknown'), "Artist", artwork, artist.get('item_id'))

    def load_albums(self, artist_id=None):
        self.albums_view.clear()
        albums = self.api.library['albums'].values()
        if artist_id:
            albums = [a for a in albums if str(a.get('artist_id')) == str(artist_id)]
        albums_list = list(albums)
        for album in albums_list:
            artwork = self.api.get_artwork_url(album.get('artwork_id'))
            self.albums_view.add_item(album.get('name'), "Album", artwork, album.get('item_id'))

    def show_album_detail(self, album_id):
        album_id = int(album_id)
        self.current_album_id = album_id
        self.current_playlist_id = None
        
        album = self.api.library['albums'].get(str(album_id)) or self.api.library['albums'].get(album_id)
        if not album:
            print("Album not found:", album_id, type(album_id))
            return
        
        artist = self.api.library['artists'].get(album.get('artist_id'))
        artist_name = artist.get('name', 'Unknown Artist') if artist else 'Unknown Artist'
        year = album.get('year', '') or album.get('release_date', '')
        artwork_url = self.api.get_artwork_url(album.get('artwork_id'))
        
        self.album_detail_view.set_album(album.get('name', 'Unknown Album'), artist_name, year, artwork_url)

        tracks = [t for t in self.api.library['tracks'].values() if str(t.get('album_id')) == str(album.get('item_id'))]
        tracks.sort(key=lambda x: x.get('track', 0))
        self.album_detail_view.set_tracks(tracks)
        
        self._current_album_tracks = [t.get('item_id') for t in tracks]
        self.content_stack.setCurrentWidget(self.album_detail_view)
        self.artist_header.setVisible(False)
    
    def show_playlist_detail(self, playlist_id):
        self.current_playlist_id = playlist_id
        self.current_album_id = None
        
        playlist = self.api.library['playlists'].get(str(playlist_id)) or self.api.library['playlists'].get(playlist_id)
        if not playlist:
            return
        
        track_ids = playlist.get('tracks', [])
        
        artwork_url = ""
        if track_ids:
            first_track = self.api.library['tracks'].get(str(track_ids[0]))
            if first_track and first_track.get('artwork_id'):
                artwork_url = self.api.get_artwork_url(first_track['artwork_id'])
        
        self.playlist_detail_view.set_playlist(
            playlist.get('name', 'Untitled Playlist'),
            len(track_ids),
            artwork_url
        )
        
        tracks = []
        for track_id in track_ids:
            track = self.api.library['tracks'].get(str(track_id))
            if track:
                tracks.append(track)
        
        self.playlist_detail_view.set_tracks(tracks)
        
        self._current_playlist_tracks = track_ids
        self.content_stack.setCurrentWidget(self.playlist_detail_view)

    def load_playlists(self):
        self.playlists_view.clear()
        playlists = self.api.library.get('playlists', {})
        
        for pid, pl in playlists.items():
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
                pid
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
            self.artist_header.setVisible(True)
        else:
            self.artist_header.setVisible(False)

        self._showing_artist_albums = True
        self.sidebar.setCurrentRow(2)
        self.load_albums(artist_id)

    def play_track_from_album(self, track_id):
        if not hasattr(self, '_current_album_tracks'):
            return
        
        try:
            track_index = self._current_album_tracks.index(track_id)
            tracks_to_queue = self._current_album_tracks[track_index:]
            
            self.current_queue = tracks_to_queue
            self.current_index = 0
            
            if self.play_queue_ws:
                self.play_queue_ws.set_queue(tracks_to_queue, play_index=0)
            else:
                # If WebSocket not connected, manually update queue display
                self.update_queue_display()
            
            self.play_track_by_id(track_id)
        except ValueError:
            pass
    
    def play_track_from_album_at_row(self, row):
        if not hasattr(self, '_current_album_tracks') or row >= len(self._current_album_tracks):
            return
        
        tracks_to_queue = self._current_album_tracks[row:]
        self.current_queue = tracks_to_queue
        self.current_index = 0
        
        if self.play_queue_ws:
            self.play_queue_ws.set_queue(tracks_to_queue, play_index=0)
        else:
            self.update_queue_display()
        
        self.play_track_by_id(self._current_album_tracks[row])
    
    def add_track_to_queue_from_album(self, row, after_current=False):
        if not hasattr(self, '_current_album_tracks') or row >= len(self._current_album_tracks):
            return
        
        track_id = self._current_album_tracks[row]
        
        if after_current and self.play_queue_ws:
            self.play_queue_ws.add_to_play_next([track_id])
        elif self.play_queue_ws:
            new_tracks = self.current_queue + [track_id]
            self.play_queue_ws.update_state({'tracks': new_tracks})
    
    def play_track_from_playlist(self, track_id):
        if not hasattr(self, '_current_playlist_tracks'):
            return
        
        try:
            track_index = self._current_playlist_tracks.index(track_id)
            tracks_to_queue = self._current_playlist_tracks[track_index:]
            
            self.current_queue = tracks_to_queue
            self.current_index = 0
            
            if self.play_queue_ws:
                self.play_queue_ws.set_queue(tracks_to_queue, play_index=0)
            else:
                self.update_queue_display()
            
            self.play_track_by_id(track_id)
        except ValueError:
            pass
    
    def play_track_from_playlist_at_row(self, row):
        if not hasattr(self, '_current_playlist_tracks') or row >= len(self._current_playlist_tracks):
            return
        
        tracks_to_queue = self._current_playlist_tracks[row:]
        self.current_queue = tracks_to_queue
        self.current_index = 0
        
        if self.play_queue_ws:
            self.play_queue_ws.set_queue(tracks_to_queue, play_index=0)
        else:
            self.update_queue_display()
        
        self.play_track_by_id(self._current_playlist_tracks[row])
    
    def add_track_to_queue_from_playlist(self, row, after_current=False):
        if not hasattr(self, '_current_playlist_tracks') or row >= len(self._current_playlist_tracks):
            return
        
        track_id = self._current_playlist_tracks[row]
        
        if after_current and self.play_queue_ws:
            self.play_queue_ws.add_to_play_next([track_id])
        elif self.play_queue_ws:
            new_tracks = self.current_queue + [track_id]
            self.play_queue_ws.update_state({'tracks': new_tracks})

    def play_track_by_id(self, track_id):
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
            self.media_player.setSource(QUrl(url))
            self.media_player.play()
            
            track_name = track.get('title', 'Unknown Track')
            artist_name = artist.get('name', 'Unknown Artist') if artist else 'Unknown Artist'
            artwork_url = self.api.get_artwork_url(track.get('artwork_id'))
            
            self.controls.set_track_info(track_name, artist_name, artwork_url)
            self.controls.set_playing(True)
            
            if self.play_queue_ws:
                self.play_queue_ws.set_current_track(track_id, track_name)

    def toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.controls.set_playing(False)
            if self.play_queue_ws:
                self.play_queue_ws.set_pause(True)
        else:
            self.media_player.play()
            self.controls.set_playing(True)
            if self.play_queue_ws:
                self.play_queue_ws.set_pause(False)

    def play_next(self):
        if not self.current_queue:
            return
            
        if self.repeat_mode == "one":
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
        
        if not self.play_queue_ws:
            self.update_queue_display()
        
        self.play_track_by_id(self.current_queue[self.current_index])

    def play_previous(self):
        if not self.current_queue:
            return
        
        if self.media_player.position() > 3000:
            self.media_player.setPosition(0)
            return
        
        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = len(self.current_queue) - 1 if self.repeat_mode == "all" else 0
        
        if not self.play_queue_ws:
            self.update_queue_display()
        
        self.play_track_by_id(self.current_queue[self.current_index])

    def toggle_shuffle(self):
        self.shuffle_enabled = not self.shuffle_enabled
        self.controls.set_shuffle(self.shuffle_enabled)
        if self.play_queue_ws:
            self.play_queue_ws.set_shuffle(self.shuffle_enabled)

    def toggle_repeat(self):
        modes = ["off", "all", "one"]
        current_idx = modes.index(self.repeat_mode)
        self.repeat_mode = modes[(current_idx + 1) % len(modes)]
        self.controls.set_repeat(self.repeat_mode)
        
        if self.play_queue_ws:
            repeat_map = {'off': 'none', 'all': 'queue', 'one': 'track'}
            self.play_queue_ws.set_repeat_mode(repeat_map[self.repeat_mode])

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
            
            current = self.media_player.position() // 1000
            total = self.media_player.duration() // 1000
            self.controls.update_time_labels(current, total)

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.play_next()
    
    def connect_play_queue(self):
        token = self.api.access_token
        if token is not None:
            self.play_queue_ws = PlayQueueWebSocket(
                token, on_state_update=self.on_queue_state_update
            )
            self.play_queue_ws.connect()
    
    def on_queue_state_update(self, state, role):
        print("Received queue state update:", state)
        self.current_queue = state.get('play_next', []) + state.get('tracks', [])
        
        tracks_data = []
        for track_id in state.get('tracks', []):
            track = self.api.library['tracks'].get(track_id)
            if track:
                artist = self.api.library['artists'].get(track.get('artist_id'))
                tracks_data.append({
                    'title': track.get('title', 'Unknown'),
                    'artist': artist.get('name', 'Unknown Artist') if artist else 'Unknown Artist',
                    'track_id': track_id
                })
        
        play_next_data = []
        for track_id in state.get('play_next', []):
            track = self.api.library['tracks'].get(track_id)
            if track:
                artist = self.api.library['artists'].get(track.get('artist_id'))
                play_next_data.append({
                    'title': track.get('title', 'Unknown'),
                    'artist': artist.get('name', 'Unknown Artist') if artist else 'Unknown Artist',
                    'track_id': track_id
                })
        
        play_index = state.get('data', {}).get('play_index', 0)
        play_from = state.get('data', {}).get('play_from', 'tracks')
        self.queue_sidebar.set_queue(tracks_data, play_next_data, play_index, play_from)
        
        repeat_mode = state.get('data', {}).get('repeat_mode', 'none')
        if repeat_mode == 'none':
            self.repeat_mode = 'off'
        elif repeat_mode == 'queue':
            self.repeat_mode = 'all'
        elif repeat_mode == 'track':
            self.repeat_mode = 'one'
        self.controls.set_repeat(self.repeat_mode)
        
        self.shuffle_enabled = state.get('shuffle', False)
        self.controls.set_shuffle(self.shuffle_enabled)
        
        if role == 'controller':
            print("This client is a controller")
    
    def play_track_from_queue(self, index):
        play_next_count = len(self.queue_sidebar.play_next_data)
        
        if index < play_next_count:
            track_id = self.queue_sidebar.play_next_data[index]['track_id']
            if self.play_queue_ws:
                new_play_next = self.play_queue_ws.state['play_next'][index:]
                self.play_queue_ws.update_state({'play_next': new_play_next})
        else:
            tracks_index = index - play_next_count
            track_id = self.queue_sidebar.tracks_data[tracks_index]['track_id']
            if self.play_queue_ws:
                self.play_queue_ws.update_state({
                    'data': {
                        **self.play_queue_ws.state['data'],
                        'play_index': tracks_index,
                        'play_from': 'tracks'
                    }
                })
        
        self.play_track_by_id(track_id)
    
    def remove_from_queue(self, index, is_play_next):
        if self.play_queue_ws:
            self.play_queue_ws.remove_from_queue(index, is_play_next)
    
    def clear_queue(self):
        if self.play_queue_ws:
            self.play_queue_ws.clear_queue()
        self.media_player.stop()
        self.controls.set_playing(False)
    
    def update_queue_display(self):
        """Manually update queue display when WebSocket is not connected"""
        print("Updating queue display manually")
        if not self.current_queue:
            print("Current queue is empty")
            self.queue_sidebar.set_queue([], [], 0, 'tracks')
            return
        
        tracks_data = []
        for track_id in self.current_queue:
            track = self.api.library['tracks'].get(str(track_id))
            if track:
                artist = self.api.library['artists'].get(track.get('artist_id'))
                tracks_data.append({
                    'title': track.get('title', 'Unknown'),
                    'artist': artist.get('name', 'Unknown Artist') if artist else 'Unknown Artist',
                    'track_id': track_id
                })
        print("Prepared", len(tracks_data), "tracks for queue display")
        self.queue_sidebar.set_queue(tracks_data, [], self.current_index, 'tracks')
    
    def reorder_queue(self, old_index, new_index):
        if self.play_queue_ws:
            tracks = self.play_queue_ws.state['tracks'].copy()
            track = tracks.pop(old_index)
            tracks.insert(new_index, track)
            self.play_queue_ws.update_state({'tracks': tracks})

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = iBroadcastNative()
    window.show()
    sys.exit(app.exec())