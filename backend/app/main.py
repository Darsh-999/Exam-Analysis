from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import get_users_collection
from app.routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_users_collection().create_index("email", unique=True)
    yield


app = FastAPI(title="Question Paper Analysis API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
