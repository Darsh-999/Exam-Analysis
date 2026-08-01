from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorCollection

from app.database import get_projects_collection, get_syllabi_collection
from app.deps import get_current_user
from app.schemas import SyllabusContentOut, SyllabusSummaryOut, SyllabusTopicOut
from app.services.analytics import unique_subtopics, unique_topics
from app.utils import get_or_404, parse_object_id

router = APIRouter(tags=["syllabi"])


def _to_syllabus_summary(doc: dict) -> SyllabusSummaryOut:
    content = (doc.get("extracted_data") or {}).get("content", [])
    return SyllabusSummaryOut(
        id=str(doc["_id"]),
        filename=doc["filename"],
        status=doc["status"],
        total_topics=unique_topics(content),
        total_subtopics=unique_subtopics(content),
    )


@router.get("/projects/{project_id}/syllabi", response_model=list[SyllabusSummaryOut])
async def list_project_syllabi(project_id: str, current_user: dict = Depends(get_current_user)):
    await get_or_404(
        get_projects_collection(), parse_object_id(project_id, "project"), "Project"
    )

    syllabi: AsyncIOMotorCollection = get_syllabi_collection()
    return [
        _to_syllabus_summary(doc)
        async for doc in syllabi.find({"project_id": project_id}).sort("uploaded_at", -1)
    ]


@router.get("/syllabi/{syllabus_id}/topics", response_model=SyllabusContentOut)
async def get_syllabus_topics(syllabus_id: str, current_user: dict = Depends(get_current_user)):
    doc = await get_or_404(
        get_syllabi_collection(), parse_object_id(syllabus_id, "syllabus"), "Syllabus"
    )

    content = (doc.get("extracted_data") or {}).get("content", [])
    return SyllabusContentOut(
        syllabus_id=str(doc["_id"]),
        filename=doc["filename"],
        content=[SyllabusTopicOut(**item) for item in content],
    )
