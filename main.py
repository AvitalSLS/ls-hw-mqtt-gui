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
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import datetime
from metric_graph import MetricGraphWidget


class MainWindow(QMainWindow):
    def handle_humidity(self, ts, humidity, unit, source="Room"):
        print(f"[GUI] Received humidity: {humidity} {unit} at {ts} from {source}")
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
        for widget in self.graph_widgets.values():
            main_layout.addWidget(widget)

        # Laser Control Button
        laser_layout = QHBoxLayout()
        self.laser_button = QPushButton("Laser ON/OFF")
        laser_layout.addWidget(QLabel("Laser Control:"))
        laser_layout.addWidget(self.laser_button)
        main_layout.addLayout(laser_layout)

        # Temperature Set Point Widgets
        setpoint_group = QGroupBox("Temperature Set Points")
        setpoint_layout = QGridLayout()
        setpoint_group.setLayout(setpoint_layout)
        setpoint_names = ["SLM1", "SLM2", "SLMInf", "Diode"]
        for idx, name in enumerate(setpoint_names):
            label = QLabel(f"{name} Set Point (°C):")
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(100)
            slider.setValue(25)
            value_display = QLineEdit("25")
            value_display.setFixedWidth(40)
            slider.valueChanged.connect(
                lambda val, ed=value_display: ed.setText(str(val))
            )
            setpoint_layout.addWidget(label, idx, 0)
            setpoint_layout.addWidget(slider, idx, 1)
            setpoint_layout.addWidget(value_display, idx, 2)
        main_layout.addWidget(setpoint_group)

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
