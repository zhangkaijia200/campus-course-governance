from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Campus Course Governance"
    app_env: str = "dev"
    secret_key: str = "change-this-in-production"
    access_token_expire_minutes: int = 120

    mysql_host: str = "mysql"
    mysql_port: int = 3306
    mysql_user: str = "course"
    mysql_password: str = "coursepass"
    mysql_database: str = "course_governance"

    redis_url: str = "redis://redis:6379/0"
    rate_limit_requests: int = 5
    rate_limit_window_seconds: int = 10
    idempotency_ttl_seconds: int = 30
    queue_stream: str = "course-selection"
    queue_group: str = "selection-workers"
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
