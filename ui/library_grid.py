from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QScrollArea, QGridLayout, QWidget, QVBoxLayout, QLabel
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtCore import QUrl, Qt, QTimer, QRect

from ui.clickable_image import ClickableImage

class LibraryGrid(QScrollArea):
    def __init__(self, item_click_callback):
        super().__init__()
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { border: none; background-color: #121212; }")
        self.container = QWidget()
        self.container.setStyleSheet("background-color: #121212;")
        self.grid = QGridLayout(self.container)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setWidget(self.container)
        
        self.callback = item_click_callback
        self.network_manager = QNetworkAccessManager()
        
        # Priority Loading State
        self.pending_items = [] # List of (label, url)
        self.active_requests = 0
        self.max_concurrent = 4 # Adjust based on your connection speed
        
        # Debounce timer for scroll events
        self.load_timer = QTimer()
        self.load_timer.setSingleShot(True)
        self.load_timer.timeout.connect(self.process_queue)
        
        # Connect to scrollbar movement
        self.verticalScrollBar().valueChanged.connect(lambda: self.load_timer.start(200))

    def clear(self):
        self.pending_items.clear()
        for i in reversed(range(self.grid.count())): 
            item = self.grid.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

    def add_item(self, title, subtitle, image_url, item_id, row, col):
        item_widget = QWidget()
        layout = QVBoxLayout(item_widget)
        
        img_label = ClickableImage(self.callback, item_id)
        img_label.setFixedSize(160, 160)
        img_label.setStyleSheet("background-color: #282828; border-radius: 8px;")
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add to queue instead of starting immediately
        if image_url:
            self.pending_items.append({'label': img_label, 'url': image_url, 'started': False})

        t_label = QLabel(title)
        t_label.setStyleSheet("color: white; font-weight: bold; margin-top: 5px;")
        t_label.setWordWrap(True)
        t_label.setFixedWidth(160)
        
        layout.addWidget(img_label)
        layout.addWidget(t_label)
        layout.addWidget(QLabel(subtitle, styleSheet="color: #b3b3b3; font-size: 12px;"))
        self.grid.addWidget(item_widget, row, col)
        
        # Trigger an initial check
        self.load_timer.start(100)

    def is_visible(self, widget):
        """Check if the widget is within the visible area of the scroll area"""
        visible_region = self.viewport().rect()
        # Map widget coordinates to the viewport
        widget_rect = widget.mapTo(self.viewport(), widget.rect().topLeft())
        return visible_region.intersects(QRect(widget_rect, widget.size()))

    def process_queue(self):
        """Sorts the queue by visibility and starts downloads"""
        if not self.pending_items:
            return

        # Separate on-screen and off-screen
        on_screen = []
        off_screen = []

        for item in self.pending_items:
            if item['started']: continue
            
            try:
                if self.is_visible(item['label']):
                    on_screen.append(item)
                else:
                    off_screen.append(item)
            except RuntimeError:
                continue # Widget was deleted

        # Priority 1: Start on-screen items
        for item in on_screen:
            if self.active_requests < self.max_concurrent:
                self.start_download(item)
        
        # Priority 2: Only start off-screen if all on-screen are ALREADY finished
        # and we still have capacity. (Based on your prompt: "Only load off-screen 
        # when every image on screen has finished loading")
        if not on_screen and self.active_requests == 0:
            for item in off_screen:
                if self.active_requests < self.max_concurrent:
                    self.start_download(item)

    def start_download(self, item):
        item['started'] = True
        self.active_requests += 1
        request = QNetworkRequest(QUrl(item['url']))
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda r=reply, lbl=item['label']: self.on_finished(lbl, r))

    def on_finished(self, label, reply):
        self.active_requests -= 1
        self.set_image(label, reply)
        # Check queue again to see if we can start next items
        self.process_queue()

    def set_image(self, label, reply):
        try:
            if not label or reply.error() != reply.NetworkError.NoError:
                return
            
            data = reply.readAll()
            img = QImage()
            if img.loadFromData(data):
                pixmap = QPixmap.fromImage(img)
                if not pixmap.isNull():
                    label.setPixmap(pixmap.scaled(
                        160, 160, 
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                        Qt.TransformationMode.SmoothTransformation
                    ))
        except RuntimeError:
            pass
        finally:
            reply.deleteLater()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.load_timer.start(200)