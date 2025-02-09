import random
import sys
from io import StringIO

import pandas as pd
import requests
from PyQt5.QtCore import QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow

TELEMETRY_SERVER_URL = "http://18.191.164.84:8080/"

# HTML map with Leaflet.js
HTML_MAP = """
<!DOCTYPE html>
<html>
<head>
    <title>Sailboat Tracker</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>
<body>
    <div id="map" style="width: 100%; height: 100vh;"></div>
    
    <script>
        var map = L.map('map').setView([37.7749, -122.4194], 10);  // Default to San Francisco
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 18,
        }).addTo(map);

        var boatMarker = L.marker([37.7749, -122.4194]).addTo(map)
            .bindPopup("Sailboat Location");

        function updateBoat(lat, lon) {
            boatMarker.setLatLng([lat, lon])
                .bindPopup("Sailboat Location: " + lat.toFixed(5) + ", " + lon.toFixed(5))
            // No longer centering the map on the boat
        }

        function addWindArrow(lat, lon, windDir, windSpeed) {
            var windColor = windSpeed < 10 ? "green" : windSpeed < 20 ? "yellow" : "red";

            var windArrow = L.marker([lat, lon], {
                icon: L.divIcon({
                    className: 'wind-arrow',
                    html: `➤`,
                    iconSize: [20, 20],
                    iconAnchor: [10, 10]
                })
            }).addTo(map);

            // Apply rotation and color after the marker has been added to the map
            windArrow.on('add', function() {
                var arrowElement = windArrow._icon;
                arrowElement.style.transform = `rotate(${windDir}deg)`;
                arrowElement.style.color = windColor;
            });

            // Add popup with wind speed
            windArrow.bindPopup(`Wind: ${windSpeed.toFixed(1)} knots`);
        }
    </script>

    <style>
        .wind-arrow {
            font-size: 20px;
            transform-origin: center;
            transition: transform 0.3s ease-in-out;
        }
    </style>
</body>
</html>
"""


class MapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Sailboat Tracker")
        self.setGeometry(100, 100, 800, 600)

        # Web View to display Leaflet map
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)

        # Load the Leaflet HTML map
        self.browser.setHtml(HTML_MAP)

        # Timer to update location every 5 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_location)
        self.timer.start(5000)

        self.timer.timeout.connect(self.update_wind_data)
        self.timer.start(5000)

    def update_location(self):
        boat_data = self.get_boat_location()
        if boat_data:
            lat, lon = boat_data
            js_code = f"updateBoat({lat}, {lon});"
            self.browser.page().runJavaScript(js_code)

    def get_boat_location(self):
        try:
            boat_status = {"latitude": random.random(), "longitude": random.random()}
            # boat_status = requests.get(TELEMETRY_SERVER_URL + "boat_status/get").json()
            return boat_status["latitude"], boat_status["longitude"]
        except Exception as e:
            print(f"Error fetching location: {e}")
            return (0, 0)

    def update_wind_data(self):
        """Fetch wind data and update the map with wind arrows."""
        wind_data = get_noaa_wind_data()

        for wind in wind_data:
            lat, lon = wind["lat"], wind["lon"]
            wind_dir = wind["wind_dir"]
            wind_speed = wind["wind_speed"]

            js_code = f"addWindArrow({lat}, {lon}, {wind_dir}, {wind_speed});"
            self.browser.page().runJavaScript(js_code)


def get_noaa_wind_data():
    """Fetch wind data from NOAA and parse it using pandas."""
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

        # Read data into pandas
        df = pd.read_csv(
            StringIO(raw_data),
            comment="#",
            sep=r"\s+",
            header=None,
            names=labels,
            na_values="MM",
            keep_default_na=True,
        )
        print(df)

        # Extract relevant columns
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

        # Convert wind speed from m/s to knots
        df["wind_speed"] = df["wind_speed"] * 1.94384  # Convert m/s to knots

        return df.to_dict(orient="records")  # Convert to list of dictionaries

    except Exception as e:
        print(f"Error fetching NOAA data: {e}")
        return []


# Run the PyQt app
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapApp()
    window.show()
    sys.exit(app.exec())
