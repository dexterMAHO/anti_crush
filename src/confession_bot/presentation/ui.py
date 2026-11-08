"""Button-based interface: labels, keyboards and one callback_data convention.

Interface standard used across the bot:
- A persistent reply keyboard is the only navigation surface; it is rebuilt per
  role so a user never sees a button they may not use.
- Inline keyboards only carry actions bound to one submission, plus paging.
- callback_data is always `action` or `action:argument`, stays well under the
  64-byte Telegram limit, and is re-authorized server-side on every press.
- Irreversible actions (rejection, withdrawal) ask for confirmation first.
- Every press is answered, so the client never shows a pending spinner.
- Labels are plain Persian text without emoji or decoration.
"""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from confession_bot.domain.policies import PERMISSIONS, Role

PAGE_SIZE = 10

SEND = "ارسال پیام جدید"
MINE = "پیام‌های من"
RULES = "قوانین"
HELP_BUTTON = "راهنما"
QUEUE = "صف بررسی"

# Reply-keyboard labels are routed like commands, never stored as submissions.
MENU_COMMANDS = {
    SEND: "/send",
    MINE: "/mine",
    RULES: "/rules",
    HELP_BUTTON: "/help",
    QUEUE: "/queue",
}

ACTION_LABELS = {
    "approve": "تأیید",
    "reject": "رد",
    "escalate": "بررسی ویژه",
    "needs_edit": "نیازمند اصلاح",
    "publish": "ثبت در صف انتشار",
    "identity": "مشاهده فرستنده",
    "history": "تاریخچه",
}

# Each item action maps to the permission that must hold for the pressing admin.
ACTION_PERMISSIONS = {
    "approve": "review",
    "reject": "review",
    "escalate": "review",
    "needs_edit": "review",
    "publish": "publish",
    "identity": "identity",
    "history": "history",
}

BUTTON_REASON = "تصمیم مدیر از طریق دکمه"


def allows(role, action):
    return role in PERMISSIONS[ACTION_PERMISSIONS[action]]


def main_menu(role):
    rows = [
        [KeyboardButton(text=SEND), KeyboardButton(text=MINE)],
        [KeyboardButton(text=RULES), KeyboardButton(text=HELP_BUTTON)],
    ]
    if role in set(Role):
        rows.append([KeyboardButton(text=QUEUE)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True)


def pairs(buttons):
    return [buttons[index : index + 2] for index in range(0, len(buttons), 2)]


def item_keyboard(code, role):
    buttons = [
        InlineKeyboardButton(text=ACTION_LABELS[action], callback_data=f"{action}:{code}")
        for action in ACTION_LABELS
        if allows(role, action)
    ]
    return InlineKeyboardMarkup(inline_keyboard=pairs(buttons)) if buttons else None


def paging_keyboard(page, more):
    row = []
    if page > 1:
        row.append(InlineKeyboardButton(text="صفحه قبل", callback_data=f"queue:{page - 1}"))
    if more:
        row.append(InlineKeyboardButton(text="صفحه بعد", callback_data=f"queue:{page + 1}"))
    return InlineKeyboardMarkup(inline_keyboard=[row]) if row else None


def confirm_keyboard(action, code):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="بله، انجام شود", callback_data=f"{action}!:{code}"),
                InlineKeyboardButton(text="انصراف", callback_data="cancel"),
            ]
        ]
    )


def withdraw_keyboard(code):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="انصراف از انتشار", callback_data=f"withdraw:{code}")]
        ]
    )


def item_text(msg):
    return (
        f"کد پیگیری: {msg.code}\n"
        f"سطح خطر: {msg.risk}\n"
        f"وضعیت بررسی: {msg.review}\n"
        f"وضعیت انتشار: {msg.publication}\n"
        f"متن پیام:\n{msg.original_text}"
    )


def identity_text(identity):
    profile = identity.get("profile") or {}
    lines = [
        f"کد پیگیری: {identity['code']}",
        f"شناسه عددی فرستنده: {identity['telegram_id']}",
        f"نام: {profile.get('first_name', 'نامشخص')}",
        f"نام کاربری: {profile.get('username', 'نامشخص')}",
        f"متن پیام:\n{identity['text']}",
    ]
    return "\n".join(lines) + "\nاین دسترسی در سوابق ثبت شد."
