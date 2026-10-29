import re
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot.database import add_expense, get_expenses, delete_expense
from bot.keyboards import after_add_kb, welcome_kb

router = Router(name="expenses")


class AddExpense(StatesGroup):
    amount = State()
    description = State()


AMOUNT_DESC_RE = re.compile(r"(?i)^\s*(.+?)\s+([\d.,]+)\s*$")
DESC_AMOUNT_RE = re.compile(r"(?i)^\s*([\d.,]+)\s+(.+)\s*$")


def parse_amount(text: str) -> float:
    text = text.replace(".", "").replace(",", ".")
    return float(text)


@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext) -> None:
    await state.set_state(AddExpense.amount)
    await message.answer("💸 <b>Add Expense</b>\n\nStep 1/2: Enter the amount (e.g., <code>150</code> or <code>1.500,50</code>)")


@router.message(AddExpense.amount)
async def process_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = parse_amount(message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Invalid amount. Please enter a positive number (e.g., <code>150</code> or <code>1.500,50</code>).")
        return

    await state.update_data(amount=amount)
    await state.set_state(AddExpense.description)
    await message.answer("📝 Step 2/2: Enter a description (e.g., <code>coffee</code>)")


@router.message(AddExpense.description)
async def process_description(message: Message, state: FSMContext) -> None:
    description = message.text.strip()
    if not description:
        await message.answer("❌ Description cannot be empty. Please try again.")
        return

    data = await state.get_data()
    amount = data["amount"]
    expense_id = await add_expense(message.from_user.id, amount, description)
    await state.clear()

    await message.answer(
        f"✅ <b>Expense added!</b>\n\n"
        f"💰 Amount: <b>{amount:.2f}</b>\n"
        f"📝 Description: <b>{description}</b>\n"
        f"🆔 ID: <code>{expense_id}</code>",
        reply_markup=after_add_kb(),
    )


@router.message(Command("cancel"), StateFilter("*"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Operation cancelled.", reply_markup=welcome_kb())


@router.message(F.text & StateFilter(None))
async def quick_add(message: Message) -> None:
    text = message.text.strip()

    match = AMOUNT_DESC_RE.match(text)
    if match:
        description, amount_str = match.groups()
    else:
        match = DESC_AMOUNT_RE.match(text)
        if not match:
            return
        amount_str, description = match.groups()

    try:
        amount = parse_amount(amount_str)
        if amount <= 0:
            return
    except ValueError:
        return

    expense_id = await add_expense(message.from_user.id, amount, description.strip())
    await message.answer(
        f"✅ <b>Expense added!</b>\n\n"
        f"💰 Amount: <b>{amount:.2f}</b>\n"
        f"📝 Description: <b>{description.strip()}</b>\n"
        f"🆔 ID: <code>{expense_id}</code>",
        reply_markup=after_add_kb(),
    )


@router.message(Command("list"))
async def cmd_list(message: Message) -> None:
    expenses = await get_expenses(message.from_user.id, 10)
    if not expenses:
        await message.answer("📭 No expenses recorded yet.")
        return

    lines = ["📋 <b>Last 10 Transactions</b>\n"]
    for exp in expenses:
        lines.append(
            f"🆔 <code>{exp['id']}</code> | "
            f"💰 {exp['amount']:.2f} | "
            f"📝 {exp['description']} | "
            f"🕐 {exp['created_at']}"
        )
    await message.answer("\n".join(lines))


@router.message(Command("delete"))
async def cmd_delete(message: Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Usage: <code>/delete <id></code>")
        return

    try:
        expense_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Invalid ID. Must be a number.")
        return

    deleted = await delete_expense(message.from_user.id, expense_id)
    if deleted:
        await message.answer(f"✅ Expense <code>{expense_id}</code> deleted.")
    else:
        await message.answer(f"❌ Expense <code>{expense_id}</code> not found.")