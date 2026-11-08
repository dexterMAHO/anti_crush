from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter

from confession_bot.application.ports import DefiniteFailure


class TelegramGateway:
    def __init__(self, bot, channel_id):
        self.bot, self.channel_id = bot, channel_id

    async def publish(self, text):
        try:
            result = await self.bot.send_message(
                self.channel_id, text, parse_mode=None, protect_content=True
            )
            return result.message_id
        except TelegramRetryAfter as exc:
            raise DefiniteFailure(exc.retry_after) from None
        except (TelegramBadRequest, TelegramForbiddenError):
            raise DefiniteFailure(300) from None

    async def notify(self, telegram_id, text):
        await self.bot.send_message(telegram_id, text, parse_mode=None)
