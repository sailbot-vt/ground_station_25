# Ground Station 25 <img src="https://github.com/user-attachments/assets/05a3d1d7-f5c2-4c9b-8a05-54f5ed727f80" alt="logo" width="50"/>

Ground Station 25 is a robust and scalable system designed to monitor and interact with real-time sailboat telemetry. It integrates both web-based and command-line interfaces to visualize and control sailboat data, providing seamless communication with the sailboat and wind data sources.

## Features

- **Real-Time Telemetry**: View and monitor sailboat telemetry (location, speed, heading) in real time.
- **Interactive Map**: Display live sailboat position and interact with the map (set waypoints, view boat orientation).
- **Wind Data Integration**: Overlay live wind data from NOAA weather stations and buoys.
- **Web-Based Interface**: Built using Node.js and Express to serve a web-based dashboard for tracking and interacting with the sailboat.
- **Python Integration**: Python is used for backend data processing and communication with external APIs.

## Getting Started

### Prerequisites

Ensure that you have the following software installed on your system:

- [Node.js](https://nodejs.org/en/) (v14 or later)
- [Python](https://www.python.org/) (v3.x or later)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/sailbot-vt/ground_station_25.git
   cd ground_station_25
   ```

2. Install the Python and NPM dependencies:
   ```bash
   pip install -r requirements.txt
   npm install
   ```

3. Give the start script executable permissions:

   ```bash
   chmod +x run.sh
   ```

4. Run the program

   ```bash
   ./run.sh
   ```

### Usage
Left click on the map to add waypoints. Right clicking removes the closest waypoint to your cursor's location.

### Demo
https://github.com/user-attachments/assets/1cfeccfd-521e-4cca-a46d-b165460b150f

