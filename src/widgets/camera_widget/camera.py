import constants
import thread_classes
import json

from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QWidget, QHBoxLayout


class CameraWidget(QWidget):
    """
    A widget to display a camera feed using QWebEngineView.

    Inherits
    -------
    `QWidget`

    Attributes
    ----------
    web_view : `QWebEngineView`
        The web view used to display the camera feed.
    """

    def __init__(self) -> None:
        super().__init__()
        self.web_view = QWebEngineView()
        self.web_view.setHtml(constants.HTML_CAMERA)

        layout = QHBoxLayout()
        layout.addWidget(self.web_view)
        self.setLayout(layout)

        self.image_fetcher = thread_classes.ImageFetcher()
        self.image_fetcher.image_fetched.connect(self.update_camera_feed)

        self.timer = constants.SUPER_SLOW_TIMER
        self.timer.timeout.connect(self.image_fetcher.get_image)
        self.timer.start()

    def update_camera_feed_starter(self) -> None:
        """Start the image fetcher thread to update the camera feed if it is not already running."""

        if not self.image_fetcher.isRunning():
            self.image_fetcher.start()

    def update_camera_feed(self, base64_encoded_image: str) -> None:
        """
        Update the camera feed with a new image.

        Parameters
        ----------
        base64_encoded_image
            The base64 encoded string of the image to display.
        """

        js_image_str = json.dumps(base64_encoded_image)

        self.web_view.page().runJavaScript(f"setBase64Image({js_image_str});")
