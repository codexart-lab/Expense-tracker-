# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-ready Telegram expense tracker bot built with:
- **Python 3.12**, **aiogram 3.13.x** (async Telegram framework)
- **FastAPI 0.115.x** + **uvicorn** (webhook server)
- **aiosqlite** (async SQLite)
- **pydantic 2.x**, **python-dotenv**
- Deployed to **Render** (webhook mode) via Docker image from **Docker Hub** (GitHub Actions)

## Key Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database (one-off)
python -m scripts.init_db

# Run locally with hot reload (requires ngrok for webhook)
uvicorn bot.main:app --reload

# Lint
ruff check bot/ scripts/
```

### Docker
```bash
# Build image
docker build -t YOUR_USERNAME/expense-bot:latest .

# Run container
docker run -d --name expense-bot -p 8000:8000 \
  --env-file .env.docker -v expense-data:/data \
  YOUR_USERNAME/expense-bot:latest
```

### Deploy
```bash
# Push to main → triggers GitHub Actions docker-publish.yml
# Image published to Docker Hub as: ${{ secrets.DOCKERHUB_USERNAME }}/expense-bot
# Deploy render.yaml on Render (Blueprints)
```

## Architecture

### File Structure
```
expense-tracker-bot/
├── bot/
│   ├── main.py           # FastAPI app, webhook, lifespan, admin endpoints
│   ├── config.py         # Env loading (fails fast on missing BOT_TOKEN/RENDER_EXTERNAL_URL)
│   ├── database.py       # Schema init + async helpers
│   ├── keyboards.py      # Inline keyboards (welcome, stats period, after-add)
│   ├── filters.py        # IsAdmin filter
│   └── handlers/
│       ├── __init__.py   # register_all(dp)
│       ├── start.py      # /start /help + welcome callbacks
│       ├── expenses.py   # /add /list /delete /cancel + quick-add regex
│       ├── stats.py      # /balance /stats + period callbacks
│       ├── export.py     # /export (CSV)
│       └── admin.py      # /backup (admin only)
├── scripts/
│   └── init_db.py        # One-off DB init
├── .github/workflows/
│   ├── ci.yml            # ruff lint on push/PR
│   └── docker-publish.yml # Build + push to Docker Hub
├── Dockerfile            # Multi-stage, non-root, healthcheck
├── docker-compose.yml    # Local dev
├── render.yaml           # Render Blueprint (image-based)
├── Procfile              # Fallback for native Render
├── requirements.txt
├── runtime.txt
├── .env.example
├── .gitignore
├── .dockerignore
├── README.md
└── LICENSE
```

### Database Schema
```sql
CREATE TABLE expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_expenses_user ON expenses(user_id);
CREATE INDEX idx_expenses_created ON expenses(created_at);
```
- Path from `DB_PATH` env (default `expenses.db`, Docker: `/data/expenses.db`)

### Critical Implementation Details

**Webhook Security** (`bot/main.py`):
- `POST /webhook` validates `X-Telegram-Bot-Api-Secret-Token` against `WEBHOOK_SECRET`
- `POST /trigger-backup` validates `X-Cron-Secret` against `WEBHOOK_SECRET`

**Admin Protection** (`bot/filters.py`):
- `IsAdmin` filter checks `message.from_user.id == ADMIN_ID`
- `/backup` command and `POST /trigger-backup` are admin-only

**Quick-add Parser** (`bot/handlers/expenses.py`):
- Regex: `(?i)^\s*(.+?)\s+([\d.,]+)\s*$` (desc amount) OR `(?i)^\s*([\d.,]+)\s+(.+)$` (amount desc)
- Guarded by `StateFilter(None)` to avoid FSM interference
- Accepts decimal comma: `1.500,50`

**Stats Periods** (`bot/handlers/stats.py`): UTC-based
- `today`: today 00:00
- `week`: now - 7 days
- `month`: now - 30 days
- `all`: no filter

**Health Check**: `GET /` returns `{"status": "ok", "service": "expense-tracker-bot"}`

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | Yes | - | From BotFather |
| `ADMIN_ID` | Yes | - | Telegram user ID (int) |
| `WEBHOOK_SECRET` | Yes | - | Long random string |
| `RENDER_EXTERNAL_URL` | Yes | - | Public webhook URL |
| `DB_PATH` | No | `expenses.db` | SQLite path |
| `PORT` | No | `8000` | Server port |

**Fail fast**: `bot/config.py` raises `RuntimeError` at import if `BOT_TOKEN` or `RENDER_EXTERNAL_URL` missing.

## Dockerfile Notes

- **Builder stage**: `python:3.12-slim`, installs `build-essential`, `gcc`, builds wheels to `/wheels`
- **Runtime stage**: `python:3.12-slim`, non-root user `app` (uid 1001), installs from wheels
- Healthcheck: `urllib.request.urlopen('http://127.0.0.1:8000/')`
- `DB_PATH=/data/expenses.db` in container

## GitHub Actions

- **ci.yml**: Runs `ruff check bot/ scripts/` on push/PR
- **docker-publish.yml**: Triggers on push to `main`, tags `v*`, `workflow_dispatch`
  - Uses `docker/metadata-action@v5` for tags: `latest`, semver, `sha-<short>`
  - Pushes to `${{ secrets.DOCKERHUB_USERNAME }}/expense-bot`

## Render Deployment (render.yaml)

- Image-based deploy from Docker Hub
- 1GB persistent disk at `/data`
- `WEBHOOK_SECRET` auto-generated
- Other secrets set manually in Render dashboard

## cron-job.org Setup

Two jobs required:
1. **Backup**: `POST https://<service>.onrender.com/trigger-backup`, header `X-Cron-Secret: <WEBHOOK_SECRET>`, daily 02:00 UTC
2. **Keep-alive**: `GET https://<service>.onrender.com/`, every 10 min

## Security Notes

- No secrets in code; `.env` in `.gitignore`; `.dockerignore` excludes `.env`, `*.db`, `.git/`
- All user queries filter by `user_id = message.from_user.id`
- Admin endpoints require header validation
- Bot command menu registered on startup via `BotCommandScopeDefault`

## Data Persistence Warning

Free Render tier `/data` is ephemeral. For production, use Render Postgres or paid disk.