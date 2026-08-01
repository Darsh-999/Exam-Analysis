from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from app.config import settings

client = AsyncIOMotorClient(settings.mongodb_uri)
database = client[settings.mongodb_db_name]


def get_users_collection() -> AsyncIOMotorCollection:
    return database["users"]


def get_projects_collection() -> AsyncIOMotorCollection:
    return database["projects"]


def get_question_papers_collection() -> AsyncIOMotorCollection:
    return database["question_papers"]


def get_syllabi_collection() -> AsyncIOMotorCollection:
    return database["syllabi"]


def get_questions_collection() -> AsyncIOMotorCollection:
    return database["questions"]
