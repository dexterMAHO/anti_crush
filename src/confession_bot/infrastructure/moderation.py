from typing import Literal

import httpx
from pydantic import BaseModel, Field

from confession_bot.domain.policies import SENSITIVE


class Verdict(BaseModel):
    categories: list[
        Literal[
            "PROFANITY",
            "HARASSMENT",
            "THREAT",
            "HATE",
            "SEXUAL_CONTENT",
            "PERSONAL_INFORMATION",
            "SPAM",
            "SCAM",
            "IMPERSONATION",
            "SENSITIVE_CONTENT",
            "OFF_TOPIC",
            "UNKNOWN",
        ]
    ] = Field(max_length=12)
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    reason: str = Field(max_length=1000)
    requires_human_review: bool = True


class HttpModeration:
    """Provider-neutral endpoint accepting text/model and returning a Verdict JSON."""

    def __init__(self, settings):
        self.settings = settings

    async def evaluate(self, text):
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                self.settings.ai_url,
                headers={"Authorization": f"Bearer {self.settings.ai_api_key.get_secret_value()}"},
                json={"text": SENSITIVE.sub("[REDACTED]", text), "model": self.settings.ai_model},
            )
            response.raise_for_status()
            result = Verdict.model_validate(response.json()).model_dump()
            return {
                **result,
                "source": "ai",
                "version": self.settings.ai_model,
                "status": "SUCCESS",
            }
