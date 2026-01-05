# ui/player_controls_flet.py
import flet as ft

class PlayerControls(ft.Container):
    def __init__(self):
        # Create controls first
        self.artwork = ft.Image(
            fit="cover",
            border_radius=4,
            src=None
        )
        
        self.track_name = ft.Text(
            "No track playing",
            color="white",
            weight=ft.FontWeight.BOLD,
            size=15,
        )
        
        self.artist_name = ft.Text(
            "",
            color="#b3b3b3",
            size=13,
        )
        
        self.shuffle_btn = ft.IconButton(
            ft.Icons.SHUFFLE,
            icon_color="#b3b3b3",
            icon_size=24,
            tooltip="Shuffle",
        )
        
        self.prev_btn = ft.IconButton(
            ft.Icons.SKIP_PREVIOUS,
            icon_color="#b3b3b3",
            icon_size=32,
            tooltip="Previous",
        )
        
        self.play_btn = ft.IconButton(
            ft.Icons.PLAY_CIRCLE_FILLED,
            icon_color="white",
            icon_size=48,
            tooltip="Play",
        )
        
        self.next_btn = ft.IconButton(
            ft.Icons.SKIP_NEXT,
            icon_color="#b3b3b3",
            icon_size=32,
            tooltip="Next",
        )
        
        self.repeat_btn = ft.IconButton(
            ft.Icons.REPEAT,
            icon_color="#b3b3b3",
            icon_size=24,
            tooltip="Repeat",
        )
        
        self.time_current = ft.Text(
            "0:00",
            color="#b3b3b3",
            size=11,
            width=40,
        )
        
        self.progress = ft.Slider(
            min=0,
            max=100,
            value=0,
            active_color="#5DADE2",
            inactive_color="#4f4f4f",
            expand=True,
            height=4,
        )
        
        self.time_total = ft.Text(
            "0:00",
            color="#b3b3b3",
            size=11,
            width=40,
        )
        
        self.volume_slider = ft.Slider(
            min=0,
            max=100,
            value=80,
            width=120,
            active_color="#5DADE2",
            inactive_color="#4f4f4f",
            height=4,
        )
        
        super().__init__(
            height=110,
            bgcolor="#181818",
            border=ft.Border.only(top=ft.border.BorderSide(1, "#282828")),
            padding=ft.Padding.symmetric(horizontal=15, vertical=10),
            content=ft.Row(
                controls=[
                    # Left: Track info (30%)
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=70,
                                height=70,
                                bgcolor="#282828",
                                border_radius=4,
                                content=self.artwork,
                            ),
                            ft.Column(
                                controls=[
                                    self.track_name,
                                    self.artist_name,
                                ],
                                spacing=2,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=15,
                        expand=3,
                    ),
                    
                    # Center: Controls (40%)
                    ft.Column(
                        controls=[
                            # Control buttons
                            ft.Row(
                                controls=[
                                    ft.Container(expand=True),
                                    self.shuffle_btn,
                                    ft.Container(width=10),
                                    self.prev_btn,
                                    ft.Container(width=10),
                                    self.play_btn,
                                    ft.Container(width=10),
                                    self.next_btn,
                                    ft.Container(width=10),
                                    self.repeat_btn,
                                    ft.Container(expand=True),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            
                            # Progress bar
                            ft.Row(
                                controls=[
                                    self.time_current,
                                    self.progress,
                                    self.time_total,
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=10,
                            ),
                        ],
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=4,
                    ),
                    
                    # Right: Volume (30%)
                    ft.Row(
                        controls=[
                            ft.Container(expand=True),
                            ft.IconButton(
                                ft.Icons.VOLUME_UP,
                                icon_color="#b3b3b3",
                                icon_size=20,
                            ),
                            self.volume_slider,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=3,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
    
    def set_track_info(self, track_name, artist_name, artwork_url=None):
        self.track_name.value = track_name
        self.artist_name.value = artist_name
        
        if artwork_url:
            self.artwork.src = artwork_url
            self.artwork.visible = True
        else:
            self.artwork.visible = False
    
    def set_playing(self, is_playing):
        self.play_btn.icon = ft.Icons.PAUSE_CIRCLE_FILLED if is_playing else ft.Icons.PLAY_CIRCLE_FILLED
    
    def set_shuffle(self, enabled):
        self.shuffle_btn.icon_color = "#5DADE2" if enabled else "#b3b3b3"
    
    def set_repeat(self, mode):
        if mode == "off":
            self.repeat_btn.icon = ft.Icons.REPEAT
            self.repeat_btn.icon_color = "#b3b3b3"
        elif mode == "all":
            self.repeat_btn.icon = ft.Icons.REPEAT
            self.repeat_btn.icon_color = "#5DADE2"
        else:  # "one"
            self.repeat_btn.icon = ft.Icons.REPEAT_ONE
            self.repeat_btn.icon_color = "#5DADE2"
    
    def update_time_labels(self, current_seconds, total_seconds):
        def format_time(seconds):
            mins = seconds // 60
            secs = seconds % 60
            return f"{mins}:{secs:02d}"
        
        self.time_current.value = format_time(current_seconds)
        self.time_total.value = format_time(total_seconds)