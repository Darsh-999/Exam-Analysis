"""Read-side helpers shared by the analytics/listing routers.

These compute counts and joins at query time rather than denormalizing data
(e.g. subject name onto each question) at write time, so they work correctly
against documents that were already processed before these endpoints existed.
"""

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
