from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def welcome_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Add expense", callback_data="add_expense"),
        InlineKeyboardButton(text="📊 Stats", callback_data="stats"),
    )
    builder.row(
        InlineKeyboardButton(text="💰 Balance", callback_data="balance"),
        InlineKeyboardButton(text="📤 Export", callback_data="export"),
    )
    return builder.as_markup()


def stats_period_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Today", callback_data="stats_today"),
        InlineKeyboardButton(text="Last 7 days", callback_data="stats_week"),
    )
    builder.row(
        InlineKeyboardButton(text="Last 30 days", callback_data="stats_month"),
        InlineKeyboardButton(text="All time", callback_data="stats_all"),
    )
    return builder.as_markup()


def after_add_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Add another", callback_data="add_expense"),
        InlineKeyboardButton(text="📊 View stats", callback_data="stats"),
    )
    builder.row(
        InlineKeyboardButton(text="💰 Balance", callback_data="balance"),
    )
    return builder.as_markup()