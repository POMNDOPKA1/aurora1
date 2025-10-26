from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")
CHANNEL_ID_RAW = os.getenv("CHANNEL_ID")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

if not BOT_TOKEN:
    raise EnvironmentError("Missing BOT_TOKEN in environment (.env)")

try:
    ADMIN_IDS = [int(i) for i in ADMIN_IDS_RAW.split(",") if i.strip()]
except ValueError:
    raise EnvironmentError("ADMIN_IDS must be comma-separated integers")

try:
    CHANNEL_ID = int(CHANNEL_ID_RAW) if CHANNEL_ID_RAW else None
except ValueError:
    raise EnvironmentError("CHANNEL_ID must be an integer (channel/chat id)")

# Data directory & default JSON paths
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

JSON_APPS = DATA_DIR / "applications.json"
JSON_FLIGHTS = DATA_DIR / "flights.json"
JSON_SIGNUPS = DATA_DIR / "flight_signups.json"
