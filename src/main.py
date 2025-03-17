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
WAYPOINTS_SERVER_URL = "http://localhost:3000/waypoints"


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
            boat_status = requests.get(TELEMETRY_SERVER_URL).json()
        except requests.RequestException:
            print("Not able to fetch data from telemetry server.")
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
            print("Not able to fetch data from waypoints server.")
            waypoints = []
        self.waypoints_fetched.emit(waypoints)

    def run(self):
        """Run the thread and fetch the data."""
        self.get_waypoints()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SailBussy Ground Station")
        self.setGeometry(100, 100, 800, 600)

        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Left section
        self.left_label = QLabel("Boat Data")
        self.left_label.setAlignment(Qt.AlignCenter)
        self.left_text_section = QTextEdit()
        self.left_text_section.setReadOnly(True)
        self.left_text_section.setText("Awaiting telemetry data...")
        left_layout.addWidget(self.left_label)
        left_layout.addWidget(self.left_text_section)
        main_layout.addLayout(left_layout, 1)

        # Middle: HTML display
        self.browser = QWebEngineView()
        self.browser.setHtml(HTML_MAP)
        main_layout.addWidget(self.browser, 4)

        # Right section
        self.right_label = QLabel("Waypoints")
        self.right_label.setAlignment(Qt.AlignCenter)
        self.right_text_section = QTextEdit()
        self.right_text_section.setReadOnly(True)
        self.right_text_section.setText("")
        right_layout.addWidget(self.right_label)
        right_layout.addWidget(self.right_text_section)
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

        # Start periodic updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_telemetry)
        self.timer.timeout.connect(self.update_waypoints)
        self.timer.start(100)  # milliseconds

    # region Right Section Functions
    def update_waypoints(self):
        """Update waypoints display with fetched waypoints."""
        if not self.waypoint_handler.isRunning():
            self.waypoint_handler.start()

    def update_waypoints_display(self, waypoints):
        """Update waypoints display with fetched waypoints."""
        waypoints_text = ""
        for waypoint in waypoints:
            waypoints_text += (
                f"Latitude: {waypoint[0]}, Longitude: {waypoint[1]}\n"
            )
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


# region Data Fetching Functions
def get_buoy_wind_data():
    """Fetch wind data from NOAA buoys."""
    url = "https://www.ndbc.noaa.gov/data/latest_obs/latest_obs.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()
        raw_data = response.text

        # Extract header labels
        lines = raw_data.split("\n")
        labels = [
            f"{i} ({j})"
            for i, j in zip(
                lines[0].replace("#", "").split(),
                lines[1].replace("#", "").split(),
            )
        ]

        df = pd.read_csv(
            StringIO(raw_data),
            comment="#",
            sep=r"\s+",
            header=None,
            names=labels,
            na_values="MM",
            keep_default_na=True,
        )

        df = df[
            ["LAT (deg)", "LON (deg)", "WDIR (degT)", "WSPD (m/s)"]
        ].dropna()
        df.rename(
            columns={
                "LAT (deg)": "lat",
                "LON (deg)": "lon",
                "WDIR (degT)": "wind_dir",
                "WSPD (m/s)": "wind_speed",
            },
            inplace=True,
        )

        return df.to_dict(orient="records")
    except requests.RequestException as e:
        print(f"Error fetching buoy data: {e}")
        return []


def get_station_wind_data():
    """Fetch wind data from NOAA weather stations."""
    url = "https://aviationweather.gov/data/cache/metars.cache.csv"
    try:
        df = pd.read_csv(url, skiprows=5, na_values="VRB")

        df = df[
            ["latitude", "longitude", "wind_dir_degrees", "wind_speed_kt"]
        ].dropna()

        # Convert wind speed from knots to m/s
        df["wind_speed"] = df["wind_speed_kt"] * 0.514444

        df.rename(
            columns={
                "latitude": "lat",
                "longitude": "lon",
                "wind_dir_degrees": "wind_dir",
            },
            inplace=True,
        )
        df = df.astype(float)

        return df.to_dict(orient="records")
    except requests.RequestException as e:
        print(f"Error fetching station data: {e}")
        return []


# endregion Data Fetching Functions

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
