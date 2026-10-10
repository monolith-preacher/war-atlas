"""Application settings loaded from environment variables (see .env.example)."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

INSECURE_SECRET = "change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="development", description="development | test | production")
    database_url: str = "postgresql+psycopg://waratlas:waratlas@localhost:5432/waratlas"
    jwt_secret: str = INSECURE_SECRET
    jwt_expire_minutes: int = 480
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    api_prefix: str = "/api/v1"
    # Optional bootstrap admin (created on startup by the entrypoint if both are set).
    admin_email: str | None = None
    admin_password: str | None = None
    # Directory with geodata files (boundaries). Defaults to <repo>/data.
    data_dir: str | None = None
    seed_on_start: bool = False
    # Network access for importers (Wikidata). Disabled in tests.
    importers_enabled: bool = True
    wikidata_user_agent: str = "WarAtlas/0.1 (https://github.com/; contact: admin)"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, v: object) -> object:
        if isinstance(v, str) and not v.strip().startswith("["):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def validate_for_runtime(self) -> None:
        if self.is_production and (self.jwt_secret == INSECURE_SECRET or len(self.jwt_secret) < 32):
            raise RuntimeError(
                "JWT_SECRET must be set to a strong value (>= 32 chars) when ENVIRONMENT=production"
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
