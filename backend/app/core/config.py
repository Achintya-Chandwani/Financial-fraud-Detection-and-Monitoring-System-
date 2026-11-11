"""
FraudShield AI — Application Configuration
Loads settings from environment variables / .env file.
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    # --- Application ---
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "change_me_in_production"

    # --- Database ---
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "fraudshield"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""

    # --- Model ---
    MODEL_PATH: str = "models/best_model.joblib"
    PREPROCESSOR_PATH: str = "models/preprocessor.joblib"
    MODEL_METRICS_PATH: str = "models/model_metrics.json"
    MODEL_VERSION: str = "1.0.0"

    # --- API ---
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:5500,http://localhost:5500"

    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/fraudshield.log"

    @property
    def database_url(self) -> str:
        from urllib.parse import quote_plus
        pwd = quote_plus(self.DB_PASSWORD)   # handles @, #, % etc.
        return (
            f"mysql+pymysql://{self.DB_USER}:{pwd}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def model_path_abs(self) -> Path:
        # Resolve relative to project root (two levels up from backend/app/core)
        base = Path(__file__).resolve().parents[3]
        return base / self.MODEL_PATH

    @property
    def preprocessor_path_abs(self) -> Path:
        base = Path(__file__).resolve().parents[3]
        return base / self.PREPROCESSOR_PATH

    @property
    def metrics_path_abs(self) -> Path:
        base = Path(__file__).resolve().parents[3]
        return base / self.MODEL_METRICS_PATH

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Global settings instance
settings = Settings()
