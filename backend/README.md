# ExamInsight — Backend

FastAPI backend for ExamInsight — handles auth, project/document management, question
extraction & classification, and trend analytics. Stores everything in MongoDB.

## Prerequisites

- Python 3.10+
- A running MongoDB instance (local or Atlas)
- An API key for the AI provider used for document extraction/classification (see `.env.example` /
  `app/config.py` for the exact setting name)

## Setup

```
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

## Configure environment variables

```
cp .env.example .env
```

Then fill in:

- `MONGODB_URI` / `MONGODB_DB_NAME` — your MongoDB connection
- `JWT_SECRET_KEY` — generate one with `python -c "import secrets; print(secrets.token_hex(32))"`
- `UPLOAD_DIR` — where uploaded question papers/syllabi are stored (defaults to `uploads`)

`app/config.py` also requires an AI provider API key that isn't currently listed in
`.env.example` — add it to `.env` as well, or the app will fail to start with a clear "field
required" error naming the missing setting.

## Run the server

```
uvicorn app.main:app --reload
```

Runs on http://127.0.0.1:8000 by default. Health check: http://127.0.0.1:8000/health.
The frontend's dev server proxies to this address — see [`../frontend/README.md`](../frontend/README.md).

## API docs

Interactive Swagger UI: http://127.0.0.1:8000/docs

## Project structure

- `app/routers/` — one file per resource: `auth`, `projects`, `documents`, `question_papers`, `questions`, `syllabi`, `trends`, `analytics`
- `app/schemas.py` — request/response models
- `app/database.py` — MongoDB collection accessors
- `app/services/` — document processing pipeline (cropping, classification, analytics helpers)
- `app/security.py` / `app/deps.py` — JWT auth helpers + the `get_current_user` dependency
- `app/storage.py` — uploaded-file handling
