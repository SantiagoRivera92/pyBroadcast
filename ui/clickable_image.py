# ui/clickable_image_flet.py
import flet as ft

class ClickableImage(ft.Container):
    def __init__(self, callback, item_id, width=160, height=160):
        super().__init__(
            width=width,
            height=height,
            bgcolor="#282828",
            border_radius=8,
            on_click=lambda e: callback(item_id),
            content=ft.Image(
                fit="cover",
                border_radius=8,
            ),
        )