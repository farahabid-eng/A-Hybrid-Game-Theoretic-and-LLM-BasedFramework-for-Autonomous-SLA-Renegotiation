from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    mistralai_api_key: str = ""
    nvidia_api_key: str = ""

    client_model: str = ""
    provider_model: str = ""
    profiling_model: str = ""
    rc_model: str = ""

    max_negotiation_rounds: int = 10

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    ui_dev_port: int = 5173


settings = Settings()
