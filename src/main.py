import os
import sys
from io import StringIO


import numpy as np
import pandas as pd
import requests

from PyQt5.QtCore import (
    Qt,
    QThread,
    QTimer,
    QCoreApplication,
    pyqtSignal,
    QUrl,
    QObject,
    pyqtSlot,
)
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QListWidget,
    QPushButton,
    QLineEdit,
    QLabel,
)


TELEMETRY_SERVER_URL = "http://18.191.164.84:8080/"
WAYPOINTS_SERVER_URL = "http://localhost:3001/waypoints"


HTML_MAP_PATH = os.getcwd() + "/src/main.html"
if not os.path.exists(HTML_MAP_PATH):
    print(f"Error: {HTML_MAP_PATH} not found.")
    sys.exit(1)
else:
    HTML_MAP = open(HTML_MAP_PATH).read()


class TelemetryUpdater(QThread):
    boat_data_fetched = pyqtSignal(
        dict
    )  # Signal to send boat data to the main thread

    def __init__(self):
        super().__init__()

    def get_boat_data(self):
        """Fetch boat data from telemetry server."""
        try:
            boat_status = requests.get(
                TELEMETRY_SERVER_URL + "/boat_status/get"
            ).json()
        except requests.RequestException:
            boat_status = {
                "position": [36.983731367697374, -76.29555376681454],
                "state": "N/A",
                "speed": 0,
                "bearing": 0,
                "heading": np.random.randint(0, 360),
                "true_wind_speed": 0,
                "true_wind_angle": 0,
                "apparent_wind_speed": 0,
                "apparent_wind_angle": 0,
                "sail_angle": 0,
                "rudder_angle": 0,
                "current_waypoint_index": 0,
                "current_route": [],
                "parameters": {},
                "vesc_data_rpm": 0,
                "vesc_data_duty_cycle": 0.0,
                "vesc_data_amp_hours": 0.0,
                "vesc_data_amp_hours_charged": 0,
                "vesc_data_current_to_vesc": 0,
                "vesc_data_voltage_to_motor": 0,
                "vesc_data_voltage_to_vesc": 0,
                "vesc_data_wattage_to_motor": 0,
                "vesc_data_time_since_vesc_startup_in_ms": 0,
                "vesc_data_motor_temperature": 0,
            }
        self.boat_data_fetched.emit(
            boat_status
        )  # Emit the signal with fallback data

    def run(self):
        """Run the thread and fetch the data."""
        self.get_boat_data()


class WaypointUpdater(QThread):
    waypoints_fetched = pyqtSignal(list)

    def __init__(self):
        super().__init__()

    def get_waypoints(self):
        """Fetch waypoints from server."""
        try:
            waypoints = requests.get(WAYPOINTS_SERVER_URL).json()
        except requests.RequestException:
            waypoints = []
        self.waypoints_fetched.emit(waypoints)

    def run(self):
        """Run the thread and fetch the data."""
        self.get_waypoints()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.waypoints = []
        self.num_waypoints = 0
        self.setWindowTitle("SailBussy Ground Station")
        self.setGeometry(100, 100, 800, 600)

        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Left section
        self.left_label = QLabel("Boat Data")
        self.left_label.setAlignment(Qt.AlignCenter)
        self.left_text_section = QTextEdit()
        self.left_text_section.setMinimumWidth(300)
        self.left_text_section.setReadOnly(True)
        self.left_text_section.setText("Awaiting telemetry data...")
        left_layout.addWidget(self.left_label)
        left_layout.addWidget(self.left_text_section)
        main_layout.addLayout(left_layout, 1)

        # Middle: HTML display
        self.browser = QWebEngineView()
        self.browser.setHtml(HTML_MAP)
        self.browser.setMinimumWidth(700)
        self.browser.setMinimumHeight(700)
        main_layout.addWidget(self.browser, 4)

        # Right section
        self.right_label = QLabel("Waypoints")
        self.right_label.setAlignment(Qt.AlignCenter)
        self.right_text_section = QTextEdit()
        self.right_text_section.setReadOnly(True)
        self.right_text_section.setMinimumWidth(300)
        self.right_text_section.setText("")
        self.right_button = QPushButton("Sync Waypoints")
        self.right_button.clicked.connect(self.sync_waypoints)
        self.right_button.setDisabled(True)
        self.right_button_can_be_clicked = False
        self.right_button.setMinimumWidth(300)
        self.right_button.setMinimumHeight(50)
        right_layout.addWidget(self.right_label)
        right_layout.addWidget(self.right_text_section)
        right_layout.addWidget(self.right_button)
        main_layout.addLayout(right_layout, 2)

        self.setLayout(main_layout)

        self.telemetry_handler = TelemetryUpdater()
        self.waypoint_handler = WaypointUpdater()

        # Connect signals to update UI
        self.telemetry_handler.boat_data_fetched.connect(
            self.update_telemetry_display
        )
        self.waypoint_handler.waypoints_fetched.connect(
            self.update_waypoints_display
        )

        # Slow timer for telemetry
        self.slow_timer = QTimer(self)
        self.slow_timer.timeout.connect(self.update_telemetry)

        # Fast timer for waypoints
        self.fast_timer = QTimer(self)
        self.fast_timer.timeout.connect(self.update_waypoints)

        # Start timers
        self.fast_timer.start(100)  # milliseconds
        self.slow_timer.start(1000)  # milliseconds

    def sync_waypoints(self):
        """Sync waypoints with the server."""
        self.right_button_can_be_clicked = False
        try:
            requests.post(
                TELEMETRY_SERVER_URL + "waypoints/set",
                json={"value": self.waypoints},
            ).json()
        except requests.RequestException as e:
            print(f"Error syncing waypoints: {e}")

    # region Right Section Functions
    def update_waypoints(self):
        """Update waypoints display with fetched waypoints."""
        if not self.waypoint_handler.isRunning():
            self.waypoint_handler.start()

    def update_waypoints_display(self, waypoints):
        """Update waypoints display with fetched waypoints."""
        self.waypoints = waypoints
        self.right_button.setDisabled(not self.right_button_can_be_clicked)
        if len(waypoints) != self.num_waypoints:
            self.right_button_can_be_clicked = True
            self.num_waypoints = len(waypoints)
        waypoints_text = ""
        for waypoint in waypoints:
            waypoints_text += f"Latitude: {round(waypoint[0], 6)}, Longitude: {round(waypoint[1], 6)}\n"
        self.right_text_section.setText(waypoints_text)

    # endregion Right Section Functions

    # region Left Section Functions

    def update_telemetry(self):
        """Update the telemetry data by fetching it."""
        if not self.telemetry_handler.isRunning():
            self.telemetry_handler.start()

    def update_telemetry_display(self, boat_data):
        """Update telemetry display with boat data."""
        telemetry_text = f"""Boat Info:
State: {boat_data.get("state", "N/A")}
Speed: {boat_data.get("speed", "N/A")} knots
Bearing: {boat_data.get("bearing", "N/A")}°
Heading: {boat_data.get("heading", "N/A")}°
True Wind Speed: {boat_data.get("true_wind_speed", "N/A")} knots
True Wind Angle: {boat_data.get("true_wind_angle", "N/A")}°
Apparent Wind Speed: {boat_data.get("apparent_wind_speed", "N/A")} knots
Apparent Wind Angle: {boat_data.get("apparent_wind_angle", "N/A")}°
Sail Angle: {boat_data.get("sail_angle", "N/A")}°
Rudder Angle: {boat_data.get("rudder_angle", "N/A")}°
Current Waypoint Index: {boat_data.get("current_waypoint_index", "N/A")}
Current Route: {boat_data.get("current_route", "N/A")}
Parameters: {boat_data.get("parameters", "N/A")}

VESC Data:
RPM: {boat_data.get("vesc_data_rpm", "N/A")}
Duty Cycle: {boat_data.get("vesc_data_duty_cycle", "N/A")}%
Amp Hours: {boat_data.get("vesc_data_amp_hours", "N/A")} Ah
Amp Hours Charged: {boat_data.get("vesc_data_amp_hours_charged", "N/A")} Ah
Current to VESC: {boat_data.get("vesc_data_current_to_vesc", "N/A")} A
Voltage to Motor: {boat_data.get("vesc_data_voltage_to_motor", "N/A")} V
Voltage to VESC: {boat_data.get("vesc_data_voltage_to_vesc", "N/A")} V
Wattage to Motor: {boat_data.get("vesc_data_wattage_to_motor", "N/A")} W
Time Since VESC Startup: {boat_data.get("vesc_data_time_since_vesc_startup_in_ms", "N/A")} ms
Motor Temperature: {boat_data.get("vesc_data_motor_temperature", "N/A")}°C
"""
        self.left_text_section.setText(telemetry_text)


# endregion Left Section Functions

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
