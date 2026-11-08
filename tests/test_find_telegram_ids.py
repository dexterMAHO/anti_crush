import importlib.util
import json
from pathlib import Path

import httpx
import pytest

spec = importlib.util.spec_from_file_location(
    "find_telegram_ids", Path(__file__).resolve().parents[1] / "scripts/find_telegram_ids.py"
)
finder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(finder)


def test_distinguish_owner_and_anonymous_channel():
    message = {
        "chat": {"type": "private"},
        "from": {"id": 42, "is_bot": False},
        "text": "owner-secret",
    }
    assert finder.identify({"message": message}, "owner-secret", "channel-secret") == {
        "OWNER_TELEGRAM_ID": 42
    }
    message["text"] = "stale marker"
    assert not finder.identify({"message": message}, "owner-secret", "channel-secret")
    channel = {
        "chat": {"type": "channel", "id": -100123},
        "text": "channel-secret",
        "sender_chat": {"id": -100123},
    }
    assert finder.identify({"channel_post": channel}, "owner-secret", "channel-secret") == {
        "CHANNEL_ID": -100123
    }
    channel["text"] = "owner-secret"
    assert not finder.identify({"channel_post": channel}, "owner-secret", "channel-secret")


def test_archive_preserves_data_with_private_permissions(tmp_path):
    path = tmp_path / "archive.jsonl"
    finder.archive_updates(path, [{"update_id": 1, "text": "پیام"}])
    assert json.loads(path.read_text())["text"] == "پیام"
    assert path.stat().st_mode & 0o777 == 0o600


def test_active_webhook_is_not_deleted(tmp_path):
    calls = []

    def handler(request):
        calls.append(request.url.path.rsplit("/", 1)[-1])
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": {"username": "test"}
                if calls[-1] == "getMe"
                else {"url": "https://example.org"},
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(finder.SetupError, match="Webhook"):
            finder.discover(client, "fake", 1, tmp_path / "archive.jsonl")
    assert calls == ["getMe", "getWebhookInfo"]


def test_conflict_error_does_not_expose_token():
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(409))) as client:
        with pytest.raises(finder.SetupError) as error:
            finder.api(client, "private-token", "getUpdates")
    assert "private-token" not in str(error.value)


def test_discovery_archives_before_advancing_offset(tmp_path, monkeypatch):
    markers = iter(["owner", "channel"])
    monkeypatch.setattr(finder.secrets, "token_hex", lambda size: next(markers))
    archive = tmp_path / "updates.jsonl"
    polls = []

    def handler(request):
        method = request.url.path.rsplit("/", 1)[-1]
        if method == "getMe":
            result = {"username": "test"}
        elif method == "getWebhookInfo":
            result = {"url": ""}
        else:
            params = json.loads(request.content)
            polls.append(params)
            if len(polls) == 1:
                result = [{"update_id": 10, "message": {"text": "old unrelated message"}}]
            else:
                assert params["offset"] == 11
                assert json.loads(archive.read_text())["update_id"] == 10
                result = [
                    {
                        "update_id": 11,
                        "message": {
                            "chat": {"type": "private"},
                            "from": {"id": 42, "is_bot": False},
                            "text": "owner-owner",
                        },
                    },
                    {
                        "update_id": 12,
                        "channel_post": {
                            "chat": {"type": "channel", "id": -100123},
                            "text": "channel-channel",
                        },
                    },
                ]
        return httpx.Response(200, json={"ok": True, "result": result})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert finder.discover(client, "fake", 10, archive) == {
            "OWNER_TELEGRAM_ID": 42,
            "CHANNEL_ID": -100123,
        }
    assert len(archive.read_text().splitlines()) == 3
