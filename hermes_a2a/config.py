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
    # Public base URL used in FilePart URIs; computed from host/port if empty
    a2a_public_url: str = ""
    # Whitelist of filesystem path prefixes that may be served via /files/{path}
    a2a_file_serve_paths: list[str] = ["/tmp", "/Users/dave/.hermes/generated_images"]


settings = Settings()
