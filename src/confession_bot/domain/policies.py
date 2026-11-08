import re
import unicodedata
from datetime import UTC, datetime
from enum import StrEnum


class DomainError(Exception):
    pass


class Role(StrEnum):
    OWNER = "OWNER"
    SENIOR_ADMIN = "SENIOR_ADMIN"
    MODERATOR = "MODERATOR"
    PUBLISHER = "PUBLISHER"


PERMISSIONS = {
    "review": {Role.OWNER, Role.SENIOR_ADMIN, Role.MODERATOR},
    "sensitive": {Role.OWNER, Role.SENIOR_ADMIN},
    "publish": {Role.OWNER, Role.PUBLISHER},
    "identity": {Role.OWNER},
    "restrict": {Role.OWNER, Role.SENIOR_ADMIN},
    "roles": {Role.OWNER},
    "history": {Role.OWNER, Role.SENIOR_ADMIN, Role.MODERATOR},
}


def authorize(role: str | None, action: str):
    if role not in PERMISSIONS[action]:
        raise DomainError("اجازه انجام این عملیات را ندارید.")


def now():
    return datetime.now(UTC)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(
        str.maketrans("يك٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "یک01234567890123456789")
    )
    text = "".join(c for c in text if unicodedata.category(c) not in {"Cf", "Mn"})
    text = text.replace("ـ", "")
    text = re.sub(r"([^\W\d_])\1{2,}", r"\1\1", text)
    return " ".join(text.lower().split())


SENSITIVE = re.compile(
    r"(?:\+?\d[\d\s().-]{7,}\d)|(?:https?://\S+|www\.\S+|t\.me/\S+)"
    r"|(?:[\w.+-]+@[\w.-]+\.[a-z]{2,})|(?:@\w{3,})"
)


def screen(text: str) -> dict:
    categories = []
    if SENSITIVE.search(text):
        categories.append("PERSONAL_INFORMATION")
    if any(word in text for word in ("میکشمت", "می‌کشمت", "می کشمت", "خواهم کشت", "kill you")):
        categories.append("THREAT")
    if any(word in text for word in ("احمق", "بی شعور", "بیشعور", "کثافت", "fuck", "bishoor")):
        categories.append("HARASSMENT")
    risk = "CRITICAL" if "THREAT" in categories else "HIGH" if categories else "LOW"
    return {
        "categories": categories,
        "risk_level": risk,
        "reason": "بررسی قواعد پایه",
        "source": "rules",
        "version": "1",
        "status": "SUCCESS",
    }


def publication_text(code: str, text: str) -> str:
    return f"💌 پیام ناشناس #{code}\n\n{text}\n\n#ناشناس #آنتی_کراش"
