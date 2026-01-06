import flet as ft
import asyncio

class AlbumTrackList(ft.Container):
    def __init__(self, play_callback):
        self.tracks_column = ft.Column(
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        super().__init__(
            bgcolor="#181818",
            expand=True,
            padding=ft.Padding.only(left=40, right=40, bottom=40),
            content=ft.Column(
                controls=[
                    # Table headers
                    ft.Row(
                        controls=[
                            ft.Container(
                                ft.Text("#", color="#b3b3b3", size=14),
                                width=40,
                            ),
                            ft.Container(
                                ft.Text("Title", color="#b3b3b3", size=14),
                                expand=True,
                            ),
                            ft.Container(
                                ft.Text("Duration", color="#b3b3b3", size=14),
                                width=80,
                            ),
                            ft.Container(
                                width=40,
                            ),
                        ],
                        height=40,
                    ),
                    ft.Divider(height=1, color="#282828"),
                    self.tracks_column,
                ],
                expand=True,
            ),
        )
        self.play_callback = play_callback
    
    def set_tracks(self, tracks):
        self.tracks_column.controls.clear()
        for i, track in enumerate(tracks):
            row = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            ft.Text(
                                str(track.get('track', i+1)),
                                color="#b3b3b3",
                                size=16,
                            ),
                            width=40,
                            alignment=ft.alignment.Alignment.CENTER,
                        ),
                        ft.Container(
                            ft.Text(
                                track.get('title', 'Unknown'),
                                color="white",
                                size=16,
                            ),
                            expand=True,
                            alignment=ft.alignment.Alignment.CENTER_LEFT,
                        ),
                        ft.Container(
                            ft.Text(
                                self.format_duration(track.get('length', 0)),
                                color="#b3b3b3",
                                size=16,
                            ),
                            width=80,
                            alignment=ft.alignment.Alignment.CENTER,
                        ),
                        ft.Container(
                            ft.IconButton(
                                ft.Icons.PLAY_CIRCLE,
                                icon_color="#5DADE2",
                                icon_size=24,
                                on_click=lambda e, tid=track.get('item_id'): self.play_track(tid),
                            ),
                            width=40,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                height=50,
                bgcolor="#181818" if i % 2 == 0 else "#1a1a1a",
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=10),
            )
            self.tracks_column.controls.append(row)
    
    def format_duration(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m}:{s:02d}"
    
    def play_track(self, track_id):
        if self.play_callback:
            if asyncio.iscoroutinefunction(self.play_callback):
                asyncio.create_task(self.play_callback(track_id))
            else:
                self.play_callback(track_id)