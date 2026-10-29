from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.database import get_balance, get_stats
from bot.keyboards import stats_period_kb, welcome_kb

router = Router(name="stats")


PERIODS = {
    "today": ("Today", None),
    "week": ("Last 7 days", None),
    "month": ("Last 30 days", None),
    "all": ("All time", None),
}


def get_since(period: str) -> str | None:
    now = datetime.utcnow()
    if period == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    elif period == "week":
        return (now - timedelta(days=7)).isoformat()
    elif period == "month":
        return (now - timedelta(days=30)).isoformat()
    return None


@router.message(Command("balance"))
async def cmd_balance(message: Message) -> None:
    total, count = await get_balance(message.from_user.id)
    await message.answer(
        f"💰 <b>Balance</b>\n\n"
        f"Total spent: <b>{total:.2f}</b>\n"
        f"Transactions: <b>{count}</b>",
        reply_markup=welcome_kb(),
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    await message.answer(
        "📊 <b>Statistics</b>\n\nSelect a period:",
        reply_markup=stats_period_kb(),
    )


@router.callback_query(F.data.startswith("stats_"))
async def cb_stats_period(callback: CallbackQuery) -> None:
    period = callback.data.split("_")[1]
    period_name = {
        "today": "Today",
        "week": "Last 7 days",
        "month": "Last 30 days",
        "all": "All time",
    }.get(period, "Unknown")

    since = get_since(period)
    stats = await get_stats(callback.from_user.id, since)

    if not stats:
        await callback.message.edit_text(
            f"📊 <b>Statistics — {period_name}</b>\n\nNo expenses recorded.",
            reply_markup=stats_period_kb(),
        )
        await callback.answer()
        return

    total = sum(s["total"] for s in stats)
    lines = [f"📊 <b>Statistics — {period_name}</b>\n"]
    lines.append(f"Total: <b>{total:.2f}</b>\n")

    for i, stat in enumerate(stats, 1):
        pct = (stat["total"] / total * 100) if total > 0 else 0
        lines.append(f"{i}. {stat['description']}: <b>{stat['total']:.2f}</b> ({pct:.1f}%)")

    lines.append("\n" + "─" * 20)
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=stats_period_kb(),
    )
    await callback.answer()