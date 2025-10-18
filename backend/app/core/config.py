import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from dotenv import load_dotenv

class Settings(BaseSettings):
    load_dotenv()

    PROJECT_NAME: str = "MailSeller API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    AUTH_SECRET: str = os.getenv('AUTH_SECRET')

    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL')

    # Redis
    REDIS_URL: str = os.getenv('REDIS_URL')

    # Admin
    ADMIN_TOKEN: str = os.getenv('ADMIN_TOKEN')

    # CORS
    ALLOWED_HOSTS: List[str] = os.getenv('ALLOWED_HOSTS', "http://localhost:3000,http://localhost:8000").split(',')

    # JWT
    SECRET_KEY: str = os.getenv('SECRET_KEY', "your-secret-key-change-this-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()