from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    mongodb_uri: str
    mongodb_db_name: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    upload_dir: str = "uploads"

    gemini_api_key: str

    # Amount to expand each extracted bounding box by on every side (top,
    # bottom, left, right), in the same normalized 0-1000 units as box_2d.
    bbox_expansion: int = 20


settings = Settings()
