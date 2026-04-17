from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    # which backend to route chat completions to
    active_backend: str = "http://localhost:11434"  # ollama default
    active_api_key: str = "ollama"

    # host inventory — override via env or .env file
    hosts: dict = Field(default_factory=dict)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
