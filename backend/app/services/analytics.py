"""Read-side helpers shared by the analytics/listing routers.

These compute counts and joins at query time rather than denormalizing data
(e.g. subject name onto each question) at write time, so they work correctly
against documents that were already processed before these endpoints existed.
"""

import re

from motor.motor_asyncio import AsyncIOMotorCollection

from app.schemas import QuestionOut, QuestionTopicOut


async def count_unique_values(
    collection: AsyncIOMotorCollection, field: str, query: dict | None = None
) -> int:
    """Counts distinct values of `field` across matching docs.

    Mongo's `distinct` flattens array fields automatically -- including a
    field nested inside an array of subdocuments (e.g.
    `extracted_data.content.topic`) -- so this also answers "how many unique
    topics/subtopics across all syllabi" without manually unwinding arrays.
    """
    values = await collection.distinct(field, query or {})
    return len([v for v in values if v not in (None, "")])


async def count_allocated_questions(collection: AsyncIOMotorCollection, query: dict) -> int:
    return await collection.count_documents({**query, "topic.0": {"$exists": True}})


async def count_unallocated_questions(collection: AsyncIOMotorCollection, query: dict) -> int:
    return await collection.count_documents({**query, "topic": {"$size": 0}})


async def count_multi_allocated_questions(collection: AsyncIOMotorCollection, query: dict) -> int:
    return await collection.count_documents({**query, "topic.1": {"$exists": True}})


async def allocation_counts_by_paper(
    collection: AsyncIOMotorCollection, project_id: str
) -> dict[str, dict[str, int]]:
    """One aggregation covering every question paper in a project, instead of
    a handful of count_documents() calls per paper.

    Returns `{question_paper_id: {total, allocated, unallocated, multi_allocated}}`.
    """
    pipeline = [
        {"$match": {"project_id": project_id}},
        {
            "$group": {
                "_id": "$question_paper_id",
                "total": {"$sum": 1},
                "allocated": {"$sum": {"$cond": [{"$gte": [{"$size": "$topic"}, 1]}, 1, 0]}},
                "multi_allocated": {
                    "$sum": {"$cond": [{"$gte": [{"$size": "$topic"}, 2]}, 1, 0]}
                },
            }
        },
    ]

    counts: dict[str, dict[str, int]] = {}
    async for row in collection.aggregate(pipeline):
        total, allocated = row["total"], row["allocated"]
        counts[row["_id"]] = {
            "total": total,
            "allocated": allocated,
            "unallocated": total - allocated,
            "multi_allocated": row["multi_allocated"],
        }
    return counts


def unique_topics(content: list[dict]) -> int:
    return len({item["topic"] for item in content if item.get("topic")})


def unique_subtopics(content: list[dict]) -> int:
    return len({name for item in content for name in item.get("subtopics", [])})


def username_from_email(email: str) -> str:
    return email.split("@", 1)[0]


def to_question_out(
    doc: dict, subject_name: str | None, subject_code: str | None, exam_date: str | None
) -> QuestionOut:
    return QuestionOut(
        question_id=str(doc["_id"]),
        subject_name=subject_name,
        subject_code=subject_code,
        exam_date=exam_date,
        question_number=doc["question_number"],
        question=doc["question"],
        mark=doc["mark"],
        cropped_image=doc.get("cropped_image", ""),
        topic=[QuestionTopicOut(**t) for t in doc.get("topic", [])],
    )


# ---------------------------------------------------------------------------
# Trend-analysis helpers
#
# Two counting conventions are used deliberately, and each function below
# says which one it follows:
#
# - "attached to every mapped topic": a question mapped to N topics
#   contributes fully to each of the N buckets (used for frequency/ranking
#   charts, where the question is genuinely "about" every topic it matched).
# - "primary topic only": a question contributes to exactly one bucket, so
#   the buckets stay additive and sum to a known total (used where the chart
#   needs its parts to sum to a whole, e.g. a stacked bar or a pie).
# ---------------------------------------------------------------------------

_EXAM_YEAR_PATTERN = re.compile(r"(\d{4})")

UNALLOCATED_LABEL = "Unallocated"
UNDATED_LABEL = "Undated"


def parse_exam_year(exam_date: str | None) -> str | None:
    """Best-effort year extraction from an extracted `exam_date` string
    (expected `YYYY/MM/DD`, but extraction isn't always clean). Returns
    None when no leading 4-digit year can be found, so callers can bucket
    the paper as "Undated" instead of dropping it.
    """
    if not exam_date:
        return None
    match = _EXAM_YEAR_PATTERN.match(exam_date.strip())
    return match.group(1) if match else None


async def paper_year_by_id(
    question_papers_collection: AsyncIOMotorCollection, project_id: str
) -> dict[str, str]:
    """Maps each question paper in a project to its exam year, or
    "Undated" when the year can't be determined.
    """
    years: dict[str, str] = {}
    cursor = question_papers_collection.find(
        {"project_id": project_id}, {"extracted_data.exam_date": 1}
    )
    async for doc in cursor:
        exam_date = (doc.get("extracted_data") or {}).get("exam_date")
        years[str(doc["_id"])] = parse_exam_year(exam_date) or UNDATED_LABEL
    return years


async def questions_per_year(
    questions_collection: AsyncIOMotorCollection, project_id: str, year_by_paper: dict[str, str]
) -> dict[str, int]:
    pipeline = [
        {"$match": {"project_id": project_id}},
        {"$group": {"_id": "$question_paper_id", "count": {"$sum": 1}}},
    ]
    totals: dict[str, int] = {}
    async for row in questions_collection.aggregate(pipeline):
        year = year_by_paper.get(row["_id"], UNDATED_LABEL)
        totals[year] = totals.get(year, 0) + row["count"]
    return totals


async def topic_frequency(
    questions_collection: AsyncIOMotorCollection, project_id: str, metric: str
) -> list[tuple[str, float]]:
    """Ranks topics by "count" (questions attached) or "marks" (total marks
    of questions attached). A question mapped to more than one topic
    contributes fully to each -- see module note above.
    """
    value_expr = {"$sum": 1} if metric == "count" else {"$sum": "$mark"}
    pipeline = [
        {"$match": {"project_id": project_id}},
        {"$unwind": "$topic"},
        {"$group": {"_id": "$topic.topic", "value": value_expr}},
        {"$sort": {"value": -1}},
    ]
    return [(row["_id"], row["value"]) async for row in questions_collection.aggregate(pipeline)]


async def subtopic_frequency(
    questions_collection: AsyncIOMotorCollection, project_id: str, metric: str
) -> list[tuple[str, float]]:
    """Same as `topic_frequency` but ranks subtopics. A question contributes
    fully to every subtopic across every topic it's mapped to.
    """
    value_expr = {"$sum": 1} if metric == "count" else {"$sum": "$mark"}
    pipeline = [
        {"$match": {"project_id": project_id}},
        {"$unwind": "$topic"},
        {"$unwind": "$topic.subtopics"},
        {"$group": {"_id": "$topic.subtopics", "value": value_expr}},
        {"$sort": {"value": -1}},
    ]
    return [(row["_id"], row["value"]) async for row in questions_collection.aggregate(pipeline)]


async def topic_counts_by_paper(
    questions_collection: AsyncIOMotorCollection, project_id: str
) -> list[tuple[str, str, int]]:
    """Returns (question_paper_id, topic, count) rows, one per topic that has
    at least one question attached to it within that paper.
    """
    pipeline = [
        {"$match": {"project_id": project_id}},
        {"$unwind": "$topic"},
        {
            "$group": {
                "_id": {"paper": "$question_paper_id", "topic": "$topic.topic"},
                "count": {"$sum": 1},
            }
        },
    ]
    return [
        (row["_id"]["paper"], row["_id"]["topic"], row["count"])
        async for row in questions_collection.aggregate(pipeline)
    ]


async def topic_distribution_for_paper(
    questions_collection: AsyncIOMotorCollection, question_paper_id: str
) -> list[tuple[str, int]]:
    """Question count per topic within a single paper, using "primary topic
    only" so the values stay meaningful as pie-chart slices. Questions with
    no mapped topic are grouped under "Unallocated".
    """
    pipeline = [
        {"$match": {"question_paper_id": question_paper_id}},
        {
            "$project": {
                "primary_topic": {
                    "$ifNull": [{"$arrayElemAt": ["$topic.topic", 0]}, UNALLOCATED_LABEL]
                }
            }
        },
        {"$group": {"_id": "$primary_topic", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    return [
        (row["_id"], row["count"]) async for row in questions_collection.aggregate(pipeline)
    ]


async def marks_per_paper_by_topic(
    questions_collection: AsyncIOMotorCollection, project_id: str
) -> dict[str, dict[str, float]]:
    """Sums each paper's question marks by "primary topic" (the first topic
    mapped to a question, or "Unallocated" if none) so a paper's per-topic
    marks are additive and sum to its total. Returns
    `{question_paper_id: {topic: marks}}`.
    """
    pipeline = [
        {"$match": {"project_id": project_id}},
        {
            "$project": {
                "question_paper_id": 1,
                "mark": 1,
                "primary_topic": {
                    "$ifNull": [{"$arrayElemAt": ["$topic.topic", 0]}, UNALLOCATED_LABEL]
                },
            }
        },
        {
            "$group": {
                "_id": {"paper": "$question_paper_id", "topic": "$primary_topic"},
                "marks": {"$sum": "$mark"},
            }
        },
    ]
    result: dict[str, dict[str, float]] = {}
    async for row in questions_collection.aggregate(pipeline):
        result.setdefault(row["_id"]["paper"], {})[row["_id"]["topic"]] = row["marks"]
    return result


async def allocation_breakdown_by_paper(
    questions_collection: AsyncIOMotorCollection, project_id: str
) -> dict[str, dict[str, int]]:
    """Per-paper counts split into three mutually exclusive buckets so they
    can be stacked to the paper's total question count.

    Contrast with `allocation_counts_by_paper`: that function's "allocated"
    bucket intentionally includes multi-allocated questions (>=1 topic); this
    one splits "exactly 1 topic" from "2+ topics" so the parts are additive.
    """
    pipeline = [
        {"$match": {"project_id": project_id}},
        {
            "$group": {
                "_id": "$question_paper_id",
                "total": {"$sum": 1},
                "unallocated": {"$sum": {"$cond": [{"$eq": [{"$size": "$topic"}, 0]}, 1, 0]}},
                "single_allocated": {
                    "$sum": {"$cond": [{"$eq": [{"$size": "$topic"}, 1]}, 1, 0]}
                },
                "multi_allocated": {
                    "$sum": {"$cond": [{"$gte": [{"$size": "$topic"}, 2]}, 1, 0]}
                },
            }
        },
    ]
    return {
        row["_id"]: {
            "total": row["total"],
            "unallocated": row["unallocated"],
            "single_allocated": row["single_allocated"],
            "multi_allocated": row["multi_allocated"],
        }
        async for row in questions_collection.aggregate(pipeline)
    }


async def mark_value_distribution(
    questions_collection: AsyncIOMotorCollection, project_id: str
) -> list[tuple[float, int]]:
    pipeline = [
        {"$match": {"project_id": project_id}},
        {"$group": {"_id": "$mark", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    return [(row["_id"], row["count"]) async for row in questions_collection.aggregate(pipeline)]


def format_mark_label(mark: float) -> str:
    return str(int(mark)) if mark == int(mark) else str(mark)
