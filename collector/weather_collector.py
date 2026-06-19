"""
Weather collector / publisher.

Pulls temperature, humidity and pressure from three different weather
APIs, fuses them into one reading per city, and publishes the result
to EMQX over MQTT.

Run from the project root with:
    python -m collector.weather_collector
or directly with:
    python collector/weather_collector.py
"""

import os
import sys
import time
import json

import requests
import paho.mqtt.client as mqtt

# Make sure the project root (one level up from this file) is importable,
# so this script works whether it's run directly or as a module.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    OPENWEATHER_KEY,
    WEATHERAPI_KEY,
    TOMORROW_KEY,
    MQTT_HOST,
    MQTT_PORT,
    MQTT_PUBLISHER_USER,
    MQTT_PUBLISHER_PASSWORD,
)

CITIES = ["Mumbai", "Pune", "Delhi", "London"]
REQUEST_TIMEOUT = 10  # seconds, so a slow API can't hang the whole loop
PUBLISH_INTERVAL = 10  # seconds


def get_temp_openweather(city):
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": OPENWEATHER_KEY, "units": "metric"}
    resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    return resp.json().get("main", {}).get("temp")


def get_humidity_weatherapi(city):
    url = "http://api.weatherapi.com/v1/current.json"
    params = {"key": WEATHERAPI_KEY, "q": city}
    resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    return resp.json().get("current", {}).get("humidity")


def get_pressure_tomorrow(city):
    url = "https://api.tomorrow.io/v4/weather/realtime"
    params = {"location": city, "apikey": TOMORROW_KEY}
    resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    return resp.json().get("data", {}).get("values", {}).get("pressureSurfaceLevel")


def build_client():
    client = mqtt.Client(
        client_id="weather_collector",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )
    client.username_pw_set(MQTT_PUBLISHER_USER, MQTT_PUBLISHER_PASSWORD)

    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT)
            break
        except OSError as e:
            print(f"Waiting for MQTT broker at {MQTT_HOST}:{MQTT_PORT}:", e)
            time.sleep(5)

    # loop_start() runs the network loop in a background thread so
    # keepalive pings and QoS acks are actually processed.
    client.loop_start()
    return client


def main():
    client = build_client()

    try:
        while True:
            for city in CITIES:
                try:
                    data = {
                        "city": city,
                        "temperature": get_temp_openweather(city),
                        "humidity": get_humidity_weatherapi(city),
                        "pressure": get_pressure_tomorrow(city),
                        "source": "multi_api_fusion",
                        "timestamp": time.time(),
                    }

                    topic = f"weather/{city.lower()}"
                    client.publish(topic, json.dumps(data), qos=1)

                    print("Published:", data)

                except requests.RequestException as e:
                    print(f"API request error for {city}:", e)
                except Exception as e:
                    print(f"Unexpected error for {city}:", e)

            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        print("Stopping collector...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
