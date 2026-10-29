# Expense Tracker Bot

A production-ready Telegram bot for tracking personal expenses. Built with Python 3.12, aiogram 3.x, FastAPI, and aiosqlite. Deployed on Render via Docker.

## Features

- **Quick add**: Type `coffee 150` or `150 coffee` (supports decimal comma: `1.500,50`)
- **Guided entry**: `/add` walks you through amount → description
- **List transactions**: `/list` shows last 10 entries with IDs
- **Balance**: `/balance` shows total spent and transaction count
- **Statistics**: `/stats` with period selection (today, 7 days, 30 days, all time)
- **Export**: `/export` downloads all transactions as CSV
- **Delete**: `/delete <id>` removes a transaction
- **Admin backup**: `/backup` sends database to admin (admin only)
- **Scheduled backups**: Daily via cron-job.org

## Quick Start

### Prerequisites

- Python 3.12+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Your Telegram User ID (from [@userinfobot](https://t.me/userinfobot))

### Local Development

```bash
# Clone and enter
git clone <your-repo>
cd expense-tracker-bot

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your values (BOT_TOKEN, ADMIN_ID, WEBHOOK_SECRET, RENDER_EXTERNAL_URL)

# Initialize database
python -m scripts.init_db

# Run locally (requires ngrok for webhook)
# ngrok http 8000
# Then set RENDER_EXTERNAL_URL to your ngrok URL in .env
uvicorn bot.main:app --reload
```

### Docker

```bash
# Build
docker build -t expense-bot .

# Run
docker run -d --name expense-bot -p 8000:8000 \
  --env-file .env.docker -v expense-data:/data \
  expense-bot
```

## Deployment

### Render (Recommended)

1. Push to GitHub
2. Connect repo to Render
3. Use **Blueprint** (render.yaml) or create Web Service manually:
   - **Type**: Docker
   - **Plan**: Free
   - **Health Check**: `/`
   - **Environment Variables**: Set `BOT_TOKEN`, `ADMIN_ID`, `WEBHOOK_SECRET`
   - **Add Disk**: 1GB at `/data` (for SQLite persistence)

### cron-job.org Setup

Create two jobs:

| Name | URL | Method | Headers | Schedule |
|------|-----|--------|---------|----------|
| Backup | `https://your-app.onrender.com/trigger-backup` | POST | `X-Cron-Secret: <WEBHOOK_SECRET>` | Daily 02:00 UTC |
| Keep-alive | `https://your-app.onrender.com/` | GET | — | Every 10 min |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | From @BotFather |
| `ADMIN_ID` | Yes | Your Telegram user ID (integer) |
| `WEBHOOK_SECRET` | Yes | Long random string for webhook auth |
| `RENDER_EXTERNAL_URL` | Yes | Public URL (e.g., `https://app.onrender.com`) |
| `DB_PATH` | No | SQLite path (default: `expenses.db`, Docker: `/data/expenses.db`) |
| `PORT` | No | Server port (default: `8000`) |

## Project Structure

```
├── bot/
│   ├── main.py          # FastAPI app, webhook, lifespan, admin endpoints
│   ├── config.py        # Env loading (fails fast on missing required vars)
│   ├── database.py      # Schema init + async helpers
│   ├── keyboards.py     # Inline keyboards
│   ├── filters.py       # IsAdmin filter
│   └── handlers/        # Command handlers
│       ├── start.py     # /start /help + welcome callbacks
│       ├── expenses.py  # /add /list /delete /cancel + quick-add regex
│       ├── stats.py     # /balance /stats + period callbacks
│       ├── export.py    # /export (CSV)
│       └── admin.py     # /backup (admin only)
├── scripts/
│   └── init_db.py       # One-off DB init
├── .github/workflows/
│   ├── ci.yml           # ruff lint
│   └── docker-publish.yml # Build + push to Docker Hub
├── Dockerfile
├── docker-compose.yml
├── render.yaml          # Render Blueprint
├── Procfile
├── requirements.txt
├── runtime.txt
├── .env.example
├── .gitignore
├── .dockerignore
└── LICENSE
```

## Security

- Webhook validated via `X-Telegram-Bot-Api-Secret-Token`
- Admin endpoints protected by `X-Cron-Secret` header
- All queries filtered by `user_id`
- No secrets in code; `.env` in `.gitignore`
- Bot command menu registered on startup

## License

MIT License - see [LICENSE](LICENSE) for details.