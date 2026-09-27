import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Financial Requirements AI"
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/fin_req_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    GEMINI_API_KEY: str = "your_gemini_api_key_here"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    JWT_SECRET: str = "change_me_in_production"
    JWT_EXPIRE_MINUTES: int = 1440

    class Config:
        env_file = ".env"

settings = Settings()
