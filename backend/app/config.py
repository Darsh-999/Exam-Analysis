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

    # Number of questions sent to Gemini per classification request.
    classification_batch_size: int = 20

    # -- Local extraction pipeline (DocLayout + Qwen via vLLM) --

    # vLLM's OpenAI-compatible endpoint serving the Qwen VL model.
    vllm_base_url: str = "http://localhost:8000/v1"
    vllm_model_name: str = "model"
    vllm_request_timeout_seconds: int = 120

    # Max number of concurrent Qwen requests in flight at once (across every
    # in-progress PDF). This is purely a client-side throttle -- vLLM's own
    # scheduler (bounded by its --gpu-memory-utilization KV-cache budget) is
    # the real admission control, so raising this just lets more requests
    # queue into vLLM directly instead of queuing behind our own semaphore.
    qwen_max_concurrency: int = 8

    # Path to the DocLayout YOLO model weights, relative to the backend
    # working directory.
    doclayout_model_path: str = "models/doclayout_yolo.pt"

    # Max number of concurrent DocLayout GPU inferences (across every
    # in-progress PDF). DocLayout shares a GPU with vLLM, so this stays low.
    doclayout_gpu_concurrency: int = 1

    # Header metadata (degree, subject, exam date, ...) is only ever found in
    # the first page's header block, so only the first N boxes are considered.
    header_bbox_limit: int = 20
    # Boxes joined per composite header image (see HEADER_IMAGE_DESIGN.md).
    header_boxes_per_image: int = 4

    # Number of consecutive cropped boxes sent per Qwen question-extraction
    # request.
    question_batch_size: int = 5


settings = Settings()
