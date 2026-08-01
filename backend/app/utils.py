from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorCollection


def parse_object_id(value: str, entity_name: str = "resource") -> ObjectId:
    try:
        return ObjectId(value)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {entity_name} id"
        )


async def get_or_404(
    collection: AsyncIOMotorCollection, doc_id: ObjectId, entity_name: str = "Resource"
) -> dict:
    doc = await collection.find_one({"_id": doc_id})
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_name} not found"
        )
    return doc
