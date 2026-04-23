import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

import os
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QSlider,
    QPushButton, QLabel, QFileDialog,
    QMenu, QDialog, QDialogButtonBox
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QAction


class ComplainDialog(QDialog):
    def __init__(self, message):
        super().__init__()

        self.setWindowTitle("Oops!")

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)

        layout = QVBoxLayout()
        message_label = QLabel(message)
        layout.addWidget(message_label)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
    

class ClickableVideoWidget(QVideoWidget):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class SimplePlayer(QMainWindow):
    def __init__(self, source: str = None):
        super().__init__()

        # the window
        self.setWindowTitle("Get wrecked, plonker!")
        self.resize(960, 600)

        # core media objects
        self.player = QMediaPlayer()

        # audio layer of the media widget
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)
        self.audio.setVolume(0.8)

        # video layer of the media widget
        self.video_widget = ClickableVideoWidget()
        self.player.setVideoOutput(self.video_widget)

        # layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        layout.addWidget(self.video_widget, stretch=1)

        # Controls row
        controls = QHBoxLayout()
        layout.addLayout(controls)

        # scrub bar
        self.scrubber = QSlider(Qt.Horizontal)
        self.scrubber.setRange(0, 0)
        controls.addWidget(self.scrubber)

        self.lbl_time = QLabel("0:00 / 0:00")
        controls.addWidget(self.lbl_time)

        # -----Signals-----

        # Player window
        self.video_widget.clicked.connect(self.toggle_play)

        # position changes
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)

        # scrubber drag
        self.scrubber.sliderMoved.connect(self.player.setPosition)

        # source is a URI passed in the command line
        if source:
            self.load(source)


    def contextMenuEvent(self, e):
        open_file_action = QAction("Open File", self)
        open_file_action.triggered.connect(self.open_file)
        open_url_action = QAction("Open URL", self)
        open_url_action.triggered.connect(self.open_url)

        context = QMenu(self)
        context.addAction(open_file_action)
        context.addAction(open_url_action)
        context.exec(e.globalPos())
    

    # Helpers
    def complain(self, message):
        dlg = ComplainDialog(message)
        dlg.exec()


    def load(self, source: str):
        """Accept either a local file path or a URI string"""
        if source.startswith(("http://", "https://", "rtsp://", "trmp://")):
            url = QUrl(source)
        else:
            if not os.path.exists(source):
                self.complain(f"The file '{source}' does not seem to exist.")
                return
            
            url = QUrl.fromLocalFile(source)
        
        self.player.setSource(url)
        self.player.play()


    @staticmethod
    def format_time(ms: int) -> str:
        s = ms // 1000
        m, s = divmod(s, 60)
        return f"{m}:{s:02d}"
    
    
    # Slots
    def open_file(self):
        """this one's for local video files on your machine"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Video",
            filter="Video Files (*.mp4 *.mkv *.avi *.mov *.m3u8 *.ts);;All Files (*)"
        )
        if path:
            self.load(path)


    def open_url(self):
        """this one's for digging a .m3u8 stream out of a webpage"""
        pass


    def toggle_play(self):
        """activated when left-clicking on the video surface"""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()


    def on_position_changed(self, position_ms: int):
        """activated when sliding the scrubber"""

        # blocks signals while we move the slider because 
        # apparently all this stuff is stupid and makes infinite loops
        self.scrubber.blockSignals(True)
        self.scrubber.setValue(position_ms)
        self.scrubber.blockSignals(False)

        duration_ms = self.player.duration()

        self.lbl_time.setText(
            f"{self.format_time(position_ms)} / {self.format_time(duration_ms)}"
        )


    def on_duration_changed(self, duration_ms: int):
        """likely called only when stream source changes"""
        self.scrubber.setRange(0, duration_ms)


def main():
    logger.info("Starting the multiplex")

    # application instance
    app = QApplication(sys.argv)
    source = sys.argv[1] if len(sys.argv) > 1 else None

    # create window
    window = SimplePlayer(source)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()