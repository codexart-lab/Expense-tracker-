from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def welcome_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➕ Add expense", callback_data="add")
    b.button(text="📊 Stats", callback_data="stats_menu")
    b.button(text="💰 Balance", callback_data="balance")
    b.button(text="📤 Export", callback_data="export")
    b.adjust(2, 2)
    return b.as_markup()


def stats_period_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Today", callback_data="stats_today")
    b.button(text="This week", callback_data="stats_week")
    b.button(text="This month", callback_data="stats_month")
    b.button(text="All time", callback_data="stats_all")
    b.adjust(2, 2)
    return b.as_markup()


def after_add_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➕ Add another", callback_data="add")
    b.button(text="📋 Recent", callback_data="list")
    b.adjust(2)
    return b.as_markup()
