import sys
from io import StringIO

import pandas as pd
import requests
from PyQt5.QtCore import QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow

TELEMETRY_SERVER_URL = "http://18.191.164.84:8080/"

HTML_MAP = open("main.html").read()

# data from https://virginiatech.maps.arcgis.com/home/item.html?id=cb1886ff0a9d4156ba4d2fadd7e8a139


class MapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SailBussy Ground Station")
        self.setGeometry(100, 100, 800, 600)

        self.browser = QWebEngineView()
        self.browser.setHtml(HTML_MAP)
        self.setCentralWidget(self.browser)

        # Timer to run functions every 5 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.clear_map)
        self.timer.timeout.connect(self.update_location)
        self.timer.timeout.connect(self.update_wind_data)
        self.timer.start(5000)
    def update_location(self):
        """Update the map with the latest boat location."""
        boat_data = self.get_boat_location()
        if boat_data:
            lat, lon, heading = boat_data
            js_code = f"map.update_boat({lat}, {lon}, {heading});"
            self.browser.page().runJavaScript(js_code)

    def clear_map(self):
        """Clear all wind arrows from the map."""
        self.browser.page().runJavaScript("map.clear_wind_arrows();")

    def get_boat_location(self):
        """Fetch boat location from telemetry server."""
        try:
            boat_status = {
                "latitude": 36.983731367697374,
                "longitude": -76.29555376681454,
                "heading": 0,
            }
            # boat_status = requests.get(TELEMETRY_SERVER_URL + "boat_status/get").json()
            return (
                boat_status["latitude"],
                boat_status["longitude"],
                boat_status["heading"],
            )
        except Exception as e:
            print(f"Error fetching location: {e}")
            return (0, 0, 0)

    def update_wind_data(self):
        """Fetch wind data and update the map with wind arrows."""
        wind_data = get_buoy_wind_data() + get_station_wind_data()

        for wind in wind_data:
            lat, lon = wind["lat"], wind["lon"]
            wind_dir = wind["wind_dir"]
            wind_speed = wind["wind_speed"]

            js_code = (
                f"map.add_wind_arrow({lat}, {lon}, {wind_dir - 180}, {wind_speed});"
            )
            self.browser.page().runJavaScript(js_code)


def get_buoy_wind_data():
    """Fetch wind data from NOAA buoys."""
    url = "https://www.ndbc.noaa.gov/data/latest_obs/latest_obs.txt"
    try:
        response = requests.get(url)
        raw_data = response.text

        # Extract header labels
        lines = raw_data.split("\n")
        labels = [
            f"{i} ({j})"
            for i, j in zip(
                lines[0].replace("#", "").split(), lines[1].replace("#", "").split()
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

        df = df[["LAT (deg)", "LON (deg)", "WDIR (degT)", "WSPD (m/s)"]].dropna()
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
    except Exception as e:
        print(f"Error fetching buoy data: {e}")
        return []


def get_station_wind_data():
    """Fetch wind data from NOAA weather stations."""
    url = "https://aviationweather.gov/data/cache/metars.cache.csv"
    try:
        df = pd.read_csv(url, skiprows=5, na_values="VRB")

        df = df[["latitude", "longitude", "wind_dir_degrees", "wind_speed_kt"]].dropna()

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
    except Exception as e:
        print(f"Error fetching station data: {e}")
        return []


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapApp()
    window.show()
    sys.exit(app.exec())
