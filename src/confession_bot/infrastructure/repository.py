from sqlalchemy import select

from confession_bot.infrastructure.database import Admin, Audit, Submission, User


class Repository:
    def __init__(self, session):
        self.session = session

    async def get(self, model, **filters):
        return await self.session.scalar(select(model).filter_by(**filters).with_for_update())

    async def list(self, model, limit=30, **filters):
        return list(
            (
                await self.session.scalars(
                    select(model)
                    .filter_by(**filters)
                    .order_by(model.created_at.desc())
                    .limit(limit)
                )
            ).all()
        )

    def add(self, obj):
        self.session.add(obj)
        return obj

    async def flush(self):
        await self.session.flush()

    async def user(self, telegram_id):
        user = await self.get(User, telegram_id=telegram_id)
        if user is None:
            user = self.add(User(telegram_id=telegram_id))
            await self.flush()
        return user

    async def role(self, telegram_id):
        admin = await self.get(Admin, telegram_id=telegram_id)
        return admin.role if admin else None

    async def submission(self, code):
        return await self.get(Submission, code=code)

    def audit(self, actor, action, target=None, **details):
        self.add(Audit(actor=actor, action=action, target=target, details=details))
