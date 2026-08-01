from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorCollection

from app.database import (
    get_projects_collection,
    get_question_papers_collection,
    get_questions_collection,
)
from app.deps import get_current_user
from app.schemas import AllocationStatus, QuestionOut
from app.services.analytics import to_question_out
from app.utils import get_or_404, parse_object_id

router = APIRouter(prefix="/projects/{project_id}/questions", tags=["questions"])


@router.get("", response_model=list[QuestionOut])
async def list_project_questions(
    project_id: str,
    subject_name: str | None = Query(default=None),
    subject_code: str | None = Query(default=None),
    topic: str | None = Query(default=None, description="Matches by topic name"),
    allocation_status: AllocationStatus | None = Query(default=None),
    current_user: dict = Depends(get_current_user),
):
    """Lists a project's questions, joined against their parent question
    paper for subject/exam-date fields. All filters are optional and combine
    with AND when given together.
    """
    await get_or_404(
        get_projects_collection(), parse_object_id(project_id, "project"), "Project"
    )

    # subject_name/subject_code live on the parent question_papers doc, so
    # narrow down which papers match first, then only pull questions from
    # those papers.
    paper_query: dict = {"project_id": project_id}
    if subject_name:
        paper_query["extracted_data.subject_name"] = subject_name
    if subject_code:
        paper_query["extracted_data.subject_code"] = subject_code

    papers: AsyncIOMotorCollection = get_question_papers_collection()
    paper_info = {
        str(doc["_id"]): doc.get("extracted_data") or {}
        async for doc in papers.find(paper_query, {"extracted_data": 1})
    }
    if not paper_info:
        return []

    question_query: dict = {
        "project_id": project_id,
        "question_paper_id": {"$in": list(paper_info.keys())},
    }
    if topic:
        question_query["topic.topic"] = topic
    if allocation_status == AllocationStatus.ALLOCATED:
        question_query["topic.0"] = {"$exists": True}
    elif allocation_status == AllocationStatus.UNALLOCATED:
        question_query["topic"] = {"$size": 0}
    elif allocation_status == AllocationStatus.MULTI_ALLOCATED:
        question_query["topic.1"] = {"$exists": True}

    questions: AsyncIOMotorCollection = get_questions_collection()
    result = []
    async for doc in questions.find(question_query).sort("created_at", 1):
        extracted = paper_info[doc["question_paper_id"]]
        result.append(
            to_question_out(
                doc,
                extracted.get("subject_name"),
                extracted.get("subject_code"),
                extracted.get("exam_date"),
            )
        )
    return result
