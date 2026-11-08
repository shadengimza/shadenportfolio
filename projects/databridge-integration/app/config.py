from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DataBridge Integration"
    soap_endpoint_url: str = "http://127.0.0.1:8000/mock-soap"
    soap_timeout_seconds: float = 5.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
