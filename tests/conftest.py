import os

import pytest
import pytest_asyncio

from confession_bot.application.service import Service
from confession_bot.config import Settings
from confession_bot.infrastructure.database import Base, database


@pytest.fixture
def settings():
    return Settings(
        _env_file=None,
        bot_token="123456:fake-token",
        channel_id=-1001234567890,
        owner_telegram_id=1,
        database_url="sqlite+aiosqlite://",
        message_cooldown_seconds=0,
    )


@pytest_asyncio.fixture
async def app(settings):
    url = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite://")
    engine, sessions = database(url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    service = Service(sessions, settings)
    await service.bootstrap()
    yield service, sessions
    await engine.dispose()
