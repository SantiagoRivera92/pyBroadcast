from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

class RoundedImage(QLabel):
    def __init__(self):
        super().__init__()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet('''
            QLabel {
                border-radius: 12px;
            }
        ''')

    def setPixmap(self, a0):
        if a0 is not None and not a0.isNull():
            width = self.width() if self.width() > 0 else a0.width()
            height = self.height() if self.height() > 0 else a0.height()
            radius = min(width, height) // 6  # 1/6th of the smallest dimension for a nice roundness
            rounded = QPixmap(width, height)
            rounded.fill(Qt.GlobalColor.transparent)
            from PyQt6.QtGui import QPainter, QPainterPath
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, width, height, radius, radius)
            painter.setClipPath(path)
            scaled = a0.scaled(
                width, height,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled)
            painter.end()
            super().setPixmap(rounded)
        else:
            super().setPixmap(a0)
