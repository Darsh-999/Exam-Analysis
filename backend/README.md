# ExamInsight — Backend

FastAPI backend for ExamInsight — handles auth, project/document management, question
extraction & classification, and trend analytics. Stores everything in MongoDB.

## Prerequisites

- Python 3.10+
- A running MongoDB instance (local or Atlas)
- An RunPod NVIDIA GPU running a local vLLM server hosting a Qwen model, plus the DocLayout YOLO model weights on disk — see "Start the local vLLM server" below. Extraction and classification both depend on vLLM being reachable; there is no external LLM API involved.

## Setup

```
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

## Start the local vLLM server

Extraction (headers, questions, syllabus topics) and classification all run against a local Qwen model served by vLLM.

```
pip install "vllm>=0.11.0"
```

```
CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen3-VL-8B-Instruct --dtype bfloat16 --max-model-len 8192 --gpu-memory-utilization 0.9 --tensor-parallel-size 1 --served-model-name model --trust-remote-code
```

OR 

```
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen3-VL-8B-Instruct --dtype bfloat16 --max-model-len 8192 --gpu-memory-utilization 0.86 --max-num-seqs 4 --max-num-batched-tokens 4096 --limit-mm-per-prompt '{"image": 6}' --mm-processor-kwargs '{"size": {"longest_edge": 1003520, "shortest_edge": 65536}}' --served-model-name model --trust-remote-code
```

## Configure environment variables

```
cp .env.example .env
```

Then fill in:

- `MONGODB_URI` / `MONGODB_DB_NAME` — your MongoDB connection
- `JWT_SECRET_KEY` — generate one with `python -c "import secrets; print(secrets.token_hex(32))"`
- `UPLOAD_DIR` — where uploaded question papers/syllabi are stored (defaults to `uploads`)

## Run the server

```
uvicorn app.main:app --reload --port 8080
```

Runs on http://127.0.0.1:8080. Health check: http://127.0.0.1:8080/health.
Requires MongoDB and the vLLM server.

## API docs

Interactive Swagger UI: http://127.0.0.1:8080/docs

## Project structure

- `app/routers/` — one file per resource: `auth`, `projects`, `documents`, `question_papers`, `questions`, `syllabi`, `trends`, `analytics` (all mounted under `/api` in `app/main.py`)
- `app/schemas.py` — request/response models
- `app/database.py` — MongoDB collection accessors
- `app/services/` — pipeline orchestration (`processing.py` for extraction, `classification.py` for classification), plus cropping/analytics helpers
- `app/local_extraction_service/` — question paper extraction: DocLayout box detection + Qwen (headers, questions), and the shared vLLM client every model call goes through
- `app/local_topic_extraction_service/` — syllabus extraction: PyMuPDF text + one Qwen call
- `app/local_classification_service/` — the classification model call (Qwen) and its prompts
- `app/classification_service/` — model-agnostic pre/postprocessing (temp-ID assignment, resolving IDs back to names) shared by classification
- `app/security.py` / `app/deps.py` — JWT auth helpers + the `get_current_user` dependency
- `app/storage.py` — uploaded-file handling