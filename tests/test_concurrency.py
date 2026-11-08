import asyncio
import os

import pytest
from test_workflow import Gateway, submit

from confession_bot.application.publisher import Publisher
from confession_bot.domain.policies import DomainError

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="Requires PostgreSQL row locking",
)


async def test_competing_decisions(app):
    service, _ = app
    code = await submit(service)
    results = await asyncio.gather(
        service.decide(1, code, "APPROVED", "first"),
        service.decide(1, code, "REJECTED", "second"),
        return_exceptions=True,
    )
    assert sum(isinstance(result, DomainError) for result in results) == 1


async def test_concurrent_quota(app):
    service, _ = app
    await service.accept(10)
    results = await asyncio.gather(
        *(service.submit(10, f"پیام آزمایشی شماره {i}", i, i) for i in range(5)),
        return_exceptions=True,
    )
    assert sum(isinstance(result, str) for result in results) == 3
    assert sum(isinstance(result, DomainError) for result in results) == 2


async def test_concurrent_publishers_send_once(app, settings):
    service, sessions = app
    code = await submit(service)
    await service.decide(1, code, "APPROVED", "ok")
    await service.enqueue(1, code)
    gateway = Gateway()
    first, second = Publisher(sessions, gateway, settings), Publisher(sessions, gateway, settings)
    results = await asyncio.gather(first.once(), second.once())
    assert sorted(results) == [False, True]
    assert len(gateway.sent) == 1
