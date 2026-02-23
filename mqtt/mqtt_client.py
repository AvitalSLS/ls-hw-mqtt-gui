import json
import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, config, on_temperature=None, on_humidity=None):
        self.config = config
        self.on_temperature = on_temperature
        self.on_humidity = on_humidity
        self.client = mqtt.Client()
        mqtt_cfg = config.get("mqtt", {})
        if mqtt_cfg.get("user") and mqtt_cfg.get("password"):
            self.client.username_pw_set(mqtt_cfg["user"], mqtt_cfg["password"])
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.topics = config.get("topics", {}).get("subscribe", [])

    def connect(self):
        mqtt_cfg = self.config.get("mqtt", {})
        self.client.connect(mqtt_cfg.get("server", "localhost"), int(mqtt_cfg.get("port", 1883)), 60)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker.")
            for topic in self.topics:
                client.subscribe(topic)
                print(f"Subscribed to {topic}")
        else:
            print(f"Failed to connect to MQTT broker, code {rc}")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode("utf-8")
        print(f"Received message on {topic}: {payload}")
        parts = topic.split("/")
        raw_source = parts[1].lower() if len(parts) > 2 else "slm1"
        # Normalize source for graph keys
        if raw_source == "slm1":
            source = "SLM1"
        elif raw_source == "slm2":
            source = "SLM2"
        elif raw_source == "slminf":
            source = "SLMInf"
        elif raw_source == "diode":
            source = "Diode"
        else:
            source = raw_source.capitalize()

        # Handle temperature
        if topic.endswith("/status/temperature"):
            try:
                data = json.loads(payload)
                ts = data.get("ts")
                temperature = data.get("temperature")
                unit = data.get("unit")
                print(f"ts: {ts}, temperature: {temperature}, unit: {unit}, source: {source}")
                if self.on_temperature:
                    self.on_temperature(ts, temperature, unit, source)
            except Exception as e:
                print(f"Error parsing JSON payload: {e}")
        # Handle humidity
        elif topic.endswith("/status/humidity"):
            try:
                data = json.loads(payload)
                ts = data.get("ts")
                humidity = data.get("humidity")
                unit = data.get("unit")
                print(f"ts: {ts}, humidity: {humidity}, unit: {unit}, source: {source}")
                if self.on_humidity:
                    self.on_humidity(ts, humidity, unit, source)
            except Exception as e:
                print(f"Error parsing JSON payload (humidity): {e}")
