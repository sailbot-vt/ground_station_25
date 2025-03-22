import os
import sys
import json
from io import StringIO
import time


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
    QGridLayout,
    QHBoxLayout,
    QTextEdit,
    QListWidget,
    QPushButton,
    QCheckBox,
    QLineEdit,
    QTabWidget,
    QLabel,
    QGroupBox,
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

        self.main_layout = QGridLayout()
        self.left_layout = QTabWidget()
        left_tab1 = QWidget()
        left_tab2 = QWidget()
        left_tab1_layout = QVBoxLayout()
        left_tab2_layout = QVBoxLayout()
        self.middle_layout = QGridLayout()
        self.right_layout = QVBoxLayout()

        # Left section
        self.left_label = QLabel("Telemetry Data")
        self.left_label.setAlignment(Qt.AlignCenter)
        self.left_text_section = QTextEdit()
        self.left_text_section.setReadOnly(True)
        self.left_text_section.setText("Awaiting telemetry data...")
        left_tab1_layout.addWidget(self.left_label)
        left_tab1_layout.addWidget(self.left_text_section)

        # tab2 section: Parameter input
        # region Parameter inputs
        # perform_forced_jibe_instead_of_tack
        self.forced_jibe_checkbox = QCheckBox(
            "Perform forced jibe instead of tack?"
        )
        left_tab2_layout.addWidget(self.forced_jibe_checkbox)

        # waypoint_accuracy
        self.hbox1 = QHBoxLayout()
        self.waypoint_accuracy_label = QLabel("Waypoint Accuracy")
        self.waypoint_accuracy_text_box = QLineEdit()
        self.waypoint_accuracy_label.setBuddy(self.waypoint_accuracy_text_box)
        self.hbox1.addWidget(self.waypoint_accuracy_label)
        self.hbox1.addWidget(self.waypoint_accuracy_text_box)
        left_tab2_layout.addLayout(self.hbox1)

        # no_sail_zone_size
        self.hbox2 = QHBoxLayout()
        self.no_sail_zone_size_label = QLabel("No Sail Zone Size")
        self.no_sail_zone_size_text_box = QLineEdit()
        self.no_sail_zone_size_label.setBuddy(self.no_sail_zone_size_text_box)
        self.hbox2.addWidget(self.no_sail_zone_size_label)
        self.hbox2.addWidget(self.no_sail_zone_size_text_box)
        left_tab2_layout.addLayout(self.hbox2)

        # autopilot_refresh_rate
        self.hbox3 = QHBoxLayout()
        self.autopilot_refresh_rate_label = QLabel("Autopilot Refresh Rate")
        self.autopilot_refresh_rate_text_box = QLineEdit()
        self.autopilot_refresh_rate_label.setBuddy(
            self.autopilot_refresh_rate_text_box
        )
        self.hbox3.addWidget(self.autopilot_refresh_rate_label)
        self.hbox3.addWidget(self.autopilot_refresh_rate_text_box)
        left_tab2_layout.addLayout(self.hbox3)

        # tack_distance
        self.hbox4 = QHBoxLayout()
        self.tack_distance_label = QLabel("Tack Distance")
        self.tack_distance_text_box = QLineEdit()
        self.tack_distance_label.setBuddy(self.tack_distance_text_box)
        self.hbox4.addWidget(self.tack_distance_label)
        self.hbox4.addWidget(self.tack_distance_text_box)
        left_tab2_layout.addLayout(self.hbox4)
        left_tab2_layout.addStretch()

        self.left_parameter_control_layout = QVBoxLayout()
        self.left_tab2_group_box = QGroupBox("Parameter Control")
        left_tab2_reset_button = QPushButton("Reset Parameters")
        left_tab2_reset_button.clicked.connect(self.reset_parameters)
        left_tab2_send_button = QPushButton("Send Parameters")
        left_tab2_send_button.clicked.connect(self.send_parameters)
        left_tab2_save_button = QPushButton("Save Parameters to File")
        left_tab2_save_button.clicked.connect(self.save_parameters)
        left_tab2_load_button = QPushButton("Load Parameters from File")
        left_tab2_load_button.clicked.connect(self.load_parameters)

        left_tab2_reset_button.setDisabled(True)
        left_tab2_send_button.setDisabled(True)
        left_tab2_save_button.setDisabled(False)
        left_tab2_load_button.setDisabled(False)
        self.left_parameter_control_layout.addWidget(left_tab2_reset_button)
        self.left_parameter_control_layout.addWidget(left_tab2_send_button)
        self.left_parameter_control_layout.addWidget(left_tab2_save_button)
        self.left_parameter_control_layout.addWidget(left_tab2_load_button)
        self.left_tab2_group_box.setLayout(self.left_parameter_control_layout)
        left_tab2_layout.addWidget(self.left_tab2_group_box)

        # endregion Parameter input
        left_tab1.setLayout(left_tab1_layout)
        left_tab2.setLayout(left_tab2_layout)
        self.left_layout.addTab(left_tab1, "Boat Data")
        self.left_layout.addTab(left_tab2, "Parameter Input")
        self.left_layout.setMinimumWidth(300)
        self.main_layout.addWidget(self.left_layout, 0, 0)

        # Middle: HTML display
        self.browser = QWebEngineView()
        self.browser.setHtml(HTML_MAP)
        self.browser.setMinimumWidth(700)
        self.browser.setMinimumHeight(700)
        self.middle_layout.addWidget(self.browser, 0, 1)
        self.main_layout.addLayout(self.middle_layout, 0, 1)

        # Right section
        self.right_label = QLabel("Waypoints")
        self.right_label.setAlignment(Qt.AlignCenter)
        self.right_text_section = QTextEdit()
        self.right_text_section.setReadOnly(True)
        self.right_text_section.setMinimumWidth(300)
        self.right_button = QPushButton("Sync Waypoints")
        self.right_button.clicked.connect(self.sync_waypoints)
        self.right_button.setDisabled(True)
        self.right_button_can_be_clicked = False
        self.right_button.setMinimumWidth(300)
        self.right_button.setMinimumHeight(50)
        self.right_layout.addWidget(self.right_label)
        self.right_layout.addWidget(self.right_text_section)
        self.right_layout.addWidget(self.right_button)
        self.main_layout.addLayout(self.right_layout, 0, 2)

        self.setLayout(self.main_layout)
        self.reset_parameters()

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
                timeout=5,
            ).json()
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}")
            print(f"Waypoints: {self.waypoints}")
            return

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

    def reset_parameters(self):
        """Reset all parameters to default values."""
        try:
            remote_params = requests.get(
                TELEMETRY_SERVER_URL + "autopilot_parameters/get",
                timeout=5,
            ).json()
            self.forced_jibe_checkbox.setChecked(
                remote_params["perform_forced_jibe_instead_of_tack"]
            )
            self.waypoint_accuracy_text_box.setText(
                str(remote_params["waypoint_accuracy"])
            )
            self.no_sail_zone_size_text_box.setText(
                str(remote_params["no_sail_zone_size"])
            )
            self.autopilot_refresh_rate_text_box.setText(
                str(remote_params["autopilot_refresh_rate"])
            )
            self.tack_distance_text_box.setText(
                str(remote_params["tack_distance"])
            )
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}")
            self.forced_jibe_checkbox.setChecked(False)
            self.waypoint_accuracy_text_box.setText("0.0")
            self.no_sail_zone_size_text_box.setText("0.0")
            self.autopilot_refresh_rate_text_box.setText("0.0")
            self.tack_distance_text_box.setText("0.0")

    def send_parameters(self):
        """Send all parameters to the server."""
        params = {
            "perform_forced_jibe_instead_of_tack": self.forced_jibe_checkbox.isChecked(),
            "waypoint_accuracy": float(self.waypoint_accuracy_text_box.text()),
            "no_sail_zone_size": float(self.no_sail_zone_size_text_box.text()),
            "autopilot_refresh_rate": float(
                self.autopilot_refresh_rate_text_box.text()
            ),
            "tack_distance": float(self.tack_distance_text_box.text()),
        }
        try:
            requests.post(
                TELEMETRY_SERVER_URL + "autopilot_parameters/set",
                json={"value": params},
            ).json()
            return True
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}")
            print(f"Parameters: {params}")
            return

    def save_parameters(self):
        """Save all parameters to a file."""
        params = {
            "perform_forced_jibe_instead_of_tack": self.forced_jibe_checkbox.isChecked(),
            "waypoint_accuracy": float(self.waypoint_accuracy_text_box.text()),
            "no_sail_zone_size": float(self.no_sail_zone_size_text_box.text()),
            "autopilot_refresh_rate": float(
                self.autopilot_refresh_rate_text_box.text()
            ),
            "tack_distance": float(self.tack_distance_text_box.text()),
        }
        file_path = os.path.join(os.getcwd(), "params.json")
        with open(file_path, "w") as f:
            json.dump(params, f, indent=4)

    def load_parameters(self):
        """Load parameters from a file."""
        try:
            with open("params.json", "r") as f:
                params = json.load(f)
            self.forced_jibe_checkbox.setChecked(
                params["perform_forced_jibe_instead_of_tack"]
            )
            self.waypoint_accuracy_text_box.setText(
                str(params["waypoint_accuracy"])
            )
            self.no_sail_zone_size_text_box.setText(
                str(params["no_sail_zone_size"])
            )
            self.autopilot_refresh_rate_text_box.setText(
                str(params["autopilot_refresh_rate"])
            )
            self.tack_distance_text_box.setText(str(params["tack_distance"]))
            return True
        except FileNotFoundError as e:
            print(e)
            return


# endregion Left Section Functions

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
