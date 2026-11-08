import secrets
from datetime import UTC, timedelta

from confession_bot.domain.policies import (
    DomainError,
    Role,
    authorize,
    normalize,
    now,
    screen,
)
from confession_bot.infrastructure.database import (
    Admin,
    Audit,
    Moderation,
    Notification,
    Submission,
)
from confession_bot.infrastructure.repository import Repository


def aware(value):
    return value.replace(tzinfo=UTC) if value and value.tzinfo is None else value


class Service:
    def __init__(self, sessions, settings, provider=None):
        self.sessions, self.settings, self.provider = sessions, settings, provider

    async def bootstrap(self):
        async with self.sessions.begin() as session:
            repo = Repository(session)
            admin = await repo.get(Admin, telegram_id=self.settings.owner_telegram_id)
            if not admin:
                repo.add(Admin(telegram_id=self.settings.owner_telegram_id, role="OWNER"))

    async def accept(self, actor):
        async with self.sessions.begin() as session:
            repo = Repository(session)
            user = await repo.user(actor)
            user.policy, user.accepted_at = self.settings.policy_version, now()
            repo.audit(actor, "ACCEPT_POLICY", user.id, version=user.policy)

    async def submit(self, actor, text, update_id, message_id, profile=None):
        async with self.sessions.begin() as session:
            repo = Repository(session)
            user = await repo.user(actor)  # Row lock serializes per-user quota checks.
            existing = await repo.get(Submission, update_id=update_id)
            if existing:
                return existing.code
            if user.policy != self.settings.policy_version:
                raise DomainError("ابتدا /rules را بخوانید و با /accept بپذیرید.")
            if user.restricted and (
                user.restricted_until is None or aware(user.restricted_until) > now()
            ):
                raise DomainError("امکان ارسال پیام برای شما محدود شده است.")
            cleaned = normalize(text)
            if (
                not self.settings.min_message_length
                <= len(text.strip())
                <= (self.settings.max_message_length)
                or not cleaned
            ):
                raise DomainError("طول پیام خارج از محدوده مجاز است.")
            recent = await repo.list(
                Submission, limit=self.settings.rate_limit_daily + 1, user_id=user.id
            )
            day = [m for m in recent if aware(m.created_at) > now() - timedelta(days=1)]
            hour = [m for m in day if aware(m.created_at) > now() - timedelta(hours=1)]
            if (
                len(day) >= self.settings.rate_limit_daily
                or len(hour) >= self.settings.rate_limit_hourly
                or (
                    recent
                    and (now() - aware(recent[0].created_at)).total_seconds()
                    < self.settings.message_cooldown_seconds
                )
            ):
                raise DomainError("سقف ارسال پیام پر شده؛ لطفاً بعداً تلاش کنید.")
            if any(m.normalized_text == cleaned for m in day):
                raise DomainError("این پیام را قبلاً ارسال کرده‌اید.")
            user.profile = profile or user.profile
            msg = repo.add(
                Submission(
                    code=secrets.token_hex(6).upper(),
                    user_id=user.id,
                    original_text=text,
                    normalized_text=cleaned,
                    update_id=update_id,
                    message_id=message_id,
                    review="RECEIVED",
                )
            )
            await repo.flush()
            repo.audit(actor, "SUBMIT", msg.code)
            return msg.code

    async def moderate_one(self):
        # AI awaits occur under the row lock; bounded timeout, no public side effects.
        async with self.sessions.begin() as session:
            from sqlalchemy import select

            msg = await session.scalar(
                select(Submission)
                .where(Submission.review == "RECEIVED")
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if not msg:
                return False
            repo = Repository(session)
            msg.review = "SCREENING"
            results = [screen(msg.normalized_text)]
            if self.provider:
                try:
                    results.append(await self.provider.evaluate(msg.normalized_text))
                except Exception as exc:
                    results.append(
                        {
                            "source": "ai",
                            "status": "FAILED",
                            "risk_level": "HIGH",
                            "categories": ["UNKNOWN"],
                            "reason": type(exc).__name__,
                        }
                    )
            ranks = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            msg.risk = max((r["risk_level"] for r in results), key=ranks.index)
            categories = {c for result in results for c in result.get("categories", [])}
            if "THREAT" in categories:
                msg.risk = "CRITICAL"
            elif "PERSONAL_INFORMATION" in categories and ranks.index(msg.risk) < 2:
                msg.risk = "HIGH"
            msg.review = "ESCALATED" if msg.risk in {"HIGH", "CRITICAL"} else "PENDING_REVIEW"
            for result in results:
                repo.add(Moderation(submission_id=msg.id, result=result))
            repo.audit(None, "SCREENED", msg.code, risk=msg.risk)
            repo.add(
                Notification(
                    telegram_id=self.settings.owner_telegram_id,
                    text=f"پیام جدید {msg.code} — {msg.review}\n/queue",
                )
            )
            return True

    async def whoami(self, actor):
        async with self.sessions.begin() as session:
            return await Repository(session).role(actor)

    async def mine(self, actor):
        async with self.sessions.begin() as session:
            repo = Repository(session)
            user = await repo.user(actor)
            return await repo.list(Submission, user_id=user.id)

    async def withdraw(self, actor, code):
        async with self.sessions.begin() as session:
            repo = Repository(session)
            user = await repo.user(actor)
            msg = await repo.submission(code)
            if not msg or msg.user_id != user.id:
                raise DomainError("پیام پیدا نشد.")
            if msg.publication not in {"NOT_QUEUED", "QUEUED", "FAILED"}:
                raise DomainError("در این مرحله انصراف ممکن نیست.")
            msg.review, msg.publication = "WITHDRAWN", "NOT_QUEUED"
            repo.audit(actor, "WITHDRAW", code)

    async def queue(self, actor, page=1):
        if not 1 <= page <= 100000:
            raise DomainError("شماره صفحه نامعتبر است.")
        async with self.sessions.begin() as session:
            repo = Repository(session)
            role = await repo.role(actor)
            if role not in set(Role):
                raise DomainError("دسترسی مدیریت ندارید.")
            from sqlalchemy import select

            states = (
                ["APPROVED"]
                if role == Role.PUBLISHER
                else ["PENDING_REVIEW", "ESCALATED", "NEEDS_EDIT", "APPROVED"]
            )
            return list(
                (
                    await session.scalars(
                        select(Submission)
                        .where(
                            Submission.review.in_(states),
                            Submission.publication.in_(["NOT_QUEUED", "FAILED", "UNCERTAIN"]),
                        )
                        .order_by(Submission.created_at)
                        .offset((page - 1) * 10)
                        .limit(10)
                    )
                ).all()
            )

    async def decide(self, actor, code, action, reason):
        if not reason.strip():
            raise DomainError("دلیل تصمیم الزامی است.")
        async with self.sessions.begin() as session:
            repo = Repository(session)
            role = await repo.role(actor)
            authorize(role, "review")
            msg = await repo.submission(code)
            if not msg or msg.review not in {"PENDING_REVIEW", "ESCALATED", "NEEDS_EDIT"}:
                raise DomainError("وضعیت پیام تغییر کرده یا پیام وجود ندارد.")
            if action == "APPROVED" and (
                msg.review == "ESCALATED" or msg.risk in {"HIGH", "CRITICAL"}
            ):
                authorize(role, "sensitive")
            if action not in {"APPROVED", "REJECTED", "ESCALATED", "NEEDS_EDIT"}:
                raise DomainError("تصمیم نامعتبر است.")
            msg.review = action
            repo.audit(actor, action, code, reason=reason)
            from confession_bot.infrastructure.database import User

            user = await repo.get(User, id=msg.user_id)
            repo.add(
                Notification(
                    telegram_id=user.telegram_id, text=f"وضعیت پیام {code}: {action}\n{reason}"
                )
            )

    async def enqueue(self, actor, code):
        async with self.sessions.begin() as session:
            repo = Repository(session)
            authorize(await repo.role(actor), "publish")
            msg = await repo.submission(code)
            if (
                not msg
                or msg.review != "APPROVED"
                or msg.publication not in {"NOT_QUEUED", "FAILED"}
            ):
                raise DomainError("پیام آماده انتشار نیست.")
            if msg.attempts >= self.settings.publication_max_attempts:
                raise DomainError("سقف تلاش انتشار تمام شده است.")
            msg.publication = "QUEUED"
            repo.audit(actor, "QUEUE_PUBLICATION", code)

    async def identity(self, actor, code, reason):
        if not reason.strip():
            raise DomainError("دلیل دسترسی الزامی است.")
        async with self.sessions.begin() as session:
            repo = Repository(session)
            authorize(await repo.role(actor), "identity")
            msg = await repo.submission(code)
            if not msg:
                raise DomainError("پیام پیدا نشد.")
            from confession_bot.infrastructure.database import User

            user = await repo.get(User, id=msg.user_id)
            repo.audit(actor, "IDENTITY_ACCESS", code, reason=reason)
            return {
                "code": msg.code,
                "text": msg.original_text,
                "telegram_id": user.telegram_id,
                "profile": user.profile,
            }

    async def set_role(self, actor, target, role):
        async with self.sessions.begin() as session:
            repo = Repository(session)
            authorize(await repo.role(actor), "roles")
            if target == self.settings.owner_telegram_id:
                raise DomainError("نقش مالک اصلی قابل تغییر نیست.")
            if role not in {"SENIOR_ADMIN", "MODERATOR", "PUBLISHER", "NONE"}:
                raise DomainError("نقش نامعتبر است.")
            admin = await repo.get(Admin, telegram_id=target)
            if admin:
                admin.role = role
            else:
                repo.add(Admin(telegram_id=target, role=role))
            repo.audit(actor, "SET_ROLE", str(target), role=role)

    async def restrict(self, actor, code, hours, reason):
        if not reason.strip() or not -1 <= hours <= 87600:
            raise DomainError("دلیل و مدت معتبر وارد کنید.")
        async with self.sessions.begin() as session:
            repo = Repository(session)
            authorize(await repo.role(actor), "restrict")
            msg = await repo.submission(code)
            if not msg:
                raise DomainError("پیام پیدا نشد.")
            from confession_bot.infrastructure.database import User

            user = await repo.get(User, id=msg.user_id)
            user.restricted = hours != -1
            user.restricted_until = now() + timedelta(hours=hours) if hours > 0 else None
            repo.audit(actor, "RESTRICT", code, hours=hours, reason=reason)

    async def history(self, actor, code):
        async with self.sessions.begin() as session:
            repo = Repository(session)
            authorize(await repo.role(actor), "history")
            rows = await repo.list(Audit, target=code)
            # Actor IDs and identity-access details are not exposed to moderators.
            return [
                f"{r.created_at}: {r.action}"
                + (
                    f" — {r.details.get('reason', '')}"
                    if r.action in {"APPROVED", "REJECTED", "ESCALATED", "NEEDS_EDIT", "RESTRICT"}
                    else ""
                )
                for r in rows
            ]

    async def reconcile(self, actor, code, message_id, reason):
        if not reason.strip() or message_id < 0:
            raise DomainError("شناسه پیام و دلیل معتبر لازم است.")
        async with self.sessions.begin() as session:
            repo = Repository(session)
            authorize(await repo.role(actor), "roles")
            msg = await repo.submission(code)
            if not msg or msg.publication != "UNCERTAIN":
                raise DomainError("پیام در وضعیت نامشخص نیست.")
            msg.publication = "PUBLISHED" if message_id else "FAILED"
            msg.channel_message_id = message_id or None
            repo.audit(actor, "RECONCILE", code, message_id=message_id, reason=reason)
            if message_id:
                from confession_bot.infrastructure.database import User

                user = await repo.get(User, id=msg.user_id)
                channel = str(self.settings.channel_id)
                link = (
                    f"https://t.me/c/{channel[4:]}/{message_id}"
                    if channel.startswith("-100")
                    else ""
                )
                repo.add(
                    Notification(
                        telegram_id=user.telegram_id,
                        text=f"انتشار پیام {code} توسط مدیر تأیید شد.\n{link}",
                    )
                )
