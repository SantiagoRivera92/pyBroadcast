import flet as ft

class AlbumHeader(ft.Container):
    def __init__(self):
        self.artwork = ft.Image(
            border_radius=16,
            src=""
        )
        
        self.album_name = ft.Text(
            "Album Name",
            color="white",
            size=48,
            weight=ft.FontWeight.BOLD,
        )
        
        self.artist_name = ft.Text(
            "Artist Name",
            color="#b3b3b3",
            size=20,
        )
        
        self.year_label = ft.Text(
            "",
            color="#b3b3b3",
            size=16,
        )
        
        super().__init__(
            height=280,
            bgcolor="#1a1a1a",
            gradient=ft.LinearGradient(
                begin=ft.alignment.Alignment.TOP_CENTER,
                end=ft.alignment.Alignment.BOTTOM_CENTER,
                colors=["#1a1a1a", "#121212"],
            ),
            padding=40,
            content=ft.Row(
                controls=[
                    # Album artwork
                    ft.Container(
                        width=180,
                        height=180,
                        bgcolor="#282828",
                        border_radius=16,
                        content=self.artwork,
                    ),
                    # Album info
                    ft.Column(
                        controls=[
                            ft.Text(
                                "ALBUM",
                                color="white",
                                size=13,
                                weight=ft.FontWeight.BOLD,
                            ),
                            self.album_name,
                            self.artist_name,
                            self.year_label,
                            ft.Container(expand=True),
                        ],
                        spacing=10,
                        expand=True,
                    ),
                    ft.Container(expand=True),
                ],
                spacing=30,
            ),
        )
    
    def set_album(self, name, artist, year, artwork_url=None):
        self.album_name.value = name
        self.artist_name.value = artist
        self.year_label.value = str(year) if year else ""
        
        if artwork_url:
            self.artwork.src = artwork_url
            self.artwork.visible = True
        else:
            self.artwork.visible = False