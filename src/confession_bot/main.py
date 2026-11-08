import asyncio
import contextlib
import logging
import os
import signal
import time
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import Update as TelegramUpdate
from sqlalchemy import text

from confession_bot.application.publisher import Publisher
from confession_bot.application.service import Service
from confession_bot.config import Settings
from confession_bot.infrastructure.database import database
from confession_bot.infrastructure.inbox import Inbox
from confession_bot.infrastructure.moderation import HttpModeration
from confession_bot.infrastructure.telegram import TelegramGateway
from confession_bot.presentation.telegram import router

log = logging.getLogger("confession_bot")
HEARTBEAT = Path("/tmp/confession-bot.heartbeat")


async def workers(service, publisher):
    while True:
        try:
            await service.moderate_one()
            await publisher.once()
            await publisher.notify_once()
        except Exception as exc:
            log.error("Worker failed: %s", type(exc).__name__)
        await asyncio.sleep(1)


async def run():
    settings = Settings()
    task = asyncio.current_task()
    asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, task.cancel)
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(message)s")
    # Do not emit HTTP bodies, tokens, user IDs, or raw exception strings.
    for name in ("httpx", "httpcore", "aiogram"):
        logging.getLogger(name).setLevel(logging.CRITICAL)
    engine, sessions = database(settings.database_url)
    bot = Bot(settings.bot_token.get_secret_value(), session=AiohttpSession(timeout=35))
    worker = None
    try:
        async with engine.connect() as lock:
            if engine.dialect.name != "postgresql":
                raise RuntimeError("Production requires PostgreSQL")
            locked = await lock.scalar(text("SELECT pg_try_advisory_lock(738219047)"))
            if not locked:
                raise RuntimeError("Another bot process is already running")
            await lock.commit()
            service = Service(
                sessions,
                settings,
                HttpModeration(settings) if settings.ai_moderation_enabled else None,
            )
            await service.bootstrap()
            publisher = Publisher(sessions, TelegramGateway(bot, settings.channel_id), settings)
            await publisher.recover()
            dispatcher = Dispatcher()
            dispatcher.include_router(router(service, settings))
            worker = asyncio.create_task(workers(service, publisher))
            await bot.delete_webhook(drop_pending_updates=False)
            offset = None
            inbox = Inbox(sessions)
            while True:
                await lock.execute(text("SELECT 1"))
                await lock.commit()
                # Persist first, then process. Pending updates survive restart.
                pending = await inbox.pending()
                if not pending:
                    updates = await bot.get_updates(offset=offset, timeout=25, allowed_updates=[])
                    await inbox.persist(updates)
                    if updates:
                        offset = updates[-1].update_id + 1
                    HEARTBEAT.write_text(str(time.time()))
                    continue
                for saved in pending:
                    try:
                        await dispatcher.feed_update(
                            bot, TelegramUpdate.model_validate(saved.payload, context={"bot": bot})
                        )
                    except Exception as exc:
                        log.error("Update processing failed: %s", type(exc).__name__)
                        # Durable inbox remains pending; no data silently discarded.
                        await asyncio.sleep(3)
                        break
                    await inbox.complete(saved.update_id)
                    HEARTBEAT.write_text(str(time.time()))
    finally:
        if worker:
            worker.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await worker
        await bot.session.close()
        await engine.dispose()
        HEARTBEAT.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    except Exception as exc:
        logging.getLogger("confession_bot").critical("Stopped: %s", type(exc).__name__)
        os._exit(1)
