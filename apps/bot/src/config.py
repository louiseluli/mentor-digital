import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    pseudonymization_pepper: str
    analytics_pepper: str
    redis_url: str
    telegram_bot_token: str
    whatsapp_verify_token: str
    whatsapp_app_secret: str
    whatsapp_phone_number_id: str
    whatsapp_access_token: str
    web_platform_url: str
    google_api_key: str
    environment: str

    def __init__(self):
        self.pseudonymization_pepper = self._require("PSEUDONYMIZATION_PEPPER")
        self.analytics_pepper = self._require("ANALYTICS_PEPPER")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.whatsapp_verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
        self.whatsapp_app_secret = os.getenv("WHATSAPP_APP_SECRET", "")
        self.whatsapp_phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        self.whatsapp_access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        self.web_platform_url = os.getenv("WEB_PLATFORM_URL", "http://localhost:3000")
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.environment = os.getenv("ENVIRONMENT", "development")

    @staticmethod
    def _require(key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Variável de ambiente obrigatória não definida: {key}")
        return value


def load_config() -> Config:
    return Config()
