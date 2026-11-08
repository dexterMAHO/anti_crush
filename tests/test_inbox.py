from aiogram.types import Update

from confession_bot.infrastructure.inbox import Inbox


async def test_inbox_retains_raw_data_and_replays_pending(app):
    _, sessions = app
    inbox = Inbox(sessions)
    event = Update.model_validate(
        {
            "update_id": 9,
            "message": {
                "message_id": 3,
                "date": 1700000000,
                "chat": {"id": 10, "type": "private"},
                "from": {"id": 10, "is_bot": False, "first_name": "User", "username": "saved"},
                "text": "original data before policy acceptance",
            },
        }
    )
    await inbox.persist([event])
    await inbox.persist([event])
    pending = await Inbox(sessions).pending()
    assert len(pending) == 1
    assert Update.model_validate(pending[0].payload).message.from_user.id == 10
    assert pending[0].payload["message"]["from"]["username"] == "saved"
    await inbox.complete(9)
    assert not await inbox.pending()
    from confession_bot.infrastructure.database import Update as StoredUpdate

    async with sessions() as session:
        row = await session.get(StoredUpdate, 9)
        assert row.payload["message"]["text"] == "original data before policy acceptance"
