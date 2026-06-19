import os
from dotenv import load_dotenv

load_dotenv()

# --- Weather API keys (set these in a .env file, never hardcode them) ---
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "")
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY", "")
TOMORROW_KEY = os.getenv("TOMORROW_KEY", "")

# --- EMQX broker connection ---
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

MQTT_PUBLISHER_USER = os.getenv("MQTT_PUBLISHER_USER", "weather_provider_1")
MQTT_PUBLISHER_PASSWORD = os.getenv("MQTT_PUBLISHER_PASSWORD", "wp1_secret")

MQTT_SUBSCRIBER_USER = os.getenv("MQTT_SUBSCRIBER_USER", "weather_subscriber_1")
MQTT_SUBSCRIBER_PASSWORD = os.getenv("MQTT_SUBSCRIBER_PASSWORD", "ws1_secret")

# --- MongoDB ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "weather_fusion")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "weather_data")

if not (OPENWEATHER_KEY and WEATHERAPI_KEY and TOMORROW_KEY):
    print(
        "WARNING: One or more weather API keys are missing. "
        "Create a .env file from .env.example and fill them in."
    )
