import sys
import webbrowser
import os

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QStackedWidget, QPushButton)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtGui import QAction, QIcon,QFontDatabase, QFont

from src.api.ibroadcast.models import Artist, Album, Track, Playlist
from src.api.ibroadcast.ibroadcast_api import iBroadcastAPI
from src.api.queue_cache import QueueCache
from src.api.lastfm.lastfm_api import LastFMAPI

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

class iBroadcastNative(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.api = iBroadcastAPI()
        self.queue_cache = QueueCache()
        self.lastfm = LastFMAPI()
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self.current_queue = []
        self.current_track_id = None
        self.shuffle_enabled = False
        self.repeat_mode = "off"
        
        self.current_album_id = None
        self.current_playlist_id = None
        
        self.track_duration = 0
        self.current_track_info = {}
        
        # Timer for updating queue cache position
        self.cache_update_timer = QTimer()
        self.cache_update_timer.timeout.connect(self.update_cache_position)
        self.cache_update_timer.start(1000)  # Update every second
        
        self.init_navigation_stack()
        self.init_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        self.timer.start(1000)
        self.is_seeking = False
        
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)  # NEW
        
        self.check_auth()
    
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
        self.resize(1400, 900)
        
        # Add menu bar - NEW
        self.create_menu_bar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
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
        dialog = OptionsDialog(self.lastfm, self.api, self)
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
        """Check if user is authenticated; if not, start OAuth flow."""
        if self.api.access_token:
            res = self.api.load_library()
            if res.get('success'):
                # Add 'Artists' as the root of the navigation stack
                self.navigation_stack = []
                self.push_page({"type": "Navigation", "id": 0})
                self.load_artists()
                self.restore_queue_from_cache()
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
                    self.load_artists()
                    self.controls.track_info.setText("")
                    self.restore_queue_from_cache()
                else:
                    self.controls.track_info.setText("Failed to load library after login.")
            else:
                self.controls.track_info.setText(f"Login failed: {token_res.get('message', 'Unknown error')}")
        elif not status.get('pending', False):
            self.oauth_poll_timer.stop()
            self.controls.track_info.setText(f"Login failed: {status.get('message', 'Unknown error')}")

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
        for album in albums:
            artwork_id = None
            tracks = self.api.get_tracks_by_album(album.id)
            for track in tracks:
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
        artist_name = ",".join([a.name for a in artists]) if artists else "Unknown Artist"
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
            tracks_to_queue = self._current_album_tracks[track_index + 1:]
            
            self.current_queue = tracks_to_queue
            self.current_track_id = track_id
            
            self.queue_cache.set_current_track(track_id, 0.0)
            self.queue_cache.set_tracks(tracks_to_queue)
            
            self.update_queue_display()
            self.play_track_by_id(track_id)
        except ValueError:
            pass
    
    def play_track_from_album_at_row(self, row):
        if not hasattr(self, '_current_album_tracks') or row >= len(self._current_album_tracks):
            return
        
        track_id = self._current_album_tracks[row]
        tracks_to_queue = self._current_album_tracks[row + 1:]
        
        self.current_queue = tracks_to_queue
        self.current_track_id = track_id
        
        self.queue_cache.set_current_track(track_id, 0.0)
        self.queue_cache.set_tracks(tracks_to_queue)
        
        self.update_queue_display()
        self.play_track_by_id(track_id)
    
    def add_track_to_queue_from_album(self, row, after_current=False):
        if not hasattr(self, '_current_album_tracks') or row >= len(self._current_album_tracks):
            return
        
        track_id = self._current_album_tracks[row]
        self.queue_cache.add_track(track_id, after_current)
        self.current_queue = self.queue_cache.tracks.copy()
        self.update_queue_display()
    
    def play_track_from_playlist(self, track_id):
        track_id = int(track_id)
        if not hasattr(self, '_current_playlist_tracks'):
            return
        try:
            track_index = self._current_playlist_tracks.index(track_id)
            tracks_to_queue = self._current_playlist_tracks[track_index + 1:]
            
            self.current_queue = tracks_to_queue
            self.current_track_id = track_id
            
            self.queue_cache.set_current_track(track_id, 0.0)
            self.queue_cache.set_tracks(tracks_to_queue)
            self.update_queue_display()
            self.play_track_by_id(track_id)
        except ValueError as e:
            pass
    
    def play_track_from_playlist_at_row(self, row):
        if not hasattr(self, '_current_playlist_tracks') or row >= len(self._current_playlist_tracks):
            return
        
        track_id = self._current_playlist_tracks[row]
        tracks_to_queue = self._current_playlist_tracks[row + 1:]
        
        self.current_queue = tracks_to_queue
        self.current_track_id = track_id
        
        self.queue_cache.set_current_track(track_id, 0.0)
        self.queue_cache.set_tracks(tracks_to_queue)
        
        self.update_queue_display()
        self.play_track_by_id(track_id)
    
    def add_track_to_queue_from_playlist(self, row, after_current=False):
        if not hasattr(self, '_current_playlist_tracks') or row >= len(self._current_playlist_tracks):
            return
        
        track_id = self._current_playlist_tracks[row]
        self.queue_cache.add_track(track_id, after_current)
        self.current_queue = self.queue_cache.tracks.copy()
        self.update_queue_display()

    def play_track_by_id(self, track_id):
        track = self.api.get_track_by_id(track_id)
        artists = self.api.get_artists_by_track(track_id)
        album = self.api.get_album_by_track(track_id)
        
        album_artists = self.api.get_artists_with_albums()

        if track:
            url = self.api.get_stream_url(track_id)
            self.media_player.setSource(QUrl(url))
            self.media_player.play()
            
            self.current_track_id = track_id
                        
            # Store track info for Last.fm scrobbling
            self.current_track_info = {
                'artist': artists[0].name if artists else 'Unknown Artist',
                'track': track.name if track else 'Unknown Track',
                'album': album.name if album else None
            }
            self.track_duration = track.length if track else 0  # Duration in seconds
            
            artwork_url = self.api.get_artwork_url(track.artwork_id if track else None)
            
            self.controls.set_track_info(track, album, artists, album_artists, artwork_url)
            self.controls.set_playing(True)
            
            # Update cache with new track
            self.queue_cache.set_current_track(track_id, 0.0)
            self.update_queue_display()

    def on_playback_state_changed(self, state):
        """Handle playback state changes for Last.fm"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            if self.lastfm.is_authenticated() and self.current_track_info:
                self.lastfm.update_now_playing(
                    self.current_track_info['artist'],
                    self.current_track_info['track'],
                    self.current_track_info.get('album')
                )

    def check_scrobble_conditions(self):
        """Check if we should scrobble the current track"""
        if not self.lastfm.is_authenticated():
            return
        
        if not self.current_track_info:
            return
        
        if self.media_player.duration() > 0:
            progress = self.media_player.position() / self.media_player.duration()
            seconds_played = self.media_player.position() / 1000.0
            if progress >= 0.3 or seconds_played >= 240:
                self.scrobble_track()

    def scrobble_track(self):
        """Scrobble the current track to Last.fm"""
        if not self.lastfm.is_authenticated():
            return
        
        if not self.current_track_info:
            return
        
        if self.current_track_info.get('scrobbled', False):
            return 
        
        self.lastfm.scrobble(
            self.current_track_info['artist'],
            self.current_track_info['track'],
            self.current_track_info.get('album')
        )
        self.current_track_info['scrobbled'] = True

    def toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.controls.set_playing(False)
        else:
            self.media_player.play()
            self.controls.set_playing(True)

    def play_next(self):
        # Check if we should scrobble before moving to next track
        self.check_scrobble_conditions()
        
        if self.repeat_mode == "one":
            self.current_track_info['scrobbled'] = False
            self.media_player.setPosition(0)
            self.media_player.play()
            return
        
        next_track = self.queue_cache.pop_next_track()
        
        if next_track:
            self.current_queue = self.queue_cache.tracks.copy()
            self.play_track_by_id(next_track)
        elif self.repeat_mode == "all" and self.current_track_id:
            self.media_player.stop()
            self.controls.set_playing(False)
        else:
            self.media_player.stop()
            self.controls.set_playing(False)

    def play_previous(self):
        # For simplicity, just restart the current track
        if self.media_player.position() > 3000:
            self.media_player.setPosition(0)
            return
        
        self.media_player.setPosition(0)

    def toggle_shuffle(self):
        self.shuffle_enabled = not self.shuffle_enabled
        self.controls.set_shuffle(self.shuffle_enabled)
        self.queue_cache.set_shuffle(self.shuffle_enabled)

    def toggle_repeat(self):
        modes = ["off", "all", "one"]
        current_idx = modes.index(self.repeat_mode)
        self.repeat_mode = modes[(current_idx + 1) % len(modes)]
        self.controls.set_repeat(self.repeat_mode)
        self.queue_cache.set_repeat_mode(self.repeat_mode)

    def set_volume(self, value):
        self.audio_output.setVolume(value / 100)

    def on_seek_start(self):
        self.is_seeking = True
        self.timer.stop()

    def on_seek_end(self):
        if self.media_player.duration() > 0:
            position = (self.controls.progress.value() / 100) * self.media_player.duration()
            self.media_player.setPosition(int(position))
            # Update time labels to reflect the seeked position immediately
            current = int(position) // 1000
            total = self.media_player.duration() // 1000
            self.controls.update_time_labels(current, total)
        self.is_seeking = False
        self.timer.start(1000)

    def on_seek_progress(self, value):
        if self.is_seeking and self.media_player.duration() > 0:
            position = (value / 100) * self.media_player.duration()
            current = int(position) // 1000
            total = self.media_player.duration() // 1000
            self.controls.update_time_labels(current, total)

    def update_position(self):
        if self.is_seeking:
            return
        if self.media_player.duration() > 0:
            pos = (self.media_player.position() / self.media_player.duration()) * 100
            self.controls.progress.setValue(int(pos))
            current = self.media_player.position() // 1000
            total = self.media_player.duration() // 1000
            self.controls.update_time_labels(current, total)
            # Check if we should scrobble
            self.check_scrobble_conditions()

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            # Track finished, check if we should scrobble
            self.check_scrobble_conditions()
            self.play_next()
    
    
    def restore_queue_from_cache(self):
        """Restore queue from cache when app starts"""
        if self.queue_cache.load():

            # Restore shuffle and repeat settings
            self.shuffle_enabled = self.queue_cache.shuffle_enabled
            self.repeat_mode = self.queue_cache.repeat_mode
            self.controls.set_shuffle(self.shuffle_enabled)
            self.controls.set_repeat(self.repeat_mode)
            
            # Rebuild queue
            self.current_track_id = self.queue_cache.current_track
            self.current_queue = self.queue_cache.tracks.copy()
                        
            # Optionally restore the current track (paused)
            if self.current_track_id:
                track = self.api.get_track_by_id(self.current_track_id)
                if track:
                    artists = self.api.get_artists_by_track(self.current_track_id)
                    artwork_url = self.api.get_artwork_url(track.artwork_id)
                    album = self.api.get_album_by_track(self.current_track_id)
                    album_artists = self.api.get_artists_with_albums()
                    
                    self.controls.set_track_info(track, album, artists, album_artists, artwork_url)    
                                    
                    # Load the media but don't play
                    url = self.api.get_stream_url(self.current_track_id)
                    self.media_player.setSource(QUrl(url))
                    
                    # Seek to the saved position once media is loaded
                    if self.queue_cache.current_position > 0:
                        def seek_on_load():
                            if self.media_player.duration() > 0:
                                position_ms = int(self.queue_cache.current_position * 1000)
                                self.media_player.setPosition(position_ms)
                                self.media_player.mediaStatusChanged.disconnect(seek_on_load)
                        
                        self.media_player.mediaStatusChanged.connect(seek_on_load)
            
            # Update the queue display AFTER everything is loaded
            self.update_queue_display()
    
    def update_cache_position(self):
        """Update cache with current playback position (called every second)"""
        if self.current_track_id and self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            position_sec = self.media_player.position() / 1000.0
            self.queue_cache.update_position(position_sec)
    
    def play_track_from_queue(self, index):
        """Play a track from the queue at the given index"""
        if 0 <= index < len(self.current_queue):
            track_id = self.current_queue[index]
            
            # Update queue to start from this track
            remaining_tracks = self.current_queue[index + 1:]
            self.queue_cache.set_current_track(track_id, 0.0)
            self.queue_cache.set_tracks(remaining_tracks)
            self.current_queue = remaining_tracks
            
            self.play_track_by_id(track_id)
    
    def remove_from_queue(self, index, is_play_next):
        """Remove a track from the queue"""
        self.queue_cache.remove_track(index)
        self.current_queue = self.queue_cache.tracks.copy()
        self.update_queue_display()
    
    def clear_queue(self):
        """Clear the entire queue"""
        self.queue_cache.clear()
        self.current_queue = []
        self.current_track_id = None
        self.media_player.stop()
        self.controls.set_playing(False)
        self.update_queue_display()
    
    def update_queue_display(self):
        """Update the queue sidebar display"""
        
        tracks_data = []
        
        # First, add the currently playing track
        if self.current_track_id:
            track = self.api.get_track_by_id(self.current_track_id)
            if track:
                artists = self.api.get_artists_by_track(int(self.current_track_id))
                artist_name = ",".join([a.name for a in artists]) if artists else "Unknown Artist"
                tracks_data.append({
                    'title': track.name,
                    'artist': artist_name,
                    'track_id': self.current_track_id,
                    'is_current': True
                })
        
        # Then add upcoming tracks from the queue
        for track_id in self.current_queue:
            track = self.api.get_track_by_id(track_id)
            if track:
                artists = self.api.get_artists_by_track(int(track_id))
                artist_name = ",".join([a.name for a in artists]) if artists else "Unknown Artist"
                tracks_data.append({
                    'title': track.name,
                    'artist': artist_name,
                    'track_id': track_id,
                    'is_current': False
                })
        
        self.queue_sidebar.set_queue(tracks_data, [], 0, 'tracks')
    
    def reorder_queue(self, old_index, new_index):
        """Reorder tracks in the queue"""
        self.queue_cache.reorder_tracks(old_index, new_index)
        self.current_queue = self.queue_cache.tracks.copy()
        self.update_queue_display()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Load NataSans font
    font_path = os.path.join(os.path.dirname(__file__), "assets", "font", "NataSans.ttf")
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id != -1:
        family = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(family))
    else:
        print("Warning: Could not load NataSans.ttf font.")
    window = iBroadcastNative()
    window.show()
    sys.exit(app.exec())
