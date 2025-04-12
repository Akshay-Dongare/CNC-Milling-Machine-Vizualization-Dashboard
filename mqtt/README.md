# Instructions for running local MQTT from CSV file
Data_streamer.py is a file that will read out a CSV file and stream the data over MQTT similar to that of the HAAS milling machines in CAMAL. This file is used to test the dynamic aspect of CNSee without being at CAMAL and directly connected to their network.

## 1. Create a python virtual environment (Python 3.12) and install dependencies
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Set up the Mosquitto Broker
### 1. Install the [MQTT Broker](htpps://mosquitto.org/)
### 2. Run the broker in Command Prompt
```
mosquitto
```

## 3. Run data_streamer.py
```
python3 data_streamer.py <BROKER_IP_ADDRESS> <CSV_FILE_PATH>
```

## 4. Run data_receiver.py
```
python3 data_receiver.py <BROKER_IP_ADDRESS>
```