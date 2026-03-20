from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Database
    DATABASE_URL: str = "sqlite:///./restaurant_agent.db"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Telnyx
    TELNYX_API_KEY: str = ""
    TELNYX_PUBLIC_KEY: str = ""
    TELNYX_CONNECTION_ID: str = ""
    TELNYX_MESSAGING_PROFILE_ID: str = ""

    # Deepgram
    DEEPGRAM_API_KEY: str = ""

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_BASIC: str = ""
    STRIPE_PRICE_ID_PRO: str = ""
    STRIPE_PRICE_ID_ENTERPRISE: str = ""

    # URLs
    BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"

    # Email (SMTP) — optional, logs to console if not set
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # Optional
    SENTRY_DSN: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
