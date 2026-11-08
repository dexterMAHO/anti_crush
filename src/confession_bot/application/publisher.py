from datetime import timedelta

from sqlalchemy import select, update

from confession_bot.application.ports import DefiniteFailure
from confession_bot.domain.policies import now, publication_text
from confession_bot.infrastructure.database import (
    Audit,
    Notification,
    Publication,
    Submission,
    User,
)


class Publisher:
    def __init__(self, sessions, gateway, settings):
        self.sessions, self.gateway, self.settings = sessions, gateway, settings

    async def recover(self):
        # Only called while holding the singleton process lock.
        async with self.sessions.begin() as session:
            await session.execute(
                update(Submission)
                .where(Submission.publication == "PUBLISHING")
                .values(publication="UNCERTAIN")
            )
            await session.execute(
                update(Publication)
                .where(Publication.status == "PUBLISHING")
                .values(status="UNCERTAIN", error="ProcessInterrupted")
            )

    async def once(self):
        async with self.sessions.begin() as session:
            msg = await session.scalar(
                select(Submission)
                .where(
                    Submission.review == "APPROVED",
                    Submission.publication.in_(["QUEUED", "FAILED"]),
                    Submission.attempts < self.settings.publication_max_attempts,
                    (Submission.retry_at.is_(None) | (Submission.retry_at <= now())),
                )
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if not msg:
                return False
            msg.publication = "PUBLISHING"
            msg.attempts += 1
            attempt = Publication(submission_id=msg.id)
            session.add(attempt)
            await session.flush()
            msg_id, attempt_id = msg.id, attempt.id
            text = publication_text(msg.code, msg.original_text)
        # Commit the claim BEFORE sending. Ambiguous failures never auto-retry.
        status, channel_id, error, retry_at = "PUBLISHED", None, None, None
        try:
            channel_id = await self.gateway.publish(text)
        except DefiniteFailure as exc:
            status, error = "FAILED", type(exc).__name__
            retry_at = now() + timedelta(seconds=exc.retry_after)
        except Exception as exc:
            status, error = "UNCERTAIN", type(exc).__name__
        async with self.sessions.begin() as session:
            msg = await session.get(Submission, msg_id, with_for_update=True)
            attempt = await session.get(Publication, attempt_id)
            msg.publication, msg.channel_message_id, msg.retry_at = status, channel_id, retry_at
            attempt.status, attempt.channel_message_id, attempt.error = status, channel_id, error
            session.add(
                Audit(
                    action="PUBLICATION_RESULT",
                    target=msg.code,
                    details={
                        "status": status,
                        "operation_id": attempt_id,
                    },
                )
            )
            if status == "PUBLISHED":
                user = await session.get(User, msg.user_id)
                channel = str(self.settings.channel_id)
                link = (
                    f"https://t.me/c/{channel[4:]}/{channel_id}"
                    if channel.startswith("-100")
                    else ""
                )
                session.add(
                    Notification(
                        telegram_id=user.telegram_id, text=f"پیام {msg.code} منتشر شد.\n{link}"
                    )
                )
        return True

    async def notify_once(self):
        async with self.sessions.begin() as session:
            note = await session.scalar(
                select(Notification)
                .where(
                    Notification.sent.is_(False),
                    Notification.attempts < 3,
                )
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if not note:
                return
            note.attempts += 1
            try:
                await self.gateway.notify(note.telegram_id, note.text)
                note.sent = True
            except Exception:
                pass  # Failure is recorded by attempts; never undo publication.
