import logging
import os
import shutil
import tempfile
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    FSInputFile,
    Update,
)
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

from bot.config import (
    ADMIN_ID,
    BOT_TOKEN,
    PORT,
    RENDER_EXTERNAL_URL,
    WEBHOOK_SECRET,
)
from bot.database import get_db_path, init_db
from bot.handlers import register_all

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ aiogram >= 3.7: parse_mode must go through DefaultBotProperties
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
register_all(dp)


async def set_my_commands() -> None:
    commands = [
        BotCommand(command="start", description="Start the bot and show welcome menu"),
        BotCommand(command="help", description="Show usage guide"),
        BotCommand(command="add", description="Guided expense entry (amount → description)"),
        BotCommand(command="list", description="Show last 10 transactions"),
        BotCommand(command="balance", description="Show total spent and transaction count"),
        BotCommand(command="stats", description="Show spending breakdown by period"),
        BotCommand(command="export", description="Export all transactions as CSV"),
        BotCommand(command="delete", description="Delete transaction by ID"),
        BotCommand(command="cancel", description="Cancel current operation"),
        BotCommand(command="backup", description="Admin: backup database"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    await bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True,
    )
    await set_my_commands()
    logger.info("Webhook set to %s", webhook_url)
    yield
    await bot.session.close()


app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(
        None, alias="X-Telegram-Bot-Api-Secret-Token"
    ),
):
    if x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret token")
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})


@app.get("/")
async def health() -> dict:
    return {"status": "ok", "service": "expense-tracker-bot"}


@app.post("/trigger-backup")
async def trigger_backup(
    request: Request,
    x_cron_secret: str | None = Header(None, alias="X-Cron-Secret"),
):
    if x_cron_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid cron secret")

    if ADMIN_ID is None:
        raise HTTPException(status_code=500, detail="ADMIN_ID not configured")

    db_path = await get_db_path()

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        shutil.copy2(db_path, tmp_path)
        await bot.send_document(
            chat_id=ADMIN_ID,
            document=FSInputFile(tmp_path, filename="expenses.db"),
            caption="📦 Scheduled backup",
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return JSONResponse({"ok": True, "message": "Backup sent to admin"})


if __name__ == "__main__":
    uvicorn.run("bot.main:app", host="0.0.0.0", port=PORT, reload=False)
