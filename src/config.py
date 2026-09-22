from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/imagerelevance"
    vision_model: str = "gemini/gemini-3.6-flash"
    embedding_model: str = "gemini/gemini-embedding-2"
    gemini_api_key: str = ""
    ollama_api_base: str = "http://localhost:11434"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
