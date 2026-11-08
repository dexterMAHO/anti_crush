from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import CallbackQuery, Message

from confession_bot.domain.policies import DomainError
from confession_bot.presentation import ui

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

HELP = """دکمه‌های پایین صفحه، مسیر اصلی کار با ربات هستند.
ارسال پیام جدید — راهنمای ارسال
پیام‌های من — آخرین پیام‌ها، وضعیت و دکمه انصراف
قوانین — قوانین و سیاست نگهداری
راهنما — همین متن
دستورهای معادل: /rules /accept /mine /withdraw CODE /help
مدیریت:
صف بررسی — ده پیام قدیمی آماده بررسی با دکمه‌های تصمیم، انتشار،
مشاهده فرستنده و تاریخچه؛ جابه‌جایی بین صفحه‌ها با دکمه‌های صفحه قبل و بعد.
دستورهای معادل و تکمیلی:
/queue PAGE — صف بررسی و انتشار؛ شماره صفحه اختیاری است
/approve CODE دلیل — تأیید
/reject CODE دلیل — رد
/escalate CODE دلیل — بررسی ویژه
/needs_edit CODE دلیل — نیازمند اصلاح
/publish CODE — ثبت در صف انتشار
/identity CODE دلیل — مشاهده هویت و متن پیام (مالک)
/restrict CODE HOURS دلیل — محدودیت؛ ۰ دائمی، منفی ۱ رفع محدودیت
/role TELEGRAM_ID ROLE — تعیین نقش؛ NONE برای لغو
/history CODE — تاریخچه عملیات
/reconcile CODE MESSAGE_ID دلیل — تطبیق انتشار نامشخص؛ صفر یعنی منتشر نشده"""

SEND_GUIDE = """برای ارسال، متن پیام خود را در همین گفت‌وگو بنویسید و بفرستید.
فقط پیام متنی پذیرفته می‌شود و پیش از انتشار توسط مدیر بررسی خواهد شد."""


def router(service, settings):
    result = Router()

    async def respond(target, text, **kwargs):
        # Telegram output limit applies to Unicode code points/UTF-16; keep chunks small.
        for start in range(0, len(text), 1800):
            chunk = text[start : start + 1800]
            last = start + 1800 >= len(text)
            try:
                # Keyboards belong on the final chunk so the menu is not repeated.
                await target.answer(chunk, parse_mode=None, **(kwargs if last else {}))
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

    async def show_queue(target, actor, page):
        rows = await service.queue(actor, page)
        role = await service.whoami(actor)
        if not rows:
            await respond(target, "در این صفحه پیامی برای بررسی نیست.")
        for msg in rows:
            await respond(target, ui.item_text(msg), reply_markup=ui.item_keyboard(msg.code, role))
        paging = ui.paging_keyboard(page, len(rows) == ui.PAGE_SIZE)
        if paging:
            await respond(target, f"صفحه {page}", reply_markup=paging)

    @result.message(F.chat.type == "private")
    async def private(message: Message, event_update):
        actor = message.from_user.id
        text = message.text or ""
        # Reply-keyboard labels are commands, never submission text.
        text = ui.MENU_COMMANDS.get(text.strip(), text)
        parts = text.split(maxsplit=3)
        cmd = parts[0].split("@")[0].lower() if parts else ""
        try:
            if cmd in {"/start", "/rules"}:
                await respond(
                    message, policy(), reply_markup=ui.main_menu(await service.whoami(actor))
                )
            elif cmd == "/help":
                await respond(message, HELP, reply_markup=ui.main_menu(await service.whoami(actor)))
            elif cmd == "/send":
                await respond(message, SEND_GUIDE)
            elif cmd == "/accept":
                await service.accept(actor)
                await respond(
                    message,
                    "پذیرش ثبت شد. اکنون پیام متنی خود را ارسال کنید.",
                    reply_markup=ui.main_menu(await service.whoami(actor)),
                )
            elif cmd == "/mine":
                rows = await service.mine(actor)
                if not rows:
                    await respond(message, "هنوز پیامی ثبت نکرده‌اید.")
                for msg in rows:
                    await respond(
                        message,
                        f"کد پیگیری: {msg.code}\n"
                        f"وضعیت بررسی: {msg.review}\n"
                        f"وضعیت انتشار: {msg.publication}",
                        reply_markup=ui.withdraw_keyboard(msg.code),
                    )
            elif cmd == "/withdraw" and len(parts) == 2:
                await service.withdraw(actor, parts[1])
                await respond(message, "از انتشار منصرف شدید؛ سوابق نزد سرویس حفظ می‌شود.")
            elif cmd == "/queue":
                await show_queue(message, actor, int(parts[1]) if len(parts) == 2 else 1)
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
                await respond(message, ui.identity_text(identity))
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
                await respond(
                    message,
                    f"پیام دریافت شد. کد پیگیری: {code}\nوضعیت را از دکمه پیام‌های من ببینید.",
                    reply_markup=ui.main_menu(await service.whoami(actor)),
                )
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
        actor = query.from_user.id
        action, _, argument = (query.data or "").partition(":")
        # A trailing "!" marks the confirmed press of a two-step action.
        action, confirmed = (action[:-1], True) if action.endswith("!") else (action, False)
        try:
            if action == "cancel":
                await answer_callback(query, "لغو شد.")
            elif action == "queue":
                await show_queue(query.message, actor, int(argument))
                await answer_callback(query, f"صفحه {argument}")
            elif action == "withdraw":
                if not confirmed:
                    await query.message.answer(
                        f"انصراف از انتشار پیام {argument}؟ سوابق حفظ می‌شود.",
                        parse_mode=None,
                        reply_markup=ui.confirm_keyboard("withdraw", argument),
                    )
                    await answer_callback(query, "تأیید لازم است.")
                else:
                    await service.withdraw(actor, argument)
                    await answer_callback(query, "انصراف ثبت شد.", show_alert=True)
            elif action in ui.ACTION_PERMISSIONS:
                role = await service.whoami(actor)
                if not ui.allows(role, action):
                    await answer_callback(query, "اجازه این عملیات را ندارید.", show_alert=True)
                elif action == "reject" and not confirmed:
                    await query.message.answer(
                        f"رد پیام {argument}؟ این تصمیم به فرستنده اطلاع داده می‌شود.",
                        parse_mode=None,
                        reply_markup=ui.confirm_keyboard("reject", argument),
                    )
                    await answer_callback(query, "تأیید لازم است.")
                elif action == "publish":
                    await service.enqueue(actor, argument)
                    await answer_callback(query, "در صف انتشار قرار گرفت.")
                elif action == "identity":
                    identity = await service.identity(actor, argument, ui.BUTTON_REASON)
                    await respond(query.message, ui.identity_text(identity))
                    await answer_callback(query, "هویت فرستنده ارسال شد.")
                elif action == "history":
                    rows = await service.history(actor, argument)
                    await respond(query.message, "\n".join(rows) or "خالی")
                    await answer_callback(query, "تاریخچه ارسال شد.")
                else:
                    await service.decide(
                        actor,
                        argument,
                        {
                            "approve": "APPROVED",
                            "reject": "REJECTED",
                            "escalate": "ESCALATED",
                            "needs_edit": "NEEDS_EDIT",
                        }[action],
                        ui.BUTTON_REASON,
                    )
                    await answer_callback(query, "تصمیم ثبت شد.")
            else:
                raise DomainError("دستور نامعتبر است.")
        except (DomainError, ValueError) as exc:
            await answer_callback(
                query,
                str(exc) if isinstance(exc, DomainError) else "دستور نامعتبر است.",
                show_alert=True,
            )

    return result
