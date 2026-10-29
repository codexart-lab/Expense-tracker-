import shutil
import tempfile
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile

from bot.filters import IsAdmin
from bot.database import get_db_path

router = Router(name="admin")
router.message.filter(IsAdmin())


@router.message(Command("backup"))
async def cmd_backup(message: Message) -> None:
    db_path = await get_db_path()

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        shutil.copy2(db_path, tmp.name)
        document = FSInputFile(tmp.name, filename="expenses.db")
        await message.answer_document(
            document=document,
            caption="📦 <b>Database Backup</b>",
        )