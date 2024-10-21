import sys
import threading
import re

import emoji
import pytchat
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextBrowser
from PySide6.QtGui import QTextCursor, QImage, QTextDocument

# New emoji dictionary mapping to image paths
NEW_EMOJI_DICT = {
    ":thanksdoc:": "./emojis/thanksdoc.png",
    ":washhands:": "./emojis/washhands.png",
    ":elbowcough:": "./emojis/elbowcough.png",
    ":hand-pink-waving:": "./emojis/hand-pink-waving.png",
    ":smiling_face_with_tear:": "./emojis/smiling_face_with_tear.png",
    # Add more custom emoji mappings here
}

def convert_text_to_emoji(text, document):
    # First, apply standard emoji conversion
    converted_text = emoji.emojize(text, language='alias')

    # Then, replace custom emoji aliases with HTML img tags
    for alias, img_path in NEW_EMOJI_DICT.items():
        img_html = f'<img src="{img_path}" height="20" />'
        converted_text = converted_text.replace(alias, img_html)

    # Log to console if there are still unconverted emoji aliases
    remaining_aliases = re.findall(r':[a-zA-Z0-9_+-]+:', converted_text)
    if remaining_aliases:
        print(f"Unconverted emoji aliases found: {', '.join(remaining_aliases)} in the text: {text}")

    return converted_text

class DraggableTextBrowser(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setOpenExternalLinks(False)
        self.setOpenLinks(False)

class TransparentWindow(QWidget):
    def __init__(self, video_id):
        super().__init__()
        self.video_id = video_id
        self.chat_messages = []
        self.max_messages = 10  # Maximum number of messages to display
        self.initUI()
        self.initChat()
        self.oldPos = None

    def initUI(self):
        self.setWindowTitle('YouTube Live Chat Viewer')
        self.setGeometry(100, 100, 400, 300)

        # Make window frameless and transparent
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout()

        # Transparent QTextBrowser
        self.chat_display = DraggableTextBrowser(self)
        self.chat_display.setStyleSheet("""
            QTextBrowser {
                background-color: rgba(0, 0, 0, 0);  /* Fully transparent */
                color: white;
                border: none;
                font-family: 'CaskaydiaCove Nerd Font', Arial, sans-serif;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.chat_display)

        self.setLayout(layout)

        # Install event filter
        self.installEventFilter(self)

    def initChat(self):
        self.chat = pytchat.create(video_id=self.video_id)
        self.chat_thread = threading.Thread(target=self.fetchChat)
        self.chat_thread.daemon = True
        self.chat_thread.start()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateUI)
        self.timer.start(100)

    def fetchChat(self):
        while self.chat.is_alive():
            for c in self.chat.get().sync_items():
                converted_message = convert_text_to_emoji(c.message, self.chat_display.document())
                self.chat_messages.append((c.author.name, converted_message))
                if len(self.chat_messages) > self.max_messages:
                    self.chat_messages.pop(0)

    def updateUI(self):
        self.chat_display.clear()
        for author, message in self.chat_messages:
            self.chat_display.append(f'<span style="color: gold;">{author}:</span> {message}')

        # Move cursor to the end to show the latest messages
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_display.setTextCursor(cursor)

    def eventFilter(self, obj, event):
        if obj is self:
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.oldPos = event.globalPosition().toPoint()
            elif event.type() == QEvent.Type.MouseMove:
                if event.buttons() & Qt.MouseButton.LeftButton:
                    delta = event.globalPosition().toPoint() - self.oldPos
                    self.move(self.pos() + delta)
                    self.oldPos = event.globalPosition().toPoint()
        return super().eventFilter(obj, event)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python app.py <live youtube video id>")
        sys.exit(1)

    video_id = sys.argv[1]
    app = QApplication(sys.argv)
    window = TransparentWindow(video_id)
    window.show()
    sys.exit(app.exec())