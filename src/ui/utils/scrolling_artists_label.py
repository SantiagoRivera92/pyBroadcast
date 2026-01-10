import base64
import os
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import Qt, pyqtSlot, QObject
from PyQt6.QtGui import QFontDatabase, QTextDocument

class LinkHandler(QObject):
    """Handler for link clicks from JavaScript"""
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
    
    @pyqtSlot(str)
    def handleClick(self, artist_id):
        if self.callback:
            self.callback(artist_id)

class ScrollingArtistsLabel(QWebEngineView):
        
    def __init__(self, parent=None, callback=None):
        super().__init__(parent)
        self.full_text = ""
        self.needs_scroll = False
        self.gap = 50
        self.onArtistClickedCallback = callback
        self.artists = []
        self.font_family = "NataSans"
        self.font_base64 = ""
        
        # 1. Load font into Python and prepare Base64 for WebEngine
        font_path = "assets/font/NataSans.ttf"
        if os.path.exists(font_path):
            # Load for PyQt6 measurement
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    self.font_family = families[0]
            
            # Convert to Base64 for CSS
            with open(font_path, "rb") as f:
                self.font_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        # Set up web channel
        self.channel = QWebChannel()
        self.link_handler = LinkHandler(self.onArtistClickedCallback)
        self.channel.registerObject("handler", self.link_handler)
        page = self.page()
        if page:
            page.setWebChannel(self.channel)
            page.setBackgroundColor(Qt.GlobalColor.transparent)
        
        self.setStyleSheet("background: transparent;")
        
    def get_common_css(self):
        """Returns the shared CSS including the @font-face"""
        font_face = ""
        if self.font_base64:
            font_face = f'''
            @font-face {{
                font-family: '{self.font_family}';
                src: url(data:font/ttf;base64,{self.font_base64});
            }}
            '''
        
        return f'''
            {font_face}
            body {{
                margin: 0;
                padding: 0;
                font-family: '{self.font_family}', sans-serif;
                overflow: hidden;
                background: transparent;
                color: white;
                font-size: 13px; /* Adjust to match your UI */
            }}
            a {{
                color: #ffffff;
                text-decoration: none;
                cursor: pointer;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        '''

    def setArtists(self, artists):
        if not artists:
            self.setHtml("")
            return
        
        self.artists = artists
        links = [f'<a href="#" data-artist-id="{a.id}">{a.name}</a>' for a in artists]
        artist_text = ", ".join(links)
        
        self.check_if_text_needs_scroll(artist_text)
        
        # Animation logic
        animation_css = ""
        container_class = ""
        if self.needs_scroll:
            container_class = "scroll-container"
            animation_css = f'''
                .container {{ white-space: nowrap; display: inline-block; }}
                .scroll-container {{
                    display: inline-block;
                    animation: scroll 15s ease-in-out infinite;
                }}
                .scroll-container:hover {{ animation-play-state: paused; }}
                @keyframes scroll {{
                    0%, 10% {{ transform: translateX(0); }}
                    45%, 55% {{ transform: translateX(calc(-100% + {self.width() - 10}px)); }}
                    90%, 100% {{ transform: translateX(0); }}
                }}
            '''

        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <style>
                {self.get_common_css()}
                {animation_css}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="{container_class}">{artist_text}</div>
            </div>
            <script>
                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    window.handler = channel.objects.handler;
                }});
                
                document.addEventListener('click', function(e) {{
                    if (e.target.tagName === 'A') {{
                        e.preventDefault();
                        var id = e.target.getAttribute('data-artist-id');
                        if (id && window.handler) window.handler.handleClick(id);
                    }}
                }});
            </script>
        </body>
        </html>
        '''
        self.setHtml(html)

    def check_if_text_needs_scroll(self, text):
        if not text:
            self.needs_scroll = False
            return
        
        doc = QTextDocument()
        # Use the same font family and size as the CSS for measurement
        font = self.font()
        font.setFamily(self.font_family)
        doc.setDefaultFont(font)
        doc.setHtml(text)
        
        self.needs_scroll = doc.idealWidth() > (self.width() - 20)

    def setOnArtistClickedCallback(self, callback):
        self.link_handler.callback = callback
        self.setCursor(Qt.CursorShape.PointingHandCursor if callback else Qt.CursorShape.ArrowCursor)

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        if self.artists:
            self.setArtists(self.artists)