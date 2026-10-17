from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "s4544_doc"

    class Config:
        env_file = ".env"

settings = Settings()