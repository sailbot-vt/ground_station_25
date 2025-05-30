# region imports
import os
import time
import base64
import requests
import json
import geopy
import geopy.distance

import constants
from icons import get_icons
import thread_classes
from widgets.popup_edit import TextEditWindow

from functools import partial
from pathlib import PurePath
from typing import Union, Literal, Optional, Any

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)
# endregion imports


class GroundStationWidget(QWidget):
    """
    Main widget for the ground station application.

    Inherits
    -------
    `QWidget`
    """

    def __init__(self) -> None:
        super().__init__()
        self.icons = get_icons()
        self.waypoints: list[list[float]] = list()
        self.num_waypoints = 0
        self.boat_data_averages = {
            "vesc_data_rpm": 0.0,
            "vesc_data_amp_hours": 0.0,
            "vesc_data_amp_hours_charged": 0.0,
            "vesc_data_current_to_vesc": 0.0,
            "vesc_data_voltage_to_motor": 0.0,
            "vesc_data_voltage_to_vesc": 0.0,
            "vesc_data_wattage_to_motor": 0.0,
            "vesc_data_motor_temperature": 0.0,
        }
        self.buoys: dict[dict[str, float]] = dict()
        self.boat_data: dict[str, Any] = dict()
        self.autopilot_parameters: dict[str, Any] = dict()
        self.telemetry_data_limits: dict[str, float] = dict()

        # region define layouts
        self.main_layout = QGridLayout()
        self.main_layout.setObjectName("main_layout")

        self.left_layout = QTabWidget()
        self.left_layout.setObjectName("left_layout")
        self.left_tab1_layout = QVBoxLayout()
        self.left_tab2_layout = QVBoxLayout()
        self.left_tab1 = QWidget()
        self.left_tab2 = QWidget()

        self.middle_layout = QGridLayout()
        self.middle_layout.setObjectName("middle_layout")

        self.right_layout = QTabWidget()
        self.right_layout.setObjectName("right_layout")
        self.right_tab1_layout = QGridLayout()
        self.right_tab2_layout = QGridLayout()
        self.right_tab1 = QWidget()
        self.right_tab2 = QWidget()
        # endregion define layouts

        # region setup UI
        # region left section
        self.left_width = 300
        # region tab1: Telemetry data
        self.left_tab1_label = QLabel("Telemetry Data")
        self.left_tab1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_tab1_text_section = QTextEdit()
        self.left_tab1_text_section.setReadOnly(True)
        self.left_tab1_text_section.setText("Awaiting telemetry data...")

        self.save_boat_data_button = self.pushbutton_maker(
            "Save Boat Data to File",
            self.icons.save,
            self.save_boat_data,
            self.left_width,
            50,
        )

        self.edit_boat_data_limits_button = self.pushbutton_maker(
            "Edit Limits",
            self.icons.edit,
            self.edit_boat_data_limits,
            self.left_width // 2,
            50,
        )

        self.side_buttons_layout = QVBoxLayout()

        self.load_boat_data_limits_button = self.pushbutton_maker(
            "Load Limits from File",
            self.icons.hard_drive,
            self.load_boat_data_limits,
            self.left_width // 2,
            25,
        )

        self.save_boat_data_limits_button = self.pushbutton_maker(
            "Save Limits to File",
            self.icons.save,
            self.save_boat_data_limits,
            self.left_width // 2,
            25,
        )

        self.side_buttons_layout.addWidget(self.load_boat_data_limits_button)
        self.side_buttons_layout.addWidget(self.save_boat_data_limits_button)

        self.left_tab1_button_groupbox = QGroupBox()
        self.left_tab1_button_layout = QGridLayout()

        self.left_tab1_button_layout.addWidget(self.save_boat_data_button, 0, 0, 1, 2)
        self.left_tab1_button_layout.addWidget(self.edit_boat_data_limits_button, 1, 0)
        self.left_tab1_button_layout.addLayout(self.side_buttons_layout, 1, 1)
        self.left_tab1_button_groupbox.setLayout(self.left_tab1_button_layout)

        self.left_tab1_layout.addWidget(self.left_tab1_label)
        self.left_tab1_layout.addWidget(self.left_tab1_text_section)
        self.left_tab1_layout.addWidget(self.left_tab1_button_groupbox)
        # endregion tab1: Telemetry data

        # region tab2: Autopilot parameter control
        # region top section
        self.autopilot_param_control_groupbox = QGroupBox("Parameter Control")
        self.autopilot_param_control_layout = QVBoxLayout()

        self.left_tab2_reset_button = self.pushbutton_maker(
            "Reset Parameters", self.icons.refresh, self.reset_parameters
        )

        self.left_tab2_send_button = self.pushbutton_maker(
            "Send Parameters", self.icons.upload, self.send_parameters
        )

        self.left_tab2_save_button = self.pushbutton_maker(
            "Save Parameters to File", self.icons.save, self.save_parameters
        )

        self.left_tab2_load_button = self.pushbutton_maker(
            "Load Parameters from File", self.icons.hard_drive, self.load_parameters
        )

        self.left_tab2_send_image_button = self.pushbutton_maker(
            "Send Image", self.icons.upload, self.send_image
        )

        self.autopilot_param_control_layout.addWidget(self.left_tab2_reset_button)
        self.autopilot_param_control_layout.addWidget(self.left_tab2_send_button)
        self.autopilot_param_control_layout.addWidget(self.left_tab2_save_button)
        self.autopilot_param_control_layout.addWidget(self.left_tab2_load_button)
        self.autopilot_param_control_layout.addWidget(self.left_tab2_send_image_button)
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
        self.perform_forced_jibe_send_button = self.autopilot_param_button_maker(
            "send", "perform_forced_jibe_instead_of_tack"
        )
        self.perform_forced_jibe_reset_button = self.autopilot_param_button_maker(
            "reset", "perform_forced_jibe_instead_of_tack"
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
        self.waypoint_accuracy_layout.addWidget(self.waypoint_accuracy_send_button)
        self.waypoint_accuracy_layout.addWidget(self.waypoint_accuracy_reset_button)
        self.autopilot_param_input_layout.addLayout(self.waypoint_accuracy_layout)

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
        self.no_sail_zone_size_layout.addWidget(self.no_sail_zone_size_send_button)
        self.no_sail_zone_size_layout.addWidget(self.no_sail_zone_size_reset_button)
        self.autopilot_param_input_layout.addLayout(self.no_sail_zone_size_layout)

        # autopilot_refresh_rate
        self.autopilot_refresh_rate_layout = QHBoxLayout()
        self.autopilot_refresh_rate_label = QLabel("Autopilot Refresh Rate")
        self.autopilot_refresh_rate_text_box = QLineEdit()
        self.autopilot_refresh_rate_label.setBuddy(self.autopilot_refresh_rate_text_box)
        self.autopilot_refresh_rate_send_button = self.autopilot_param_button_maker(
            "send", "autopilot_refresh_rate"
        )
        self.autopilot_refresh_rate_reset_button = self.autopilot_param_button_maker(
            "reset", "autopilot_refresh_rate"
        )
        self.autopilot_refresh_rate_layout.addWidget(self.autopilot_refresh_rate_label)
        self.autopilot_refresh_rate_layout.addWidget(
            self.autopilot_refresh_rate_text_box
        )
        self.autopilot_refresh_rate_layout.addWidget(
            self.autopilot_refresh_rate_send_button
        )
        self.autopilot_refresh_rate_layout.addWidget(
            self.autopilot_refresh_rate_reset_button
        )
        self.autopilot_param_input_layout.addLayout(self.autopilot_refresh_rate_layout)

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
        self.autopilot_param_input_groupbox.setLayout(self.autopilot_param_input_layout)
        self.left_tab2_layout.addWidget(self.autopilot_param_input_groupbox)
        # endregion bottom section
        # endregion Parameter input

        self.left_tab1.setLayout(self.left_tab1_layout)
        self.left_tab2.setLayout(self.left_tab2_layout)
        self.left_layout.addTab(self.left_tab1, "Boat Data")
        self.left_layout.addTab(self.left_tab2, "Autopilot Control")
        self.left_layout.setMaximumWidth(self.left_width)
        self.main_layout.addWidget(self.left_layout, 0, 0)

        # endregion left section

        # region middle section
        self.browser = QWebEngineView()
        self.browser.setHtml(constants.HTML_MAP)
        self.browser.setMinimumWidth(700)
        self.browser.setMinimumHeight(700)
        self.middle_layout.addWidget(self.browser, 0, 1)
        self.main_layout.addLayout(self.middle_layout, 0, 1)
        # endregion middle section

        # region right section
        self.right_width = 300

        # region tab1: waypoint data
        self.right_tab1_label = QLabel("Waypoints")
        self.right_tab1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_tab1_table = QTableWidget()
        self.right_tab1_table.setMinimumWidth(self.right_width)

        self.can_send_waypoints = True
        self.send_waypoints_button = self.pushbutton_maker(
            "Send Waypoints",
            self.icons.upload,
            self.send_waypoints,
            self.right_width // 2,
            50,
            self.can_send_waypoints,
        )

        self.can_reset_waypoints = False
        self.clear_waypoints_button = self.pushbutton_maker(
            "Clear Waypoints",
            self.icons.delete,
            self.clear_waypoints,
            self.right_width // 2,
            50,
            self.can_send_waypoints,
        )

        self.can_pull_waypoints = True
        self.pull_waypoints_button = self.pushbutton_maker(
            "Pull Waypoints",
            self.icons.download,
            self.pull_waypoints,
            self.right_width // 2,
            50,
            self.can_pull_waypoints,
        )

        self.focus_boat_button = self.pushbutton_maker(
            "Zoom to Boat",
            self.icons.boat,
            self.zoom_to_boat,
            self.right_width // 2,
            50,
        )

        self.right_tab1_layout.addWidget(self.right_tab1_label, 0, 0, 1, 2)
        self.right_tab1_layout.addWidget(self.right_tab1_table, 1, 0, 1, 2)
        self.right_tab1_layout.addWidget(self.send_waypoints_button, 2, 0)
        self.right_tab1_layout.addWidget(self.clear_waypoints_button, 2, 1)
        self.right_tab1_layout.addWidget(self.focus_boat_button, 3, 0)
        self.right_tab1_layout.addWidget(self.pull_waypoints_button, 3, 1)
        self.right_tab1.setLayout(self.right_tab1_layout)
        # endregion tab1: waypoint data

        # region tab2: buoy data
        self.right_tab2_label = QLabel("Buoy Data")
        self.right_tab2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_tab2_table = QTableWidget()
        self.right_tab2_table.setMinimumWidth(self.right_width)

        self.edit_buoy_data_button = self.pushbutton_maker(
            "Edit Buoy Data",
            self.icons.edit,
            self.edit_buoy_data,
            self.right_width,
            50,
        )

        self.save_buoy_data_button = self.pushbutton_maker(
            "Save Buoy Data",
            self.icons.save,
            self.save_buoy_data,
            self.right_width // 2,
            50,
        )

        self.load_buoy_data_button = self.pushbutton_maker(
            "Load Buoy Data",
            self.icons.hard_drive,
            self.load_buoy_data,
            self.right_width // 2,
            50,
        )

        self.right_tab2_layout.addWidget(self.right_tab2_label, 0, 0, 1, 2)
        self.right_tab2_layout.addWidget(self.right_tab2_table, 1, 0, 1, 2)
        self.right_tab2_layout.addWidget(self.edit_buoy_data_button, 2, 0, 1, 2)
        self.right_tab2_layout.addWidget(self.save_buoy_data_button, 3, 0)
        self.right_tab2_layout.addWidget(self.load_buoy_data_button, 3, 1)
        self.right_tab2.setLayout(self.right_tab2_layout)
        # endregion tab2: buoy data

        self.right_layout.addTab(self.right_tab1, "Waypoints")
        self.right_layout.addTab(self.right_tab2, "Buoy Data")
        self.right_layout.setMaximumWidth(self.right_width)
        self.main_layout.addWidget(self.right_layout, 0, 2)
        # endregion right section

        self.setLayout(self.main_layout)
        # endregion setup UI

        self.telemetry_handler = thread_classes.TelemetryUpdater()
        self.js_waypoint_handler = thread_classes.WaypointFetcher()

        # Connect signals to update UI
        self.telemetry_handler.boat_data_fetched.connect(self.update_telemetry_display)
        self.js_waypoint_handler.waypoints_fetched.connect(
            self.update_waypoints_display
        )

        # Slow timer
        self.slow_timer = constants.SLOW_TIMER
        constants.SLOW_TIMER.timeout.connect(self.update_telemetry_starter)

        # Fast timer
        self.fast_timer = constants.FAST_TIMER
        constants.FAST_TIMER.timeout.connect(self.js_waypoint_handler_starter)

        # Start timers
        self.fast_timer.start()
        self.slow_timer.start()

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
                    constants.TELEMETRY_SERVER_ENDPOINTS["set_waypoints"],
                    json={"value": self.waypoints},
                )
                js_code = "map.change_color_waypoints('red')"
                self.browser.page().runJavaScript(js_code)
            except requests.exceptions.ConnectionError as e:
                print(f"Connection error: {e}")
                print(f"Waypoints: {self.waypoints}")
        else:
            try:
                requests.post(
                    constants.TELEMETRY_SERVER_ENDPOINTS["waypoints_test"],
                    json={"value": self.waypoints},
                )
            except requests.exceptions.ConnectionError as e:
                print(f"Connection error: {e}")
                print(f"Waypoints: {self.waypoints}")

    def pull_waypoints(self) -> None:
        """Pull waypoints from the telemetry server and add them to the map."""

        try:
            remote_waypoints: list[list[float]] = requests.get(
                constants.TELEMETRY_SERVER_ENDPOINTS["boat_status"]
            ).json()["current_route"]
            if remote_waypoints:
                existing_waypoints = self.waypoints.copy()
                self.browser.page().runJavaScript("map.clear_waypoints()")
                for waypoint in remote_waypoints:
                    self.browser.page().runJavaScript(
                        f"map.add_waypoint({waypoint[0]}, {waypoint[1]})"
                    )
                self.browser.page().runJavaScript("map.change_color_waypoints('red')")
                for waypoint in existing_waypoints:
                    self.browser.page().runJavaScript(
                        f"map.add_waypoint({waypoint[0]}, {waypoint[1]})"
                    )
            else:
                print("No waypoints found on the server.")
            self.can_pull_waypoints = False
            self.pull_waypoints_button.setDisabled(not self.can_pull_waypoints)

        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}")

    def get_autopilot_parameters(self) -> None:
        """Get autopilot parameters from the server."""

        try:
            remote_params: dict = requests.get(
                constants.TELEMETRY_SERVER_ENDPOINTS["get_autopilot_parameters"]
            ).json()
            if remote_params == {}:
                print("Connection successful but no parameters found.")
            else:
                self.autopilot_parameters = remote_params
                self.forced_jibe_checkbox.setChecked(
                    self.autopilot_parameters["perform_forced_jibe_instead_of_tack"]
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
        """Send all autopilot parameters to the server."""

        try:
            self.autopilot_parameters = {
                "perform_forced_jibe_instead_of_tack": self.forced_jibe_checkbox.isChecked(),
                "waypoint_accuracy": float(self.waypoint_accuracy_text_box.text()),
                "no_sail_zone_size": float(self.no_sail_zone_size_text_box.text()),
                "autopilot_refresh_rate": float(
                    self.autopilot_refresh_rate_text_box.text()
                ),
                "tack_distance": float(self.tack_distance_text_box.text()),
            }
            requests.post(
                constants.TELEMETRY_SERVER_ENDPOINTS["set_autopilot_parameters"],
                json={"value": self.autopilot_parameters},
            )
        except ValueError or requests.exceptions.ConnectionError as e:
            print(f"Error: {e}")
            print(f"Parameters: {self.autopilot_parameters}")

    def send_individual_parameter(self, parameter: str) -> None:
        """
        Send individual autopilot parameter to the server.

        Parameters
        ----------
        parameter
            The autopilot parameter to send. Should be one of the keys in `self.autopilot_parameters`.
        """

        try:
            self.autopilot_parameters = {
                "perform_forced_jibe_instead_of_tack": self.forced_jibe_checkbox.isChecked(),
                "waypoint_accuracy": self.safe_convert_to_float(
                    self.waypoint_accuracy_text_box.text()
                ),
                "no_sail_zone_size": self.safe_convert_to_float(
                    self.no_sail_zone_size_text_box.text()
                ),
                "autopilot_refresh_rate": self.safe_convert_to_float(
                    self.autopilot_refresh_rate_text_box.text()
                ),
                "tack_distance": self.safe_convert_to_float(
                    self.tack_distance_text_box.text()
                ),
            }

            requests.post(
                constants.TELEMETRY_SERVER_ENDPOINTS["set_autopilot_parameters"],
                json={"value": {parameter: self.autopilot_parameters[parameter]}},
            )

        except ValueError or requests.exceptions.ConnectionError as e:
            print(f"Error: {e}")
            print(f"Inputed parameter: {parameter}")

    def reset_individual_parameter(self, parameter: str) -> None:
        """
        Reset individual autopilot parameter to the value from the server.

        Parameters
        ----------
        parameter
            The autopilot parameter to reset. Should be one of the keys in `self.autopilot_parameters`.
        """

        try:
            existing_params: dict = requests.get(
                constants.TELEMETRY_SERVER_ENDPOINTS["get_autopilot_parameters"]
            ).json()
            if existing_params == {}:
                print("Connection successful but no parameters found.")
            else:
                self.autopilot_parameters[parameter] = existing_params[parameter]
                self.forced_jibe_checkbox.setChecked(
                    self.autopilot_parameters["perform_forced_jibe_instead_of_tack"]
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
        """
        Save autopilot parameters to a file.

        Files are stored in the `autopilot_params` directory and are named `params_<timestamp>.json`
        where `<timestamp>` is nanoseconds since unix epoch.
        """

        try:
            self.autopilot_parameters = {
                "perform_forced_jibe_instead_of_tack": self.forced_jibe_checkbox.isChecked(),
                "waypoint_accuracy": float(self.waypoint_accuracy_text_box.text()),
                "no_sail_zone_size": float(self.no_sail_zone_size_text_box.text()),
                "autopilot_refresh_rate": float(
                    self.autopilot_refresh_rate_text_box.text()
                ),
                "tack_distance": float(self.tack_distance_text_box.text()),
            }
            file_path = PurePath(
                constants.AUTO_PILOT_PARAMS_DIR / f"params_{time.time_ns()}.json"
            )

            with open(file_path, "w") as f:
                json.dump(self.autopilot_parameters, f, indent=4)

        except ValueError as e:
            print(f"Error: {e}")
            print(f"Parameters: {self.autopilot_parameters}")

    def load_parameters(self) -> None:
        """
        Load values for the autopilot parameters from a file.

        If no file is selected, the most recent file in the `autopilot_params` directory is used.
        """

        try:
            param_files = os.listdir(constants.AUTO_PILOT_PARAMS_DIR)
            if not param_files:
                print("No parameter files found.")

            else:
                chosen_file = QFileDialog.getOpenFileName(
                    self,
                    "Select Parameter File",
                    constants.AUTO_PILOT_PARAMS_DIR.as_posix(),
                    "*.json",
                )
                if chosen_file == ("", ""):
                    chosen_file = [
                        PurePath(constants.AUTO_PILOT_PARAMS_DIR / max(param_files))
                    ]
                with open(chosen_file[0], "r") as f:
                    self.autopilot_parameters = json.load(f)
                    self.forced_jibe_checkbox.setChecked(
                        self.autopilot_parameters["perform_forced_jibe_instead_of_tack"]
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

    def send_image(self) -> None:
        """
        Send image to the server.

        This function only for testing purposes.
        """

        try:
            # read image from file and encode it to base64
            image = PurePath(constants.ASSETS_DIR / "test.jpg")
            with open(image, "rb") as f:
                image = f.read()
            base64_encoded_image = base64.b64encode(image).decode("utf-8")
            autopilot_parameters = self.autopilot_parameters
            autopilot_parameters["current_camera_image"] = base64_encoded_image
            requests.post(
                constants.TELEMETRY_SERVER_ENDPOINTS["set_autopilot_parameters"],
                json={"value": autopilot_parameters},
            ).json()
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}")
        except FileNotFoundError as e:
            print(f"File not found: {e}")

    def reset_parameters(self) -> None:
        """Reset all parameters to values from the server."""

        self.get_autopilot_parameters()

    def save_boat_data(self) -> None:
        """
        Saves latest entry in the `self.boat_data` array to a file.

        Files are stored in the `boat_data` directory and are named `boat_data_<timestamp>.json`
        where `<timestamp>` is nanoseconds since unix epoch.
        """

        try:
            file_path = PurePath(
                constants.BOAT_DATA_DIR / f"boat_data_{time.time_ns()}.json"
            )
            with open(file_path, "w") as f:
                json.dump(self.boat_data, f, indent=4)
        except Exception as e:
            print(f"Error: {e}")

    def edit_boat_data_limits(self) -> None:
        """
        Opens a text edit window to edit the telemetry data limits.

        `self.edit_boat_data_limits_callback` is called when the user closes or clicks the save button in the text edit window.
        `self.edit_boat_data_limits_callback` recieves the text from the text edit window when the user clicks the save button,
        otherwise it recieves the text without any changes.
        """

        try:
            initial_config = json.dumps(self.telemetry_data_limits, indent=4)
            self.text_edit_window = TextEditWindow(initial_text=initial_config)
            self.text_edit_window.setWindowTitle("Edit Boat Data Limits")
            self.text_edit_window.user_text_emitter.connect(
                self.edit_boat_data_limits_callback
            )
            self.text_edit_window.show()
        except Exception as e:
            print(f"Error: {e}")

    def edit_boat_data_limits_callback(self, text: str) -> None:
        """
        Callback function for the `edit_boat_data_limits` function.

        This function is called when the user closes the text edit window.
        It retrieves the edited text and saves it to the `self.telemetry_data_limits` variable and closes the window.

        Parameters
        ----------
        text
            The text entered by the user in the text edit window.
        """

        try:
            edited_config = text
            self.telemetry_data_limits = json.loads(edited_config)
        except Exception as e:
            print(f"Error: {e}")

    def load_boat_data_limits(self) -> None:
        """
        Load upper and lower bounds for some of the telemetry data, if no file selected use `default.json`.

        Files are stored in the `boat_data_bounds` directory and are named `boat_data_bounds_<timestamp>.json`
        where `<timestamp>` is nanoseconds since unix epoch.
        """

        try:
            chosen_file = QFileDialog.getOpenFileName(
                self,
                "Select Parameter File",
                constants.BOAT_DATA_LIMITS_DIR.as_posix(),
                "*.json",
            )
            if chosen_file == ("", ""):
                chosen_file = [
                    PurePath(constants.BOAT_DATA_LIMITS_DIR / "default.json")
                ]
            with open(chosen_file[0], "r") as f:
                self.telemetry_data_limits = json.load(f)
        except FileNotFoundError as e:
            print(e)

    def save_boat_data_limits(self) -> None:
        """
        Save upper and lower bounds for some of the telemetry data.

        Files are stored in the `boat_data_bounds` directory and are named `boat_data_bounds_<timestamp>.json`
        where `<timestamp>` is nanoseconds since unix epoch.
        """

        try:
            file_path = PurePath(
                constants.BOAT_DATA_LIMITS_DIR
                / f"boat_data_bounds_{time.time_ns()}.json",
            )
            with open(file_path, "w") as f:
                json.dump(self.telemetry_data_limits, f, indent=4)
        except Exception as e:
            print(f"Error: {e}")

    def edit_buoy_data(self) -> None:
        """
        Opens a text edit window to edit the buoy data.

        `self.edit_buoy_data_callback` is called when the user closes or clicks the save button in the text edit window.
        `self.edit_buoy_data_callback` recieves the text from the text edit window when the user clicks the save button,
        otherwise it recieves the text without any changes.
        """

        try:
            buoy_json = json.dumps(self.buoys, indent=4)
            self.text_edit_window = TextEditWindow(initial_text=buoy_json)
            self.text_edit_window.setWindowTitle("Edit Buoy GPS Coordinates")
            self.text_edit_window.user_text_emitter.connect(
                self.edit_buoy_data_callback
            )
            self.text_edit_window.show()
        except Exception as e:
            print(f"Error: {e}")

    def edit_buoy_data_callback(self, text: str) -> None:
        """
        Callback function for the `edit_buoy_data` function.

        This function is called when the user closes the text edit window.
        It retrieves the edited text and saves it to the `self.buoys` variable and closes the window.

        Parameters
        ----------
        text
            The text entered by the user in the text edit window.
        """

        try:
            edited_bouys = text
            if self.buoys != json.loads(edited_bouys):
                self.buoys = json.loads(edited_bouys)
                self.update_buoy_table()

        except Exception as e:
            print(f"Error: {e}")

    def update_buoy_table(self) -> None:
        self.right_tab2_table.clear()
        self.right_tab2_table.setRowCount(0)
        self.right_tab2_table.setColumnCount(2)
        self.right_tab2_table.setHorizontalHeaderLabels(["Latitude", "Longitude"])

        clear_js_buoys = "map.clear_buoys()"
        self.browser.page().runJavaScript(clear_js_buoys)

        for buoy in self.buoys:
            self.right_tab2_table.insertRow(self.right_tab2_table.rowCount())
            add_js_buoy = (
                f"map.add_buoy({self.buoys[buoy]['lat']}, {self.buoys[buoy]['lon']})"
            )
            self.browser.page().runJavaScript(add_js_buoy)
            for i, coord in enumerate(["lat", "lon"]):
                item = QTableWidgetItem(f"{float(self.buoys[buoy][coord]):.13f}")
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.right_tab2_table.setItem(
                    self.right_tab2_table.rowCount() - 1, i, item
                )
        self.right_tab2_table.resizeColumnsToContents()
        self.right_tab2_table.resizeRowsToContents()

    def save_buoy_data(self) -> None:
        """
        Saves latest entry in the `self.buoys` array to a file.

        Files are stored in the `buoy_data` directory and are named `buoy_data_<timestamp>.json`
        where `<timestamp>` is nanoseconds since unix epoch.
        """

        try:
            file_path = PurePath(
                constants.BUOY_DATA_DIR / f"buoy_data_{time.time_ns()}.json"
            )
            with open(file_path, "w") as f:
                json.dump(self.buoys, f, indent=4)
        except Exception as e:
            print(f"Error: {e}")

    def load_buoy_data(self) -> None:
        """
        Load buoy data from the `buoy_data` directory, if none selected use `default.json`.

        Files are stored in the `buoy_data` directory and are named `buoy_data_<timestamp>.json`
        where `<timestamp>` is nanoseconds since unix epoch.
        """

        try:
            buoy_files = os.listdir(constants.BUOY_DATA_DIR)
            if not buoy_files:
                print("No buoy data files found.")
            else:
                chosen_file = QFileDialog.getOpenFileName(
                    self,
                    "Select Buoy Data File",
                    constants.BUOY_DATA_DIR.as_posix(),
                    "*.json",
                )
                if chosen_file == ("", ""):
                    chosen_file = [PurePath(constants.BUOY_DATA_DIR / "default.json")]
                with open(chosen_file[0], "r") as f:
                    self.buoys = json.load(f)
                self.update_buoy_table()
        except FileNotFoundError as e:
            print(e)

    def clear_waypoints(self) -> None:
        """Clear waypoints from the table."""

        self.can_reset_waypoints = False
        self.can_pull_waypoints = True
        self.pull_waypoints_button.setDisabled(not self.can_pull_waypoints)
        js_code = "map.clear_waypoints()"
        self.browser.page().runJavaScript(js_code)

    def zoom_to_boat(self) -> None:
        """Center the view on the boat's position."""

        if isinstance(self.boat_data.get("position"), list):
            js_code = "map.focus_map_on_boat()"
            self.browser.page().runJavaScript(js_code)
        else:
            print("Boat position not available.")

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
        self.clear_waypoints_button.setDisabled(not self.can_reset_waypoints)
        self.pull_waypoints_button.setDisabled(not self.can_pull_waypoints)
        if self.num_waypoints != len(self.waypoints):
            self.num_waypoints = len(self.waypoints)
            if self.num_waypoints == 0:
                self.can_pull_waypoints = True
            else:
                self.can_pull_waypoints = False
            self.can_send_waypoints = True
            self.can_reset_waypoints = True

            self.right_tab1_table.clear()
            self.right_tab1_table.setRowCount(0)
            self.right_tab1_table.setColumnCount(2)
            self.right_tab1_table.setHorizontalHeaderLabels(["Latitude", "Longitude"])

            for waypoint in waypoints:
                self.right_tab1_table.insertRow(self.right_tab1_table.rowCount())
                for i, coord in enumerate(waypoint):
                    item = QTableWidgetItem(f"{coord:.13f}")
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    self.right_tab1_table.setItem(
                        self.right_tab1_table.rowCount() - 1, i, item
                    )
            self.right_tab1_table.resizeColumnsToContents()
            self.right_tab1_table.resizeRowsToContents()

    def update_telemetry_display(
        self,
        boat_data: dict[
            str, Union[float, str, tuple[float, float], list[tuple[float, float]]]
        ],
    ) -> None:
        """
        Update telemetry display with boat data.

        Parameters
        ----------
        boat_data
            Dictionary containing boat data fetched from the telemetry server.
        """

        def fix_formatting(data_item: Optional[float]) -> str:
            """
            Applies some formatting rules that multiple keys have in common.

            <ol>
            <li> If the value is None, it is replaced with -69.420.
            <li> If the value is negative, it is multiplied by -1.
            <li> The value is rounded to 5 decimal places.
            </ol>

            Examples
            -------
            >>> fix_formatting(-69.420)
            '69.42000'
            >>> fix_formatting(None)
            '-69.42000'

            Parameters
            ----------
            data_item
                The float value to format.

            Returns
            -------
            str
                The formatted value.
            """

            return (
                f"{abs(data_item):.5f}" if data_item is not None else f"{-69.420:.5f}"
            )

        def convert_to_seconds(ms: float) -> float:
            """
            Converts milliseconds to seconds. 1000 milliseconds = 1 second.

            Parameters
            ----------
            ms
                The time in milliseconds.

            Returns
            -------
            float
                The time in seconds.
            """

            return ms * 1000

        def get_distance_to_waypoint(
            cur_position: list[float, float], next_waypoint: list[float, float]
        ) -> float:
            """
            Calculates the distance to the next waypoint from the current position using geopy.

            Parameters
            ----------
            cur_position
                The current position of the boat as a list of latitude and longitude.
            next_waypoint
                The next waypoint as a list of latitude and longitude.

            Returns
            -------
            float
                The distance to the next waypoint in meters.
            """

            if next_waypoint:
                return geopy.distance.geodesic(next_waypoint, cur_position).m
            else:
                return geopy.distance.Distance(0.0).m

        try:
            current_position = boat_data.get("position")
            waypoint_route = boat_data.get("current_route", [])
            index = boat_data.get("current_waypoint_index", "N/A")
            distance_to_next_waypoint = get_distance_to_waypoint(
                current_position, waypoint_route[index]
            )
        except Exception as e:
            print(e)
            distance_to_next_waypoint = 0.0

        if self.boat_data == {}:
            telemetry_text = f"""Boat Info:
Position: {boat_data.get("position", -69.420)[0]:.8f}, {boat_data.get("position", -69.420)[1]:.8f}
State: {boat_data.get("state", "N/A")}
Speed: {boat_data.get("speed", -69.420):.5f} knots
Distance To Next WP: {distance_to_next_waypoint:.5f} meters
Bearing: {boat_data.get("bearing", -69.420):.5f}°
Heading: {boat_data.get("heading", -69.420):.5f}°
True Wind Speed: {boat_data.get("true_wind_speed", -69.420):.5f} knots
True Wind Angle: {boat_data.get("true_wind_angle", -69.420):.5f}°
Apparent Wind Speed: {boat_data.get("apparent_wind_speed", -69.420):.5f} knots
Apparent Wind Angle: {boat_data.get("apparent_wind_angle", -69.420):.5f}°
Sail Angle: {boat_data.get("sail_angle", -69.420):.5f}°
Rudder Angle: {boat_data.get("rudder_angle", -69.420):.5f}°
Current Waypoint Index: {boat_data.get("current_waypoint_index", "N/A")}
Current Route: {boat_data.get("current_route", "N/A")}

VESC Data:
RPM: {fix_formatting(boat_data.get("vesc_data_rpm"))}
Duty Cycle: {fix_formatting(boat_data.get("vesc_data_duty_cycle"))}%
Amp Hours: {boat_data.get("vesc_data_amp_hours", -69.420):.5f} Ah
Current to VESC: {boat_data.get("vesc_data_current_to_vesc", -69.420):.5f} A
Voltage to VESC: {boat_data.get("vesc_data_voltage_to_vesc", -69.420):.5f} V
Wattage to Motor: {fix_formatting(boat_data.get("vesc_data_wattage_to_motor"))} W
Voltage to Motor: {boat_data.get("vesc_data_voltage_to_motor", -69.420):.5f} V
Time Since VESC Startup: {convert_to_seconds(boat_data.get("vesc_data_time_since_vesc_startup_in_ms", -1.0)):.5f} seconds 
Motor Temperature: {fix_formatting(boat_data.get("vesc_data_motor_temperature"))}°C
"""
        else:
            for key in self.boat_data_averages.keys():
                # self.boat_data = data from one iteration in the past
                # boat_data = data from the current iteration
                current_value = boat_data.get(key)
                if current_value is not None:
                    self.boat_data_averages[key] = (
                        self.boat_data_averages[key] + current_value
                    ) / 2

            telemetry_text = f"""Boat Info:
Position: {boat_data.get("position", -69.420)[0]:.8f}, {boat_data.get("position", -69.420)[1]:.8f}
State: {boat_data.get("state", "N/A")}
Speed: {boat_data.get("speed", -69.420):.5f} knots
Distance To Next WP: {distance_to_next_waypoint:.5f} meters
Bearing: {boat_data.get("bearing", -69.420):.5f}°
Heading: {boat_data.get("heading", -69.420):.5f}°
True Wind Speed: {boat_data.get("true_wind_speed", -69.420):.5f} knots
True Wind Angle: {boat_data.get("true_wind_angle", -69.420):.5f}°
Apparent Wind Speed: {boat_data.get("apparent_wind_speed", -69.420):.5f} knots
Apparent Wind Angle: {boat_data.get("apparent_wind_angle", -69.420):.5f}°
Sail Angle: {boat_data.get("sail_angle", -69.420):.5f}°
Rudder Angle: {boat_data.get("rudder_angle", -69.420):.5f}°
Current Waypoint Index: {boat_data.get("current_waypoint_index", "N/A")}
Current Route: {boat_data.get("current_route", "N/A")}

VESC Data:
RPM: {fix_formatting(self.boat_data_averages.get("vesc_data_rpm"))}
Duty Cycle: {fix_formatting(boat_data.get("vesc_data_duty_cycle"))}%
Amp Hours: {self.boat_data_averages.get("vesc_data_amp_hours", -69.420):.5f} Ah
Current to VESC: {self.boat_data_averages.get("vesc_data_current_to_vesc", -69.420):.5f} A
Voltage to VESC: {self.boat_data_averages.get("vesc_data_voltage_to_vesc", -69.420):.5f} V
Wattage to Motor: {fix_formatting(self.boat_data_averages.get("vesc_data_wattage_to_motor"))} W
Voltage to Motor: {self.boat_data_averages.get("vesc_data_voltage_to_motor", -69.420):.5f} V
Time Since VESC Startup: {convert_to_seconds(boat_data.get("vesc_data_time_since_vesc_startup_in_ms", -1)):.5f} seconds 
Motor Temperature: {fix_formatting(self.boat_data_averages.get("vesc_data_motor_temperature"))}°C
"""

        if isinstance(boat_data.get("position"), list):
            js_code = f"map.update_boat_location({boat_data.get('position')[0]}, {boat_data.get('position')[1]})"
            self.browser.page().runJavaScript(js_code)

        if isinstance(boat_data.get("heading"), float):
            js_code = f"map.update_boat_heading({boat_data.get('heading')})"
            self.browser.page().runJavaScript(js_code)

        self.left_tab1_text_section.setText(telemetry_text)
        self.boat_data = boat_data

    # endregion pyqt thread functions

    # region helper functions
    def autopilot_param_button_maker(self, action: str, param: str) -> QPushButton:
        """
        Create a button for autopilot parameters. Wrapper for `self.pushbutton_maker`.

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

        if action == "send":
            return self.pushbutton_maker(
                button_text="",
                icon=self.icons.upload,
                max_width=25,
                min_height=None,
                function=partial(self.send_individual_parameter, param),
            )
        elif action == "reset":
            return self.pushbutton_maker(
                button_text="",
                icon=self.icons.delete,
                max_width=25,
                min_height=None,
                function=partial(self.reset_individual_parameter, param),
            )
        else:
            raise ValueError("Invalid action. Use 'send' or 'reset'.")

    def pushbutton_maker(
        self,
        button_text: str,
        icon: QIcon,
        function: callable,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        is_clickable: bool = True,
    ) -> QPushButton:
        """
        Create a QPushButton with the specified features.

        Parameters
        ----------
        button_text
            The text to display on the button.
        icon
            The icon to display on the button.
        function
            The function to connect to the button's clicked signal.
        max_width
            The maximum width of the button. If not specified, not used.
        min_height
            The minimum height of the button. If not specified, not used.
        is_clickable
            Whether the button should be clickable. Defaults to `True`.

        Returns
        -------
        QPushButton
            The created button.
        """

        button = QPushButton(button_text)
        button.setIcon(icon)
        if max_width is not None:
            button.setMaximumWidth(max_width)
        if min_height is not None:
            button.setMinimumHeight(min_height)
        button.clicked.connect(function)
        button.setDisabled(not is_clickable)
        return button

    def safe_convert_to_float(self, x) -> Union[float, Literal[0]]:
        """
        Safely convert a value to float, returning 0 if conversion fails.

        Parameters
        ----------
        x
            The value to convert to float.

        Returns
        -------
        float or Literal[0]
            The converted float value, or 0 if conversion fails.
        """

        try:
            return float(x)
        except ValueError:
            return 0

    # endregion helper functions
