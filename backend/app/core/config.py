from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MediLens AI"
    frontend_url: str = "http://localhost:5173"

    # Database
    database_url: str = "sqlite:///./medilens.db"

    # Security (JWT)
    secret_key: str  # koi default nahi: .env mein hona zaroori hai
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()