import uuid

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from confession_bot.domain.policies import now


class Base(DeclarativeBase):
    pass


class Record:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now)


class User(Record, Base):
    __tablename__ = "users"
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    profile: Mapped[dict] = mapped_column(JSON, default=dict)
    policy: Mapped[str | None] = mapped_column(String(100))
    accepted_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    restricted: Mapped[bool] = mapped_column(default=False)
    restricted_until: Mapped[object | None] = mapped_column(DateTime(timezone=True))


class Admin(Base):
    __tablename__ = "admins"
    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    role: Mapped[str] = mapped_column(String(30))


class Submission(Record, Base):
    __tablename__ = "submissions"
    code: Mapped[str] = mapped_column(String(24), unique=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    original_text: Mapped[str] = mapped_column(Text)
    normalized_text: Mapped[str] = mapped_column(Text)
    update_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    message_id: Mapped[int] = mapped_column(BigInteger)
    review: Mapped[str] = mapped_column(String(30), default="RECEIVED")
    publication: Mapped[str] = mapped_column(String(30), default="NOT_QUEUED")
    risk: Mapped[str] = mapped_column(String(20), default="LOW")
    channel_message_id: Mapped[int | None] = mapped_column(BigInteger)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    retry_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        Index("ix_user_created", "user_id", "created_at"),
        Index("ix_review_publication", "review", "publication"),
    )


class Moderation(Record, Base):
    __tablename__ = "moderation_results"
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), index=True)
    result: Mapped[dict] = mapped_column(JSON)


class Audit(Record, Base):
    __tablename__ = "audit_logs"
    actor: Mapped[int | None] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String(80))
    target: Mapped[str | None] = mapped_column(String(100), index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class Update(Base):
    __tablename__ = "telegram_updates"
    update_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)
    processed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now)


class Publication(Record, Base):
    __tablename__ = "publication_attempts"
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="PUBLISHING")
    error: Mapped[str | None] = mapped_column(String(100))
    channel_message_id: Mapped[int | None] = mapped_column(BigInteger)


class Notification(Record, Base):
    __tablename__ = "notifications"
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    text: Mapped[str] = mapped_column(Text)
    sent: Mapped[bool] = mapped_column(default=False)
    attempts: Mapped[int] = mapped_column(default=0)


def database(url):
    engine = create_async_engine(url, pool_pre_ping=True)
    return engine, async_sessionmaker(engine, expire_on_commit=False)
