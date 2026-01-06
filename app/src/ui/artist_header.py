import flet as ft

class ArtistHeader(ft.Container):
    def __init__(self, visible=False):
        self.artwork = ft.Image(
            border_radius=90,
            src=""
        )
        
        self.artist_name = ft.Text(
            "Artist Name",
            color="white",
            size=56,
            weight=ft.FontWeight.BOLD,
        )
        
        super().__init__(
            height=280,
            visible=visible,
            bgcolor="#1a1a1a",
            padding=40,
            content=ft.Row(
                controls=[
                    # Artist artwork
                    ft.Container(
                        width=180,
                        height=180,
                        bgcolor="#282828",
                        border_radius=90,
                        content=self.artwork,
                    ),
                    # Artist info
                    ft.Column(
                        controls=[
                            ft.Text(
                                "ARTIST",
                                color="white",
                                size=13,
                                weight=ft.FontWeight.BOLD,
                            ),
                            self.artist_name,
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
    
    def set_artist(self, name, artwork_url=None):
        self.artist_name.value = name
        
        if artwork_url:
            self.artwork.src = artwork_url
            self.artwork.visible = True
        else:
            self.artwork.visible = False
            # Show first letter as placeholder
            first_letter = name[0].upper() if name else "?"
            self.content.content.controls[0].content = ft.Container(
                width=180,
                height=180,
                bgcolor="#5DADE2",
                border_radius=90,
                alignment=ft.alignment.Alignment.CENTER,
                content=ft.Text(
                    first_letter,
                    color="white",
                    size=72,
                    weight=ft.FontWeight.BOLD,
                ),
            )