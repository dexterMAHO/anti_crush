from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    bot_token: SecretStr
    channel_id: int
    owner_telegram_id: int = Field(gt=0)
    database_url: str
    policy_version: str = "provider-retention-v1"
    min_message_length: int = Field(default=5, ge=1)
    max_message_length: int = Field(default=2000, le=3000)
    rate_limit_hourly: int = Field(default=3, ge=1)
    rate_limit_daily: int = Field(default=10, ge=1)
    message_cooldown_seconds: int = Field(default=30, ge=0)
    ai_moderation_enabled: bool = False
    ai_url: str = ""
    ai_api_key: SecretStr = SecretStr("")
    ai_model: str = ""
    publication_max_attempts: int = Field(default=3, ge=1)
    log_level: str = "INFO"

    @model_validator(mode="after")
    def validate_settings(self):
        if self.min_message_length > self.max_message_length:
            raise ValueError("Invalid message length range")
        if self.ai_moderation_enabled and not self.ai_url.startswith("https://"):
            raise ValueError("AI_URL must be an HTTPS moderation endpoint")
        return self
