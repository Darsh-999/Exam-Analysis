import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import (
    get_projects_collection,
    get_question_papers_collection,
    get_questions_collection,
    get_syllabi_collection,
    get_users_collection,
)
from app.routers import (
    analytics,
    auth,
    documents,
    projects,
    question_papers,
    questions,
    syllabi,
    trends,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_users_collection().create_index("email", unique=True)
    await get_projects_collection().create_index("owner_id")
    await get_question_papers_collection().create_index([("project_id", 1), ("status", 1)])
    await get_syllabi_collection().create_index([("project_id", 1), ("status", 1)])
    await get_questions_collection().create_index(
        [("project_id", 1), ("question_paper_id", 1)]
    )
    await get_question_papers_collection().create_index("extracted_data.subject_name")
    await get_syllabi_collection().create_index("extracted_data.content.topic")
    yield


app = FastAPI(title="Question Paper Analysis API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(documents.router)
api_router.include_router(syllabi.router)
api_router.include_router(question_papers.router)
api_router.include_router(questions.router)
api_router.include_router(analytics.router)
api_router.include_router(trends.router)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if _frontend_dist.is_dir():
    app.mount("/assets", StaticFiles(directory=_frontend_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        candidate = _frontend_dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_frontend_dist / "index.html")
