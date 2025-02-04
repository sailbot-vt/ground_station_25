import sys
from typing import Any

import requests
from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

RUN_WITH_SAILOR_STANDARDS = True
DEGREE_SIGN = u'\N{DEGREE SIGN}'
TELEMETRY_SERVER_URL = 'http://18.191.164.84:8080/'

class WayPointWidget(QWidget):
    def __init__(self, text, on_delete, on_edit):
        super().__init__()
        self.text = text

        # Main layout for the widget
        layout = QHBoxLayout()
        # left, top, right, bottom
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Delete button
        delete_button = QPushButton("-")
        delete_button.setFixedSize(25, 25)
        delete_button.clicked.connect(lambda: on_delete(self))
        layout.addWidget(delete_button)

        # Edit button
        edit_button = QPushButton("\u270E")
        edit_button.setFixedSize(25, 25)
        edit_button.clicked.connect(self._enable_edit)
        layout.addWidget(edit_button)

        # Up button
        up_button = QPushButton("\u2B81")
        up_button.setFixedSize(25, 25)
        layout.addWidget(up_button)

        # Down button
        down_button = QPushButton("\u2B83")
        down_button.setFixedSize(25, 25)
        layout.addWidget(down_button)

        # Editable text field
        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        self.line_edit.returnPressed.connect(lambda: self._save_edit(on_edit))
        layout.addWidget(self.line_edit)

        self.setLayout(layout)

    def _enable_edit(self):
        self.line_edit.setReadOnly(False)
        self.line_edit.setFocus()

    def _save_edit(self, on_edit):
        self.line_edit.setReadOnly(True)
        new_text = self.line_edit.text()
        on_edit(self, new_text)

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SailBussy Ground Station")

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()

        # Telemetry display (left side)
        self.telemetry_display = QTextEdit()
        self.telemetry_display.setReadOnly(True)
        self.telemetry_display.setMinimumWidth(200)
        main_layout.addWidget(self.telemetry_display, 0)

        # Google Maps integration
        self.map_view = QWebEngineView()
        self.map_view.setHtml("""
            <!DOCTYPE html>
            <html>
            <head>
                <!-- Add script to the <head> of your page to load the embeddable map component -->
                <script type="module" src="https://js.arcgis.com/embeddable-components/4.31/arcgis-embeddable-components.esm.js"></script>
            </head>
            <body>
                <!-- Add custom element to <body> of your page -->
                <arcgis-embedded-map style="height:600px;width:700px;" item-id="feb19231fc8c4aa79e6317fca5e18026" theme="dark" portal-url="https://virginiatech.maps.arcgis.com" legend-enabled ></arcgis-embedded-map>
            </body>
            </html>
        """)
        main_layout.addWidget(self.map_view, 1)

        right_layout = QVBoxLayout()

        # Add waypoint button
        add_button = QPushButton("Add a Waypoint")
        add_button.clicked.connect(self.add_waypoint)
        right_layout.addWidget(add_button)

        # Waypoint list widget
        self.list_widget = QListWidget()
        right_layout.addWidget(self.list_widget)

        # Combine layouts
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, 0)

        central_widget.setLayout(main_layout)

        self.add_waypoint("(0, 0)")
        self.add_waypoint("(1, 1)")
        self.add_waypoint("(2, 2)")

        # Telemetry updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_telemetry)
        self.timer.start(5000)  # Updates every 5 seconds

    def add_waypoint(self, text="New Item"):
        def delete_waypoint(widget):
            for i in range(self.list_widget.count()):
                if self.list_widget.itemWidget(self.list_widget.item(i)) == widget:
                    self.list_widget.takeItem(i)
                    break

        def edit_waypoint(widget, new_text):
            widget.text = new_text

        # Create waypoint widget
        waypoint_widget = WayPointWidget(text, on_delete=delete_waypoint, on_edit=edit_waypoint)

        # Add to list widget
        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(waypoint_widget.sizeHint())
        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, waypoint_widget)

    def update_telemetry(self):
        """
        Fetch and display telemetry data.
        """
        boat_status = request_boat_status()
        telemetry_text = (
            f"Position: {boat_status['position'][0]}, {boat_status['position'][1]}\n"
            f"State: {boat_status['state']}\n"
            f"Speed: {boat_status['speed']} m/s\n"
            f"Bearing: {boat_status['bearing']}{DEGREE_SIGN}\n"
            f"Heading: {boat_status['heading']}{DEGREE_SIGN}\n"
            f"True Wind Speed: {boat_status['true_wind_speed']} m/s\n"
            f"True Wind Angle: {boat_status['apparent_wind_angle']}{DEGREE_SIGN}\n"
            f"Sail Angle: {boat_status['sail_angle']}{DEGREE_SIGN}\n"
            f"Rudder Angle: {boat_status['rudder_angle']}{DEGREE_SIGN}\n"
            f"Current Waypoint: {boat_status['current_waypoint'][0]}, {boat_status['current_waypoint'][1]}\n"
            f"Current Route: {boat_status['current_route']}"
        )
        self.telemetry_display.setText(telemetry_text)

def request_boat_status() -> dict[str, Any]:
    """
    Should return a dictionary with the following keys:
        position            | latitude, longitude tuple
        state               | string
        speed               | float in m/s
        bearing             | degrees
        heading             | degrees
        true_wind_speed     | m/s
        true_wind_angle     | degrees
        apparent_wind_speed | m/s
        apparent_wind_angle | degrees
        sail_angle          | degrees
        rudder_angle        | degrees
        current_waypoint    | latitude, longitude tuple
        current_route       | list of latitude, longitude tuples
    :rtype: dict[str, Union[Tuple[float, float], str, float, int, List[Tuple[float, float]]]]
    """
    try:
        # print("Requesting boat status...")
        boat_status = requests.get(TELEMETRY_SERVER_URL + "boat_status/get").json()
    except requests.exceptions.ConnectionError:
        # print("Failed to connect to telemetry server.")
        boat_status = {
            "position": (0, 0),
            "state": "test",
            "speed": 0.0,
            "bearing": 0,
            "heading": 0,
            "true_wind_speed": 0,
            "apparent_wind_angle": 0,
            "sail_angle": 0,
            "rudder_angle": 0,
            "current_waypoint": (0, 0),
            "current_route": (0, 0),
        }
    return boat_status

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
