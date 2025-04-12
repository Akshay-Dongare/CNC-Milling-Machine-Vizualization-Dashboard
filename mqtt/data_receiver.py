import paho.mqtt.client as mqtt
import argparse
import pandas as pd
import json
import threading

# Macros for QOS
QOS = 2
RETAIN = False
CLIENT_ID = "DataReceiver"
CLEAN_SESSION = False

# Topics
STATUS_TOPIC = "Data/" + CLIENT_ID + "/"
DATA_TOPIC = "Data/DataStreamer/"

CSV_HEADERS = ['timestamp', 'temperature', 'vibration', 'pressure',
               'motor_current', 'power', 'failure']


def parse_message(json_message):
    row = pd.DataFrame(json_message)
    print(row)


def on_connect(client, userdata, flags, reason_code, properties):
    client.publish(STATUS_TOPIC, "online", qos=QOS, retain=RETAIN)
    client.subscribe(DATA_TOPIC, qos=QOS)


def on_disconnect(client, suerdata, flags, reason_code, properties):
    client.publish(STATUS_TOPIC, "offline", qos=QOS, retain=RETAIN)


def on_message(client, userdata, msg):
    if msg.topic == DATA_TOPIC:
        message = msg.payload.decode()
        try:
            json_message = json.loads(message)
            thread = threading.Thread(target=parse_message, args=(json_message,))
            thread.start()

        except Exception:
            pass


try:
    # Parse args
    parser = argparse.ArgumentParser(description="Data Receiver from Data Streamer")
    parser.add_argument('broker_ip', type=str, help="Broker IP Address")
    args = parser.parse_args()

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=CLIENT_ID,
        clean_session=CLEAN_SESSION,
    )

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.will_set("Status/DataReceiver/", "offline", qos=QOS, retain=RETAIN)
    client.connect(args.broker_ip)

    # Start the MQTT Client
    client.loop_forever()


except KeyboardInterrupt:
    pass

finally:
    pass
