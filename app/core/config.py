from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    app_name: str = "Card Limit API"
    app_env: str = "development"
    database_url: str = (
        "postgresql+psycopg://card_user:example_password@localhost:5432/card_limit"
    )
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
