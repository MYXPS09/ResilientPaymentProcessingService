from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SERVICE_NAME: str = "Payment Gateway Service"
    SERVICE_DESCRIPTION: str = "Simulates a real-world payment processing system"
    SERVICE_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str
    REDIS_URL: str
    API_CLIENT_KEY: str

    MAX_RETRIES: int = 3
    RETRY_BASE_DELAY: float = 1.0
    RETRY_MAX_DELAY: float = 30.0

    GATEWAY_SUCCESS_RATE: float = 0.65
    GATEWAY_TIMEOUT_RATE: float = 0.10
    GATEWAY_DELAY_MIN: float = 0.2
    GATEWAY_DELAY_MAX: float = 1.5
    GATEWAY_TIMEOUT_SECONDS: float = 5.0

    CB_FAILURE_THRESHOLD: int = 5
    CB_RECOVERY_TIMEOUT: float = 30.0

    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW: int = 60

    model_config = SettingsConfigDict(env_file=(".env", ".env.example"), env_file_encoding="utf-8", extra="ignore")

settings = Settings()
