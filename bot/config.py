import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
DB_PATH = os.getenv("DB_PATH", "expenses.db")
PORT = int(os.getenv("PORT", "8000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is required")
if not RENDER_EXTERNAL_URL:
    raise RuntimeError("RENDER_EXTERNAL_URL environment variable is required")

if ADMIN_ID:
    ADMIN_ID = int(ADMIN_ID)