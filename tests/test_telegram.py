from datetime import UTC, datetime

from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.methods import AnswerCallbackQuery, SendMessage
from aiogram.types import Message, Update

from confession_bot.presentation import ui
from confession_bot.presentation.telegram import router


class FakeSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.calls = []

    async def close(self):
        pass

    async def stream_content(self, *args, **kwargs):
        yield b""

    async def make_request(self, bot, method, timeout=None):
        self.calls.append(method)
        if isinstance(method, AnswerCallbackQuery):
            return True
        assert isinstance(method, SendMessage)
        return Message(
            message_id=len(self.calls),
            date=datetime.now(UTC),
            chat={"id": method.chat_id, "type": "private"},
            text=method.text,
        )


async def test_bot_commands_and_forged_callback(app, settings):
    service, _ = app
    transport = FakeSession()
    bot = Bot(settings.bot_token.get_secret_value(), session=transport)
    dispatcher = Dispatcher()
    dispatcher.include_router(router(service, settings))

    async def send(actor, content, identifier):
        await dispatcher.feed_update(
            bot,
            Update.model_validate(
                {
                    "update_id": identifier,
                    "message": {
                        "message_id": identifier,
                        "date": 1700000000,
                        "chat": {"id": actor, "type": "private"},
                        "from": {"id": actor, "is_bot": False, "first_name": "Test"},
                        "text": content,
                    },
                }
            ),
        )

    await send(10, "/start", 1)
    assert "ارائه‌دهنده" in transport.calls[-1].text
    await send(10, "/accept", 2)
    await send(10, "این پیام از رابط تلگرام ثبت شد", 3)
    code = (await service.mine(10))[0].code
    await service.moderate_one()
    await dispatcher.feed_update(
        bot,
        Update.model_validate(
            {
                "update_id": 4,
                "callback_query": {
                    "id": "callback-id",
                    "chat_instance": "chat",
                    "from": {"id": 10, "is_bot": False, "first_name": "Test"},
                    "data": f"approve:{code}",
                    "message": {
                        "message_id": 3,
                        "date": 1700000000,
                        "chat": {"id": 10, "type": "private"},
                        "text": "forged",
                    },
                },
            }
        ),
    )
    assert (await service.mine(10))[0].review == "PENDING_REVIEW"
    await send(1, f"/approve {code} بررسی شد", 5)
    await send(1, f"/publish {code}", 6)
    assert (await service.mine(10))[0].publication == "QUEUED"
    await bot.session.close()


async def feed(dispatcher, bot, actor, data, identifier, message_id=1):
    await dispatcher.feed_update(
        bot,
        Update.model_validate(
            {
                "update_id": identifier,
                "callback_query": {
                    "id": f"callback-{identifier}",
                    "chat_instance": "chat",
                    "from": {"id": actor, "is_bot": False, "first_name": "Admin"},
                    "data": data,
                    "message": {
                        "message_id": message_id,
                        "date": 1700000000,
                        "chat": {"id": actor, "type": "private"},
                        "text": "item",
                    },
                },
            }
        ),
    )


async def test_button_interface_menu_identity_and_confirmation(app, settings):
    service, _ = app
    transport = FakeSession()
    bot = Bot(settings.bot_token.get_secret_value(), session=transport)
    dispatcher = Dispatcher()
    dispatcher.include_router(router(service, settings))

    async def send(actor, content, identifier):
        await dispatcher.feed_update(
            bot,
            Update.model_validate(
                {
                    "update_id": identifier,
                    "message": {
                        "message_id": identifier,
                        "date": 1700000000,
                        "chat": {"id": actor, "type": "private"},
                        "from": {"id": actor, "is_bot": False, "first_name": "Test"},
                        "text": content,
                    },
                }
            ),
        )

    # The owner sees the moderation button; a plain user does not.
    await send(1, "/start", 1)
    assert ui.QUEUE in str(transport.calls[-1].reply_markup)
    await send(10, "/start", 2)
    assert ui.QUEUE not in str(transport.calls[-1].reply_markup)

    # Reply-keyboard labels act as commands instead of becoming submissions.
    await send(10, ui.RULES, 3)
    assert "ارائه‌دهنده" in transport.calls[-1].text
    await send(10, ui.SEND, 4)
    assert "متن پیام خود را" in transport.calls[-1].text
    assert await service.mine(10) == []

    await send(10, "/accept", 5)
    await send(10, "متن پیام آزمایشی برای رابط دکمه‌ای", 6)
    code = (await service.mine(10))[0].code
    await service.moderate_one()

    # Queue items carry item actions for the owner and a page footer.
    await send(1, ui.QUEUE, 7)
    item = next(call for call in transport.calls if "سطح خطر" in (call.text or ""))
    assert code in item.text
    labels = str(item.reply_markup)
    assert ui.ACTION_LABELS["identity"] in labels and ui.ACTION_LABELS["publish"] in labels
    assert "متن پیام آزمایشی" in item.text

    # Identity: the owner gets the sender ID next to the message text, audited.
    await feed(dispatcher, bot, 1, f"identity:{code}", 8)
    identity = transport.calls[-2].text
    assert "شناسه عددی فرستنده: 10" in identity and "متن پیام آزمایشی" in identity
    assert "ثبت شد" in identity
    assert any("IDENTITY_ACCESS" in row for row in await service.history(1, code))

    # A moderator may decide but must not reach identity.
    await service.set_role(1, 20, "MODERATOR")
    await feed(dispatcher, bot, 20, f"identity:{code}", 9)
    assert transport.calls[-1].show_alert is True
    assert (await service.identity(1, code, "check"))["text"]

    # Rejection is confirmed in two steps.
    await feed(dispatcher, bot, 20, f"reject:{code}", 10)
    assert "رد پیام" in transport.calls[-2].text
    assert (await service.mine(10))[0].review == "PENDING_REVIEW"
    await feed(dispatcher, bot, 20, f"reject!:{code}", 11)
    assert (await service.mine(10))[0].review == "REJECTED"
    await bot.session.close()


async def test_withdraw_button_requires_confirmation(app, settings):
    service, _ = app
    transport = FakeSession()
    bot = Bot(settings.bot_token.get_secret_value(), session=transport)
    dispatcher = Dispatcher()
    dispatcher.include_router(router(service, settings))
    await service.accept(10)
    code = await service.submit(10, "پیام قابل انصراف از طریق دکمه", 100, 100)

    await feed(dispatcher, bot, 10, f"withdraw:{code}", 101)
    assert "انصراف از انتشار پیام" in transport.calls[-2].text
    assert (await service.mine(10))[0].review == "RECEIVED"
    await feed(dispatcher, bot, 10, f"withdraw!:{code}", 102)
    assert (await service.mine(10))[0].review == "WITHDRAWN"
    await bot.session.close()
