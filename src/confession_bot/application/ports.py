from typing import Protocol


class ModerationProvider(Protocol):
    async def evaluate(self, text: str) -> dict: ...


class Gateway(Protocol):
    async def publish(self, text: str) -> int: ...
    async def notify(self, telegram_id: int, text: str) -> None: ...


class DefiniteFailure(Exception):
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after


class UncertainFailure(Exception):
    pass
