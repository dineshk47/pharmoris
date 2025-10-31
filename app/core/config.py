from typing import Optional
from pydantic import AnyUrl, field_validator
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    APP_NAME: str = "phramoris-backend"
    ENV: str = "development"
    DEBUG: bool = True

    DATABASE_URL: AnyUrl
    USDA_API_KEY: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    RATE_LIMIT_REQUESTS: int = 15
    RATE_LIMIT_PERIOD_SECONDS: int = 60

    API_KEY: str
    API_KEY_NAME: str = "X-API-Key"

    @field_validator("API_KEY", "API_KEY_NAME", mode="before")
    def validate_api_key_settings(cls, v: Optional[str], field: str) -> str:
        if not v:
            raise ValueError(f"{field.name} environment variable is required")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
