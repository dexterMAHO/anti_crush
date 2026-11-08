from sqlalchemy import select

from confession_bot.infrastructure.database import Update


class Inbox:
    """Archive every delivered update before Telegram is allowed to acknowledge it."""

    def __init__(self, sessions):
        self.sessions = sessions

    async def persist(self, events):
        async with self.sessions.begin() as session:
            for event in events:
                if not await session.get(Update, event.update_id):
                    session.add(
                        Update(
                            update_id=event.update_id,
                            payload=event.model_dump(mode="json", exclude_none=True, by_alias=True),
                        )
                    )

    async def pending(self):
        async with self.sessions() as session:
            return list(
                (
                    await session.scalars(
                        select(Update)
                        .where(Update.processed.is_(False))
                        .order_by(Update.update_id)
                        .limit(100)
                    )
                ).all()
            )

    async def complete(self, update_id):
        async with self.sessions.begin() as session:
            row = await session.get(Update, update_id)
            row.processed = True
