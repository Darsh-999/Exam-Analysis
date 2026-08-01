from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorCollection

from app.database import (
    get_projects_collection,
    get_question_papers_collection,
    get_questions_collection,
)
from app.deps import get_current_user
from app.schemas import ChartOut, ChartPoint, QuestionOut, QuestionPaperSummaryOut
from app.services.analytics import (
    allocation_counts_by_paper,
    to_question_out,
    topic_distribution_for_paper,
)
from app.utils import get_or_404, parse_object_id

router = APIRouter(tags=["question-papers"])

_EMPTY_COUNTS = {"total": 0, "allocated": 0, "unallocated": 0, "multi_allocated": 0}


@router.get(
    "/projects/{project_id}/question-papers", response_model=list[QuestionPaperSummaryOut]
)
async def list_project_question_papers(
    project_id: str, current_user: dict = Depends(get_current_user)
):
    await get_or_404(
        get_projects_collection(), parse_object_id(project_id, "project"), "Project"
    )

    papers: AsyncIOMotorCollection = get_question_papers_collection()
    docs = [doc async for doc in papers.find({"project_id": project_id}).sort("uploaded_at", -1)]
    counts_by_paper = await allocation_counts_by_paper(get_questions_collection(), project_id)

    result = []
    for doc in docs:
        extracted = doc.get("extracted_data") or {}
        counts = counts_by_paper.get(str(doc["_id"]), _EMPTY_COUNTS)
        result.append(
            QuestionPaperSummaryOut(
                id=str(doc["_id"]),
                filename=doc["filename"],
                status=doc["status"],
                subject_name=extracted.get("subject_name"),
                subject_code=extracted.get("subject_code"),
                total_questions=counts["total"],
                total_marks=extracted.get("total_marks"),
                total_allocated_questions=counts["allocated"],
                total_unallocated_questions=counts["unallocated"],
                total_multi_allocated_questions=counts["multi_allocated"],
            )
        )
    return result


@router.get("/question-papers/{question_paper_id}/questions", response_model=list[QuestionOut])
async def list_question_paper_questions(
    question_paper_id: str, current_user: dict = Depends(get_current_user)
):
    paper = await get_or_404(
        get_question_papers_collection(),
        parse_object_id(question_paper_id, "question paper"),
        "Question paper",
    )
    extracted = paper.get("extracted_data") or {}

    questions: AsyncIOMotorCollection = get_questions_collection()
    return [
        to_question_out(
            doc, extracted.get("subject_name"), extracted.get("subject_code"), extracted.get("exam_date")
        )
        async for doc in questions.find({"question_paper_id": question_paper_id}).sort(
            "created_at", 1
        )
    ]


@router.get(
    "/question-papers/{question_paper_id}/trends/topic-distribution", response_model=ChartOut
)
async def get_question_paper_topic_distribution(
    question_paper_id: str, current_user: dict = Depends(get_current_user)
):
    """Pie chart: share of this paper's questions belonging to each topic.
    Pair with `GET /projects/{project_id}/question-papers` to build a
    paper-picker dropdown above the chart.
    """
    paper = await get_or_404(
        get_question_papers_collection(),
        parse_object_id(question_paper_id, "question paper"),
        "Question paper",
    )

    rows = await topic_distribution_for_paper(get_questions_collection(), question_paper_id)

    return ChartOut(
        title=f"Topic Distribution - {paper['filename']}",
        chart_type="pie",
        description=(
            "Share of this paper's questions belonging to each topic. Each "
            "question is counted under its first-listed mapped topic only, "
            "so slices sum exactly to the paper's total question count. "
            "Questions with no mapped topic appear as 'Unallocated'."
        ),
        data=[ChartPoint(label=name, value=count) for name, count in rows],
    )
