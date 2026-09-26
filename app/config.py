from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./albania_bridge.db"
    session_secret_key: str = "development-only-change-me"
    environment: str = "development"
    openai_api_key: str | None = None
    admin_email: str = "admin@example.com"
    admin_password: str = "change-me"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def validate_production(self):
        if self.environment == "production" and len(self.session_secret_key) < 32:
            raise ValueError("SESSION_SECRET_KEY must be at least 32 characters in production")


settings = Settings()
settings.validate_production()
