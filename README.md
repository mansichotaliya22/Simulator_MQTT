# Weather Fusion Simulator

Pulls weather data from three different APIs (OpenWeatherMap, WeatherAPI,
Tomorrow.io), fuses it into one reading per city, publishes it to an EMQX
MQTT broker, stores it in MongoDB, and displays the latest readings on a
small Flask dashboard.

## What was fixed

- `collector/weather_collector.py` and `subscriber/subscriber.py` failed
  with `ModuleNotFoundError` when run directly — fixed by adding the
  project root to `sys.path`.
- Dashboard crashed with `TemplateNotFound: index.html` — the template
  folder was named `template` instead of Flask's expected `templates`;
  renamed it.
- Dashboard always showed an empty table — it was reading from a
  different MongoDB collection (`data`) than the subscriber was writing
  to (`weather_data`). Both now read/write `MONGO_COLLECTION_NAME` from
  config, set to `weather_data`.
- Subscriber connected to EMQX with no username/password while the
  collector did — added matching credentials so this works once you
  enable authentication on EMQX.
- Collector never called `client.loop_start()`, so the MQTT connection
  would silently drop after the keepalive timeout — fixed.
- Added timeouts to the `requests.get()` calls so a slow weather API
  can't hang the whole collector loop.
- API keys were hardcoded in `config.py` — moved to a `.env` file via
  `python-dotenv`. **The original keys were visible in your uploaded
  project — rotate them, since anyone who saw that file now has them.**
- Removed the empty, unused `publisher/` folder (`weather_collector.py`
  already does the publishing).
- The dashboard's "search a city" form fetched temperature and humidity
  but had lost its pressure field along the way — added it back, fused
  from OpenWeatherMap and Tomorrow.io the same way temperature already
  is.
- The periodic background collector had also silently stopped including
  pressure in its readings — restored.
- Submitting a city published to MQTT and immediately re-queried MongoDB
  on the same request, but the subscriber (a separate process) needs a
  moment to actually write the document — so the page could show stale
  data right after a search. Now each submission carries a unique
  `request_id` and the dashboard briefly polls MongoDB for that exact
  document before rendering, so you see your real result instead of
  having to refresh.

## How the city search works

1. You type a city into the form on the dashboard and submit.
2. The dashboard fetches temperature, humidity, and pressure for that
   city from OpenWeatherMap, WeatherAPI, and Tomorrow.io, and fuses
   them (averaging where more than one source has a value).
3. It publishes the fused reading to EMQX on `weather/<city>`, the same
   topic pattern the background collector uses.
4. The subscriber service picks it up and writes it to MongoDB.
5. The dashboard waits briefly for that exact write to land, then shows
   the city, temperature, humidity, and pressure in the table.

## What changed in this round

- The dashboard's MQTT publish step connected to EMQX once with no
  retry. If you submitted a city search in the few seconds right after
  `docker compose up`, before EMQX had finished starting, it would fail
  with a connection error. It now retries for up to ~10 seconds, the
  same pattern already used by the collector and subscriber.
- `docker-compose.yml` now has a real healthcheck on MongoDB (`mongosh`
  ping) and makes `subscriber`/`dashboard` wait for Mongo to report
  healthy — not just "container started" — before they start. EMQX is
  left without a gating healthcheck since its built-in `emqx ctl status`
  check is known to report false negatives in some Docker setups even
  while the broker is working fine; the app-level retry loops handle
  that case instead.
- Removed the obsolete `version: "3.8"` line from `docker-compose.yml`
  (modern Docker Compose ignores it and warns about it).
- Added `run.ps1` — a PowerShell script that builds/starts everything,
  waits until the dashboard actually responds, and prints the dashboard
  and EMQX URLs directly in your terminal (see below).

## Quick start on Windows (PowerShell)

```powershell
.\run.ps1
```

This will:
1. Create `.env` from `.env.example` for you if it doesn't exist yet
   (and tell you to fill in your API keys and re-run).
2. Run `docker compose up -d --build`.
3. Poll `http://localhost:5000` until the dashboard actually responds.
4. Print both URLs directly in your PowerShell window:

```
=================================================
  Dashboard:       http://localhost:5000
  EMQX Dashboard:  http://localhost:18083  (login: admin / public)
=================================================
```

5. Open the dashboard in your default browser automatically.

If PowerShell blocks the script with an execution-policy error, run it
once with:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

## Running it

### Windows (PowerShell) — recommended

```powershell
.\run.ps1
```

See the "Quick start" section above for exactly what this does.

### Manual / any OS

```bash
cp .env.example .env
# edit .env and fill in your real API keys

docker compose up -d --build
```

This builds and starts four containers:
- **emqx** — the MQTT broker, on `localhost:1883` (MQTT) and
  `localhost:18083` (web dashboard, login `admin` / `public`)
- **mongo** — MongoDB on `localhost:27017`
- **subscriber** — listens to EMQX and writes readings into MongoDB
- **dashboard** — the Flask web app, on `localhost:5000`

Check they all came up:

```bash
docker compose ps
```

Then open `http://localhost:5000`, type a city, and submit.

By default EMQX allows anonymous connections, so the code works
immediately even though it sends a username/password. If you want EMQX
to actually *enforce* those credentials:

1. Go to the EMQX Dashboard → **Access Control → Authentication**.
2. Add a "Built-in Database" authenticator.
3. Add two users matching your `.env` values:
   - `weather_provider_1` / `wp1_secret`
   - `weather_subscriber_1` / `ws1_secret`
4. Turn off "allow anonymous" once both users are created.

### Optional: the periodic background collector

`weather_collector.py` auto-fetches a fixed list of cities every 10
seconds. It isn't part of `docker-compose.yml` — only the on-demand
city search is. To run it too:

```bash
pip install -r requirements.txt
python -m collector.weather_collector
```

Your `.env`'s default `MQTT_HOST=localhost` / `MQTT_PORT=1883` works
fine here since EMQX's port is published to your machine by Compose.

## Viewing the stored data

```bash
docker exec -it mongo mongosh
```

```javascript
use weather_fusion
db.weather_data.find().sort({_id: -1}).limit(10).pretty()
```

Or connect MongoDB Compass / any GUI client to `mongodb://localhost:27017`
and browse to the `weather_fusion` database → `weather_data` collection.
If you've dropped that collection before, don't worry — MongoDB
recreates the database and collection automatically the next time a
document is inserted, which happens the moment you search a city.

```
Simulator/
├── collector/
│   └── weather_collector.py   # fetches + publishes (the "publisher")
├── subscriber/
│   └── subscriber.py          # subscribes + writes to MongoDB
├── database/
│   └── mongo.py
├── dashboard/
│   ├── app.py
│   ├── templates/index.html
│   └── static/style.css
├── config.py
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── run.ps1
└── requirements.txt
```
