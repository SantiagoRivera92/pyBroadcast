from PyQt6.QtWidgets import QFrame
from PyQt6.QtCore import Qt

class HoverableWidget(QFrame):
    def __init__(self, callback, item_id):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setStyleSheet('''
            QWidget {
                border-radius: 12px;
            }
        ''')
        self.callback = callback
        self.item_id = item_id
        self._hover = False
        self._active = False
        
            
    def enterEvent(self, event):
        self._hover = True
        self.update_style()
        super().enterEvent(event)
        
    def leaveEvent(self, a0):
        self._hover = False
        self._active = False
        self.update_style()
        super().leaveEvent(a0)
        
    def mousePressEvent(self, a0):
        self._active = True
        self.update_style()
        super().mousePressEvent(a0)
        
    def mouseReleaseEvent(self, a0):
        self._active = False
        self.update_style()
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self.callback(self.item_id)
        super().mouseReleaseEvent(a0)
        
    def update_style(self):
        if self._active:
            self.setStyleSheet('''
                background: #1a1a1a;
                border-radius: 12px;
            ''')
        elif self._hover:
            self.setStyleSheet('''
                background: #313a4d;
                border-radius: 12px;
            ''')
        else:
            self.setStyleSheet('''
                background: none;
                border-radius: 12px;
            ''')