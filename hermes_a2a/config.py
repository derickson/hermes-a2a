from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    hermes_url: str = "http://127.0.0.1:8642"
    hermes_api_key: str
    hermes_model: str = "hermes-agent"
    hermes_timeout: float = 120.0

    a2a_host: str = "0.0.0.0"
    a2a_port: int = 9000
    a2a_log_level: str = "info"


settings = Settings()
