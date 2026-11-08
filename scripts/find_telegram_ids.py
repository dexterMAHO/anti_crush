#!/usr/bin/env python3
"""Discover setup IDs without requiring database or complete bot settings."""

import argparse
import getpass
import json
import os
import secrets
import sys
import time
from pathlib import Path

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


class SetupError(Exception):
    pass


def api(client: httpx.Client, token: str, method: str, **data):
    response = client.post(f"https://api.telegram.org/bot{token}/{method}", json=data)
    if response.status_code == 401:
        raise SetupError("توکن نامعتبر است؛ توکن BotFather را وارد کنید.")
    if response.status_code == 409:
        raise SetupError("ربات یا دریافت‌کننده دیگری فعال است؛ ابتدا آن را متوقف کنید.")
    if response.status_code == 429:
        raise SetupError("محدودیت درخواست تلگرام؛ کمی صبر کنید و دوباره اجرا کنید.")
    if response.is_error:
        raise SetupError(f"خطای ارتباط با تلگرام؛ کد HTTP: {response.status_code}")
    body = response.json()
    if not body.get("ok"):
        raise SetupError("تلگرام درخواست را نپذیرفت.")
    return body["result"]


def identify(update: dict, owner_marker: str, channel_marker: str) -> dict[str, int]:
    """Only accept fresh, distinct markers; channel authors may be anonymous."""
    found = {}
    message = update.get("message") or {}
    user = message.get("from") or {}
    if (
        message.get("chat", {}).get("type") == "private"
        and message.get("text", "").strip() == owner_marker
        and user.get("id")
        and not user.get("is_bot", True)
        and not message.get("forward_origin")
    ):
        found["OWNER_TELEGRAM_ID"] = user["id"]
    post = update.get("channel_post") or {}
    if (
        post.get("chat", {}).get("type") == "channel"
        and post.get("text", "").strip() == channel_marker
        and not post.get("forward_origin")
    ):
        found["CHANNEL_ID"] = post["chat"]["id"]
    return found


def archive_updates(path: Path, updates: list[dict]) -> None:
    """Flush received data before advancing the Telegram polling offset."""
    if not updates:
        return
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(descriptor, "a", encoding="utf-8") as archive:
        os.fchmod(archive.fileno(), 0o600)
        for update in updates:
            archive.write(json.dumps(update, ensure_ascii=False) + "\n")
        archive.flush()
        os.fsync(archive.fileno())


def discover(client: httpx.Client, token: str, timeout: int, archive: Path) -> dict[str, int]:
    bot = api(client, token, "getMe")
    if api(client, token, "getWebhookInfo").get("url"):
        raise SetupError(
            "این ربات Webhook فعال دارد. ابتدا دریافت Webhook را در سرویس فعلی متوقف "
            "و تنظیم آن را حذف کنید؛ اسکریپت خودکار آن را حذف نمی‌کند."
        )
    owner_marker = f"owner-{secrets.token_hex(6)}"
    channel_marker = f"channel-{secrets.token_hex(6)}"
    print(f"ربات: @{bot['username']}")
    print("از حسابی که می‌خواهید مالک ربات باشد، این متن را خصوصی برای ربات بفرستید:")
    print(owner_marker)
    print("\nربات را ادمین کانال مقصد با مجوز ارسال پیام کنید؛ سپس این متن را در کانال منتشر کنید:")
    print(channel_marker)
    print(f"\nتا {timeout} ثانیه منتظر می‌مانم. دریافت‌ها در {archive} نگهداری می‌شوند.")
    deadline = time.monotonic() + timeout
    found: dict[str, int] = {}
    offset = None
    while time.monotonic() < deadline and len(found) < 2:
        params = {
            "timeout": min(20, max(1, int(deadline - time.monotonic()))),
            "allowed_updates": [],
        }
        if offset is not None:
            params["offset"] = offset
        updates = api(client, token, "getUpdates", **params)
        archive_updates(archive, updates)
        for update in updates:
            for key, value in identify(update, owner_marker, channel_marker).items():
                if key not in found:
                    found[key] = value
                    print(f"پیدا شد: {key}={value}", flush=True)
        if updates:
            offset = max(event["update_id"] for event in updates) + 1
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="یافتن شناسه مالک و کانال تلگرام")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--timeout", type=int, default=300, help="زمان انتظار به ثانیه")
    parser.add_argument("--archive", type=Path, default=ROOT / ".local" / "id-discovery.jsonl")
    args = parser.parse_args()
    if args.timeout < 1:
        parser.error("--timeout باید مثبت باشد.")
    token = os.environ.get("BOT_TOKEN") or dotenv_values(args.env_file).get("BOT_TOKEN")
    if not token:
        token = getpass.getpass("توکن BotFather (ورودی پنهان): ").strip()
    if not token:
        print("توکن وارد نشده است.", file=sys.stderr)
        return 1
    print("پیش از ادامه، ربات اصلی را متوقف کنید: docker compose stop bot")
    print("این ابزار برای راه‌اندازی اولیه است؛ دریافت‌های آن به صف پردازش ربات منتقل نمی‌شوند.")
    try:
        with httpx.Client(timeout=35) as client:
            found = discover(client, token, args.timeout, args.archive)
    except SetupError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (httpx.HTTPError, OSError, ValueError):
        # Never print HTTP exceptions: request URLs contain the bot token.
        print("خطای شبکه، پاسخ نامعتبر یا مشکل ذخیره آرشیو؛ دوباره تلاش کنید.", file=sys.stderr)
        return 1
    print("\nمقادیر پیدا‌شده را در .env قرار دهید:")
    for key in ("OWNER_TELEGRAM_ID", "CHANNEL_ID"):
        if key in found:
            print(f"{key}={found[key]}")
    if len(found) < 2:
        print("زمان تمام شد؛ یکی از شناسه‌ها دریافت نشده است. مراحل بالا را بررسی کنید.")
        return 1
    print("فایل .env تغییر نکرده است. پس از تکمیل تنظیمات: docker compose up -d --build")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print("\nمتوقف شد.")
        sys.exit(130)
