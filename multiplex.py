import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QSlider,
    QPushButton, QLabel, QFileDialog
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QUrl


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
        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)

        # layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        layout.addWidget(self.video_widget, stretch=1)

        # scrub bar
        self.scrubber = QSlider(Qt.Horizontal)
        self.scrubber.setRange(0, 0)
        layout.addWidget(self.scrubber)

        # Controls row
        controls = QHBoxLayout()
        layout.addLayout(controls)

        self.btn_open = QPushButton("Open File")
        self.btn_play = QPushButton("Play")
        self.btn_stop = QPushButton("Stop")
        self.lbl_time = QLabel("0:00 / 0:00")

        controls.addWidget(self.btn_open)
        controls.addWidget(self.btn_play)
        controls.addWidget(self.btn_stop)
        controls.addStretch()
        controls.addWidget(self.lbl_time)

        # -----Signals-----

        # Buttons
        self.btn_open.clicked.connect(self.open_file)
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_stop.clicked.connect(self.player.stop)

        # state changes
        self.player.playbackStateChanged.connect(self.on_state_changed)

        # position changes
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)

        # scrubber drag
        self.scrubber.sliderMoved.connect(self.player.setPosition)

        # source is a URI passed in the command line
        if source:
            self.load(source)

    
    # Helpers
    def load(self, source: str):
        """Accept either a local file path or a URI string"""
        if source.startswith(("http://", "https://", "rtsp://", "trmp://")):
            url = QUrl(source)
        else:
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
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Video",
            filter="Video Files (*.mp4 *.mkv *.avi *.mov *.m3u8 *.ts);;All Files (*)"
        )
        if path:
            self.load(path)


    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()


    def on_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_play.setText("Pause")
        else:
            self.btn_play.setText("Play")


    def on_position_changed(self, position_ms: int):
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
        self.scrubber.setRange(0, duration_ms)


def main():
    logger.info("Doin stuff!")

    # application instance
    app = QApplication(sys.argv)
    source = sys.argv[1] if len(sys.argv) > 1 else None

    # create window
    window = SimplePlayer(source)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()