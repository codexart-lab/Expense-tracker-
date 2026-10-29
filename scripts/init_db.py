import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.database import init_db
from bot.config import DB_PATH


async def main():
    print(f"Initializing database at {DB_PATH}...")
    await init_db()
    print("Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(main())