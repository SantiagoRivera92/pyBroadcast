from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import QTimer, Qt, QPropertyAnimation, QRect
from PyQt6.QtGui import QPainter, QFontMetrics

class ScrollingLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.full_text = ""
        self.scroll_offset = 0
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self.scroll_text)
        self.scroll_speed = 30  # milliseconds between scroll updates
        self.wait_time = 2000  # Wait before starting scroll
        self.wait_timer = QTimer(self)
        self.wait_timer.timeout.connect(self.start_scrolling)
        self.is_scrolling = False
        self.needs_scroll = False
        
    def setText(self, a0):
        self.full_text =a0
        super().setText(a0)
        self.scroll_offset = 0
        self.stop_scrolling()
        self.check_if_needs_scroll()
        
    def check_if_needs_scroll(self):
        """Check if text is too long and needs scrolling"""
        if not self.full_text:
            self.needs_scroll = False
            return
            
        fm = QFontMetrics(self.font())
        text_width = fm.horizontalAdvance(self.full_text)
        available_width = self.width()
        
        self.needs_scroll = text_width > available_width
        
        if self.needs_scroll:
            # Wait before starting to scroll
            self.wait_timer.start(self.wait_time)
        else:
            super().setText(self.full_text)
    
    def start_scrolling(self):
        """Start the scrolling animation"""
        self.wait_timer.stop()
        if self.needs_scroll:
            self.is_scrolling = True
            self.scroll_timer.start(self.scroll_speed)
    
    def stop_scrolling(self):
        """Stop scrolling animation"""
        self.is_scrolling = False
        self.scroll_timer.stop()
        self.wait_timer.stop()
        self.scroll_offset = 0
        self.update()
    
    def scroll_text(self):
        """Update scroll position"""
        if not self.needs_scroll:
            return
            
        fm = QFontMetrics(self.font())
        text_width = fm.horizontalAdvance(self.full_text)
        
        # Scroll by 1 pixel
        self.scroll_offset += 1
        
        # Reset when we've scrolled past the text
        # Add some padding before looping
        if self.scroll_offset > text_width + 50:
            self.scroll_offset = -self.width()
        
        self.update()
    
    def paintEvent(self, a0):
        """Custom paint to draw scrolling text"""
        if not self.needs_scroll or not self.is_scrolling:
            super().paintEvent(a0)
            return
        
        painter = QPainter(self)
        painter.setPen(self.palette().color(self.foregroundRole()))
        painter.setFont(self.font())
        
        # Draw the text at the offset position
        x = -self.scroll_offset
        y = self.height() // 2 + painter.fontMetrics().ascent() // 2
        
        painter.drawText(x, y, self.full_text)
        
        # Draw another copy for seamless loop
        text_width = painter.fontMetrics().horizontalAdvance(self.full_text)
        painter.drawText(x + text_width + 50, y, self.full_text)
        
        painter.end()
    
    def resizeEvent(self, a0):
        """Recheck if scrolling is needed when widget is resized"""
        super().resizeEvent(a0)
        if self.full_text:
            self.stop_scrolling()
            self.check_if_needs_scroll()
    
    def enterEvent(self, event):
        """Start scrolling on hover"""
        super().enterEvent(event)
        if self.needs_scroll and not self.is_scrolling:
            self.wait_timer.start(self.wait_time)
    
    def leaveEvent(self, a0):
        """Stop scrolling when mouse leaves"""
        super().leaveEvent(a0)
        if self.is_scrolling:
            self.stop_scrolling()
            if self.needs_scroll:
                # Show beginning of text
                super().setText(self.full_text)