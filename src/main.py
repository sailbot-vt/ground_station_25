import os
from pathlib import Path
import sys
import json
import time
from typing import Union
from functools import partial


import numpy as np
import requests

from PyQt5.QtCore import QThread, QTimer, pyqtSignal, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QGridLayout,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QLineEdit,
    QCheckBox,
    QGroupBox,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
)


TELEMETRY_SERVER_ENDPOINTS = {
    "boat_status": "http://18.191.164.84:8080/boat_status/get",
    "waypoints_test": "http://18.191.164.84:8080/waypoints/test",
    "get_waypoints": "http://18.191.164.84:8080/waypoints/get",
    "set_waypoints": "http://18.191.164.84:8080/waypoints/set",
    "get_autopilot_parameters": "http://18.191.164.84:8080/autopilot_parameters/get",
    "set_autopilot_parameters": "http://18.191.164.84:8080/autopilot_parameters/set",
}
WAYPOINTS_SERVER_URL = "http://localhost:3001/waypoints"


HTML_MAP_PATH = Path(os.path.dirname(os.path.abspath(__file__)), "main.html")
if not os.path.exists(HTML_MAP_PATH):
    print(f"Error: {HTML_MAP_PATH} not found.")
    sys.exit(1)
else:
    HTML_MAP = open(HTML_MAP_PATH).read()


class TelemetryUpdater(QThread):
    """
    Thread to fetch telemetry data from the telemetry server.

    Inherits
    -------
    `QThread`

    Attributes
    ----------
    boat_data_fetched : `pyqtSignal`
        Signal to send boat data to the main thread. Emits a dictionary containing telemetry data.
    """

    boat_data_fetched = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__()

    def get_boat_data(self) -> None:
        try:
            boat_status = requests.get(
                TELEMETRY_SERVER_ENDPOINTS["boat_status"], timeout=5
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
            print("Failed to fetch boat data. Using default values.")
        self.boat_data_fetched.emit(boat_status)

    def run(self) -> None:
        self.get_boat_data()


class JSWaypointFetcher(QThread):
    """
    Thread to fetch waypoints from the local server.

    Inherits
    -------
    `QThread`

    Attributes
    ----------
    waypoints_fetched : `pyqtSignal`
        Signal to send waypoints to the main thread. Emits a list of lists containing
        waypoints, where each waypoint is a list of `[latitude, longitude]`.
    """

    waypoints_fetched = pyqtSignal(list)

    def __init__(self) -> None:
        super().__init__()

    def get_waypoints(self) -> None:
        try:
            waypoints = requests.get(WAYPOINTS_SERVER_URL).json()
        except requests.RequestException:
            waypoints = []
        self.waypoints_fetched.emit(waypoints)

    def run(self) -> None:
        self.get_waypoints()


class MainWindow(QWidget):
    """
    Main window for the ground station application.

    Inherits
    -------
    `QWidget`
    """

    def __init__(self) -> None:
        super().__init__()
        self.waypoints = []
        self.num_waypoints = 0
        self.autopilot_parameters = {}
        self.setWindowTitle("SailBussy Ground Station")
        self.setGeometry(100, 100, 800, 600)
        self.up_arrow = self.style().standardIcon(
            QStyle.StandardPixmap.SP_ArrowUp
        )
        self.down_arrow = self.style().standardIcon(
            QStyle.StandardPixmap.SP_ArrowDown
        )
        self.right_arrow = self.style().standardIcon(
            QStyle.StandardPixmap.SP_ArrowRight
        )
        self.left_arrow = self.style().standardIcon(
            QStyle.StandardPixmap.SP_ArrowLeft
        )

        # region define layouts
        self.main_layout = QGridLayout()
        self.left_layout = QTabWidget()
        self.middle_layout = QGridLayout()
        self.right_layout = QVBoxLayout()
        self.left_tab1_layout = QVBoxLayout()
        self.left_tab2_layout = QVBoxLayout()
        self.left_tab1 = QWidget()
        self.left_tab2 = QWidget()
        # endregion define layouts

        # region setup UI
        # region left section
        # region tab1: Telemetry data
        self.left_tab1_label = QLabel("Telemetry Data")
        self.left_tab1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_tab1_text_section = QTextEdit()
        self.left_tab1_text_section.setReadOnly(True)
        self.left_tab1_text_section.setText("Awaiting telemetry data...")
        self.left_tab1_layout.addWidget(self.left_tab1_label)
        self.left_tab1_layout.addWidget(self.left_tab1_text_section)
        # endregion tab1: Telemetry data

        # region tab2: Autopilot parameter control
        # region top section
        self.autopilot_param_control_groupbox = QGroupBox("Parameter Control")
        self.autopilot_param_control_layout = QVBoxLayout()

        self.left_tab2_reset_button = QPushButton("Reset Parameters")
        self.left_tab2_reset_button.clicked.connect(self.reset_parameters)
        self.left_tab2_send_button = QPushButton("Send Parameters")
        self.left_tab2_send_button.clicked.connect(self.send_parameters)
        self.left_tab2_save_button = QPushButton("Save Parameters to File")
        self.left_tab2_save_button.clicked.connect(self.save_parameters)
        self.left_tab2_load_button = QPushButton("Load Parameters from File")
        self.left_tab2_load_button.clicked.connect(self.load_parameters)

        self.left_tab2_reset_button.setDisabled(False)
        self.left_tab2_send_button.setDisabled(False)
        self.left_tab2_save_button.setDisabled(False)
        self.left_tab2_load_button.setDisabled(False)

        self.autopilot_param_control_layout.addWidget(
            self.left_tab2_reset_button
        )
        self.autopilot_param_control_layout.addWidget(
            self.left_tab2_send_button
        )
        self.autopilot_param_control_layout.addWidget(
            self.left_tab2_save_button
        )
        self.autopilot_param_control_layout.addWidget(
            self.left_tab2_load_button
        )
        self.autopilot_param_control_groupbox.setLayout(
            self.autopilot_param_control_layout
        )
        self.left_tab2_layout.addWidget(self.autopilot_param_control_groupbox)
        # endregion top section

        # region bottom section
        self.autopilot_param_input_groupbox = QGroupBox("Parameter Input")
        self.autopilot_param_input_layout = QVBoxLayout()

        # perform_forced_jibe_instead_of_tack
        self.perform_forced_jibe_instead_of_tack_layout = QHBoxLayout()
        self.forced_jibe_label = QLabel("Forced jibe instead of tack")
        self.forced_jibe_checkbox = QCheckBox()
        self.forced_jibe_label.setBuddy(self.forced_jibe_checkbox)
        self.perform_forced_jibe_send_button = (
            self.autopilot_param_button_maker(
                "send", "perform_forced_jibe_instead_of_tack"
            )
        )
        self.perform_forced_jibe_reset_button = (
            self.autopilot_param_button_maker(
                "reset", "perform_forced_jibe_instead_of_tack"
            )
        )
        self.perform_forced_jibe_instead_of_tack_layout.addWidget(
            self.forced_jibe_label
        )
        self.perform_forced_jibe_instead_of_tack_layout.addWidget(
            self.forced_jibe_checkbox
        )
        self.perform_forced_jibe_instead_of_tack_layout.addWidget(
            self.perform_forced_jibe_send_button
        )
        self.perform_forced_jibe_instead_of_tack_layout.addWidget(
            self.perform_forced_jibe_reset_button
        )
        self.autopilot_param_input_layout.addLayout(
            self.perform_forced_jibe_instead_of_tack_layout
        )

        # waypoint_accuracy
        self.waypoint_accuracy_layout = QHBoxLayout()
        self.waypoint_accuracy_label = QLabel("Waypoint Accuracy")
        self.waypoint_accuracy_text_box = QLineEdit()
        self.waypoint_accuracy_label.setBuddy(self.waypoint_accuracy_text_box)
        self.waypoint_accuracy_send_button = self.autopilot_param_button_maker(
            "send", "waypoint_accuracy"
        )
        self.waypoint_accuracy_reset_button = self.autopilot_param_button_maker(
            "reset", "waypoint_accuracy"
        )
        self.waypoint_accuracy_layout.addWidget(self.waypoint_accuracy_label)
        self.waypoint_accuracy_layout.addWidget(self.waypoint_accuracy_text_box)
        self.waypoint_accuracy_layout.addWidget(
            self.waypoint_accuracy_send_button
        )
        self.waypoint_accuracy_layout.addWidget(
            self.waypoint_accuracy_reset_button
        )
        self.autopilot_param_input_layout.addLayout(
            self.waypoint_accuracy_layout
        )

        # no_sail_zone_size
        self.no_sail_zone_size_layout = QHBoxLayout()
        self.no_sail_zone_size_label = QLabel("No Sail Zone Size")
        self.no_sail_zone_size_text_box = QLineEdit()
        self.no_sail_zone_size_label.setBuddy(self.no_sail_zone_size_text_box)
        self.no_sail_zone_size_send_button = self.autopilot_param_button_maker(
            "send", "no_sail_zone_size"
        )
        self.no_sail_zone_size_reset_button = self.autopilot_param_button_maker(
            "reset", "no_sail_zone_size"
        )
        self.no_sail_zone_size_layout.addWidget(self.no_sail_zone_size_label)
        self.no_sail_zone_size_layout.addWidget(self.no_sail_zone_size_text_box)
        self.no_sail_zone_size_layout.addWidget(
            self.no_sail_zone_size_send_button
        )
        self.no_sail_zone_size_layout.addWidget(
            self.no_sail_zone_size_reset_button
        )
        self.autopilot_param_input_layout.addLayout(
            self.no_sail_zone_size_layout
        )

        # autopilot_refresh_rate
        self.autopilot_refresh_rate_layout = QHBoxLayout()
        self.autopilot_refresh_rate_label = QLabel("Autopilot Refresh Rate")
        self.autopilot_refresh_rate_text_box = QLineEdit()
        self.autopilot_refresh_rate_label.setBuddy(
            self.autopilot_refresh_rate_text_box
        )
        self.autopilot_refresh_rate_send_button = (
            self.autopilot_param_button_maker("send", "autopilot_refresh_rate")
        )
        self.autopilot_refresh_rate_reset_button = (
            self.autopilot_param_button_maker("reset", "autopilot_refresh_rate")
        )
        self.autopilot_refresh_rate_layout.addWidget(
            self.autopilot_refresh_rate_label
        )
        self.autopilot_refresh_rate_layout.addWidget(
            self.autopilot_refresh_rate_text_box
        )
        self.autopilot_refresh_rate_layout.addWidget(
            self.autopilot_refresh_rate_send_button
        )
        self.autopilot_refresh_rate_layout.addWidget(
            self.autopilot_refresh_rate_reset_button
        )
        self.autopilot_param_input_layout.addLayout(
            self.autopilot_refresh_rate_layout
        )

        # tack_distance
        self.tack_distance_layout = QHBoxLayout()
        self.tack_distance_label = QLabel("Tack Distance")
        self.tack_distance_text_box = QLineEdit()
        self.tack_distance_label.setBuddy(self.tack_distance_text_box)
        self.tack_distance_send_button = self.autopilot_param_button_maker(
            "send", "tack_distance"
        )
        self.tack_distance_reset_button = self.autopilot_param_button_maker(
            "reset", "tack_distance"
        )
        self.tack_distance_layout.addWidget(self.tack_distance_label)
        self.tack_distance_layout.addWidget(self.tack_distance_text_box)
        self.tack_distance_layout.addWidget(self.tack_distance_send_button)
        self.tack_distance_layout.addWidget(self.tack_distance_reset_button)
        self.autopilot_param_input_layout.addLayout(self.tack_distance_layout)

        self.autopilot_param_input_layout.addStretch()
        self.autopilot_param_input_groupbox.setLayout(
            self.autopilot_param_input_layout
        )
        self.left_tab2_layout.addWidget(self.autopilot_param_input_groupbox)
        # endregion bottom section

        self.left_tab1.setLayout(self.left_tab1_layout)
        self.left_tab2.setLayout(self.left_tab2_layout)
        self.left_layout.addTab(self.left_tab1, "Boat Data")
        self.left_layout.addTab(self.left_tab2, "Autopilot Control")
        self.left_layout.setFixedWidth(300)
        self.main_layout.addWidget(self.left_layout, 0, 0)
        # endregion Parameter input
        # endregion left section

        # region middle section
        self.browser = QWebEngineView()
        self.browser.setHtml(HTML_MAP)
        self.browser.setMinimumWidth(700)
        self.browser.setMinimumHeight(700)
        self.middle_layout.addWidget(self.browser, 0, 1)
        self.main_layout.addLayout(self.middle_layout, 0, 1)
        # endregion middle section

        # region right section
        self.right_width = 295
        self.right_label = QLabel("Waypoints")
        self.right_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_table = QTableWidget()
        self.right_table.setMinimumWidth(self.right_width)

        self.send_waypoints_button = QPushButton("Send Waypoints")
        self.send_waypoints_button.setIcon(self.up_arrow)
        self.send_waypoints_button.setMinimumWidth(self.right_width)
        self.send_waypoints_button.setMinimumHeight(50)
        self.send_waypoints_button.clicked.connect(self.send_waypoints)
        self.send_waypoints_button.setDisabled(True)
        self.can_send_waypoints = False

        self.right_layout.addWidget(self.right_label)
        self.right_layout.addWidget(self.right_table)
        self.right_layout.addWidget(self.send_waypoints_button)
        self.main_layout.addLayout(self.right_layout, 0, 2)
        # endregion right section
        self.setLayout(self.main_layout)
        # endregion setup UI

        self.get_autopilot_parameters()

        self.telemetry_handler = TelemetryUpdater()
        self.js_waypoint_handler = JSWaypointFetcher()

        # Connect signals to update UI
        self.telemetry_handler.boat_data_fetched.connect(
            self.update_telemetry_display
        )
        self.js_waypoint_handler.waypoints_fetched.connect(
            self.update_waypoints_display
        )

        # Slow timer for telemetry
        self.slow_timer = QTimer(self)
        self.slow_timer.timeout.connect(self.update_telemetry_starter)

        # Fast timer for waypoints
        self.fast_timer = QTimer(self)
        self.fast_timer.timeout.connect(self.js_waypoint_handler_starter)

        # Start timers
        self.fast_timer.start(100)  # milliseconds
        self.slow_timer.start(1000)  # milliseconds

    # region button functions
    def send_waypoints(self, test: bool = False) -> None:
        """
        Send waypoints to the server.

        Parameters
        ----------
        test
            If `True`, use the test waypoint endpoint. Defaults to `False`.
        """

        if not test:
            try:
                requests.post(
                    TELEMETRY_SERVER_ENDPOINTS["set_waypoints"],
                    json={"value": self.waypoints},
                    timeout=5,
                ).json()
            except requests.exceptions.ConnectionError as e:
                print(f"Connection error: {e}")
                print(f"Waypoints: {self.waypoints}")
        else:
            try:
                requests.post(
                    TELEMETRY_SERVER_ENDPOINTS["waypoints_test"],
                    json={"value": self.waypoints},
                    timeout=5,
                ).json()
            except requests.exceptions.ConnectionError as e:
                print(f"Connection error: {e}")
                print(f"Waypoints: {self.waypoints}")

    def get_autopilot_parameters(self) -> None:
        """Get autopilot parameters from the server."""

        try:
            remote_params = requests.get(
                TELEMETRY_SERVER_ENDPOINTS["get_autopilot_parameters"],
                timeout=5,
            ).json()
            if remote_params == {}:
                print("Connection successful but no parameters found.")
            else:
                self.autopilot_parameters = remote_params
                self.forced_jibe_checkbox.setChecked(
                    self.autopilot_parameters[
                        "perform_forced_jibe_instead_of_tack"
                    ]
                )
                self.waypoint_accuracy_text_box.setText(
                    str(self.autopilot_parameters["waypoint_accuracy"])
                )
                self.no_sail_zone_size_text_box.setText(
                    str(self.autopilot_parameters["no_sail_zone_size"])
                )
                self.autopilot_refresh_rate_text_box.setText(
                    str(self.autopilot_parameters["autopilot_refresh_rate"])
                )
                self.tack_distance_text_box.setText(
                    str(self.autopilot_parameters["tack_distance"])
                )
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}")

    def send_parameters(self) -> None:
        """Send all parameters to the server."""

        try:
            self.autopilot_parameters = {
                "perform_forced_jibe_instead_of_tack": self.forced_jibe_checkbox.isChecked(),
                "waypoint_accuracy": float(
                    self.waypoint_accuracy_text_box.text()
                ),
                "no_sail_zone_size": float(
                    self.no_sail_zone_size_text_box.text()
                ),
                "autopilot_refresh_rate": float(
                    self.autopilot_refresh_rate_text_box.text()
                ),
                "tack_distance": float(self.tack_distance_text_box.text()),
            }
            requests.post(
                TELEMETRY_SERVER_ENDPOINTS["set_autopilot_parameters"],
                json={"value": self.autopilot_parameters},
            ).json()
        except ValueError or requests.exceptions.ConnectionError as e:
            print(f"Error: {e}")
            print(f"Parameters: {self.autopilot_parameters}")

    def send_individual_parameter(self, parameter: str) -> None:
        """
        Send individual parameter to the server.

        Parameters
        ----------
        parameter
            The parameter to send. Should be one of the keys in `self.autopilot_parameters`.
        """

        try:
            self.autopilot_parameters = {
                "perform_forced_jibe_instead_of_tack": self.forced_jibe_checkbox.isChecked(),
                "waypoint_accuracy": float(
                    self.waypoint_accuracy_text_box.text()
                ),
                "no_sail_zone_size": float(
                    self.no_sail_zone_size_text_box.text()
                ),
                "autopilot_refresh_rate": float(
                    self.autopilot_refresh_rate_text_box.text()
                ),
                "tack_distance": float(self.tack_distance_text_box.text()),
            }
            existing_params = requests.get(
                TELEMETRY_SERVER_ENDPOINTS["get_autopilot_parameters"],
                timeout=5,
            ).json()
            if existing_params == {}:
                print("Connection successful but no parameters found.")
            else:
                existing_params[parameter] = self.autopilot_parameters[
                    parameter
                ]
                requests.post(
                    TELEMETRY_SERVER_ENDPOINTS["set_autopilot_parameters"],
                    json={"value": existing_params},
                ).json()
        except ValueError or requests.exceptions.ConnectionError as e:
            print(f"Error: {e}")
            print(f"Inputed parameter: {parameter}")

    def reset_individual_parameter(self, parameter: str) -> None:
        """
        Reset individual parameter to the default value.

        Parameters
        ----------
        parameter
            The parameter to reset. Should be one of the keys in `self.autopilot_parameters`.
        """

        try:
            existing_params = requests.get(
                TELEMETRY_SERVER_ENDPOINTS["get_autopilot_parameters"],
                timeout=5,
            ).json()
            if existing_params == {}:
                print("Connection successful but no parameters found.")
            else:
                self.autopilot_parameters[parameter] = existing_params[
                    parameter
                ]
                self.forced_jibe_checkbox.setChecked(
                    self.autopilot_parameters[
                        "perform_forced_jibe_instead_of_tack"
                    ]
                )
                self.waypoint_accuracy_text_box.setText(
                    str(self.autopilot_parameters["waypoint_accuracy"])
                )
                self.no_sail_zone_size_text_box.setText(
                    str(self.autopilot_parameters["no_sail_zone_size"])
                )
                self.autopilot_refresh_rate_text_box.setText(
                    str(self.autopilot_parameters["autopilot_refresh_rate"])
                )
                self.tack_distance_text_box.setText(
                    str(self.autopilot_parameters["tack_distance"])
                )
        except ValueError or requests.exceptions.ConnectionError as e:
            print(f"Error: {e}")
            print(f"Inputed parameter: {parameter}")

    def save_parameters(self) -> None:
        """Save all parameters to a file."""

        try:
            self.autopilot_parameters = {
                "perform_forced_jibe_instead_of_tack": self.forced_jibe_checkbox.isChecked(),
                "waypoint_accuracy": float(
                    self.waypoint_accuracy_text_box.text()
                ),
                "no_sail_zone_size": float(
                    self.no_sail_zone_size_text_box.text()
                ),
                "autopilot_refresh_rate": float(
                    self.autopilot_refresh_rate_text_box.text()
                ),
                "tack_distance": float(self.tack_distance_text_box.text()),
            }
            file_path = os.path.join(
                os.getcwd(),
                "autopilot_params/",
                f"params_{time.time_ns()}.json",
            )
            with open(file_path, "w") as f:
                json.dump(self.autopilot_parameters, f, indent=4)
        except ValueError as e:
            print(f"Error: {e}")
            print(f"Parameters: {self.autopilot_parameters}")

    def load_parameters(self) -> None:
        """Load parameters from a file."""

        try:
            if "autopilot_params" not in os.listdir(os.getcwd()):
                print("autopilot_params directory not found. Creating it.")
                os.makedirs(os.getcwd() + "autopilot_params/")

            autopilot_params_dir = Path(os.getcwd(), "autopilot_params")
            param_files = os.listdir(autopilot_params_dir)
            if not param_files:
                print("No parameter files found.")

            else:
                latest_param_file = Path(autopilot_params_dir, max(param_files))
                with open(latest_param_file, "r") as f:
                    self.autopilot_parameters = json.load(f)
                    self.forced_jibe_checkbox.setChecked(
                        self.autopilot_parameters[
                            "perform_forced_jibe_instead_of_tack"
                        ]
                    )
                    self.waypoint_accuracy_text_box.setText(
                        str(self.autopilot_parameters["waypoint_accuracy"])
                    )
                    self.no_sail_zone_size_text_box.setText(
                        str(self.autopilot_parameters["no_sail_zone_size"])
                    )
                    self.autopilot_refresh_rate_text_box.setText(
                        str(self.autopilot_parameters["autopilot_refresh_rate"])
                    )
                    self.tack_distance_text_box.setText(
                        str(self.autopilot_parameters["tack_distance"])
                    )
        except FileNotFoundError as e:
            print(e)

    def reset_parameters(self) -> None:
        """Reset all parameters to values from the server."""

        self.get_autopilot_parameters()

    # endregion button functions

    # region pyqt thread functions
    def js_waypoint_handler_starter(self) -> None:
        """Starts the JS waypoint handler thread."""

        if not self.js_waypoint_handler.isRunning():
            self.js_waypoint_handler.start()

    def update_telemetry_starter(self) -> None:
        """Starts the telemetry handler thread."""

        if not self.telemetry_handler.isRunning():
            self.telemetry_handler.start()

    def update_waypoints_display(self, waypoints: list[list[float]]) -> None:
        """
        Update waypoints display with fetched waypoints.

        Parameters
        ----------
        waypoints
            List of waypoints fetched from the server.
        """

        self.waypoints = waypoints
        self.send_waypoints_button.setDisabled(not self.can_send_waypoints)
        if len(waypoints) != self.num_waypoints:
            self.can_send_waypoints = True
            self.num_waypoints = len(waypoints)

            self.right_table.clear()
            self.right_table.setRowCount(0)
            self.right_table.setColumnCount(2)
            self.right_table.setHorizontalHeaderLabels(
                ["Latitude", "Longitude"]
            )

            for waypoint in waypoints:
                self.right_table.insertRow(self.right_table.rowCount())
                for i, coord in enumerate(waypoint):
                    item = QTableWidgetItem(str(round(coord, 10)))
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    self.right_table.setItem(
                        self.right_table.rowCount() - 1, i, item
                    )
            self.right_table.resizeColumnsToContents()
            self.right_table.resizeRowsToContents()

    def update_telemetry_display(
        self, boat_data: dict[str, Union[str, float]]
    ) -> None:
        """
        Update telemetry display with boat data.

        Parameters
        ----------
        boat_data
            Dictionary containing boat data fetched from the server.
        """

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
        self.left_tab1_text_section.setText(telemetry_text)

    # endregion pyqt thread functions

    # region helper functions

    def autopilot_param_button_maker(
        self, action: str, param: str
    ) -> QPushButton:
        """
        Create a button for autopilot parameters.

        Parameters
        ----------
        action
            The action to perform when the button is clicked, either "send" or "reset".
        param
            The parameter to set.

        Returns
        -------
        QPushButton
            The created button.
        """

        button = QPushButton()
        button.setMaximumWidth(25)
        if action == "send":
            button.setIcon(self.up_arrow)
            button.clicked.connect(
                partial(self.send_individual_parameter, param)
            )
            return button
        elif action == "reset":
            button.setIcon(self.down_arrow)
            button.clicked.connect(
                partial(self.reset_individual_parameter, param)
            )
            return button
        else:
            raise ValueError("Invalid action. Use 'send' or 'reset'.")

    # endregion helper functions


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
