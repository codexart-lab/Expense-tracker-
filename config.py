import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
DB_PATH = "expenses.db"
