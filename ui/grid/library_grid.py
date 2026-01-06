from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QScrollArea, QGridLayout, QWidget, QVBoxLayout, QFrame
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtCore import QUrl, Qt, QTimer, QRect

from ui.utils.rounded_image import RoundedImage
from ui.utils.hoverable_widget import HoverableWidget
from ui.utils.scrolling_label import ScrollingLabel

class LibraryGrid(QScrollArea):
    def __init__(self, item_click_callback):
        super().__init__()
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { border: none; background-color: #0f0f0f; }")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.container = QWidget()
        self.container.setStyleSheet("background-color: #0f0f0f;")
        self.grid = QGridLayout(self.container)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid.setSpacing(10)
        self.grid.setContentsMargins(10, 10, 10, 10)
        
        
        self.setWidget(self.container)
        
        self.callback = item_click_callback
        self.network_manager = QNetworkAccessManager()
        
        # Item dimensions for column calculation
        self.item_width = 180
        self.item_spacing = 10
        self.margin = 20
        
        # Priority Loading State
        self.pending_items = [] # List of (label, url)
        self.active_requests = 0
        self.max_concurrent = 4
        
        # Queue for items to add
        self.items_queue = []
        self.current_row = 0
        self.current_col = 0
        self.columns = 5 
        
        # Debounce timer for scroll events
        self.load_timer = QTimer()
        self.load_timer.setSingleShot(True)
        self.load_timer.timeout.connect(self.process_queue)
        
        # Connect to scrollbar movement if verticalScrollBar exists
        v_scrollbar = self.verticalScrollBar()
        if v_scrollbar is not None:
            v_scrollbar.valueChanged.connect(lambda: self.load_timer.start(200))

    def calculate_columns(self):
        """Calculate how many columns can fit in the current width"""
        viewport = self.viewport()
        if viewport is None:
            available_width = 0
        else:
            available_width = viewport.width() - (2 * self.margin)
        cols = max(1, available_width // (self.item_width + self.item_spacing))
        return cols

    def clear(self):
        self.pending_items.clear()
        self.items_queue.clear()
        self.current_row = 0
        self.current_col = 0
        for i in reversed(range(self.grid.count())): 
            item = self.grid.itemAt(i)
            if item:
                item_widget = item.widget()
                if item_widget:
                    item_widget.deleteLater()

    def add_item(self, title, subtitle, image_url, item_id, row=None, col=None):
        """Add item to grid. If row/col are None, auto-calculate based on current position"""
        # Queue the item for processing
        self.items_queue.append({
            'title': title,
            'subtitle': subtitle,
            'image_url': image_url,
            'item_id': item_id
        })
        
        # Process queue on next event loop
        QTimer.singleShot(0, self.process_items_queue)

    def process_items_queue(self):
        """Process queued items and add them to the grid"""
        if not self.items_queue:
            return
        
        # Recalculate columns based on current width
        self.columns = self.calculate_columns()
        
        # Add all queued items
        while self.items_queue:
            item_data = self.items_queue.pop(0)
            self._add_item_to_grid(
                item_data['title'],
                item_data['subtitle'],
                item_data['image_url'],
                item_data['item_id']
            )

    def _add_item_to_grid(self, title, subtitle, image_url, item_id):
        """Internal method to add item to grid at current position"""
        item_widget = HoverableWidget(self.callback, item_id)
        layout = QVBoxLayout(item_widget)

        img_label = RoundedImage()
        img_label.setFixedSize(self.item_width, self.item_width)
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add to queue instead of starting immediately
        if image_url:
            self.pending_items.append({'label': img_label, 'url': image_url, 'started': False})
        
        t_label = ScrollingLabel(item_widget)
        t_label.setText(title)
        t_label.setGap(25)
        t_label.setStyleSheet('''
            QLabel {
                color: white;
                font-weight: bold;
                margin-top: 5px;
                font-size: 18px;
            }
        ''')
        t_label.setWordWrap(True)
        t_label.setFixedWidth(self.item_width + 2)
        t_label.setFixedHeight(28)

        s_label = ScrollingLabel(item_widget)
        s_label.setText(subtitle)
        s_label.setGap(25)
        s_label.setStyleSheet('''
            QLabel {
                color: #b3b3b3;
                font-size: 14px;
                margin-left: 2px;
            }
        ''')
        s_label.setWordWrap(True)
        s_label.setFixedWidth(self.item_width + 2)

        layout.addWidget(img_label)
        layout.addWidget(t_label)
        layout.addWidget(s_label)
        
        # Add to grid at current position
        self.grid.addWidget(item_widget, self.current_row, self.current_col)
        
        # Update position for next item
        self.current_col += 1
        if self.current_col >= self.columns:
            self.current_col = 0
            self.current_row += 1
        
        # Trigger an initial check
        self.load_timer.start(100)

    def is_visible(self, widget):
        """Check if the widget is within the visible area of the scroll area"""
        try:
            viewport = self.viewport()
            if viewport is not None:        
                visible_region = viewport.rect()
                widget_rect = widget.mapTo(viewport, widget.rect().topLeft())
                return visible_region.intersects(QRect(widget_rect, widget.size()))
            return False
        except RuntimeError:
            return False

    def process_queue(self):
        """Sorts the queue by visibility and starts downloads"""
        if not self.pending_items:
            return

        # Separate on-screen and off-screen
        on_screen = []
        off_screen = []

        for item in self.pending_items:
            if item['started']: 
                continue
            
            try:
                if self.is_visible(item['label']):
                    on_screen.append(item)
                else:
                    off_screen.append(item)
            except RuntimeError:
                continue

        # Priority 1: Start on-screen items
        for item in on_screen:
            if self.active_requests < self.max_concurrent:
                self.start_download(item)
        
        # Priority 2: Only start off-screen if all on-screen are finished
        if not on_screen and self.active_requests == 0:
            for item in off_screen:
                if self.active_requests < self.max_concurrent:
                    self.start_download(item)

    def start_download(self, item):
        item['started'] = True
        self.active_requests += 1
        request = QNetworkRequest(QUrl(item['url']))
        reply = self.network_manager.get(request)
        if reply is not None:
            reply.finished.connect(lambda r=reply, lbl=item['label']: self.on_finished(lbl, r))

    def on_finished(self, label, reply):
        self.active_requests -= 1
        self.set_image(label, reply)
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
                        self.item_width, self.item_width, 
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                        Qt.TransformationMode.SmoothTransformation
                    ))
        except RuntimeError:
            pass
        finally:
            reply.deleteLater()

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        # Recalculate layout when window is resized
        new_columns = self.calculate_columns()
        if new_columns != self.columns and self.grid.count() > 0:
            self.columns = new_columns
            # Re-layout existing items
            self._relayout_items()
        self.load_timer.start(200)
    
    def _relayout_items(self):
        """Re-arrange grid items when column count changes"""
        items = []
        for i in range(self.grid.count()):
            item = self.grid.itemAt(i)
            if item and item.widget():
                items.append(item.widget())
        
        # Remove all items from grid (but don't delete them)
        for item in items:
            self.grid.removeWidget(item)
        
        # Re-add items with new layout
        for i, widget in enumerate(items):
            row = i // self.columns
            col = i % self.columns
            self.grid.addWidget(widget, row, col)
        
        # Update current position
        if items:
            self.current_row = (len(items) - 1) // self.columns
            self.current_col = (len(items) - 1) % self.columns + 1
            if self.current_col >= self.columns:
                self.current_col = 0
                self.current_row += 1
