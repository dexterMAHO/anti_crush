import json

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from confession_bot.domain.policies import DomainError

POLICY = """قوانین و سیاست نگهداری اطلاعات
پیام شما فقط برای مخاطبان کانال ناشناس است، نه برای ارائه‌دهنده سرویس.
سرویس متن اصلی پیام‌ها، شناسه عددی، پروفایل دریافتی از تلگرام، تعاملات،
تصمیم‌های مدیریت و سوابق انتشار را بدون حذف خودکار نگهداری می‌کند.
مدیر دارای مجوز می‌تواند هویت فرستنده را بررسی کند؛ این دسترسی ثبت می‌شود.
انصراف فقط مانع انتشار می‌شود و به معنی حذف سوابق نیست.
اطلاعاتی که تلگرام در اختیار ربات قرار نمی‌دهد جمع‌آوری نمی‌شود.
تهدید، آزار و افشای اطلاعات شخصی دیگران مجاز نیست.
تمام پیام‌ها پیش از انتشار توسط مدیر بررسی می‌شوند.
برای پذیرش این سیاست /accept را بزنید."""

HELP = """ارسال: پس از پذیرش قوانین، یک پیام متنی بفرستید.
/rules — قوانین و سیاست نگهداری
/accept — پذیرش قوانین
/mine — آخرین پیام‌ها و وضعیت
/withdraw CODE — انصراف از انتشار، با حفظ سوابق
/help — راهنما
مدیریت:
/queue PAGE — صف بررسی و انتشار؛ شماره صفحه اختیاری است
/approve CODE دلیل — تأیید
/reject CODE دلیل — رد
/escalate CODE دلیل — بررسی ویژه
/needs_edit CODE دلیل — نیازمند اصلاح
/publish CODE — ثبت در صف انتشار
/identity CODE دلیل — مشاهده هویت (مالک)
/restrict CODE HOURS دلیل — محدودیت؛ ۰ دائمی، منفی ۱ رفع محدودیت
/role TELEGRAM_ID ROLE — تعیین نقش؛ NONE برای لغو
/history CODE — تاریخچه عملیات
/reconcile CODE MESSAGE_ID دلیل — تطبیق انتشار نامشخص؛ صفر یعنی منتشر نشده"""


def router(service, settings):
    result = Router()

    async def respond(message, text, **kwargs):
        # Telegram output limit applies to Unicode code points/UTF-16; keep chunks small.
        for start in range(0, len(text), 1800):
            try:
                await message.answer(text[start : start + 1800], parse_mode=None, **kwargs)
            except TelegramForbiddenError:
                return  # Blocked recipients must not poison the durable inbox.

    def policy():
        ai = (
            "\nبررسی هوش مصنوعی فعال است و متن با پوشاندن الگوهای حساس به سرویس "
            "پردازش خارجی ارسال می‌شود."
            if settings.ai_moderation_enabled
            else "\nبررسی هوش مصنوعی خارجی غیرفعال است."
        )
        return POLICY + ai + f"\nنسخه سیاست: {settings.policy_version}"

    @result.message(F.chat.type == "private")
    async def private(message: Message, event_update):
        actor = message.from_user.id
        text = message.text or ""
        parts = text.split(maxsplit=3)
        cmd = parts[0].split("@")[0].lower() if parts else ""
        try:
            if cmd in {"/start", "/rules"}:
                await respond(message, policy())
            elif cmd == "/help":
                await respond(message, HELP)
            elif cmd == "/accept":
                await service.accept(actor)
                await respond(message, "پذیرش ثبت شد. اکنون پیام متنی خود را ارسال کنید.")
            elif cmd == "/mine":
                rows = await service.mine(actor)
                await respond(
                    message,
                    "\n".join(f"{m.code}: {m.review} / {m.publication}" for m in rows)
                    or "هنوز پیامی ثبت نکرده‌اید.",
                )
            elif cmd == "/withdraw" and len(parts) == 2:
                await service.withdraw(actor, parts[1])
                await respond(message, "از انتشار منصرف شدید؛ سوابق نزد سرویس حفظ می‌شود.")
            elif cmd == "/queue":
                rows = await service.queue(actor, int(parts[1]) if len(parts) == 2 else 1)
                if not rows:
                    await respond(message, "صف خالی است.")
                for msg in rows:
                    buttons = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="تأیید", callback_data=f"approve:{msg.code}"
                                ),
                                InlineKeyboardButton(
                                    text="بررسی ویژه", callback_data=f"escalate:{msg.code}"
                                ),
                                InlineKeyboardButton(
                                    text="انتشار", callback_data=f"publish:{msg.code}"
                                ),
                            ]
                        ]
                    )
                    await respond(
                        message,
                        f"{msg.code} | {msg.risk} | {msg.review} | {msg.publication}\n"
                        f"{msg.original_text}",
                        reply_markup=buttons,
                    )
            elif cmd in {"/approve", "/reject", "/escalate", "/needs_edit"} and len(parts) >= 3:
                await service.decide(
                    actor,
                    parts[1],
                    {
                        "/approve": "APPROVED",
                        "/reject": "REJECTED",
                        "/escalate": "ESCALATED",
                        "/needs_edit": "NEEDS_EDIT",
                    }[cmd],
                    text.split(maxsplit=2)[2],
                )
                await respond(message, "تصمیم ثبت شد.")
            elif cmd == "/publish" and len(parts) == 2:
                await service.enqueue(actor, parts[1])
                await respond(message, "در صف انتشار قرار گرفت.")
            elif cmd == "/identity" and len(parts) >= 3:
                identity = await service.identity(actor, parts[1], text.split(maxsplit=2)[2])
                await respond(message, json.dumps(identity, ensure_ascii=False))
            elif cmd == "/role" and len(parts) == 3:
                await service.set_role(actor, int(parts[1]), parts[2].upper())
                await respond(message, "نقش ثبت شد.")
            elif cmd == "/restrict" and len(parts) == 4:
                await service.restrict(actor, parts[1], int(parts[2]), parts[3])
                await respond(message, "محدودیت به‌روز شد.")
            elif cmd == "/history" and len(parts) == 2:
                await respond(message, "\n".join(await service.history(actor, parts[1])) or "خالی")
            elif cmd == "/reconcile" and len(parts) == 4:
                await service.reconcile(actor, parts[1], int(parts[2]), parts[3])
                await respond(message, "نتیجه تطبیق ثبت شد.")
            elif cmd.startswith("/"):
                await respond(message, "دستور یا آرگومان نامعتبر است. /help")
            elif not message.text:
                await respond(message, "برای انتشار فقط پیام متنی پذیرفته می‌شود.")
            else:
                code = await service.submit(
                    actor,
                    text,
                    event_update.update_id,
                    message.message_id,
                    message.from_user.model_dump(mode="json", exclude_none=True),
                )
                await respond(message, f"پیام دریافت شد. کد پیگیری: {code}\nوضعیت: /mine")
        except (DomainError, ValueError) as exc:
            await respond(
                message, str(exc) if isinstance(exc, DomainError) else "ورودی نامعتبر است. /help"
            )

    async def answer_callback(query, text, show_alert=False):
        try:
            await query.answer(text, show_alert=show_alert)
        except TelegramBadRequest:
            pass  # Telegram callback answers expire; durable actions do not.

    @result.callback_query()
    async def callback(query: CallbackQuery):
        if not query.message or query.message.chat.type != "private":
            await answer_callback(query, "فقط در گفت‌وگوی خصوصی.", show_alert=True)
            return
        try:
            action, code = (query.data or "").split(":", 1)
            if action == "publish":
                await service.enqueue(query.from_user.id, code)
            elif action in {"approve", "escalate"}:
                await service.decide(
                    query.from_user.id,
                    code,
                    "APPROVED" if action == "approve" else "ESCALATED",
                    "تصمیم مدیر از طریق دکمه",
                )
            else:
                raise DomainError("دستور نامعتبر است.")
            await answer_callback(query, "ثبت شد.")
        except (DomainError, ValueError) as exc:
            await answer_callback(
                query,
                str(exc) if isinstance(exc, DomainError) else "دستور نامعتبر است.",
                show_alert=True,
            )

    return result
