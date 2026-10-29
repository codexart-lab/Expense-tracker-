from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery

from bot.keyboards import welcome_kb
from bot.database import get_balance

router = Router(name="start")


WELCOME_TEXT = (
    "👋 <b>Welcome to Expense Tracker Bot!</b>\n\n"
    "I'll help you track your expenses easily.\n\n"
    "<b>Quick add:</b> Just type <code>coffee 150</code> or <code>150 coffee</code>\n"
    "(also accepts <code>1.500,50</code> with decimal comma)\n\n"
    "<b>Commands:</b>\n"
    "• /add — guided entry (amount → description)\n"
    "• /list — last 10 transactions\n"
    "• /balance — total spent + count\n"
    "• /stats — breakdown by period\n"
    "• /export — CSV of all transactions\n"
    "• /delete <id> — delete by ID\n"
    "• /cancel — abort current operation"
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=welcome_kb())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=welcome_kb())


@router.callback_query(F.data == "balance")
async def cb_balance(callback: CallbackQuery) -> None:
    total, count = await get_balance(callback.from_user.id)
    await callback.message.edit_text(
        f"💰 <b>Balance</b>\n\n"
        f"Total spent: <b>{total:.2f}</b>\n"
        f"Transactions: <b>{count}</b>",
        reply_markup=welcome_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "add_expense")
async def cb_add_expense(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "💸 <b>Add Expense</b>\n\n"
        "Send me a message like:\n"
        "• <code>coffee 150</code>\n"
        "• <code>150 coffee</code>\n"
        "• <code>lunch 1.500,50</code>\n\n"
        "Or use /add for guided entry.",
        reply_markup=welcome_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "stats")
async def cb_stats(callback: CallbackQuery) -> None:
    from bot.keyboards import stats_period_kb
    await callback.message.edit_text(
        "📊 <b>Statistics</b>\n\nSelect a period:",
        reply_markup=stats_period_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "export")
async def cb_export(callback: CallbackQuery) -> None:
    from bot.handlers.export import cmd_export
    await cmd_export(callback.message)
    await callback.answer()