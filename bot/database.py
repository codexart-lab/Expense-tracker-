import aiosqlite
from pathlib import Path

from bot.config import DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_expenses_user ON expenses(user_id);
CREATE INDEX IF NOT EXISTS idx_expenses_created ON expenses(created_at);
"""


async def init_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def add_expense(user_id: int, amount: float, description: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO expenses (user_id, amount, description) VALUES (?, ?, ?)",
            (user_id, amount, description),
        )
        await db.commit()
        return cursor.lastrowid


async def get_expenses(user_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, amount, description, created_at FROM expenses WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_balance(user_id: int) -> tuple[float, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT SUM(amount) as total, COUNT(*) as count FROM expenses WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        total = row[0] if row[0] is not None else 0.0
        count = row[1] if row[1] is not None else 0
        return total, count


async def get_stats(user_id: int, since: str | None = None) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if since:
            cursor = await db.execute(
                """
                SELECT description, SUM(amount) as total
                FROM expenses
                WHERE user_id = ? AND created_at >= ?
                GROUP BY description
                ORDER BY total DESC
                """,
                (user_id, since),
            )
        else:
            cursor = await db.execute(
                """
                SELECT description, SUM(amount) as total
                FROM expenses
                WHERE user_id = ?
                GROUP BY description
                ORDER BY total DESC
                """,
                (user_id,),
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_all_expenses(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, created_at, amount, description FROM expenses WHERE user_id = ? ORDER BY created_at",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def delete_expense(user_id: int, expense_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM expenses WHERE user_id = ? AND id = ?",
            (user_id, expense_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_db_path() -> str:
    return DB_PATH