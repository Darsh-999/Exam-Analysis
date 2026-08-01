from fastapi import APIRouter, Depends, Query

from app.database import (
    get_projects_collection,
    get_question_papers_collection,
    get_questions_collection,
)
from app.deps import get_current_user
from app.schemas import (
    AllocationBreakdownEntry,
    AllocationHealthOut,
    ChartOut,
    ChartPoint,
    FrequencyMetric,
    HeatmapCell,
    HeatmapOut,
    MarksPerPaperEntry,
    MarksPerPaperOut,
    MarksTopicSegment,
)
from app.services.analytics import (
    UNDATED_LABEL,
    allocation_breakdown_by_paper,
    format_mark_label,
    mark_value_distribution,
    marks_per_paper_by_topic,
    paper_year_by_id,
    parse_exam_year,
    questions_per_year,
    subtopic_frequency,
    topic_counts_by_paper,
    topic_frequency,
)
from app.utils import get_or_404, parse_object_id

router = APIRouter(prefix="/projects/{project_id}/trends", tags=["trends"])


async def _ensure_project_exists(project_id: str) -> None:
    await get_or_404(get_projects_collection(), parse_object_id(project_id, "project"), "Project")


@router.get("/questions-per-year", response_model=ChartOut)
async def get_questions_per_year(project_id: str, current_user: dict = Depends(get_current_user)):
    """Bar chart: total questions extracted per exam year."""
    await _ensure_project_exists(project_id)

    year_by_paper = await paper_year_by_id(get_question_papers_collection(), project_id)
    totals = await questions_per_year(get_questions_collection(), project_id, year_by_paper)

    dated_years = sorted(year for year in totals if year != UNDATED_LABEL)
    ordered_years = dated_years + ([UNDATED_LABEL] if UNDATED_LABEL in totals else [])

    return ChartOut(
        title="Questions per Year",
        chart_type="bar",
        description=(
            "Total number of questions extracted per exam year, based on each "
            "question paper's exam date. Papers whose exam date could not be "
            "determined are grouped under 'Undated' -- render that as its own "
            "bar rather than dropping it."
        ),
        x_label="Year",
        y_label="Number of Questions",
        data=[ChartPoint(label=year, value=totals[year]) for year in ordered_years],
    )


@router.get("/topic-frequency", response_model=ChartOut)
async def get_topic_frequency(
    project_id: str,
    metric: FrequencyMetric = Query(
        default=FrequencyMetric.COUNT,
        description="'count' ranks by number of questions, 'marks' ranks by total marks",
    ),
    current_user: dict = Depends(get_current_user),
):
    """Horizontal bar chart: topics ranked by how often (or how heavily)
    they're tested. Use `metric=marks` for the marks-weighted variant of the
    same chart.
    """
    await _ensure_project_exists(project_id)

    ranked = await topic_frequency(get_questions_collection(), project_id, metric.value)

    if metric == FrequencyMetric.COUNT:
        title = "Most Frequently Tested Topics"
        value_label = "Number of Questions"
        description = (
            "Ranks topics by how many questions are attached to them. A "
            "question mapped to more than one topic (multi-allocated) is "
            "counted once for each topic it's attached to, so this is 'how "
            "often does this topic come up', not a partition of all questions."
        )
    else:
        title = "Highest-Weighted Topics"
        value_label = "Total Marks"
        description = (
            "Ranks topics by the total marks of the questions attached to "
            "them. A question mapped to more than one topic contributes its "
            "full marks to each of those topics."
        )

    return ChartOut(
        title=title,
        chart_type="horizontal_bar",
        description=description,
        x_label=value_label,
        y_label="Topic",
        data=[ChartPoint(label=name, value=value) for name, value in ranked],
    )


@router.get("/subtopic-frequency", response_model=ChartOut)
async def get_subtopic_frequency(
    project_id: str,
    metric: FrequencyMetric = Query(
        default=FrequencyMetric.COUNT,
        description="'count' ranks by number of questions, 'marks' ranks by total marks",
    ),
    current_user: dict = Depends(get_current_user),
):
    """Horizontal bar chart: subtopics ranked by how often (or how heavily)
    they're tested. Use `metric=marks` for the marks-weighted variant.
    """
    await _ensure_project_exists(project_id)

    ranked = await subtopic_frequency(get_questions_collection(), project_id, metric.value)

    if metric == FrequencyMetric.COUNT:
        title = "Most Frequently Tested Subtopics"
        value_label = "Number of Questions"
        description = (
            "Ranks subtopics by how many questions are attached to them. A "
            "question mapped to more than one subtopic is counted once for "
            "each subtopic it's attached to."
        )
    else:
        title = "Highest-Weighted Subtopics"
        value_label = "Total Marks"
        description = (
            "Ranks subtopics by the total marks of the questions attached to "
            "them. A question mapped to more than one subtopic contributes "
            "its full marks to each of those subtopics."
        )

    return ChartOut(
        title=title,
        chart_type="horizontal_bar",
        description=description,
        x_label=value_label,
        y_label="Subtopic",
        data=[ChartPoint(label=name, value=value) for name, value in ranked],
    )


@router.get("/marks-per-paper", response_model=MarksPerPaperOut)
async def get_marks_per_paper(project_id: str, current_user: dict = Depends(get_current_user)):
    """Stacked vertical bar chart (with a total-marks line): one bar per
    question paper, ordered by exam date, each segmented by how many marks
    went to each topic.
    """
    await _ensure_project_exists(project_id)

    papers = get_question_papers_collection()
    paper_docs = [
        doc
        async for doc in papers.find(
            {"project_id": project_id},
            {"filename": 1, "extracted_data.subject_code": 1, "extracted_data.exam_date": 1},
        )
    ]

    def sort_key(doc: dict) -> tuple:
        exam_date = (doc.get("extracted_data") or {}).get("exam_date") or ""
        return (parse_exam_year(exam_date) is None, exam_date, doc["filename"])

    paper_docs.sort(key=sort_key)

    marks_by_paper = await marks_per_paper_by_topic(get_questions_collection(), project_id)

    entries = []
    for doc in paper_docs:
        paper_id = str(doc["_id"])
        extracted = doc.get("extracted_data") or {}
        topic_marks = marks_by_paper.get(paper_id, {})
        segments = [
            MarksTopicSegment(topic=topic, marks=marks)
            for topic, marks in sorted(
                topic_marks.items(), key=lambda item: item[1], reverse=True
            )
        ]
        entries.append(
            MarksPerPaperEntry(
                paper_id=paper_id,
                filename=doc["filename"],
                subject_code=extracted.get("subject_code") or None,
                exam_date=extracted.get("exam_date") or None,
                total_marks=sum(topic_marks.values()),
                segments=segments,
            )
        )

    return MarksPerPaperOut(
        title="Marks per Paper by Topic",
        chart_type="stacked_bar_with_line",
        description=(
            "One bar per question paper (x-axis, ordered left-to-right by "
            "exam date -- undated papers last), stacked by how many marks "
            "each topic contributed. Each question's marks are counted under "
            "its first-listed mapped topic only ('Unallocated' if it has "
            "none), so a bar's segments always sum exactly to its "
            "total_marks -- draw the connecting line through each bar's "
            "total_marks value."
        ),
        x_label="Question Paper",
        y_label="Marks",
        data=entries,
    )


@router.get("/topic-year-heatmap", response_model=HeatmapOut)
async def get_topic_year_heatmap(project_id: str, current_user: dict = Depends(get_current_user)):
    """Heatmap: topics (rows) x exam years (columns), cell intensity = number
    of questions on that topic that year. Shows which topics are trending up
    or down over time.
    """
    await _ensure_project_exists(project_id)

    year_by_paper = await paper_year_by_id(get_question_papers_collection(), project_id)
    rows = await topic_counts_by_paper(get_questions_collection(), project_id)

    cells: dict[tuple[str, str], int] = {}
    topic_totals: dict[str, int] = {}
    years_seen: set[str] = set()
    for paper_id, topic, count in rows:
        year = year_by_paper.get(paper_id, UNDATED_LABEL)
        key = (topic, year)
        cells[key] = cells.get(key, 0) + count
        topic_totals[topic] = topic_totals.get(topic, 0) + count
        years_seen.add(year)

    ordered_topics = sorted(topic_totals, key=lambda t: topic_totals[t], reverse=True)
    ordered_years = sorted(year for year in years_seen if year != UNDATED_LABEL)
    if UNDATED_LABEL in years_seen:
        ordered_years.append(UNDATED_LABEL)

    return HeatmapOut(
        title="Topic Popularity by Year",
        chart_type="heatmap",
        description=(
            "Question count per topic per exam year. Topics (rows) are "
            "ordered by all-time question count (most-tested first), years "
            "(columns) chronologically with 'Undated' last if present. Any "
            "(topic, year) combination missing from 'data' has a count of 0 "
            "-- render it accordingly rather than leaving a gap."
        ),
        x_label="Year",
        y_label="Topic",
        rows=ordered_topics,
        columns=ordered_years,
        data=[
            HeatmapCell(row=topic, column=year, value=count)
            for (topic, year), count in cells.items()
        ],
    )


@router.get("/allocation-health", response_model=AllocationHealthOut)
async def get_allocation_health(project_id: str, current_user: dict = Depends(get_current_user)):
    """Stacked bar chart: per paper, how many questions are unallocated,
    single-allocated, or multi-allocated. A data-quality/coverage view of the
    classification pipeline rather than an exam-content trend.
    """
    await _ensure_project_exists(project_id)

    papers = get_question_papers_collection()
    paper_docs = [
        doc
        async for doc in papers.find({"project_id": project_id}, {"filename": 1}).sort(
            "uploaded_at", 1
        )
    ]
    breakdown = await allocation_breakdown_by_paper(get_questions_collection(), project_id)

    empty_counts = {"total": 0, "unallocated": 0, "single_allocated": 0, "multi_allocated": 0}
    entries = []
    for doc in paper_docs:
        counts = breakdown.get(str(doc["_id"]), empty_counts)
        entries.append(
            AllocationBreakdownEntry(
                paper_id=str(doc["_id"]),
                filename=doc["filename"],
                total_questions=counts["total"],
                unallocated=counts["unallocated"],
                single_allocated=counts["single_allocated"],
                multi_allocated=counts["multi_allocated"],
            )
        )

    return AllocationHealthOut(
        title="Classification Coverage per Question Paper",
        chart_type="stacked_bar",
        description=(
            "For each question paper, splits its questions into three "
            "mutually exclusive, stackable buckets: unallocated (no topic "
            "matched), single_allocated (exactly one topic), and "
            "multi_allocated (two or more topics). The three always sum to "
            "total_questions for that paper."
        ),
        x_label="Question Paper",
        y_label="Number of Questions",
        data=entries,
    )


@router.get("/mark-distribution", response_model=ChartOut)
async def get_mark_distribution(project_id: str, current_user: dict = Depends(get_current_user)):
    """Bar chart / histogram: number of questions per distinct mark value,
    showing the exam's question-weight structure (e.g. mostly 2-markers vs
    10-markers).
    """
    await _ensure_project_exists(project_id)

    rows = await mark_value_distribution(get_questions_collection(), project_id)

    return ChartOut(
        title="Question Mark-Value Distribution",
        chart_type="bar",
        description=(
            "Number of questions per distinct mark value across the whole "
            "project (e.g. how many 2-mark vs 10-mark questions), showing "
            "how exam weight is structured."
        ),
        x_label="Marks",
        y_label="Number of Questions",
        data=[ChartPoint(label=format_mark_label(mark), value=count) for mark, count in rows],
    )
