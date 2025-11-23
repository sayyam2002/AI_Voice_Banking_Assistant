# backend/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60*24
    ALGORITHM: str
    GEMINI_API_KEY: str = "ADD YOUR GEMINI KEYS HERE"

    # location where your old main.py exists (for reference to integrate voice logic)
    EXISTING_MAIN_PATH: str

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()