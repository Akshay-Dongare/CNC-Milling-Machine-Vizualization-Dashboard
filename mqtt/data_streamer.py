import paho.mqtt.client as mqtt
import argparse
from time import sleep
import pandas as pd
import json

# Macros for QOS
QOS = 2
RETAIN = False
CLIENT_ID = "DataStreamer"
CLEAN_SESSION = False

# Topics
STATUS_TOPIC = "Data/" + CLIENT_ID + "/"
DATA_TOPIC = "Data/" + CLIENT_ID + "/"

CSV_HEADERS = ['timestamp', 'temperature', 'vibration', 'pressure', 
               'motor_current', 'power', 'failure']

MESSAGE_DELAY = 1


def on_connect(client, userdata, flags, reason_code, properties):
    client.publish(STATUS_TOPIC, "online", qos=QOS, retain=RETAIN)


def on_disconnect(client, suerdata, flags, reason_code, properties):
    client.publish(STATUS_TOPIC, "offline", qos=QOS, retain=RETAIN)


def on_message(client, userdata, msg):
    pass


try:
    # Parse args
    parser = argparse.ArgumentParser(description="Data Streamer from CSV file")
    parser.add_argument('broker_ip', type=str, help="Broker IP Address")
    parser.add_argument('csv_file', type=str, help="CSV File with Machine Data")
    args = parser.parse_args()

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=CLIENT_ID,
        clean_session=CLEAN_SESSION,
    )

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.will_set("Status/DataStreamer/", "offline", qos=QOS, retain=RETAIN)
    client.connect(args.broker_ip)

    # Start the MQTT Client
    client.loop_start()

    machine_df = pd.read_csv(args.csv_file, header=None, names=CSV_HEADERS)

    # converts row to json array and adds to datastream
    for row in machine_df.itertuples():
        json_row = {
            'timestamp': [row.timestamp],
            'temperature': [row.temperature],
            'vibration': [row.vibration],
            'motor_current': [row.motor_current],
            'power': [row.power],
            'failure': [row.failure]
        }
        json_string = json.dumps(json_row)
        client.publish(DATA_TOPIC, json_string, qos=QOS, retain=RETAIN)
        sleep(MESSAGE_DELAY)


except KeyboardInterrupt:
    pass

finally:
    client.loop_stop()
