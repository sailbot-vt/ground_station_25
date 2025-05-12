# Ground Station 25 <img src="https://github.com/user-attachments/assets/05a3d1d7-f5c2-4c9b-8a05-54f5ed727f80" alt="logo" width="50"/>

Ground Station 25 is a robust and scalable system designed to monitor and interact with real-time sailboat telemetry. It integrates both web-based and command-line interfaces to visualize and control sailboat data, providing seamless communication with the sailboat and wind data sources.

## Getting Started

### Prerequisites

Ensure that you have the following software installed on your system:

- [Go](https://go.dev/doc/install) (1.24.3)
- [Python](https://www.python.org/) (v3.x or later)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/sailbot-vt/ground_station_25.git
   cd ground_station_25
   ```

2. Install the Python dependencies:

   ```bash
   pip install -r requirements.txt
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

### Demo (might be out of date with current iteration)

<https://github.com/user-attachments/assets/4d5181cc-672a-436c-bc56-e994ac10a0eb>
