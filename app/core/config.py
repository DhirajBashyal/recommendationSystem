from pydantic_settings import BaseSettings
from typing import Any, List
import secrets

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1/token"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    

    PROJECT_NAME: str = "Recommendation System"
    OPENAI_API_KEY: str = "recomm_project"
    LLM_MODEL_NAME: str = "gpt-3.5-turbo-instruct"
    SECRET_KEY: str = "your key here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # REDIS_HOST: str = "redis"
    # REDIS_PORT: int = 6379
    # REDIS_DB: int = 0
    # REDIS_PASSWORD: str = ""
    
   
    BASE_LLM_MODEL: str = "gpt-3.5-turbo-instruct"
    MODEL_OUTPUT_DIR: str = "./models"
    
   
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8000", "http://localhost:3000"]
    

    # POSTGRES_SERVER: str = "localhost"
    # POSTGRES_PORT: int = 5432
    # POSTGRES_USER: str = "dhirajbashyal"  # Use your macOS username
    # POSTGRES_PASSWORD: str = "1234567890"
    # POSTGRES_DB: str = "db_demo"
    
    @property
    def DATABASE_URI(self) -> str:
        return "postgresql://dhirajbashyal:1234567890@localhost:5432/recom_demo"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

