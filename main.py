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
        import json
        ts = int(time.time() * 1000)
        # Get current value from field, default to 0 if empty or invalid
        try:
            current_value = float(self.diode_current_field.text().strip())
        except:
            current_value = 0.0
        payload = {"ts": ts, "current": current_value, "unit": "A"}
        topic = "diodeDriver/1/get/current"
        try:
            self.diode_current_field.setText("...")
            self.mqtt_client.client.publish(topic, json.dumps(payload))
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

        # Metric Graphs for SLM1, SLM2, SLM3, Diode, Room (all keys lowercase)
        self.graph_widgets = {
            "slm1": MetricGraphWidget("SLM1 Temperature (°C)"),
            "slm2": MetricGraphWidget("SLM2 Temperature (°C)"),
            "slm3": MetricGraphWidget("SLM3 Temperature (°C)"),
            "diode": MetricGraphWidget("Diode (°C)"),
            "room": MetricGraphWidget("Room Temperature (°C)"),
            "roomhumidity": MetricGraphWidget("Room Humidity (%)"),
        }

        # Add SLM graph widgets with 'read LUT' button and temperatureTarget control
        slm_keys = ["slm1", "slm2", "slm3", "diode"]
        self.temp_target_fields = {}
        for key in slm_keys:
            graph_widget = self.graph_widgets[key]
            graph_widget.setMinimumHeight(120)  # Ensure graph is at least as tall as Diode Driver
            graph_layout = QHBoxLayout()
            graph_layout.addWidget(graph_widget)
            read_lut_btn = QPushButton("Read LUT")
            read_lut_btn.setFixedWidth(80)
            read_lut_btn.clicked.connect(lambda _, k=key: self.handle_read_lut(k))
            graph_layout.addWidget(read_lut_btn)
            # Temperature Target control
            temp_target_field = QLineEdit()
            temp_target_field.setPlaceholderText("Target °C")
            temp_target_field.setFixedWidth(60)
            self.temp_target_fields[key] = temp_target_field
            graph_layout.addWidget(temp_target_field)
            set_temp_btn = QPushButton("Set T")
            set_temp_btn.setFixedWidth(60)
            set_temp_btn.clicked.connect(lambda _, k=key: self.handle_set_temperature_target(k))
            graph_layout.addWidget(set_temp_btn)
            main_layout.addLayout(graph_layout)

        # Add Room Temperature and Humidity graphs (read-only, no controls)
        for key in ["room", "roomhumidity"]:
            graph_widget = self.graph_widgets[key]
            main_layout.addWidget(graph_widget)

        # Diode Driver Control Section
        diode_control_group = QGroupBox("Diode Driver Control")
        diode_control_layout = QHBoxLayout()
        
        # Current field
        self.diode_current_field = QLineEdit()
        self.diode_current_field.setPlaceholderText("0.00")
        self.diode_current_field.setFixedWidth(80)
        diode_control_layout.addWidget(QLabel("Current (A):"))
        diode_control_layout.addWidget(self.diode_current_field)
        
        # Get Current button
        get_current_btn = QPushButton("Get Current")
        get_current_btn.clicked.connect(self.handle_get_diode_current)
        diode_control_layout.addWidget(get_current_btn)
        
        # Set Current button
        set_current_btn = QPushButton("Set Current")
        set_current_btn.clicked.connect(self.handle_set_diode_current)
        diode_control_layout.addWidget(set_current_btn)
        
        # Up/Down buttons
        current_up_btn = QPushButton("▲")
        current_up_btn.setFixedWidth(30)
        current_up_btn.clicked.connect(self.handle_current_up)
        diode_control_layout.addWidget(current_up_btn)
        
        current_down_btn = QPushButton("▼")
        current_down_btn.setFixedWidth(30)
        current_down_btn.clicked.connect(self.handle_current_down)
        diode_control_layout.addWidget(current_down_btn)
        
        # Enable checkbox
        self.diode_enable_checkbox = QCheckBox("Enable")
        self.diode_enable_checkbox.toggled.connect(self.handle_diode_enable_toggle)
        diode_control_layout.addWidget(self.diode_enable_checkbox)
        
        diode_control_group.setLayout(diode_control_layout)
        main_layout.addWidget(diode_control_group)

    def handle_set_temperature_target(self, key):
        field = self.temp_target_fields.get(key)
        if not field:
            return
        value_str = field.text().strip()
        try:
            value = float(value_str)
        except Exception:
            field.setText("ERR")
            return
        if not (20.0 <= value <= 50.0):
            field.setText("20-50C")
            return
        import time, json
        ts = int(time.time() * 1000)
        payload = {"ts": ts, "temperature": value, "unit": "C"}
        topic = f"temperatureSensor/{key}/set/temperatureTarget"
        try:
            self.mqtt_client.client.publish(topic, json.dumps(payload))
            print(f"Published to {topic}: {payload}")
        except Exception as e:
            print(f"Failed to publish temperatureTarget: {e}")
            field.setText("ERR")
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
        topic = "diodeDriver/1/set/current"
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
        topic = "diodeDriver/1/set/enable"
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
