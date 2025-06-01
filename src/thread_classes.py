import requests
import constants
from typing import Union
from PyQt5.QtCore import QThread, pyqtSignal


class TelemetryUpdater(QThread):
    """
    Thread to fetch telemetry data from the telemetry server.

    Inherits
    --------
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
        """Fetch boat data from the telemetry server and emit it."""

        try:
            boat_status: dict[str, Union[str, float, list[float], list[list[float]]]]
            boat_status = requests.get(
                constants.TELEMETRY_SERVER_ENDPOINTS["boat_status"]
            ).json()
        except requests.exceptions.RequestException:
            boat_status = {
                "position": [36.983731367697374, -76.29555376681454],
                "state": "failed_to_fetch",
                "full_autonomy_maneuver": "N/A",
                "speed": 0.0,
                "bearing": 0.0,
                "heading": 0.0,
                "true_wind_speed": 0.0,
                "true_wind_angle": 0.0,
                "apparent_wind_speed": 0.0,
                "apparent_wind_angle": 0.0,
                "sail_angle": 0.0,
                "rudder_angle": 0.0,
                "current_waypoint_index": 0,
                "current_route": [[0.0, 0.0]],
                "vesc_data_rpm": 0.0,
                "vesc_data_duty_cycle": 0.0,
                "vesc_data_amp_hours": 0.0,
                "vesc_data_amp_hours_charged": 0.0,
                "vesc_data_current_to_vesc": 0.0,
                "vesc_data_voltage_to_motor": 0.0,
                "vesc_data_voltage_to_vesc": 0.0,
                "vesc_data_wattage_to_motor": 0.0,
                "vesc_data_time_since_vesc_startup_in_ms": 0.0,
                "vesc_data_motor_temperature": 0.0,
            }
            print("Failed to fetch boat data. Using default values.")
        self.boat_data_fetched.emit(boat_status)

    def run(self) -> None:
        self.get_boat_data()


class WaypointFetcher(QThread):
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
        """Fetch waypoints from the local server and emit them."""

        try:
            waypoints = requests.get(constants.WAYPOINTS_SERVER_URL).json()
        except requests.exceptions.RequestException:
            waypoints = []
            print("Failed to fetch waypoints. Using empty list.")
        self.waypoints_fetched.emit(waypoints)

    def run(self) -> None:
        self.get_waypoints()


class ImageFetcher(QThread):
    """
    Thread to fetch images from the telemetry server.

    Inherits
    -------
    `QThread`

    Attributes
    ----------
    image_fetched : `pyqtSignal`
        Signal to send image to the main thread. Emits a base64 encoded string of the image.
    """

    image_fetched = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()

    def get_image(self) -> None:
        try:
            image_data = requests.get(
                constants.TELEMETRY_SERVER_ENDPOINTS["get_autopilot_parameters"],
                timeout=5,
            ).json()
            base64_encoded_image = image_data.get("current_camera_image")

        except requests.exceptions.RequestException:
            base64_encoded_image = open(
                constants.ASSETS_DIR / "cool-guy-base64.txt"
            ).read()
            print("Failed to fetch image. Using cool guy image.")

        self.image_fetched.emit(base64_encoded_image)

    def run(self) -> None:
        self.get_image()
