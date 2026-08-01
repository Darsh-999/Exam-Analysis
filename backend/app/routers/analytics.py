from fastapi import APIRouter, Depends

from app.database import (
    get_projects_collection,
    get_question_papers_collection,
    get_questions_collection,
    get_syllabi_collection,
)
from app.deps import get_current_user
from app.schemas import GlobalCountsOut
from app.services.analytics import count_unique_values

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/counts", response_model=GlobalCountsOut)
async def get_global_counts(current_user: dict = Depends(get_current_user)):
    projects = get_projects_collection()
    question_papers = get_question_papers_collection()
    syllabi = get_syllabi_collection()
    questions = get_questions_collection()

    return GlobalCountsOut(
        total_projects=await projects.count_documents({}),
        total_question_papers=await question_papers.count_documents({}),
        total_syllabi=await syllabi.count_documents({}),
        total_subjects=await count_unique_values(question_papers, "extracted_data.subject_name"),
        total_questions=await questions.count_documents({}),
        total_topics=await count_unique_values(syllabi, "extracted_data.content.topic"),
    )
