from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWidgets import QBoxLayout
from PyQt6.QtCore import Qt, pyqtSlot, QObject

from typing import Optional

from src.api.ibroadcast.models import Artist

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
        self.artist_layout: Optional[QBoxLayout] = None
        self.artists: list[Artist] = []
        self.onArtistClickedCallback = callback
        if callback:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.link_handler = LinkHandler(callback)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        # Set up web channel for communication between JS and Python
        self.channel = QWebChannel()
        self.channel.registerObject("handler", self.link_handler)
        page = self.page()
        if page:
            page.setWebChannel(self.channel)
            page.setBackgroundColor(Qt.GlobalColor.transparent)
        
        # Make background transparent
        self.setStyleSheet("background: transparent;")

            
    def setArtists(self, artists: list[Artist]):
        """Set multiple artists as clickable links with CSS scrolling"""
        if not artists:
            self.setHtml("")
            self.needs_scroll = False
            return
        
        self.artists = artists
        
        # Build artist links
        links = []
        for artist in artists:
            # Use data attribute instead of href to avoid navigation
            link = f'<a href="#" data-artist-id="{artist.id}">{artist.name}</a>'
            links.append(link)
        artist_text = ", ".join(links)
        
        # Check if we need scrolling
        self.check_if_text_needs_scroll(artist_text)
        
        if self.needs_scroll:
            # Use CSS animation for scrolling
            html = f'''
            <!DOCTYPE html>
            <html>
            <head>
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: inherit;
                    overflow: hidden;
                    background: transparent;
                    color: white;
                }}
                .container {{
                    white-space: nowrap;
                    display: inline-block;
                }}
                .scroll-container {{
                    display: inline-block;
                    animation: scroll 15s ease-in-out infinite;
                }}
                .scroll-container:hover {{
                    animation-play-state: paused;
                }}
                @keyframes scroll {{
                    0%, 10% {{ 
                        transform: translateX(0); 
                    }}
                    45%, 55% {{ 
                        transform: translateX(calc(-100% + {self.width() - 20}px)); 
                    }}
                    90%, 100% {{ 
                        transform: translateX(0); 
                    }}
                }}
                a {{
                    color: #ffffff;
                    text-decoration: none;
                    cursor: pointer;
                }}
                a:visited {{
                    color: #ffffff;
                }}
                a:hover {{
                    text-decoration: underline;
                    color: #ffffff;
                }}
            </style>
            </head>
            <body>
                <div class="container">
                    <div class="scroll-container">{artist_text}</div>
                </div>
                <script>
                    new QWebChannel(qt.webChannelTransport, function(channel) {{
                        var handler = channel.objects.handler;
                        
                        document.addEventListener('click', function(e) {{
                            if (e.target.tagName === 'A') {{
                                e.preventDefault();
                                var artistId = e.target.getAttribute('data-artist-id');
                                if (artistId && handler) {{
                                    console.log('Clicked artist:', artistId);
                                    handler.handleClick(artistId);
                                }}
                            }}
                        }});
                    }});
                </script>
            </body>
            </html>
            '''
        else:
            # No scrolling needed, just display normally
            html = f'''
            <!DOCTYPE html>
            <html>
            <head>
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: inherit;
                    background: transparent;
                    color: white;
                }}
                a {{
                    color: #ffffff;
                    text-decoration: none;
                    cursor: pointer;
                }}
                a:visited {{
                    color: #ffffff;
                }}
                a:hover {{
                    text-decoration: underline;
                    color: #ffffff;
                }}
            </style>
            </head>
            <body>{artist_text}
                <script>
                    new QWebChannel(qt.webChannelTransport, function(channel) {{
                        var handler = channel.objects.handler;
                        
                        document.addEventListener('click', function(e) {{
                            if (e.target.tagName === 'A') {{
                                e.preventDefault();
                                var artistId = e.target.getAttribute('data-artist-id');
                                if (artistId && handler) {{
                                    console.log('Clicked artist:', artistId);
                                    handler.handleClick(artistId);
                                }}
                            }}
                        }});
                    }});
                </script>
            </body>
            </html>
            '''
        
        self.setHtml(html)

    def setGap(self, gap):
        self.gap = gap
        
    def setText(self, text):
        """For backwards compatibility"""
        self.full_text = text
        self.setHtml(text)
        
    def check_if_text_needs_scroll(self, text):
        """Check if text is too long and needs scrolling"""
        if not text:
            self.needs_scroll = False
            return
        
        # Strip HTML tags to measure actual text width
        from PyQt6.QtGui import QTextDocument
        doc = QTextDocument()
        doc.setHtml(text)
        doc.setDefaultFont(self.font())
        
        text_width = doc.idealWidth()
        available_width = self.width() - 20  # Account for padding
        self.needs_scroll = text_width > available_width
    
    def resizeEvent(self, a0):
        """Recheck if scrolling is needed when widget is resized"""
        super().resizeEvent(a0)
        if self.artists:
            self.setArtists(self.artists)