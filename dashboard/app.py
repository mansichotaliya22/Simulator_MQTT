import os
import sys
import json
import re
import time
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paho.mqtt.client as mqtt
import requests
from flask import Flask, render_template, request

from config import (
    OPENWEATHER_KEY,
    WEATHERAPI_KEY,
    TOMORROW_KEY,
    MQTT_HOST,
    MQTT_PORT,
    MQTT_PUBLISHER_USER,
    MQTT_PUBLISHER_PASSWORD,
)
from database.mongo import MongoDB

app = Flask(__name__)
db = MongoDB()

REQUEST_TIMEOUT = 10


def get_openweather_values(city):
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": OPENWEATHER_KEY, "units": "metric"}
    resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    main = resp.json().get("main", {})
    return {
        "temperature": main.get("temp"),
        "pressure": main.get("pressure"),
    }


def get_humidity(city):
    url = "http://api.weatherapi.com/v1/current.json"
    params = {"key": WEATHERAPI_KEY, "q": city}
    resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json().get("current", {}).get("humidity")


def get_tomorrow_values(city):
    url = "https://api.tomorrow.io/v4/weather/realtime"
    params = {"location": city, "apikey": TOMORROW_KEY}
    resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    values = resp.json().get("data", {}).get("values", {})
    return {
        "temperature": values.get("temperature"),
        "humidity": values.get("humidity"),
        "pressure": values.get("pressureSurfaceLevel"),
    }


def average(values):
    numbers = [value for value in values if value is not None]
    if not numbers:
        return None
    return round(sum(numbers) / len(numbers), 2)


def get_weather(city):
    # OpenWeatherMap and WeatherAPI are treated as required sources: if the
    # city name is invalid, we want the HTTPError to propagate so the route
    # can show a clear "city not found" message.
    openweather = get_openweather_values(city)
    humidity_value = get_humidity(city)

    # Tomorrow.io is treated as optional/supplementary — if it fails, we
    # still have data from the other two sources.
    tomorrow = {}
    try:
        tomorrow = get_tomorrow_values(city)
    except requests.RequestException:
        tomorrow = {}

    temperature = average([openweather.get("temperature"), tomorrow.get("temperature")])
    humidity = average([humidity_value, tomorrow.get("humidity")])
    pressure = average([openweather.get("pressure"), tomorrow.get("pressure")])

    return {
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure,
    }


def build_publish_client():
    client = mqtt.Client(
        client_id=f"weather_dashboard_{int(time.time())}",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )
    client.username_pw_set(MQTT_PUBLISHER_USER, MQTT_PUBLISHER_PASSWORD)

    last_error = None
    for _ in range(5):
        try:
            client.connect(MQTT_HOST, MQTT_PORT)
            return client
        except OSError as e:
            last_error = e
            time.sleep(2)
    raise last_error


def publish_weather(data):
    topic_city = re.sub(r"[^a-z0-9_-]+", "-", data["city"].lower()).strip("-")
    topic = f"weather/{topic_city or 'unknown'}"

    client = build_publish_client()
    client.loop_start()
    result = client.publish(topic, json.dumps(data), qos=1)
    result.wait_for_publish()
    client.loop_stop()
    client.disconnect()


def wait_for_document(request_id, timeout=3.0, interval=0.3):
    """
    Publishing happens over MQTT and a separate subscriber process writes
    to MongoDB, so the write isn't instantaneous from this request's point
    of view. Poll briefly for the subscriber to catch up so the page can
    show the freshly stored values instead of stale ones.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        doc = db.find_one({"request_id": request_id})
        if doc:
            return doc
        time.sleep(interval)
    return None


@app.route("/", methods=["GET", "POST"])
def home():
    message = None
    error = None

    if request.method == "POST":
        city = request.form.get("city", "").strip()

        if not city:
            error = "Please enter a city name."
        else:
            try:
                weather = get_weather(city)
                request_id = uuid.uuid4().hex
                data = {
                    "request_id": request_id,
                    "city": city,
                    "temperature": weather["temperature"],
                    "humidity": weather["humidity"],
                    "pressure": weather["pressure"],
                    "source": "user_city_lookup",
                    "timestamp": time.time(),
                }
                publish_weather(data)

                stored = wait_for_document(request_id)
                if stored:
                    message = (
                        f"Weather for {city}: "
                        f"temperature {stored.get('temperature')}\u00b0C, "
                        f"humidity {stored.get('humidity')}%, "
                        f"pressure {stored.get('pressure')} hPa "
                        "(stored in MongoDB)."
                    )
                else:
                    message = (
                        f"Published weather data for {city}. It's on its way to "
                        "the database — refresh in a moment if it's not below yet."
                    )
            except requests.HTTPError:
                error = f"Could not find weather data for {city}. Check the city name or API key."
            except requests.RequestException as e:
                error = f"Weather API request failed: {e}"
            except OSError as e:
                error = f"Could not connect to MQTT broker: {e}"

    data = db.fetch_latest(limit=30)
    return render_template("index.html", data=data, message=message, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
