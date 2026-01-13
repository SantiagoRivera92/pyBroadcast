from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, pyqtSignal

class ArtistLinksLabel(QLabel):
    artistClicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setOpenExternalLinks(False)
        self.linkActivated.connect(self.on_link_activated)
        self.setStyleSheet("""
            QLabel {
                color: #b3b3b3;
                font-size: 13px;
                background: transparent;
                border: none;
                padding: 0;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_artists(self, artists):
        if not artists:
            self.setText("")
            return
            
        links = []
        for artist in artists:
            # We use a custom scheme or just the ID in the href
            links.append(f'<a href="{artist.id}" style="color: #b3b3b3; text-decoration: none;">{artist.name}</a>')
        
        self.setText(", ".join(links))

    def on_link_activated(self, link):
        self.artistClicked.emit(link)

    def enterEvent(self, event):
        # We don't want to underline the whole label on hover, 
        # but QLabel's RichText doesn't easily support per-link hover in CSS
        # without complex event handling or WebEngine.
        # However, we can use a hover style that applies to links if they were <span>ed, 
        # but simpler is just letting the cursor indicate clickability.
        super().enterEvent(event)
