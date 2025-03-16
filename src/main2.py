import os
import sys
from io import StringIO

import numpy as np
import pandas as pd
import requests
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

TELEMETRY_SERVER_URL = "http://18.191.164.84:8080/"
WAYPOINTS_SERVER_URL = "http://localhost:3000/waypoints"


# Check if the main.html file exists before loading it
HTML_MAP_PATH = "main.html"
if not os.path.exists(HTML_MAP_PATH):
    print(f"Error: {HTML_MAP_PATH} not found.")
    sys.exit(1)
else:
    HTML_MAP = open(HTML_MAP_PATH).read()


class EditableListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.__persistent_editor_activated_flag = False
        self.__consecutive_add_when_enter_pressed_flag = True
        self.setStyleSheet("QListWidget::item { margin: 5px; }")

    def addItem(self, item):
        super().addItem(item)
        self.setCurrentItem(item)
        self.openPersistentEditor(item)  # open the editor
        self.setFocus()
        self.__persistent_editor_activated_flag = True

    def setConsecutiveAddWhenEnterPressed(self, f: bool):
        self.__consecutive_add_when_enter_pressed_flag = f

    def mousePressEvent(
        self, e
    ):  # make editor closed when user clicked somewhere else
        if self.__persistent_editor_activated_flag:
            self.closeIfPersistentEditorStillOpen()
        return super().mousePressEvent(e)

    def mouseDoubleClickEvent(
        self, e
    ):  # Let user edit the item when double clicking certain item
        item = self.itemAt(e.pos())
        self.openPersistentEditor(item)
        self.__persistent_editor_activated_flag = True
        return super().mouseDoubleClickEvent(e)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Tab:  # add new item when user pressed tab
            self.addItem(QListWidgetItem())
            return
        elif (
            e.key() == Qt.Key_Return
        ):  # make editor closed when user pressed enter
            self.closeIfPersistentEditorStillOpen()
            if self.__consecutive_add_when_enter_pressed_flag:
                pass
            else:
                return
        elif (
            e.key() == Qt.Key_Up or e.key() == Qt.Key_Down
        ):  # make editor closed when user pressed up or down button
            self.closeIfPersistentEditorStillOpen()
            return super().keyPressEvent(e)
        elif e.key() == Qt.Key_F2:  # Let user edit the item when pressing F2
            item = self.currentItem()
            if item:
                self.openPersistentEditor(item)
                self.__persistent_editor_activated_flag = True
        return super().keyPressEvent(e)

    def closeIfPersistentEditorStillOpen(
        self,
    ):  # Check if user are editing item
        item = self.currentItem()
        if item:
            if self.isPersistentEditorOpen(item):
                self.closePersistentEditor(item)
                self.__persistent_editor_activated_flag = False


class MapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SailBussy Ground Station")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()

        self.telemetry_display = QTextEdit()
        self.telemetry_display.setReadOnly(True)
        self.telemetry_display.setMinimumWidth(200)
        self.main_layout.addWidget(self.telemetry_display, 0)

        self.browser = QWebEngineView()
        self.browser.setHtml(HTML_MAP)
        self.main_layout.addWidget(self.browser, 1)

        self.right_widget = EditableListWidget()
        self.right_widget.setLayout(QVBoxLayout())
        self.main_layout.addWidget(self.right_widget, 0)

        self.central_widget.setLayout(self.main_layout)

        self.add_waypoint_button = QPushButton("Add Waypoint")
        self.add_waypoint_button.clicked.connect(self.add_waypoint)
        self.right_widget.layout().addWidget(self.add_waypoint_button)

        test = QListWidgetItem()
        self.right_widget.addItem(test)

        self.browser.page().setWebChannel(QWebChannel())
        # Timer to run functions every 5 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.clear_map)
        self.timer.timeout.connect(self.update_boat_data)
        self.timer.timeout.connect(self.update_wind_data)
        self.timer.timeout.connect(self.update_waypoints)
        self.timer.start(5000)

    def update_waypoints(self):
        """Update the map with waypoints."""
        existing_waypoints = {item.text() for item in self.right_widget.findItems("*", QListWidget.ItemIsSelectable)}
        waypoints = requests.get(WAYPOINTS_SERVER_URL).json()
        for waypoint in waypoints:
            waypoint_text = f"({waypoint[0]}, {waypoint[1]})"
            if waypoint_text not in existing_waypoints:
                self.right_widget.addItem(QListWidgetItem(waypoint_text))

        for item in self.right_widget.selectedItems():
            if item.text() == "":
                continue
            lat, lon = map(float, item.text().strip("()").split(","))
            js_code = f"map.add_waypoint({lat}, {lon});"
            self.browser.page().runJavaScript(js_code)

    def add_waypoint(self):
        """Add a waypoint to the list."""
        item = QListWidgetItem()  # Replace with actual lat/lon
        self.right_widget.addItem(item)

    def update_boat_data(self):
        """Update the map with the latest boat location."""
        boat_data = self.get_boat_data()
        if boat_data:
            self.update_telemetry_display(boat_data)
            js_code = f"map.update_boat({boat_data.get('position', [0, 0])[0]}, {boat_data.get('position', [0, 0])[1]}, {boat_data.get('heading', 0)});"
            self.browser.page().runJavaScript(js_code)

    def update_telemetry_display(self, boat_data):
        """Update telemetry display with boat data."""
        telemetry_text = f"""
Boat Info:
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
        self.telemetry_display.setText(telemetry_text)

    def clear_map(self):
        """Clear all wind arrows from the map."""
        self.browser.page().runJavaScript("map.clear_wind_arrows();")

    def get_boat_data(self):
        """Fetch boat data from telemetry server."""
        try:
            boat_status = requests.get(
                TELEMETRY_SERVER_URL + "boat_status/get"
            ).json()
            return boat_status
        except requests.RequestException:
            return {
                "position": [0, 0],
                "state": "N/A",
                "speed": 0,
                "bearing": 0,
                "heading": 0,
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

    def update_wind_data(self):
        """Fetch wind data and update the map with wind arrows."""
        wind_data = get_buoy_wind_data() + get_station_wind_data()

        for wind in wind_data:
            lat, lon = wind["lat"], wind["lon"]
            wind_dir = wind["wind_dir"]
            wind_speed = wind["wind_speed"]

            js_code = f"map.add_wind_arrow({lat}, {lon}, {wind_dir - 180}, {wind_speed});"
            self.browser.page().runJavaScript(js_code)


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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapApp()
    window.show()
    sys.exit(app.exec())
