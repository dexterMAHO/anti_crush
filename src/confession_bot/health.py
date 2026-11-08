import asyncio
import time

from sqlalchemy import text

from confession_bot.config import Settings
from confession_bot.infrastructure.database import database
from confession_bot.main import HEARTBEAT


async def check():
    assert time.time() - float(HEARTBEAT.read_text()) < 120
    engine, _ = database(Settings().database_url)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check())
