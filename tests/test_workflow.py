import pytest
from sqlalchemy import select

from confession_bot.application.ports import DefiniteFailure
from confession_bot.application.publisher import Publisher
from confession_bot.domain.policies import DomainError, normalize, publication_text, screen
from confession_bot.infrastructure.database import Audit, Moderation, Submission


class Gateway:
    def __init__(self, failure=None):
        self.sent = []
        self.failure = failure

    async def publish(self, text):
        self.sent.append(text)
        if self.failure:
            raise self.failure
        return 42

    async def notify(self, actor, text):
        pass


async def submit(service, text="این یک پیام آزمایشی است", update=100):
    await service.accept(10)
    code = await service.submit(10, text, update, update, {"username": "private_name"})
    await service.moderate_one()
    return code


def test_normalization_and_sensitive_information():
    assert normalize("  يك ۱۲٣\u200b  ") == "یک 123"
    assert screen(normalize("شماره ۰۹۱۲۱۲۳۴۵۶۷"))["risk_level"] == "HIGH"
    assert screen(normalize("من می‌کشمت"))["risk_level"] == "CRITICAL"
    assert "<b>hi</b>" in publication_text("ABC", "<b>hi</b>")


async def test_policy_and_duplicates(app):
    service, _ = app
    with pytest.raises(DomainError):
        await service.submit(10, "پیام آزمایشی", 1, 1)
    code = await submit(service)
    assert await service.submit(10, "متن متفاوت", 100, 100) == code
    with pytest.raises(DomainError):
        await service.submit(10, "این یک پیام آزمایشی است", 101, 101)


async def test_happy_path_and_public_identity(app, settings):
    service, sessions = app
    code = await submit(service)
    await service.decide(1, code, "APPROVED", "بررسی شد")
    await service.enqueue(1, code)
    gateway = Gateway()
    publisher = Publisher(sessions, gateway, settings)
    assert await publisher.once()
    assert not await publisher.once()
    assert len(gateway.sent) == 1
    assert "private_name" not in gateway.sent[0]
    assert (await service.mine(10))[0].channel_message_id == 42


async def test_permissions_and_stale_decision(app):
    service, _ = app
    code = await submit(service)
    with pytest.raises(DomainError):
        await service.decide(10, code, "APPROVED", "forged")
    await service.set_role(1, 20, "MODERATOR")
    with pytest.raises(DomainError):
        await service.identity(20, code, "reason")
    with pytest.raises(DomainError):
        await service.enqueue(20, code)
    await service.decide(20, code, "APPROVED", "ok")
    with pytest.raises(DomainError):
        await service.decide(20, code, "REJECTED", "stale")
    assert (await service.identity(1, code, "investigation"))["telegram_id"] == 10


async def test_sensitive_needs_senior(app):
    service, _ = app
    code = await submit(service, "تماس با من 09121234567")
    await service.set_role(1, 20, "MODERATOR")
    with pytest.raises(DomainError):
        await service.decide(20, code, "APPROVED", "ok")
    await service.decide(1, code, "APPROVED", "بررسی ویژه انجام شد")


async def test_withdraw_keeps_content_and_ownership(app, settings):
    service, sessions = app
    code = await submit(service)
    with pytest.raises(DomainError):
        await service.withdraw(11, code)
    await service.decide(1, code, "APPROVED", "ok")
    await service.enqueue(1, code)
    await service.withdraw(10, code)
    assert not await Publisher(sessions, Gateway(), settings).once()
    assert (await service.mine(10))[0].original_text == "این یک پیام آزمایشی است"


async def test_ambiguous_timeout_never_retried(app, settings):
    service, sessions = app
    code = await submit(service)
    await service.decide(1, code, "APPROVED", "ok")
    await service.enqueue(1, code)
    gateway = Gateway(TimeoutError())
    publisher = Publisher(sessions, gateway, settings)
    await publisher.once()
    assert not await publisher.once()
    assert (await service.mine(10))[0].publication == "UNCERTAIN"
    with pytest.raises(DomainError):
        await service.enqueue(1, code)
    await service.reconcile(1, code, 42, "وجود پیام در کانال تأیید شد")
    assert (await service.mine(10))[0].publication == "PUBLISHED"


async def test_definite_failure_bounded(app, settings):
    service, sessions = app
    code = await submit(service)
    await service.decide(1, code, "APPROVED", "ok")
    await service.enqueue(1, code)
    gateway = Gateway(DefiniteFailure(0))
    publisher = Publisher(sessions, gateway, settings)
    for _ in range(settings.publication_max_attempts):
        assert await publisher.once()
    assert not await publisher.once()
    assert len(gateway.sent) == settings.publication_max_attempts


async def test_ai_failure_preserved(app):
    service, sessions = app

    class Broken:
        async def evaluate(self, text):
            raise TimeoutError("secret contents")

    service.provider = Broken()
    code = await submit(service)
    msg = (await service.mine(10))[0]
    assert msg.review == "ESCALATED"
    async with sessions() as session:
        results = list((await session.scalars(select(Moderation))).all())
        assert len(results) == 2
        assert results[1].result["status"] == "FAILED"
        assert "secret contents" not in str(results[1].result)
        assert await session.scalar(select(Audit).where(Audit.target == code))


async def test_restriction_and_rate_limit(app):
    service, _ = app
    code = await submit(service)
    await service.restrict(1, code, 0, "spam")
    with pytest.raises(DomainError):
        await service.submit(10, "یک پیام دیگر", 101, 101)
    await service.restrict(1, code, -1, "رفع شد")
    await service.submit(10, "یک پیام دیگر", 101, 101)
    await service.submit(10, "یک پیام سوم", 102, 102)
    with pytest.raises(DomainError):
        await service.submit(10, "یک پیام چهارم", 103, 103)


async def test_crash_recovery(app, settings):
    service, sessions = app
    code = await submit(service)
    async with sessions.begin() as session:
        msg = await session.scalar(select(Submission).where(Submission.code == code))
        msg.publication = "PUBLISHING"
    await Publisher(sessions, Gateway(), settings).recover()
    assert (await service.mine(10))[0].publication == "UNCERTAIN"
