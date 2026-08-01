import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import (
    get_projects_collection,
    get_question_papers_collection,
    get_questions_collection,
    get_syllabi_collection,
    get_users_collection,
)
from app.routers import auth, documents, projects

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
    yield


app = FastAPI(title="Question Paper Analysis API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(documents.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
