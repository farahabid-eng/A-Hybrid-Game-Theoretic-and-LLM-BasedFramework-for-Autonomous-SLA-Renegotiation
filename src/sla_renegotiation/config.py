from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    mistralai_api_key: str = "mn6HBPtSTcOkOcPSyfthImylIJtTHtpb"

    client_model: str = "mistral-large-latest"
    provider_model: str = "mistral-large-latest"
    profiling_model: str = "mistral-small-latest"
    rc_model: str = "mistral-small-latest"

    max_negotiation_rounds: int = 10

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    ui_dev_port: int = 5173


settings = Settings()
