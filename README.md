# Weather Simulator

A real-time weather monitoring system that fetches weather data from OpenWeatherMap, WeatherAPI, and Tomorrow.io, fuses the readings, publishes them through MQTT using EMQX, stores them in MongoDB, and displays the latest records on a Flask dashboard.

## Features

* Multi-API weather data fusion
* MQTT communication using EMQX
* MongoDB storage
* Flask dashboard for visualization
* Dockerized architecture
* Optional background collector

## Architecture

```text
Weather APIs
     │
     ▼
Dashboard / Collector
     │
     ▼
    EMQX
     │
     ▼
 Subscriber
     │
     ▼
  MongoDB
     │
     ▼
Flask Dashboard
```

## Prerequisites

* Docker Desktop with Docker Compose
* OpenWeatherMap API Key
* WeatherAPI Key
* Tomorrow.io API Key
* Python 3.10+ (optional collector)

## Setup

Create the environment file:

```powershell
copy .env.example .env
```

Add your API keys to `.env`:

```env
OPENWEATHER_KEY=your_openweather_key
WEATHERAPI_KEY=your_weatherapi_key
TOMORROW_KEY=your_tomorrowio_key
```

## Running the Application

### Option 1: PowerShell Script

```powershell
.\run.ps1
```

### Option 2: Docker Compose

```bash
docker compose up -d --build
```

Check container status:

```bash
docker compose ps
```

## Access URLs

Flask Dashboard:

```text
http://localhost:5000
```

EMQX Dashboard:

```text
http://localhost:18083
```

Default credentials:

```text
Username: admin
Password: public
```

## Optional Background Collector

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the collector:

```bash
python -m collector.weather_collector
```

## MongoDB Commands

Show latest 10 records:

```powershell
docker exec mongo mongosh weather_fusion --quiet --eval "db.weather_data.find().sort({_id:-1}).limit(10).pretty()"
```

Count documents:

```powershell
docker exec mongo mongosh weather_fusion --quiet --eval "db.weather_data.countDocuments()"
```

Open Mongo shell:

```powershell
docker exec -it mongo mongosh
```

Switch database:

```javascript
use weather_fusion
```

Show latest records:

```javascript
db.weather_data.find().sort({_id:-1}).limit(10).pretty()
```

Filter by city:

```javascript
db.weather_data.find({city:"Mumbai"})
```

Exit:

```javascript
exit
```

## Docker Commands

Check running containers:

```bash
docker compose ps
```

View subscriber logs:

```bash
docker compose logs subscriber
```

Follow logs:

```bash
docker compose logs -f subscriber
```

Stop containers:

```bash
docker compose down
```

Remove containers and volumes:

```bash
docker compose down -v
```

Rebuild and restart:

```bash
docker compose up -d --build
```

## Project Structure

```text
Simulator/
│
├── collector/
│   └── weather_collector.py
├── subscriber/
│   └── subscriber.py
├── database/
│   └── mongo.py
├── dashboard/
│   ├── app.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       └── style.css
├── config.py
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── run.ps1
├── requirements.txt
└── README.md
```

## Tech Stack

* Python
* Flask
* MQTT
* EMQX
* MongoDB
* Docker
* OpenWeatherMap API
* WeatherAPI
* Tomorrow.io API

## Author

**Mansi Chotaliya**

IoT Weather Fusion Simulator – Real-Time Weather Monitoring System using MQTT, EMQX, MongoDB, Docker, and Flask.
