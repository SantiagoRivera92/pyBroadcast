import flet as ft
from audio.MyBroadcastAudio import MyBroadcastAudio

import webbrowser
import asyncio
from api.ibroadcast_api import iBroadcastAPI

from ui.library_grid import LibraryGrid
from ui.artist_header import ArtistHeader
from ui.player_controls import PlayerControls
from ui.album_header import AlbumHeader
from ui.album_track_list import AlbumTrackList

class iBroadcastFlet:
    def __init__(self, page: ft.Page):
        self.page = page
        self.api = iBroadcastAPI()
        self.current_queue = []
        self.current_index = 0
        self.shuffle_enabled = False
        self.repeat_mode = "off"
        self.is_playing = False
        self.current_track_id = None
        self._showing_artist_albums = False
        
        self.audio = MyBroadcastAudio(src="")
        self.page.overlay.append(self.audio.audio)
        
        self.init_ui()
        asyncio.create_task(self.check_auth())

    def init_ui(self):
        self.page.title = "pyBroadcast"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#121212"
        
        # Create UI components first
        self.search_input = ft.TextField(
            hint_text="Search tracks, artists, or albums...",
            width=450,
            bgcolor="#242424",
            color="white",
            border_radius=20,
            content_padding=10,
            on_change=self.handle_search,
            border_color="transparent",
            focused_border_color="#5DADE2",
            text_size=14,
        )
        
        header = ft.Container(
            content=ft.Row(
                controls=[
                    self.search_input,
                    ft.Container(expand=True),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            bgcolor="#000000",
            height=70,
            border=ft.Border.only(bottom=ft.border.BorderSide(1, "#282828")),  # Keep as is
            padding=ft.Padding.symmetric(horizontal=20),  # Keep as is
        )
        
        # Sidebar
        self.sidebar_buttons = []
        self.sidebar = ft.Column(
            controls=[],
            width=250,
            spacing=2,
        )
        
        sidebar_items = ["Home", "Artists", "Albums", "Playlists"]
        for i, item in enumerate(sidebar_items):
            btn = ft.TextButton(
                content=ft.Text(item),  # FIXED: Use content=ft.Text() instead of text=
                style=ft.ButtonStyle(
                    color="#b3b3b3",
                    bgcolor=ft.Colors.TRANSPARENT,
                    padding=ft.Padding.symmetric(vertical=15, horizontal=20),  # Keep as is
                ),
                data=i,
                on_click=self.switch_view,
            )
            self.sidebar_buttons.append(btn)
            self.sidebar.controls.append(btn)
        
        # Set first button as active
        self.sidebar_buttons[0].style.color = "#5DADE2"
        
        
        # Create views
        self.artist_header = ArtistHeader(visible=False)
        
        self.home_view = LibraryGrid(lambda album_id: asyncio.create_task(self.show_album_detail(album_id)))
        self.artists_view = LibraryGrid(lambda artist_id: asyncio.create_task(self.show_artist_albums(artist_id)))
        self.albums_view = LibraryGrid(lambda album_id: asyncio.create_task(self.show_album_detail(album_id)))
        self.playlists_view = LibraryGrid(lambda playlist_id: asyncio.create_task(self.play_playlist(playlist_id)))
        
        # Current content view
        self.current_view = self.home_view
        
        # Content container
        self.content_container = ft.Container(
            content=ft.Column(
                controls=[
                    self.artist_header,
                    self.current_view,
                ],
                expand=True,
            ),
            expand=True,
        )
        
        # Player controls
        self.controls = PlayerControls()
        self.controls.play_btn.on_click = self.toggle_play
        self.controls.next_btn.on_click = self.play_next
        self.controls.prev_btn.on_click = self.play_previous
        self.controls.volume_slider.on_change = self.set_volume
        self.controls.shuffle_btn.on_click = self.toggle_shuffle
        self.controls.repeat_btn.on_click = self.toggle_repeat
        
        # Main layout
        body = ft.Row(
            controls=[
                ft.Container(
                    content=self.sidebar,
                    bgcolor="#000000",
                    width=250,
                ),
                self.content_container,
            ],
            expand=True,
        )
        
        self.page.add(
            header,
            body,
            self.controls,
        )
    
    async def handle_search(self, e):
        text = e.control.value
        if len(text) < 2:
            if self.sidebar_buttons[0].content.value == "Home":  # FIXED: Access text via content.value
                await self.load_home()
            return
        
        self.home_view.clear()
        self.artist_header.visible = False
        self.page.update()
        
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
        
        self.page.update()
    
    async def check_auth(self):
        if self.api.access_token:
            res = self.api.load_library()
            if res.get('success'):
                await self.load_home()
        else:
            self.controls.set_track_info("Login Required...", "")
            auth_res = self.api.start_oauth_flow()
            if 'auth_url' in auth_res:
                webbrowser.open(auth_res['auth_url'])
                # Poll for OAuth callback
                asyncio.create_task(self.poll_oauth_callback())
    
    async def poll_oauth_callback(self):
        while True:
            status = self.api.check_callback_status()
            if status.get('success') and 'code' in status:
                token_res = self.api.exchange_code_for_token(status['code'])
                if token_res.get('success'):
                    lib_res = self.api.load_library()
                    if lib_res.get('success'):
                        await self.load_home()
                        self.controls.set_track_info("", "")
                        break
                    else:
                        self.controls.set_track_info("Failed to load library after login.", "")
                        break
                else:
                    self.controls.set_track_info(f"Login failed: {token_res.get('message', 'Unknown error')}", "")
                    break
            elif not status.get('pending', False):
                self.controls.set_track_info(f"Login failed: {status.get('message', 'Unknown error')}", "")
                break
            await asyncio.sleep(1)
    
    async def switch_view(self, e):
        index = e.control.data
        
        # Update sidebar button colors
        for i, btn in enumerate(self.sidebar_buttons):
            if i == index:
                btn.style.color = "#5DADE2"
            else:
                btn.style.color = "#b3b3b3"
        
        # Switch views
        if index == 0:
            self.current_view = self.home_view
            await self.load_home()
        elif index == 1:
            self.current_view = self.artists_view
            await self.load_artists()
        elif index == 2:
            self.current_view = self.albums_view
            await self.load_albums()
        elif index == 3:
            self.current_view = self.playlists_view
            await self.load_playlists()
        
        # Update content container
        self.content_container.content = ft.Column(
            controls=[self.artist_header, self.current_view],
            expand=True,
        )

        if index != 2 or not self._showing_artist_albums:
            self.artist_header.visible = False

        self._showing_artist_albums = False
        self.page.update()
    
    async def load_home(self):
        self.home_view.clear()
        albums = list(self.api.library['albums'].items())[:30]
        for i, (aid, album) in enumerate(albums):
            artwork = self.api.get_artwork_url(album.get('artwork_id'))
            self.home_view.add_item(album.get('name'), "Album", artwork, aid, i // 5, i % 5)
        self.page.update()
    
    async def load_artists(self):
        self.artists_view.clear()
        artists = sorted(self.api.library['artists'].values(), key=lambda x: str(x.get('name', '')).lower())
        for i, artist in enumerate(artists):
            artwork = self.api.get_artwork_url(artist.get('artwork_id'))
            self.artists_view.add_item(artist.get('name', 'Unknown'), "Artist", artwork, artist.get('item_id'), i // 5, i % 5)
        self.page.update()
    
    async def load_albums(self, artist_id=None):
        self.albums_view.clear()
        albums = self.api.library['albums'].values()
        if artist_id:
            albums = [a for a in albums if str(a.get('artist_id')) == str(artist_id)]
        albums_list = list(albums)
        for i, album in enumerate(albums_list):
            artwork = self.api.get_artwork_url(album.get('artwork_id'))
            self.albums_view.add_item(album.get('name'), "Album", artwork, album.get('item_id'), i // 5, i % 5)
        self.page.update()
    
    async def load_playlists(self):
        self.playlists_view.clear()
        playlists = self.api.library.get('playlists', {})
        
        for i, (pid, pl) in enumerate(playlists.items()):
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
        self.page.update()
    
    async def show_album_detail(self, album_id):
        album = self.api.library['albums'].get(str(album_id)) or self.api.library['albums'].get(album_id)
        if not album:
            return
                
        album_header = AlbumHeader()
        album_track_list = AlbumTrackList(self.play_track_by_id)
        
        artist = self.api.library['artists'].get(album.get('artist_id'))
        artist_name = artist.get('name', 'Unknown Artist') if artist else 'Unknown Artist'
        year = album.get('year', '') or album.get('release_date', '')
        artwork_url = self.api.get_artwork_url(album.get('artwork_id'))
        
        album_header.set_album(album.get('name', 'Unknown Album'), artist_name, year, artwork_url)
        
        tracks = [t for t in self.api.library['tracks'].values() if str(t.get('album_id')) == str(album.get('item_id'))]
        tracks.sort(key=lambda x: x.get('track', 0))
        album_track_list.set_tracks(tracks)
        
        album_detail = ft.Column(
            controls=[album_header, album_track_list],
            expand=True,
        )
        
        # Replace current view with album detail
        self.current_view = album_detail
        self.content_container.content = ft.Column(
            controls=[self.artist_header, album_detail],
            expand=True,
        )
        self.artist_header.visible = False
        self.page.update()
    
    async def show_artist_albums(self, artist_id):
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
            self.artist_header.visible = True
        
        self._showing_artist_albums = True
        
        # Switch to albums view for this artist
        self.sidebar_buttons[2].style.color = "#5DADE2"
        self.sidebar_buttons[0].style.color = "#b3b3b3"
        self.sidebar_buttons[1].style.color = "#b3b3b3"
        self.sidebar_buttons[3].style.color = "#b3b3b3"
        
        self.current_view = self.albums_view
        self.content_container.content = ft.Column(
            controls=[self.artist_header, self.albums_view],
            expand=True,
        )
        await self.load_albums(artist_id)
        self.page.update()
    
    async def play_playlist(self, playlist_id):
        pl = self.api.library['playlists'].get(playlist_id)
        if pl and pl.get('tracks'):
            track_ids = pl['tracks']
            self.current_queue = track_ids
            self.current_index = 0
            await self.play_track_by_id(track_ids[0])
    
    async def play_album(self, album_id):
        await self.show_album_detail(album_id)
    
    async def play_track_by_id(self, track_id):
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
            self.audio.set_audio_source(url)
            await self.audio.play()

            track_name = track.get('title', 'Unknown Track')
            artist_name = artist.get('name', 'Unknown Artist') if artist else 'Unknown Artist'
            artwork_url = self.api.get_artwork_url(track.get('artwork_id'))

            self.controls.set_track_info(track_name, artist_name, artwork_url)
            self.controls.set_playing(True)
            self.is_playing = True
            self.current_track_id = track_id
    
    async def toggle_play(self, e):
        if self.is_playing:
            await self.audio.pause()
            self.is_playing = False
            self.controls.set_playing(False)
        else:
            await self.audio.play()
            if self.current_track_id:
                await self.play_track_by_id(self.current_track_id)
            self.is_playing = True
            self.controls.set_playing(True)
        self.audio.update()
        self.page.update()
    
    async def play_next(self, e):
        if not self.current_queue:
            return
            
        if self.repeat_mode == "one":
            # Replay current track
            if self.current_track_id:
                await self.play_track_by_id(self.current_track_id)
            return
        
        self.current_index += 1
        
        if self.current_index >= len(self.current_queue):
            if self.repeat_mode == "all":
                self.current_index = 0
            else:
                self.is_playing = False
                self.controls.set_playing(False)
                self.page.update()
                return
        
        await self.play_track_by_id(self.current_queue[self.current_index])
    
    async def play_previous(self, e):
        if not self.current_queue:
            return
        
        # If more than 3 seconds into track, restart it
        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = len(self.current_queue) - 1 if self.repeat_mode == "all" else 0
        
        await self.play_track_by_id(self.current_queue[self.current_index])
    
    async def toggle_shuffle(self, e):
        self.shuffle_enabled = not self.shuffle_enabled
        self.controls.set_shuffle(self.shuffle_enabled)
        self.page.update()
    
    async def toggle_repeat(self, e):
        modes = ["off", "all", "one"]
        current_idx = modes.index(self.repeat_mode)
        self.repeat_mode = modes[(current_idx + 1) % len(modes)]
        self.controls.set_repeat(self.repeat_mode)
        self.page.update()
    
    async def set_volume(self, e):
        volume = e.control.value / 100
        self.audio.set_volume(volume)
        self.audio.update()

def main(page: ft.Page):
    app = iBroadcastFlet(page)

if __name__ == "__main__":
    ft.run(main)