import L from 'leaflet';
import 'leaflet-rotatedmarker';

// import * as L from 'https://unpkg.com/leaflet@1.8.0/dist/leaflet.js';
// import 'https://unpkg.com/leaflet-rotatedmarker@0.1.1/dist/leaflet-rotatedmarker.js';

class map_interface {
    static map_options = {
        center: [36.983731367697374, -76.29555376681454],
        zoom: 13
    }
    static boat_icon = L.icon({
        iconUrl: "../assets/boat.png",
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    })
    static wind_icon = L.icon({
        iconUrl: "../assets/arrow.png",
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    })

    constructor() {
        this.boat = {
            heading: 0,
            location: [36.983731367697374, -76.29555376681454]
        }
        this.map = L.map("map", map_interface.map_options)

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 18
        }).addTo(this.map)

        this.boat_marker = L.marker(this.boat.location, {
            icon: map_interface.boat_icon,
            rotationAngle: this.boat.heading,
            rotationOrigin: "center"
        })
            .addTo(this.map)
            .bindPopup("Sailboat Location:\n ${}")
    }

    update_boat(lat, lon, heading) {
        this.boat.location = [lat, lon]
        this.boat.heading = heading
        this.boat_marker
            .setLatLng(this.boat.location)
            .bindPopup("Sailboat Location: " + lat.toFixed(5) + ", " + lon.toFixed(5))
    }

    add_wind_arrow(lat, lon, wind_dir, wind_speed) {
        // Skip adding if too far from the boat
        if (
            Math.abs(lat - this.boat.location[0]) > 0.5 ||
            Math.abs(lon - this.boat.location[1]) > 0.5
        ) {
            return
        }

        var windArrowMarker = L.marker([lat, lon], {
            icon: map_interface.wind_icon,
            rotationAngle: wind_dir,
            rotationOrigin: "center"
        }).addTo(this.map)

        windArrowMarker.bindPopup(`Wind: ${wind_dir}°, ${wind_speed} m/s`)
    }

    clear_wind_arrows() {
        this.map.eachLayer(layer => {
            if (layer instanceof L.Marker) {
                const popup = layer.getPopup()
                const content = popup?.getContent()
                if (
                    content &&
                    typeof content === "string" &&
                    content.includes("Wind:")
                ) {
                    this.map.removeLayer(layer)
                }
            }
        })
    }
}
