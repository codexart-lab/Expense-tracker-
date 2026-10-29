from aiogram import Dispatcher

from bot.handlers import start, expenses, stats, export, admin


def register_all(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(expenses.router)
    dp.include_router(stats.router)
    dp.include_router(export.router)
    dp.include_router(admin.router)