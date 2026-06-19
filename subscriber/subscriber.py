"""
Weather subscriber.

Subscribes to all weather/+ topics on EMQX and stores every fused
reading into MongoDB.

Run from the project root with:
    python -m subscriber.subscriber
or directly with:
    python subscriber/subscriber.py
"""

import os
import sys
import json
import time

import paho.mqtt.client as mqtt

# Make sure the project root (one level up from this file) is importable,
# so this script works whether it's run directly or as a module.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MQTT_HOST, MQTT_PORT, MQTT_SUBSCRIBER_USER, MQTT_SUBSCRIBER_PASSWORD
from database.mongo import MongoDB

db = MongoDB()


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("Connected to EMQX broker")
        client.subscribe("weather/+")
    else:
        print("Failed to connect, reason code:", reason_code)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
    except json.JSONDecodeError as e:
        print("Received malformed payload, skipping:", e)
        return

    data["topic"] = msg.topic
    data["received_at"] = time.time()

    db.insert_data(data)
    print("Stored in MongoDB:", data)


def main():
    client = mqtt.Client(
        client_id="weather_subscriber",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )
    client.username_pw_set(MQTT_SUBSCRIBER_USER, MQTT_SUBSCRIBER_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT)
            break
        except OSError as e:
            print(f"Waiting for MQTT broker at {MQTT_HOST}:{MQTT_PORT}:", e)
            time.sleep(5)

    client.loop_forever()


if __name__ == "__main__":
    main()
