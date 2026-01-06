import flet as ft

class LibraryGrid(ft.GridView):
    def __init__(self, item_click_callback):
        super().__init__(
            expand=True,
            runs_count=5,
            max_extent=200,
            child_aspect_ratio=0.8,
            spacing=15,
            run_spacing=15,
            padding=40,
        )
        self.callback = item_click_callback
        self.pending_images = {}
        self.loading_queue = []
        self.max_concurrent = 4
        self.active_requests = 0
    
    def clear(self):
        self.controls.clear()
        self.pending_images.clear()
        self.loading_queue.clear()
    
    def add_item(self, title, subtitle, image_url, item_id, row, col):
        # Create image container
        img_container = ft.Container(
            width=160,
            height=160,
            bgcolor="#282828",
            border_radius=8,
            alignment=ft.alignment.Alignment.CENTER,
            on_click=lambda e, item_id=item_id: self.callback(item_id),
        )
        
        # Add image if URL provided
        if image_url:
            img = ft.Image(
                src=image_url,
                border_radius=8,
                visible=True,
            )
            img_container.content = img
            # Store reference for potential future use
            self.pending_images[len(self.controls)] = {
                'container': img_container,
                'image': img,
                'url': image_url,
                'loaded': False,
            }
        
        # Create text labels
        title_text = ft.Text(
            title,
            color="white",
            weight=ft.FontWeight.BOLD,
            width=160,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        
        subtitle_text = ft.Text(
            subtitle,
            color="#b3b3b3",
            size=12,
            width=160,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        
        # Create item card
        card = ft.Container(
            content=ft.Column(
                controls=[
                    img_container,
                    ft.Container(height=5),
                    title_text,
                    subtitle_text,
                ],
                spacing=2,
            ),
            width=180,
        )
        
        self.controls.append(card)
    
    def scroll_to_index(self, index):
        pass