from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

class ClickableImage(QLabel):
    def __init__(self, callback, item_id):
        super().__init__()
        self.callback = callback
        self.item_id = item_id
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, ev):
        self.callback(self.item_id)