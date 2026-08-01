from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from app.config import settings

client = AsyncIOMotorClient(settings.mongodb_uri)
database = client[settings.mongodb_db_name]


def get_users_collection() -> AsyncIOMotorCollection:
    return database["users"]
