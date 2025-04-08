import os
import sys
from pathlib import Path

# base url for telemetry server
TELEMETRY_SERVER_URL = "http://18.191.164.84:8080/"

# endpoints for telemetry server, format is `TELEMETRY_SERVER_URL` + `endpoint`
TELEMETRY_SERVER_ENDPOINTS = {
    "boat_status": TELEMETRY_SERVER_URL + "boat_status/get",
    "waypoints_test": TELEMETRY_SERVER_URL + "waypoints/test",
    "get_waypoints": TELEMETRY_SERVER_URL + "waypoints/get",
    "set_waypoints": TELEMETRY_SERVER_URL + "waypoints/set",
    "get_autopilot_parameters": TELEMETRY_SERVER_URL + "autopilot_parameters/get",
    "set_autopilot_parameters": TELEMETRY_SERVER_URL + "autopilot_parameters/set",
}

# url for local waypoints server
WAYPOINTS_SERVER_URL = "http://localhost:3001/waypoints"

try:
    # should be the path to wherever `ground_station_25` is located
    TOP_LEVEL_DIR = Path(os.getcwd())

    SRC_DIR = Path(TOP_LEVEL_DIR / "src")

    HTML_MAP_PATH = Path(SRC_DIR / "map.html")
    HTML_MAP = open(HTML_MAP_PATH).read()

    if "autopilot_params" not in os.listdir(SRC_DIR):
        os.makedirs(SRC_DIR / "autopilot_params")

    if "boat_data" not in os.listdir(SRC_DIR):
        os.makedirs(SRC_DIR / "boat_data")

    AUTO_PILOT_PARAMS_DIR = Path(SRC_DIR / "autopilot_params")
    BOAT_DATA_DIR = Path(SRC_DIR / "boat_data")
    ASSETS_DIR = Path(TOP_LEVEL_DIR / "assets")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
