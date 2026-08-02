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

    # Amount to expand each extracted bounding box by on every side
    bbox_expansion: int = 20

    # Number of questions sent per classification request
    classification_batch_size: int = 20

    # -- Local extraction pipeline (DocLayout + Qwen via vLLM) --

    vllm_base_url: str = "http://localhost:8000/v1"
    vllm_model_name: str = "model"
    vllm_request_timeout_seconds: int = 120

    # Max number of concurrent Qwen requests in flight at once
    qwen_max_concurrency: int = 8

    # Path to the DocLayout YOLO model weights
    doclayout_model_path: str = "models/doclayout_yolo.pt"

    # Max number of concurrent DocLayout GPU inferences
    doclayout_gpu_concurrency: int = 1

    # Header metadata first N boxes
    header_bbox_limit: int = 20
    
    # Boxes joined per composite header image
    header_boxes_per_image: int = 4

    # Number of consecutive cropped boxes
    question_batch_size: int = 5


settings = Settings()
