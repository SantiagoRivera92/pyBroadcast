from PyQt6.QtWidgets import QFrame
from PyQt6.QtCore import Qt

class HoverableWidget(QFrame):
    def __init__(self, callback, item_id):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.callback = callback
        self.item_id = item_id
        self._hover = False
        self._active = False
        self.update_style()
        
    def enterEvent(self, event):
        self._hover = True
        super().enterEvent(event)
        
    def leaveEvent(self, a0):
        self._hover = False
        self._active = False
        super().leaveEvent(a0)
        
    def mousePressEvent(self, a0):
        self._active = True
        super().mousePressEvent(a0)
        
    def mouseReleaseEvent(self, a0):
        self._active = False
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self.callback(self.item_id)
        super().mouseReleaseEvent(a0)
        
    def update_style(self):
        # We define the hover and pressed states using CSS pseudo-classes
        # This allows subclasses to define their own background/border which won't be wiped
        self.setStyleSheet('''
            HoverableWidget {
                border-radius: 12px;
                background: transparent;
            }
            HoverableWidget:hover {
                background: rgba(255, 255, 255, 0.08);
            }
            HoverableWidget:pressed {
                background: rgba(255, 255, 255, 0.12);
            }
            /* Ensure child labels (like those in LibraryGrid) are transparent to show parent background */
            HoverableWidget QLabel {
                background: transparent;
            }
        ''')