import sys
import signal
import yaml
import os
from mqtt.mqtt_client import MQTTClient
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QGroupBox,
    QGridLayout,
    QLineEdit,
    QCheckBox,
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import datetime
from metric_graph import MetricGraphWidget


class MainWindow(QMainWindow):
    def handle_get_diode_current(self):
        print("Get Current button pressed for Diode Driver")
        import time
        ts = int(time.time() * 1000)
        payload = {"ts": ts}
        topic = "diodeDriver/0/get/current"
        try:
            self.diode_current_field.setText("...")
            self.mqtt_client.client.publish(topic, str(payload))
            print(f"Published to {topic}: {payload}")
        except Exception as e:
            print(f"Failed to publish diode current request: {e}")
            self.diode_current_field.setText("ERR")
    def handle_diode_current(self, ts, current, unit, source=None):
        print(f"[GUI] Received diode current: {current} {unit} at {ts}")
        try:
            value = float(current)
            display = f"{value:.2f}"
        except Exception:
            display = str(current)
        self.diode_current_field.setText(display)
    def handle_humidity(self, ts, humidity, unit, source="Room"):
        print(f"[GUI] Received humidity: {humidity} {unit} at {ts} from {source}")
        # Map humidity from 'Room' to 'roomhumidity' graph
        if source.lower() == "room":
            key = "roomhumidity"
        else:
            key = source.lower()
        if key in self.graph_widgets:
            self.graph_widgets[key].update_metric(ts, humidity, unit)


    def handle_temperature(self, ts, temperature, unit, source="SLM1"):
        print(f"[GUI] Received temperature: {temperature} {unit} at {ts} from {source}")
        key = source.lower()
        if key in self.graph_widgets:
            self.graph_widgets[key].update_metric(ts, temperature, unit)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MQTT GUI")
        self.setGeometry(100, 100, 1000, 800)

        # Load config.yaml
        self.config = self.load_config()

        # MQTT setup
        self.mqtt_client = MQTTClient(
            self.config,
            on_temperature=self.handle_temperature,
            on_humidity=self.handle_humidity
        )
        self.mqtt_client.on_diode_current = self.handle_diode_current
        self.mqtt_client.connect()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Metric Graphs for SLM1, SLM2, SLMInf, Diode, Room (all keys lowercase)
        self.graph_widgets = {
            "slm1": MetricGraphWidget("SLM1 Temperature (°C)"),
            "slm2": MetricGraphWidget("SLM2 Temperature (°C)"),
            "slminf": MetricGraphWidget("SLMInf Temperature (°C)"),
            "diode": MetricGraphWidget("Diode (°C)"),
            "room": MetricGraphWidget("Room Temperature (°C)"),
            "roomhumidity": MetricGraphWidget("Room Humidity (%)"),
        }

        # Add SLM graph widgets with 'read LUT' button
        slm_keys = ["slm1", "slm2", "slminf", "diode"]
        for key in slm_keys:
            graph_widget = self.graph_widgets[key]
            graph_widget.setMinimumHeight(120)  # Ensure graph is at least as tall as Diode Driver
            graph_layout = QHBoxLayout()
            graph_layout.addWidget(graph_widget)
            read_lut_btn = QPushButton("Read LUT")
            read_lut_btn.setFixedWidth(80)
            read_lut_btn.clicked.connect(lambda _, k=key: self.handle_read_lut(k))
            graph_layout.addWidget(read_lut_btn)
            main_layout.addLayout(graph_layout)

        diode_driver_group = QGroupBox("Diode Driver")
        diode_driver_layout = QVBoxLayout()
        diode_driver_layout.setContentsMargins(4, 4, 4, 4)
        diode_driver_layout.setSpacing(4)

        # Current control group
        current_group = QGroupBox("Current")
        current_group.setMaximumHeight(60)
        current_layout = QHBoxLayout()
        current_layout.setContentsMargins(2, 2, 2, 2)
        current_layout.setSpacing(2)
        get_current_btn = QPushButton("Get")
        get_current_btn.setFixedWidth(60)
        get_current_btn.clicked.connect(self.handle_get_diode_current)
        current_layout.addWidget(get_current_btn)
        set_current_btn = QPushButton("Set")
        set_current_btn.setFixedWidth(60)
        set_current_btn.clicked.connect(self.handle_set_diode_current)
        current_layout.addWidget(set_current_btn)
        self.diode_current_field = QLineEdit()
        self.diode_current_field.setText("---")
        self.diode_current_field.setFixedWidth(70)
        current_layout.addWidget(self.diode_current_field)

        # Up/Down buttons
        updown_layout = QVBoxLayout()
        updown_layout.setSpacing(0)
        updown_layout.setContentsMargins(0, 0, 0, 0)
        up_btn = QPushButton("▲")
        up_btn.setFixedSize(18, 10)
        up_btn.clicked.connect(self.handle_current_up)
        down_btn = QPushButton("▼")
        down_btn.setFixedSize(18, 10)
        down_btn.clicked.connect(self.handle_current_down)
        updown_layout.addWidget(up_btn)
        updown_layout.addWidget(down_btn)
        current_layout.addLayout(updown_layout)

        current_layout.addWidget(QLabel("[A]"))
        current_group.setLayout(current_layout)

        diode_driver_layout.addWidget(current_group)

        # Enable checkbox
        self.diode_enable_checkbox = QCheckBox("Enable")
        self.diode_enable_checkbox.setChecked(False)
        self.diode_enable_checkbox.stateChanged.connect(self.handle_diode_enable_toggle)
        diode_driver_layout.addWidget(self.diode_enable_checkbox)

        diode_driver_group.setLayout(diode_driver_layout)
        # Set width and height to keep the block compact
        diode_driver_group.setMinimumWidth(self.width() // 4)
        diode_driver_group.setMaximumWidth(self.width() // 4)
        diode_driver_group.setMaximumHeight(120)
        main_layout.addWidget(diode_driver_group)
    def handle_set_diode_current(self):
        value = self.diode_current_field.text().strip()
        try:
            float_value = float(value)
        except Exception:
            self.diode_current_field.setText("ERR")
            return
        import time
        ts = int(time.time() * 1000)
        payload = {"ts": ts, "current": float_value, "unit": "A"}
        topic = "diodeDriver/0/set/current"
        import json
        try:
            self.mqtt_client.client.publish(topic, json.dumps(payload))
            print(f"Published to {topic}: {payload}")
        except Exception as e:
            print(f"Failed to publish diode set current: {e}")
    
    def handle_diode_enable_toggle(self):
        enabled = self.diode_enable_checkbox.isChecked()
        print(f"Diode enable toggled: {enabled}")
        import time
        import json
        ts = int(time.time() * 1000)
        payload = {"ts": ts, "enable": 1 if enabled else 0, "unit": "none"}
        topic = "diodeDriver/0/set/enable"
        try:
            self.mqtt_client.client.publish(topic, json.dumps(payload))
            print(f"Published to {topic}: {payload}")
        except Exception as e:
            print(f"Failed to publish diode enable: {e}")
    
    def handle_current_up(self):
        try:
            value = float(self.diode_current_field.text())
            value = min(value + 1, 50)
            self.diode_current_field.setText(f"{value:.2f}")
        except Exception:
            self.diode_current_field.setText("0.00")
    
    def handle_current_down(self):
        try:
            value = float(self.diode_current_field.text())
            value = max(value - 1, 0)
            self.diode_current_field.setText(f"{value:.2f}")
        except Exception:
            self.diode_current_field.setText("0.00")
        def handle_get_diode_current(self):
            print("Get Current button pressed for Diode Driver")
            # Placeholder: fetch current from MQTT or other source
            # For now, just set a dummy value
            # TODO: Implement actual fetch logic
            self.diode_current_display.setText("--")
    def handle_read_lut(self, slm_key):
        print(f"Read LUT button pressed for {slm_key}")
        import time
        ts = int(time.time() * 1000)
        payload = {"ts": ts}
        topic = f"hwc/{slm_key}/get/lut"
        try:
            self.mqtt_client.client.publish(topic, str(payload))
            print(f"Published to {topic}: {payload}")
        except Exception as e:
            print(f"Failed to publish LUT request: {e}")

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Failed to load config.yaml: {e}")
            return {}

    def _create_metric_group(self, title, widget_or_text):
        group = QGroupBox(title)
        layout = QVBoxLayout()
        if isinstance(widget_or_text, str):
            layout.addWidget(QLabel(widget_or_text))
        else:
            layout.addWidget(widget_or_text)
        group.setLayout(layout)
        return group


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Enable Ctrl+C to close the app
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
