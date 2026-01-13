import sys
import webbrowser
import os
import time

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QStackedWidget, QPushButton)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtGui import QAction, QIcon,QFontDatabase, QFont

from src.api.ibroadcast.models import Artist, Album, Track, Playlist
from src.api.ibroadcast.ibroadcast_api import iBroadcastAPI
from src.api.ibroadcast.play_queue_socket import PlayQueueSocket

from src.ui.search.search_header import SearchHeader
from src.ui.navigation.sidebar_navigation import SidebarNavigation
from src.ui.grid.library_grid import LibraryGrid
from src.ui.player.player_controls import PlayerControls
from src.ui.artist.artist_header import ArtistHeader
from src.ui.album.album_detail_view import AlbumDetailView
from src.ui.playlist.playlist_detail_view import PlaylistDetailView
from src.ui.queue.queue_sidebar import QueueSidebar
from src.ui.utils.context_menus import TrackContextMenu
from src.ui.utils.options_dialog import OptionsDialog
from src.ui.login.login_screen import LoginScreen
from src.core.mpris_manager import MPRISManager

from src.core.credentials_manager import CredentialsManager

class iBroadcastNative(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.api = iBroadcastAPI()
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self.tracks = []
        self.play_next_queue = []
        self.play_index = 0
        self.play_from = "tracks"
        
        self.current_track_id = None
        self.shuffle_enabled = False
        self.repeat_mode = "none" # "none", "queue", or "track"
        
        self.current_album_id = None
        self.current_playlist_id = None
        
        self.track_duration = 0
        self.current_track_info = {}
        
        self.init_navigation_stack()
        self.init_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        self.timer.start(100) # 100ms for smooth UI updates
        self.is_seeking = False
        
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)  # NEW
        
        # Play Queue Socket
        self.socket = PlayQueueSocket()
        self.socket.stateUpdated.connect(self.on_server_state_updated)
        self.socket.libraryUpdateRequested.connect(self.on_library_update_requested)
        # self.socket.sessionEnded.connect(self.logout) # Implement logout if needed

        self.last_server_state = {}
        self.last_sync_time = 0
        self.pending_seek_ms = 0
        self.role = "player" # Default to player until told otherwise

        # MPRIS Manager for Linux
        self.mpris = MPRISManager(self)
        self.mpris.start()

        self.check_auth()
    
    def connect_to_queue(self):
        """Fetch token and connect to Play Queue Server"""
        result = self.api.get_play_queue_token()
        if result:
            token = result.get('token')
            session_uuid = result.get('session_uuid')
            self.socket.connect_to_server(token, session_uuid)

    def on_library_update_requested(self, last_modified):
        self.api.load_library()
        self.load_artists()

    def on_server_state_updated(self, state):
        self.last_server_state = state
        self.role = state.get("role", "player")
        
        # 1. Update Internal State
        if "tracks" in state:
            self.tracks = state["tracks"]
        if "play_next" in state:
            self.play_next_queue = state["play_next"]
        
        data = state.get("data", {})
        if "play_from" in data:
            self.play_from = data["play_from"]
        if "play_index" in data:
            self.play_index = data["play_index"]
        if "repeat_mode" in data:
            self.repeat_mode = data["repeat_mode"]
        if "shuffle" in state:
            self.shuffle_enabled = state["shuffle"]
        
        self.update_queue_display()
        
        # 2. Playback State
        current_song_id = state.get("current_song")
        is_paused = state.get("pause", False)
        
        # Determine if we should be playing music
        if self.role == "player":
            # Position Sync (only if not seeking locally)
            if not self.is_seeking:
                start_time = state.get("start_time", 0)
                start_pos = state.get("start_position", 0)
                
                if current_song_id:
                    if is_paused:
                        target_pos_ms = int(start_pos * 1000)
                    else:
                        now = time.time()
                        target_pos_ms = int((now - (start_time - start_pos)) * 1000)
                    
                    if current_song_id != self.current_track_id:
                        self.play_track_by_id(current_song_id, from_server=True, start_playing=not is_paused, position_ms=target_pos_ms)
                    else:
                        diff = abs(self.media_player.position() - target_pos_ms)
                        if diff > 2000:
                            self.media_player.setPosition(max(0, target_pos_ms))
            
            # Pause/Play transition
            if is_paused:
                if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    self.media_player.pause()
            else:
                if self.media_player.playbackState() != QMediaPlayer.PlaybackState.PlayingState and current_song_id:
                    self.media_player.play()
        else:
            # We are a controller: Stop local playback if it was running
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.stop()
            
            # Still update the UI to show what's playing elsewhere
            if current_song_id and current_song_id != self.current_track_id:
                self._update_ui_for_track(current_song_id)

        # Update Controls UI
        self.controls.set_playing(not is_paused)
        self.controls.set_shuffle(self.shuffle_enabled)
        self.controls.set_repeat(self.repeat_mode)
        self.audio_output.setVolume(state.get("volume", self.audio_output.volume()))
        
        # Update MPRIS
        self.mpris.update_status("Paused" if is_paused else "Playing")
        self.mpris.update_volume(self.audio_output.volume())

        # Store last state for position prediction
        self.last_server_state = state

    def _update_ui_for_track(self, track_id):
        """Update Now Playing UI without starting playback (for controller role)."""
        track = self.api.get_track_by_id(track_id)
        if not track: return
        artists = self.api.get_artists_by_track(track_id)
        album = self.api.get_album_by_track(track_id)
        album_artists = self.api.get_artists_with_albums()
        self.current_track_id = track_id
        
        artist_name = artists[0].name if artists else 'Unknown Artist'
        self.current_track_info = {
            'artist': artist_name,
            'track': track.name,
            'album': album.name if album else None
        }
        self.track_duration = track.length
        artwork_url = self.api.get_artwork_url(track.artwork_id)
        self.controls.set_track_info(track, album, artists, album_artists, artwork_url)
        
        # Update MPRIS metadata
        self.mpris.update_metadata({
            'track_id': track_id,
            'title': track.name,
            'artist': artist_name,
            'album': album.name if album else '',
            'art_url': artwork_url,
            'length': float(track.length)
        })

    def push_state_to_server(self):
        """Construct state from local player and send to server."""
        if not self.socket.is_connected:
            return

        # iBroadcast logic: role "player" is responsible for advancing state.
        if self.role != "player":
            # Controllers usually don't push state unless they are explicitly changing something
            # (In iBroadcast model, commands like "skip" are sent as set_state by the source)
            # but here we follow: "Any time a play queue's state is updated by a client, 
            # the server will send a set_state command to all OTHER clients."
            pass

        is_paused = (self.media_player.playbackState() != QMediaPlayer.PlaybackState.PlayingState)
        
        # Values
        state = {
            "current_song": self.current_track_id if self.current_track_id else 0,
            "data": {
                "play_from": self.play_from,
                "play_index": self.play_index,
                "repeat_mode": self.repeat_mode,
                "crossfade": False
            },
            "name": self.current_track_info.get('track', ''),
            "pause": is_paused,
            "tracks": self.tracks,
            "play_next": self.play_next_queue,
            "shuffle": self.shuffle_enabled,
            "start_position": self.media_player.position() / 1000.0,
            "start_time": time.time(), 
            "volume": self.audio_output.volume()
        }
        
        self.socket.send_set_state(state)

    def init_navigation_stack(self):
        """Initialize the navigation stack and last search query."""
        self.navigation_stack = []
        self._last_search_query = None

    def push_page(self, page):
        """Push a page onto the navigation stack if it's not a duplicate of the current top."""
        if self.navigation_stack:
            top = self.navigation_stack[-1]
            # For search, only push if query is different and not empty
            if page['type'] == 'Search' and top['type'] == 'Search':
                if page.get('query') == top.get('query'):
                    return
            # For other types, only push if type/id differ
            elif page['type'] == top['type'] and page.get('id') == top.get('id'):
                return
        self.navigation_stack.append(page)

    def pop_page(self):
        """Pop the current page from the navigation stack and return the previous one, or None.
        Never pop the root navigation element (first Navigation type in stack)."""
        if len(self.navigation_stack) > 1:
            # Find the first navigation element (root)
            root_index = None
            for i, page in enumerate(self.navigation_stack):
                if page.get('type') == 'Navigation':
                    root_index = i
                    break
            # Only pop if we're not at the root
            if root_index is not None and len(self.navigation_stack) > root_index + 1:
                self.navigation_stack.pop()
                return self.navigation_stack[-1]
        # Never pop the root navigation element
        return self.navigation_stack[-1] if self.navigation_stack else None

    def go_back(self):
        """Navigate to the previous page in the stack, if any."""
        prev = self.pop_page()
        if prev:
            if prev['type'] == 'Artist':
                self.show_artist_albums(prev['id'])
            elif prev['type'] == 'Album':
                self.show_album_detail(prev['id'])
            elif prev['type'] == 'Navigation':
                self.switch_view(prev['id'])
            elif prev['type'] == 'Search':
                self.handle_search(prev['query'])
                
    def init_ui(self):
        self.setWindowTitle("pyBroadcast")
        
        self.create_menu_bar()
        
        # Root Stack for Login vs Main App
        self.root_stack = QStackedWidget()
        self.setCentralWidget(self.root_stack)
        
        # 1. Login Screen
        self.login_screen = LoginScreen()
        self.login_screen.loginRequested.connect(self.on_login_requested)
        self.root_stack.addWidget(self.login_screen)
        
        # 2. Main App Container
        self.main_app_widget = QWidget()
        self.setup_main_app_ui(self.main_app_widget)
        self.root_stack.addWidget(self.main_app_widget)
        
        # Default to login screen (hidden until check_auth decides)
        self.root_stack.setCurrentWidget(self.login_screen)

    def setup_main_app_ui(self, central_widget):
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add a horizontal layout for back button + search header
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(0)


        self.back_btn = QPushButton()
        self.back_btn.setIcon(QIcon.fromTheme("go-previous"))
        self.back_btn.setFixedSize(36, 36)
        self.back_btn.setToolTip("Back")
        self.back_btn.setStyleSheet('''
            QPushButton {
                border-radius: 18px;
                background: transparent;
                border: none;
                margin: 4px;
            }
            QPushButton:hover {
                background: #333333;
            }
        ''')
        self.back_btn.clicked.connect(self.go_back)
        top_bar_layout.addWidget(self.back_btn)

        self.search_header = SearchHeader()
        self.search_header.searchTextChanged.connect(self.handle_search)
        top_bar_layout.addWidget(self.search_header)

        main_layout.addLayout(top_bar_layout)

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
        self._showing_artist_albums = False
        self.artist_header.setVisible(self._showing_artist_albums)
        content_layout.addWidget(self.artist_header)
        
        self.content_stack = QStackedWidget()
        self.artists_view = LibraryGrid(self.show_artist_albums, self.api)
        self.albums_view = LibraryGrid(self.show_album_detail, self.api)
        self.playlists_view = LibraryGrid(self.show_playlist_detail, self.api)
        self.search_results_view = LibraryGrid(self.handle_search_result_click, self.api)
        self.album_detail_view = AlbumDetailView()
        self.album_detail_view.playTrackRequested.connect(self.play_track_from_album)
        self.album_detail_view.upButtonClicked.connect(self.show_artist_albums)
        self.playlist_detail_view = PlaylistDetailView()
        self.playlist_detail_view.playTrackRequested.connect(self.play_track_from_playlist)
        self.playlist_detail_view.upButtonClicked.connect(self.load_playlists)   

        self.content_stack.addWidget(self.artists_view)
        self.content_stack.addWidget(self.albums_view)
        self.content_stack.addWidget(self.playlists_view)
        self.content_stack.addWidget(self.album_detail_view)
        self.content_stack.addWidget(self.playlist_detail_view)
        self.content_stack.addWidget(self.search_results_view)

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
        self.controls.progress.valueChanged.connect(self.on_seek_progress)
        self.controls.albumClicked.connect(self.show_album_detail)
        self.controls.artistClicked.connect(self.show_artist_albums)

    def handle_search_result_click(self, item_id):
        # Try to find the item in artists, albums, or tracks
        if isinstance(item_id, Artist):
            self.show_artist_albums(item_id)
        elif isinstance(item_id, Album):
            self.show_album_detail(item_id)
        elif isinstance(item_id, Track):
            self.clear_queue()
            self.play_track_by_id(item_id)
        elif isinstance(item_id, Playlist):
            self.show_playlist_detail(item_id)

    def create_menu_bar(self):
        """Create the menu bar - NEW"""
        menubar = self.menuBar()
        
        # File menu
        if menubar is not None:
            file_menu = menubar.addMenu("&File")
            if file_menu is not None:
                options_action = QAction("&Options", self)
                options_action.setShortcut("Ctrl+,")
                options_action.triggered.connect(self.show_options)
                file_menu.addAction(options_action)
                
                file_menu.addSeparator()
                
                exit_action = QAction("E&xit", self)
                exit_action.setShortcut("Ctrl+Q")
                exit_action.triggered.connect(self.close)
                file_menu.addAction(exit_action)
    
    def show_options(self):
        """Show the options dialog - NEW"""
        dialog = OptionsDialog(self.api, self, on_close_callback=self.check_auth)
        dialog.exec()

    def show_track_context_menu_album(self, pos):
        table = self.album_detail_view.album_track_list.table
        row = table.rowAt(pos.y())
        if row < 0:
            return
        
        menu = TrackContextMenu(self, is_playlist=False)
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
        
        menu = TrackContextMenu(self, is_playlist=True)
        menu.play_action.triggered.connect(lambda: self.play_track_from_playlist_at_row(row))
        menu.add_next_action.triggered.connect(lambda: self.add_track_to_queue_from_playlist(row, after_current=True))
        menu.add_end_action.triggered.connect(lambda: self.add_track_to_queue_from_playlist(row, after_current=False))
        menu.go_to_album_action.triggered.connect(lambda: self._go_to_album_from_playlist_row(row))
        
        viewport = table.viewport()
        if viewport:
            menu.exec(viewport.mapToGlobal(pos))
            

    def _go_to_album_from_playlist_row(self, row):
        if not hasattr(self, '_current_playlist_tracks') or row >= len(self._current_playlist_tracks):
            return
        track_id = self._current_playlist_tracks[row]
        album = self.api.get_album_by_track(int(track_id))
        if album:
            self.show_album_detail(album.id)
    
    

    def handle_search(self, text):
        if len(text) < 3:
            # Pop the existing search page
            if self.navigation_stack and self.navigation_stack[-1].get('type') == 'Search':
                self.pop_page()
            return

        query = text.lower()
        # If the last page is a search, update its query; otherwise, push a new search page
        if self.navigation_stack and self.navigation_stack[-1].get('type') == 'Search':
            self.navigation_stack[-1]['query'] = query
        else:
            self.push_page({"type": "Search", "query": query})
        self._last_search_query = query

        self.artist_header.setVisible(False)

        results = self.api.search(text)

        self.search_results_view.clear()
        for result in results:
            artwork_id = 0
            if isinstance(result, Artist):
                artwork_id = result.artwork_id
            elif isinstance(result, Album):
                tracks = self.api.get_tracks_by_album(result.id)
                for track in tracks:
                    if track.artwork_id != 0:
                        artwork_id = track.artwork_id
                        break
            elif isinstance(result, Track):
                artwork_id = result.artwork_id
            elif isinstance(result, Playlist):
                artwork_id = result.artwork_id
            else:
                continue
            self.search_results_view.add_item(result, self.api.get_artwork_url(artwork_id))
        self.content_stack.setCurrentWidget(self.search_results_view)

    def check_auth(self):
        """Check if iBroadcast credentials are present and user is authenticated."""
        
        if not CredentialsManager.has_ibroadcast_credentials():
            # Show login screen and let it handle inputs
            self.root_stack.setCurrentWidget(self.login_screen)
            return

        if self.api.access_token:
            res = self.api.load_library()
            if res.get('success'):
                self.root_stack.setCurrentWidget(self.main_app_widget)
                # Add 'Artists' as the root of the navigation stack
                self.navigation_stack = []
                self.push_page({"type": "Navigation", "id": 0})
                self.load_artists()
                self.connect_to_queue() # Connect to WS
            else:
                # Token might be invalid, try OAuth flow or re-login
                self.start_login_flow()
        else:
            self.start_login_flow()

    def on_login_requested(self, client_id, client_secret):
        """Called when user clicks login on the LoginScreen"""
        CredentialsManager.set_credential(CredentialsManager.IBROADCAST_CLIENT_ID, client_id)
        CredentialsManager.set_credential(CredentialsManager.IBROADCAST_CLIENT_SECRET, client_secret)
        # Re-initialize API with new keys
        self.api = iBroadcastAPI() 
        self.start_login_flow()

    def start_login_flow(self):
        """Initiate OAuth flow"""
        self.root_stack.setCurrentWidget(self.login_screen)
        auth_res = self.api.start_oauth_flow()
        if 'auth_url' in auth_res:
            webbrowser.open(auth_res['auth_url'])
            self.oauth_poll_timer = QTimer()
            self.oauth_poll_timer.setInterval(1000)
            self.oauth_poll_timer.timeout.connect(self.poll_oauth_callback)
            self.oauth_poll_timer.start()
        else:
            self.login_screen.set_error(auth_res.get('message', 'Failed to start login flow'))

    def poll_oauth_callback(self):
        status = self.api.check_callback_status()
        if status.get('success') and 'code' in status:
            self.oauth_poll_timer.stop()
            token_res = self.api.exchange_code_for_token(status['code'])
            if token_res.get('success'):
                lib_res = self.api.load_library()
                if lib_res.get('success'):
                    self.root_stack.setCurrentWidget(self.main_app_widget)
                    self.load_artists()
                    self.connect_to_queue() # Connect to WS
                else:
                    self.login_screen.set_error("Failed to load library after login.")
            else:
                self.login_screen.set_error(f"Login failed: {token_res.get('message', 'Unknown error')}")
        elif not status.get('pending', False):
            self.oauth_poll_timer.stop()
            self.login_screen.set_error(f"Login failed: {status.get('message', 'Unknown error')}")

    def switch_view(self, index, push_to_stack=True):
        if push_to_stack:
            # User clicked a sidebar navigation link: reset stack to just this root
            self.navigation_stack = []
            self.push_page({"type": "Navigation", "id": index})
        self.content_stack.setCurrentIndex(index)
        self.current_album_id = None
        self._showing_artist_albums = False

        if index == 0:
            self.load_artists()
        elif index == 1:
            self.load_albums()
        elif index == 2:
            self.load_playlists()


    def load_artists(self):
        self.content_stack.setCurrentWidget(self.artists_view)
        self._showing_artist_albums=False
        self.artist_header.setVisible(self._showing_artist_albums)
        self.artists_view.clear()
        artists = self.api.get_artists_with_albums()
        for artist in artists:
            self.artists_view.add_item(artist, self.api.get_artwork_url(artist.artwork_id))
    
    def load_albums(self, artist_id=None):
        self.content_stack.setCurrentWidget(self.albums_view)
        self.artist_header.setVisible(self._showing_artist_albums)
        self.albums_view.clear()
        albums = None
        if artist_id:
            albums = self.api.get_artist_albums(artist_id)
        else:
            albums = self.api.get_albums()
        if albums:
            for album in albums:
                artwork_id = None
                tracks = self.api.get_tracks_by_album(album.id)
                for track in tracks:
                    if track.artwork_id != 0:
                        artwork_id = track.artwork_id
                        break
                self.albums_view.add_item(album, self.api.get_artwork_url(artwork_id))
        else:
            # No albums found: Find the songs where the artist appears, then get those albums.
            if artist_id:
                tracks = self.api.get_tracks_by_artist(artist_id)
                album_ids = set()
                for track in tracks:
                    album = self.api.get_album_by_track(track.id)
                    if album:
                        album_ids.add(album.id)
                for album_id in album_ids:
                    album = self.api.get_album_by_id(album_id)
                    if album:
                        artwork_id = None
                        album_tracks = self.api.get_tracks_by_album(album.id)
                        for track in album_tracks:
                            if track.artwork_id != 0:
                                artwork_id = track.artwork_id
                                break
                        self.albums_view.add_item(album, self.api.get_artwork_url(artwork_id))
            
    def show_album_detail(self, album_id, push_to_stack=True):
        if isinstance(album_id, int):
            album = self.api.get_album_by_id(album_id)
        elif isinstance(album_id, Album):
            album = album_id
            album_id = album.id
        else:
            return
        
        if push_to_stack:
            self.push_page({"type": "Album", "id": album_id})
        self.current_album_id = album_id
        self.current_playlist_id = None
        
        if not album:
            return
        artists = self.api.get_artists_by_album(album_id)
        artist_name = ", ".join([a.name for a in artists]) if artists else "Unknown Artist"
        year = album.year
        tracks = self.api.get_tracks_by_album(album_id)
        artwork_url = None
        for track in tracks:
            if track.artwork_id != 0:
                artwork_url = self.api.get_artwork_url(track.artwork_id)
                break
        
        self.album_detail_view.set_artist_id(artists[0].id if artists else None)
        self.album_detail_view.set_album(album.name, artist_name, year, artwork_url)
        
        tracks.sort(key=lambda x: x.track_number if x.track_number is not None else 0)
        self.album_detail_view.set_tracks(tracks)
        
        self._current_album_tracks = [t.id for t in tracks]
        self.content_stack.setCurrentWidget(self.album_detail_view)
        self._showing_artist_albums=False
        self.artist_header.setVisible(self._showing_artist_albums)
        self.artist_header.upButtonClicked.connect(self.load_artists)
    
    def show_playlist_detail(self, playlist_id):
        if isinstance(playlist_id, int):
            playlist = self.api.get_playlist_by_id(playlist_id)
        elif isinstance(playlist_id, Playlist):
            playlist = playlist_id
            playlist_id = playlist.id
        else:
            return
        self.current_playlist_id = playlist_id
        self.current_album_id = None
                
        if not playlist:
            return
        
        tracks = self.api.get_playlist_tracks(playlist_id)
        
        self.playlist_detail_view.set_playlist(
            playlist.name,
            len(tracks),
            self.api.get_artwork_url(playlist.artwork_id)
        )
        
        self.playlist_detail_view.set_tracks(tracks)
        
        self._current_playlist_tracks = [t.id for t in tracks]
        self.content_stack.setCurrentWidget(self.playlist_detail_view)

    def load_playlists(self):
        
        self.artist_header.setVisible(False)
        self.content_stack.setCurrentWidget(self.playlists_view)
        self.playlists_view.clear()
        playlists = self.api.get_playlists()
        
        for playlist in playlists:
            self.playlists_view.add_item(playlist, self.api.get_artwork_url(playlist.artwork_id))

    def show_artist_albums(self, artist_id, push_to_stack=True):
        
        if isinstance(artist_id, int):
            artist = self.api.get_artist_by_id(artist_id)
        elif isinstance(artist_id, str) and artist_id.isdigit():
            artist = self.api.get_artist_by_id(int(artist_id))
            artist_id = int(artist_id)
        elif isinstance(artist_id, Artist):
            artist = artist_id
            artist_id = artist.id
        else:
            return
            
        if push_to_stack:
            self.push_page({"type": "Artist", "id": int(artist_id)})
        
        if artist:
            self.artist_header.set_artist(artist.name, self.api.get_artwork_url(artist.artwork_id))
            self._showing_artist_albums = True
            self.content_stack.setCurrentWidget(self.albums_view)
            self.load_albums(artist_id)
        else:
            self._showing_artist_albums = False


    def play_track_from_album(self, track_id):
        if not hasattr(self, '_current_album_tracks'):
            return
        
        try:
            track_index = self._current_album_tracks.index(track_id)
            self.tracks = self._current_album_tracks.copy()
            self.play_index = track_index
            self.play_from = "tracks"
            self.play_next_queue = []
            
            self.update_queue_display()
            self.play_track_by_id(track_id)
        except ValueError:
            pass
    
    def play_track_from_album_at_row(self, row):
        if not hasattr(self, '_current_album_tracks') or row >= len(self._current_album_tracks):
            return
        
        track_id = self._current_album_tracks[row]
        self.tracks = self._current_album_tracks.copy()
        self.play_index = row
        self.play_from = "tracks"
        self.play_next_queue = []
        
        self.update_queue_display()
        self.play_track_by_id(track_id)
    
    def add_track_to_queue_from_album(self, row, after_current=False):
        if not hasattr(self, '_current_album_tracks') or row >= len(self._current_album_tracks):
            return
        
        track_id = self._current_album_tracks[row]
        # Append to play_next or end of tracks? 
        # iBroadcast context menu usually has "Play Next" and "Add to Queue"
        if after_current:
            self.play_next_queue.insert(0, track_id)
        else:
            self.tracks.append(track_id)
        self.update_queue_display()
        self.push_state_to_server()
    
    def play_track_from_playlist(self, track_id):
        track_id = int(track_id)
        if not hasattr(self, '_current_playlist_tracks'):
            return
        try:
            track_index = self._current_playlist_tracks.index(track_id)
            self.tracks = self._current_playlist_tracks.copy()
            self.play_index = track_index
            self.play_from = "tracks"
            self.play_next_queue = []
            
            self.update_queue_display()
            self.play_track_by_id(track_id)
        except ValueError as e:
            pass
    
    def play_track_from_playlist_at_row(self, row):
        if not hasattr(self, '_current_playlist_tracks') or row >= len(self._current_playlist_tracks):
            return
        
        track_id = self._current_playlist_tracks[row]
        self.tracks = self._current_playlist_tracks.copy()
        self.play_index = row
        self.play_from = "tracks"
        self.play_next_queue = []
        
        self.update_queue_display()
        self.play_track_by_id(track_id)
    
    def add_track_to_queue_from_playlist(self, row, after_current=False):
        if not hasattr(self, '_current_playlist_tracks') or row >= len(self._current_playlist_tracks):
            return
        
        track_id = self._current_playlist_tracks[row]
        if after_current:
            self.play_next_queue.insert(0, track_id)
        else:
            self.tracks.append(track_id)
        self.update_queue_display()
        self.push_state_to_server()

    def play_track_by_id(self, track_id, from_server=False, start_playing=True, position_ms=0):
        track = self.api.get_track_by_id(track_id)
        artists = self.api.get_artists_by_track(track_id)
        album = self.api.get_album_by_track(track_id)
        
        album_artists = self.api.get_artists_with_albums()

        if track:
            url = self.api.get_stream_url(track_id)
            self.pending_seek_ms = position_ms
            self.media_player.setSource(QUrl(url))
            
            # Reset UI progress immediately for visual feedback
            self.controls.progress.setValue(0)
            self.controls.time_current.setText("0:00")
            
            if start_playing:
                self.media_player.play()
            else:
                self.media_player.pause()
            
            self.current_track_id = track_id
                        
            # Store track info
            self.current_track_info = {
                'artist': artists[0].name if artists else 'Unknown Artist',
                'track': track.name if track else 'Unknown Track',
                'album': album.name if album else None
            }
            self.track_duration = track.length if track else 0  # Duration in seconds
            
            artwork_url = self.api.get_artwork_url(track.artwork_id if track else None)
            
            
            self.controls.set_track_info(track, album, artists, album_artists, artwork_url)
            self.controls.set_playing(start_playing)
            
            # Update MPRIS metadata
            self.mpris.update_metadata({
                'track_id': track_id,
                'title': track.name,
                'artist': self.current_track_info['artist'],
                'album': album.name if album else '',
                'art_url': artwork_url,
                'length': float(track.length)
            })
            self.mpris.update_status("Playing")
            
            self.update_queue_display()
            
            if not from_server:
                self.push_state_to_server()

    def on_playback_state_changed(self, state):
        """Handle playback state changes"""
        # We push state when play/pause changes locally
        self.push_state_to_server()
        
        # Update MPRIS status
        is_playing = (self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState)
        self.mpris.update_status("Playing" if is_playing else "Paused")



    def toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.controls.set_playing(False)
        else:
            self.media_player.play()
            self.controls.set_playing(True)
        self.push_state_to_server()

    def play_next(self):
        """Play the next track based on server-synced queues."""
        if self.role != "player":
            # Just send a 'next' command if we are a controller? 
            # Or just wait for the player to advance.
            # Usually iBroadcast controllers send a command to the player.
            # For now, let's just do nothing or send a specific command if supported.
            return

        # 1. Handle play_next queue (must be consumed)
        if self.play_from == "play_next" or len(self.play_next_queue) > 0:
            if len(self.play_next_queue) > 0:
                self.play_from = "play_next"
                # Pop the current one (if we were already playing it) or the first one
                # Logic: play_next always plays the first item. 
                # After it finishes, we should have already popped it? 
                # Let's say we pop it NOW before playing the NEXT one.
                self.play_next_queue.pop(0)
                
                if len(self.play_next_queue) > 0:
                    self.play_track_by_id(self.play_next_queue[0])
                else:
                    self.play_from = "tracks"
                    if self.play_index < len(self.tracks):
                        self.play_track_by_id(self.tracks[self.play_index])
                    else:
                        self.media_player.stop()
            else:
                self.play_from = "tracks"
                self.play_next_in_tracks()
        else:
            self.play_next_in_tracks()

    def play_next_in_tracks(self):
        """Advance within the persistent tracks queue"""
        if self.repeat_mode == "track":
            self.media_player.setPosition(0)
            self.media_player.play()
            return

        self.play_index += 1
        
        if self.play_index >= len(self.tracks):
            if self.repeat_mode == "queue":
                self.play_index = 0
                if self.tracks:
                    self.play_track_by_id(self.tracks[0])
            else:
                self.media_player.stop()
                self.controls.set_playing(False)
        else:
            self.play_track_by_id(self.tracks[self.play_index])

    def play_previous(self):
        """Handle 'Previous' command"""
        if self.role != "player": return

        # If we are > 3s into the track, just restart it
        if self.media_player.position() > 3000:
            self.media_player.setPosition(0)
            return
        
        if self.play_from == "tracks" and self.play_index > 0:
            self.play_index -= 1
            self.play_track_by_id(self.tracks[self.play_index])
        else:
            # Restart current track if we can't go back
            self.media_player.setPosition(0)

    def toggle_shuffle(self):
        self.shuffle_enabled = not self.shuffle_enabled
        self.controls.set_shuffle(self.shuffle_enabled)
        self.push_state_to_server()

    def toggle_repeat(self):
        modes = ["off", "all", "one"]
        current_idx = modes.index(self.repeat_mode)
        self.repeat_mode = modes[(current_idx + 1) % len(modes)]
        self.controls.set_repeat(self.repeat_mode)
        self.push_state_to_server()

    def set_volume(self, value):
        self.audio_output.setVolume(value / 100)
        self.push_state_to_server()

    def on_seek_start(self):
        self.is_seeking = True
        self.timer.stop()

    def on_seek_end(self):
        if self.media_player.duration() > 0:
            position = (self.controls.progress.value() / 1000) * self.media_player.duration()
            self.media_player.setPosition(int(position))
            # Update time labels to reflect the seeked position immediately
            current = int(position) // 1000
            total = self.media_player.duration() // 1000
            self.controls.update_time_labels(current, total)
        self.is_seeking = False
        self.timer.start(100)

    def on_seek_progress(self, value):
        if self.is_seeking and self.media_player.duration() > 0:
            position = (value / 1000) * self.media_player.duration()
            current = int(position) // 1000
            total = self.media_player.duration() // 1000
            self.controls.update_time_labels(current, total)

    def update_position(self):
        if self.is_seeking:
            return

        current_ms = 0
        total_ms = 0

        if self.role == "player":
            if self.media_player.duration() > 0:
                current_ms = self.media_player.position()
                total_ms = self.media_player.duration()
        else:
            # Controller role: predict position based on server state
            state = self.last_server_state
            if state and "current_song" in state:
                start_time = state.get("start_time", 0)
                start_pos = state.get("start_position", 0)
                is_paused = state.get("pause", False)
                
                track = self.api.get_track_by_id(state["current_song"])
                if track:
                    total_ms = track.length * 1000
                    if is_paused:
                        current_ms = int(start_pos * 1000)
                    else:
                        now = time.time()
                        current_ms = int((now - (start_time - start_pos)) * 1000)
                    
                    # Clamp
                    current_ms = max(0, min(current_ms, total_ms))

        if total_ms > 0:
            pos = (current_ms / total_ms) * 1000
            self.controls.progress.setValue(int(pos))
            self.controls.update_time_labels(current_ms // 1000, total_ms // 1000)
            
        # 2. Periodic State Sync (every 2 seconds)
        now = time.time()
        if now - self.last_sync_time >= 2.0:
            if self.role == "player" and self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.push_state_to_server()
            self.last_sync_time = now

    def on_media_status_changed(self, status):
        """Handle media player status changes"""
        if status == QMediaPlayer.MediaStatus.LoadedMedia or status == QMediaPlayer.MediaStatus.BufferedMedia:
            if self.pending_seek_ms > 0:
                self.media_player.setPosition(self.pending_seek_ms)
                self.pending_seek_ms = 0

        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.play_next()
    
    
    def update_queue_display(self):
        """Update the queue sidebar display from tracks/play_next state"""
        tracks_data = []
        
        # 1. Show Up Next
        for track_id in self.play_next_queue:
            track = self.api.get_track_by_id(track_id)
            if track:
                artists = self.api.get_artists_by_track(track_id)
                artist_name = ", ".join([a.name for a in artists]) if artists else "Unknown Artist"
                tracks_data.append({
                    'title': track.name,
                    'artist': artist_name,
                    'track_id': track_id,
                    'is_current': (self.play_from == "play_next" and track_id == self.current_track_id)
                })
        
        # 2. Show tracks queue
        for i, track_id in enumerate(self.tracks):
            track = self.api.get_track_by_id(track_id)
            if track:
                artists = self.api.get_artists_by_track(track_id)
                artist_name = ", ".join([a.name for a in artists]) if artists else "Unknown Artist"
                is_curr = (self.play_from == "tracks" and i == self.play_index)
                tracks_data.append({
                    'title': track.name,
                    'artist': artist_name,
                    'track_id': track_id,
                    'is_current': is_curr
                })
        
        # Align with QueueSidebar.set_queue(tracks_data, play_next_data, current_index, play_from)
        # Note: We are flattening everything into tracks_data for simplicity in display,
        # but let's just pass them properly if QueueSidebar supports it.
        self.queue_sidebar.set_queue(tracks_data, [], self.play_index, self.play_from)

    def remove_from_queue(self, index, is_play_next=False):
        """Handle manual removal from queue in UI (flattended index)"""
        if index < 0: return
        
        if index < len(self.play_next_queue):
            self.play_next_queue.pop(index)
        else:
            tracks_idx = index - len(self.play_next_queue)
            if 0 <= tracks_idx < len(self.tracks):
                self.tracks.pop(tracks_idx)
                if tracks_idx < self.play_index:
                    self.play_index -= 1
                elif tracks_idx == self.play_index:
                    # Current song removed? Skip to next.
                    self.play_next()
        
        self.update_queue_display()
        self.push_state_to_server()

    def clear_queue(self):
        self.tracks = []
        self.play_next_queue = []
        self.play_index = 0
        self.play_from = "tracks"
        self.current_track_id = None
        self.media_player.stop()
        self.controls.set_playing(False)
        self.update_queue_display()
        self.push_state_to_server()

    def play_track_from_queue(self, index):
        """Play a track from the queue at the given (flattened) index"""
        if index < 0: return

        if index < len(self.play_next_queue):
            track_id = self.play_next_queue[index]
            # iBroadcast logic: play_next is consumed.
            # If we jump to the 5th item, items 0-4 are removed.
            self.play_next_queue = self.play_next_queue[index:]
            self.play_from = "play_next"
            self.play_track_by_id(track_id)
        else:
            tracks_idx = index - len(self.play_next_queue)
            if 0 <= tracks_idx < len(self.tracks):
                track_id = self.tracks[tracks_idx]
                self.play_index = tracks_idx
                self.play_from = "tracks"
                self.play_track_by_id(track_id)
        
        self.update_queue_display()
        self.push_state_to_server()

    def reorder_queue(self, old_index, new_index):
        # Flattened reorder logic
        # For now, only support reordering if within 'tracks' (ignoring play_next for reorder)
        if len(self.play_next_queue) == 0:
            if old_index < len(self.tracks) and new_index < len(self.tracks):
                tid = self.tracks.pop(old_index)
                self.tracks.insert(new_index, tid)
                if old_index == self.play_index:
                    self.play_index = new_index
                elif old_index < self.play_index <= new_index:
                    self.play_index -= 1
                elif new_index <= self.play_index < old_index:
                    self.play_index += 1
        
        self.update_queue_display()
        self.push_state_to_server()

    def closeEvent(self, event):
        """Pause playback on server when closing if we are the player"""
        if self.role == "player":
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.pause()
                # We need to force a sync before the socket closes
                self.push_state_to_server()
                # Give a small moment for the push to go out
                time.sleep(0.5)
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Load NataSans font
    font_path = os.path.join(os.path.dirname(__file__), "assets", "font", "NataSans.ttf")
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id != -1:
        family = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(family))
    window = iBroadcastNative()
    window.showMaximized()
    sys.exit(app.exec())
