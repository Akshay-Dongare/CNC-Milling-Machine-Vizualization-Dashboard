import paho.mqtt.client as mqtt
import json
import time
import pandas as pd
from flask import Flask
import threading
import os
import ssl

VOLTAGE = 220

# MQTT Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '8883'))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'machine/data')
MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
def load_dataset():
    """Load and prepare the dataset from CSV."""
    df = pd.read_csv('Predictive_Maintenance_v2.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def publisher():
    """Background task that reads the dataset and publishes each row via MQTT."""
    df = load_dataset()
    client = mqtt.Client(protocol=mqtt.MQTTv5)

    # Enable TLS/SSL
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)

    
    MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
    MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    try:
        print("Connecting to MQTT broker...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        print("Connected successfully to HiveMQ Cloud!")
        
        total_rows = len(df)
        current_row = 0
        print("Starting to publish data from dataset...")
        
        while True:
            row = df.iloc[current_row]
            message = {
                'timestamp': row['timestamp'].isoformat(),
                'temperature': row['temperature'],
                'vibration': row['vibration'],
                'pressure': row['pressure'],
                'motor_current': row['motor_current'],
                'power': row['motor_current'] * VOLTAGE,
                'failure': row['failure']
            }
            print(f"Publishing: {message}")
            client.publish(MQTT_TOPIC, json.dumps(message))
            current_row = (current_row + 1) % total_rows
            time.sleep(1)
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()

app = Flask(__name__)

@app.route('/')
def index():
    return "MQTT Publisher is running!"

if __name__ == "__main__":
    publisher_thread = threading.Thread(target=publisher, daemon=True)
    publisher_thread.start()
    app.run(host='0.0.0.0', port=8080)