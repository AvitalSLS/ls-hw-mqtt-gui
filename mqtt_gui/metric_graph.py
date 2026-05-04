from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import datetime

class MetricGraphWidget(QWidget):
    def __init__(self, title="--", parent=None):
        super().__init__(parent)
        self.temp_label = QLabel("--")
        self.temp_times = []
        self.temp_values = []
        self.fig = Figure(figsize=(5, 2), facecolor="#222222")
        self.ax = self.fig.add_subplot(111, facecolor="#222222")
        self.canvas = FigureCanvas(self.fig)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(title))
        layout.addWidget(self.temp_label)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def update_metric(self, ts, value, unit):
        self.temp_label.setText(f"{value} {unit}")
        try:
            dt = datetime.datetime.fromtimestamp(ts / 1000.0)
            if not self.temp_times or dt > self.temp_times[-1]:
                self.temp_times.append(dt)
                self.temp_values.append(value)
            else:
                print(f"Ignored out-of-order timestamp: {dt}")
            self.temp_times = self.temp_times[-100:]
            self.temp_values = self.temp_values[-100:]
            self.ax.clear()
            self.ax.set_facecolor("#222222")
            self.ax.plot(self.temp_times, self.temp_values, marker="o", color="#00ffcc")
            self.ax.set_ylabel("Value", color="white")
            self.ax.set_xlabel("Time", color="white")
            self.ax.tick_params(axis='x', colors='white')
            self.ax.tick_params(axis='y', colors='white')
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
            self.fig.autofmt_xdate()
            for spine in self.ax.spines.values():
                spine.set_color('white')
            self.canvas.draw()
        except Exception as e:
            print(f"Error updating graph: {e}")
