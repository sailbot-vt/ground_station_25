import requests
import constants
from typing import Union
from PyQt5.QtCore import QThread, pyqtSignal
# import numpy as np
# import cv2


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
        """Fetch boat data from the telemetry server and emit it."""

        try:
            boat_status: dict[
                str, Union[str, float, list[float], list[tuple[float, float]]]
            ]
            boat_status = requests.get(
                constants.TELEMETRY_SERVER_ENDPOINTS["boat_status"], timeout=5
            ).json()
        except requests.RequestException:
            boat_status = {
                "position": [36.983731367697374, -76.29555376681454],
                "state": "N/A",
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
                "current_route": [(0.0, 0.0)],
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
        """Fetch waypoints from the local server and emit them."""

        try:
            waypoints = requests.get(constants.WAYPOINTS_SERVER_URL).json()
        except requests.RequestException:
            waypoints = []
        self.waypoints_fetched.emit(waypoints)

    def run(self) -> None:
        self.get_waypoints()


# class ImageFetcher(QThread):
#     """
#     Thread to fetch images from the telemetry server.

#     Inherits
#     -------
#     `QThread`

#     Attributes
#     ----------
#     image_fetched : `pyqtSignal`
#         Signal to send image to the main thread. Emits a numpy array containing the image.
#     """

#     image_fetched = pyqtSignal(np.ndarray)

#     def __init__(self) -> None:
#         super().__init__()

#     def get_image(self) -> None:
#         try:
#             base64_encoded_image = requests.get(
#                 constants.TELEMETRY_SERVER_ENDPOINTS["get_autopilot_parameters"],
#                 timeout=5,
#             ).json()["current_camera_image"]
#             jpg_original = base64.b64decode(base64_encoded_image)
#             jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
#             img = cv2.imdecode(jpg_as_np, flags=1)
#             self.image_fetched.emit(img)
#         except Exception as e:
#             print(f"Failed to fetch image: {e}")
#             image = np.zeros((480, 640, 3), dtype=np.uint8)
#             self.image_fetched.emit(image)

#     def run(self) -> None:
#         self.get_image()
