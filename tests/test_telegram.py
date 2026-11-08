from datetime import UTC, datetime

from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.methods import AnswerCallbackQuery, SendMessage
from aiogram.types import Message, Update

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
