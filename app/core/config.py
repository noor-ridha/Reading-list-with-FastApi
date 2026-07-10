from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int
    database_url: str

    # Redis
    redis_host: str
    redis_port: int
    redis_url: str

    # Auth
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    # App
    environment: str

    #test
    test_database_url: str


settings = Settings()