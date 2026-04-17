from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    active_backend: str = "http://localhost:11434"
    active_api_key: str = "ollama"
    hosts: dict = Field(default_factory=dict)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_json_schema": True,
    }


settings = Settings()
