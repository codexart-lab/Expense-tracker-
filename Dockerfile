# Build stage
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/wheels -r requirements.txt


# Runtime stage
FROM python:3.12-slim

RUN groupadd -r app && useradd -r -g app -u 1001 app

WORKDIR /app

COPY --from=builder /wheels /usr/local

COPY --chown=app:app bot/ ./bot/
COPY --chown=app:app scripts/ ./scripts/

ENV DB_PATH=/data/expenses.db
ENV PYTHONUNBUFFERED=1

USER app

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/')"

EXPOSE 8000

CMD ["uvicorn", "bot.main:app", "--host", "0.0.0.0", "--port", "8000"]