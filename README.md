# MQTT GUI Application

This is a Python desktop application for monitoring and controlling devices via MQTT. It displays real-time metrics (such as temperature and humidity) in graphs and provides controls for device interaction.

## Features
- Subscribe to MQTT topics for temperature and humidity metrics
- Real-time graphing of SLM1, SLM2, SLM3, Diode, Room temperature, and Room humidity
- Device control buttons (e.g., Laser ON/OFF)
- Temperature set point sliders
- Modular, extensible codebase (easy to add more metrics or controls)

## Requirements
- Python 3.10+
- See `requirements.txt` for dependencies

## Setup
1. Clone the repository:
   ```sh
   git clone <repo-url>
   cd ls-hw-mqtt-gui
   ```
2. Create and activate a virtual environment:
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Allow access to AWS CodeArtifact (for private package repository):
   ```sh
   aws codeartifact login --tool pip --repository solver-simulations --domain ls-dev-repo --domain-owner 541441380680 --region eu-central-1
   ```
4. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
5. Copy and edit `config.yaml` to set your MQTT broker and topics.

## Running the App
```sh
python main.py
```

## Configuration
Edit `config.yaml` to set your MQTT broker details and topic subscriptions. Example:
```yaml
mqtt:
  server: "localhost"
  port: 1883
  user: "user"
  password: "pass"
topics:
  subscribe:
    - "temperatureSensor/SLM1/status/temperature"
    - "temperatureSensor/Room/status/humidity"
    # Add more topics as needed
```

## Adding New Metrics
- To add a new metric (e.g., pressure), add a new entry in `graph_widgets` in `main.py` and handle the corresponding MQTT topic in `mqtt_client.py`.

## License
MIT
