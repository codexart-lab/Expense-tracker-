import csv
import io
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile

from bot.database import get_all_expenses
from bot.keyboards import welcome_kb

router = Router(name="export")


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    expenses = await get_all_expenses(message.from_user.id)

    if not expenses:
        await message.answer("📭 No expenses to export.", reply_markup=welcome_kb())
        return

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "created_at", "amount", "description"])
    for exp in expenses:
        writer.writerow([exp["id"], exp["created_at"], f"{exp['amount']:.2f}", exp["description"]])

    csv_data = output.getvalue().encode("utf-8")
    document = BufferedInputFile(csv_data, filename="expenses.csv")

    await message.answer_document(
        document=document,
        caption=f"📤 <b>Export Complete</b>\n\n{len(expenses)} transactions exported.",
        reply_markup=welcome_kb(),
    )