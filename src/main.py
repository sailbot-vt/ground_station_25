import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QIcon

from widgets.groundstation import GroundStationWidget
from icons import get_icons
import constants


class MainWindow(QMainWindow):
    """
    Main window for the ground station application.

    Inherits
    -------
    `QMainWindow`
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SailBussy Ground Station")
        self.setGeometry(constants.WINDOW_BOX)
        self.main_widget = GroundStationWidget()
        self.setCentralWidget(self.main_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("SailBussy Ground Station")
    app.setStyle("Fusion")
    app_icon: QIcon = get_icons().boat
    app.setWindowIcon(app_icon)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
