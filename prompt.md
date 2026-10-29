# TASK

Build a complete, production-ready Telegram **expense tracker bot** as a GitHub repository. The final repo must be deployable to **Render** (webhook mode) and publishable to **Docker Hub** via **GitHub Actions**.

Deliver every file with full contents, no placeholders, no "…". Include a README with deploy steps.

---

# TECH STACK (fixed)

- Python 3.12
- aiogram 3.13.x (async Telegram framework)
- FastAPI 0.115.x + uvicorn (web server for webhook)
- aiosqlite (async SQLite driver)
- pydantic 2.x
- python-dotenv
- Docker (multi-stage build, non-root user, healthcheck)

Do NOT use polling. Use **webhook mode only**.

---

# FEATURES

## User-facing
- `/start` — rich HTML welcome message with an inline keyboard:
  - ➕ Add expense · 📊 Stats · 💰 Balance · 📤 Export
- `/help` — usage guide
- **Quick add** by plain text: `coffee 150` OR `150 coffee` (also accepts `1.500,50` decimal comma)
- `/add` — guided FSM flow: prompt amount → prompt description → save
- `/list` — last 10 transactions for that user
- `/balance` — total spent + transaction count
- `/stats` — inline period buttons: Today / Last 7 days / Last 30 days / All time
  - Breaks down by description, shows amount + percentage
- `/export` — sends CSV file of all user transactions (id, created_at, amount, description)
- `/delete <id>` — delete transaction by ID (scoped to that user)
- `/cancel` — abort any active FSM

## Admin-only (gated by ADMIN_ID env var)
- `/backup` — copies SQLite DB and sends the `.db` file to admin
- `POST /trigger-backup` — HTTP endpoint for **cron-job.org** scheduled backups
  - Requires header `X-Cron-Secret: <WEBHOOK_SECRET>`
  - Sends the backup file to the admin chat

## Bot command menu
On startup, register a `BotCommandScopeDefault` menu with all commands above.

## Security
- Webhook endpoint `/webhook` validates `X-Telegram-Bot-Api-Secret-Token` header against `WEBHOOK_SECRET` env var. Return 403 on mismatch.
- Admin endpoints validate `X-Cron-Secret` header.
- `/backup` command protected by `IsAdmin` filter.
- All user-scoped queries filter by `user_id = message.from_user.id`.

## Health
- `GET /` returns `{"status": "ok", "service": "expense-tracker-bot"}`

---

# DATABASE SCHEMA (SQLite, auto-created on startup)

```sql
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    amount      REAL    NOT NULL,
    description TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_expenses_user ON expenses(user_id);
CREATE INDEX IF NOT EXISTS idx_expenses_created ON expenses(created_at);
```

DB path from env `DB_PATH`, default `expenses.db` (Docker: `/data/expenses.db`).

---

# REQUIRED FILE STRUCTURE

```
expense-tracker-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app + webhook + lifespan
│   ├── config.py               # env loading (fails fast if required vars missing)
│   ├── database.py             # schema init + helper
│   ├── keyboards.py            # welcome_kb, stats_period_kb, after_add_kb
│   ├── filters.py              # IsAdmin filter
│   └── handlers/
│       ├── __init__.py         # register_all(dp)
│       ├── start.py            # /start /help + welcome callbacks
│       ├── expenses.py         # /add /list /delete /cancel + quick-add regex handler
│       ├── stats.py            # /balance /stats + period callbacks
│       ├── export.py           # /export
│       └── admin.py            # /backup
├── scripts/
│   └── init_db.py              # one-off DB init
├── .github/workflows/
│   ├── ci.yml                  # ruff lint on push/PR
│   └── docker-publish.yml      # build + push to Docker Hub
├── Dockerfile                  # multi-stage, non-root, healthcheck
├── .dockerignore
├── docker-compose.yml          # local dev (mounts /data, reads .env.docker)
├── .env.example
├── .gitignore
├── requirements.txt
├── render.yaml                 # Render Blueprint (image-based deploy)
├── Procfile                    # fallback for native Render deploy
├── runtime.txt
├── README.md
└── LICENSE                     # MIT
```

---

# IMPLEMENTATION REQUIREMENTS

## `bot/config.py`
- Load `.env` via python-dotenv.
- Read: `BOT_TOKEN`, `ADMIN_ID` (int), `WEBHOOK_SECRET`, `RENDER_EXTERNAL_URL`, `DB_PATH` (default `expenses.db`), `PORT` (default 8000).
- **Raise `RuntimeError` at import if `BOT_TOKEN` or `RENDER_EXTERNAL_URL` is missing** (fail fast).

## `bot/main.py`
- Instantiate `Bot(token=..., parse_mode="HTML")` and `Dispatcher()`.
- Call `register_all(dp)` from `bot.handlers`.
- FastAPI `lifespan`:
  1. `await init_db()`
  2. `await bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/webhook", secret_token=WEBHOOK_SECRET, drop_pending_updates=True)`
  3. `await set_my_commands()`
  4. yield → `await bot.session.close()`
- `POST /webhook` → validate secret header → `Update.model_validate(...)` → `dp.feed_update(...)`.
- `GET /` → health JSON.
- `POST /trigger-backup` → validate `X-Cron-Secret` → copy DB → `bot.send_document(ADMIN_ID, ...)`.
- `if __name__ == "__main__": uvicorn.run("bot.main:app", host="0.0.0.0", port=PORT)`.

## `bot/handlers/expenses.py` — quick-add parser
Use a regex message filter compatible with aiogram 3's `F.text.regexp(...)`. Accept both orders:
- `(?i)^\s*(.+?)\s+([\d.,]+)\s*$` → "coffee 150"
- `(?i)^\s*([\d.,]+)\s+(.+)$` → "150 coffee"

Guard with `StateFilter(None)` so it doesn't fire during FSM. Truncate description to 100 chars. Reject amounts ≤ 0.

On save, reply with `✅ Saved: <b>{desc}</b> — {amount:,.2f}` and `after_add_kb()`.

## `bot/handlers/stats.py`
Period ranges in UTC:
- `today` → today 00:00
- `week` → now − 7 days
- `month` → now − 30 days
- `all` → no filter

## `bot/handlers/export.py`
CSV via stdlib `csv` + `tempfile`, send via `FSInputFile`, delete after sending.

## `bot/handlers/admin.py`
`@router.message(Command("backup"), IsAdmin())` — copy DB file to temp, send to admin, delete temp.

---

# DOCKERFILE REQUIREMENTS

Two-stage build:

1. **Builder** (`python:3.12-slim`):
   - Install `build-essential`, `gcc`
   - `pip wheel --wheel-dir /wheels -r requirements.txt`

2. **Runtime** (`python:3.12-slim`):
   - `groupadd --gid 1001 app && useradd --uid 1001 --gid app --create-home app`
   - `pip install --no-index --find-links=/wheels -r requirements.txt`
   - `COPY --chown=app:app bot/ ./bot/` and `scripts/`
   - `RUN mkdir -p /data && chown app:app /data`
   - `USER app`
   - `EXPOSE 8000`
   - `HEALTHCHECK` using `urllib.request.urlopen('http://127.0.0.1:8000/')`
   - `CMD ["uvicorn", "bot.main:app", "--host", "0.0.0.0", "--port", "8000"]`
   - Env defaults: `PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000 DB_PATH=/data/expenses.db`

---

# GITHUB ACTIONS — `.github/workflows/docker-publish.yml`

Trigger on:
- push to `main`
- tags matching `v*`
- `workflow_dispatch`

Use these actions:
- `actions/checkout@v4`
- `docker/setup-buildx-action@v3`
- `docker/login-action@v3` with `secrets.DOCKERHUB_USERNAME` / `secrets.DOCKERHUB_TOKEN`
- `docker/metadata-action@v5` producing tags:
  - `latest` (only on default branch)
  - `{{version}}` from semver tag
  - `sha-<short>` for every commit
- `docker/build-push-action@v6` with:
  - `push: true`
  - `cache-from: type=gha`, `cache-to: type=gha,mode=max`
  - `context: .`

Output image: `${{ secrets.DOCKERHUB_USERNAME }}/expense-bot`.

## `.github/workflows/ci.yml`

Simple lint on push/PR:
```yaml
- uses: actions/setup-python@v5 with python-version: "3.12"
- run: pip install ruff && ruff check bot/ scripts/
```

---

# RENDER CONFIGURATION — `render.yaml`

Image-based deploy (not Git build):

```yaml
services:
  - type: web
    name: expense-tracker-bot
    runtime: image
    image:
      url: docker.io/YOUR_DOCKERHUB_USERNAME/expense-bot:latest
    plan: starter
    envVars:
      - key: BOT_TOKEN        { sync: false }
      - key: ADMIN_ID         { sync: false }
      - key: WEBHOOK_SECRET   { generateValue: true }
      - key: RENDER_EXTERNAL_URL { sync: false }
      - key: DB_PATH          { value: /data/expenses.db }
    disk:
      name: bot-data
      mountPath: /data
      sizeGB: 1
```

---

# README.md REQUIREMENTS

Include these sections:

1. **Badges**: CI status, Docker Hub pulls (image name `YOUR_DOCKERHUB_USERNAME/expense-bot`).
2. **Features** — bullet list from above.
3. **Quick start (Render)** — steps:
   - Fork repo
   - Set GitHub secrets `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`
   - Push to `main` → image auto-publishes to Docker Hub
   - Deploy `render.yaml` on Render (Blueprints)
   - Set env vars: `BOT_TOKEN`, `ADMIN_ID`, `WEBHOOK_SECRET`, `RENDER_EXTERNAL_URL`
4. **Local dev**:
   ```bash
   git clone ...
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env   # fill in
   python -m scripts.init_db
   uvicorn bot.main:app --reload
   ngrok http 8000        # set RENDER_EXTERNAL_URL=https://<ngrok>
   ```
5. **Docker**:
   ```bash
   docker build -t YOUR_USERNAME/expense-bot:latest .
   docker run -d --name expense-bot -p 8000:8000 \
     --env-file .env.docker -v expense-data:/data \
     YOUR_USERNAME/expense-bot:latest
   ```
6. **cron-job.org setup** — two jobs:
   - `POST https://<service>.onrender.com/trigger-backup`, header `X-Cron-Secret: <WEBHOOK_SECRET>`, daily 02:00
   - `GET https://<service>.onrender.com/`, every 10 min (keep-alive ping)
7. **Commands table** (command → description).
8. **Usage examples** — quick-add, guided add, stats, export.
9. **Data persistence warning** — free tier `/data` is ephemeral; use Render Postgres or paid disk for production.
10. **License** — MIT.

---

# `.env.example`

```dotenv
BOT_TOKEN=123456:ABC-your-token-from-BotFather
ADMIN_ID=123456789
WEBHOOK_SECRET=generate-a-long-random-string
RENDER_EXTERNAL_URL=https://your-service.onrender.com
DB_PATH=expenses.db
# PORT=8000
```

---

# ACCEPTANCE CRITERIA

The generated repo must:

1. ✅ `pip install -r requirements.txt` succeeds on Python 3.12.
2. ✅ `uvicorn bot.main:app` starts without error once env vars are set.
3. ✅ `docker build -t test/expense-bot .` completes in <3 minutes and produces an image <250MB.
4. ✅ `docker run -e ... test/expense-bot` responds `200` at `GET /`.
5. ✅ Sending `/start` in Telegram (with a public webhook URL) shows the welcome keyboard.
6. ✅ Sending `coffee 150` saves a row and replies with "✅ Saved".
7. ✅ `/export` sends a valid CSV.
8. ✅ `/backup` from non-admin is ignored (no reply, no error).
9. ✅ `/backup` from admin sends the DB file.
10. ✅ `POST /trigger-backup` with wrong `X-Cron-Secret` returns 403.
11. ✅ Pushing to `main` triggers the `docker-publish` workflow, which pushes `latest` + `sha-<short>` to Docker Hub.
12. ✅ No secret is hardcoded; `.env` is in `.gitignore`; `.dockerignore` excludes `.env`, `*.db`, `.git/`.

---

# OUTPUT FORMAT

Produce:
1. A single numbered list of every file to create.
2. A fenced code block per file with full contents and language hint.
3. A final "next steps" section: the exact `git` and `docker` commands to publish.
4. Do not explain the code inline — the code speaks for itself. Keep prose minimal (≤ 100 words per file).
