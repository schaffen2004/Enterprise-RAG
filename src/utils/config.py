from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    rag_db_host: str = "localhost"
    rag_db_port: int = 5432
    rag_db_name: str
    rag_db_user: str
    rag_db_password: str

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "ap-southeast-1"
    s3_bucket: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    max_upload_size_mb: int = 20

    app_host: str = "0.0.0.0"
    app_port: int = 8000

    @property
    def database_url(self) -> str:
        user = quote_plus(self.rag_db_user)
        password = quote_plus(self.rag_db_password)
        return (
            f"postgresql+psycopg2://{user}:{password}"
            f"@{self.rag_db_host}:{self.rag_db_port}/{self.rag_db_name}"
        )

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
