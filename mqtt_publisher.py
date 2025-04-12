import paho.mqtt.client as mqtt
import json
import time
import random
import os
from datetime import datetime

# MQTT Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'machine/data')
MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

def generate_machine_data():
    """Generate simulated machine data"""
    return {
        'timestamp': datetime.now().isoformat(),
        'temperature': round(random.uniform(50, 90), 2),
        'vibration': round(random.uniform(0.1, 1.0), 2),
        'pressure': round(random.uniform(1.0, 5.0), 2),
        'motor_current': round(random.uniform(2.0, 10.0), 2),
        'power': round(random.uniform(100, 500), 2),
        'failure': random.choice([0, 1])
    }

def main():
    client = mqtt.Client()
    
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    client.on_connect = on_connect
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        print(f"Publisher connected to {MQTT_BROKER}:{MQTT_PORT}")
        
        while True:
            data = generate_machine_data()
            client.publish(MQTT_TOPIC, json.dumps(data))
            print(f"Published: {data}")
            time.sleep(5)  # Publish every 5 seconds
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()