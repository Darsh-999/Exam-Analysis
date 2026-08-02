import asyncio
import logging
from datetime import datetime, timezone

from bson import ObjectId
from pymongo import UpdateOne

from app.classification_service.postprocess import resolve_question_mappings
from app.classification_service.preprocess import (
    assign_question_ids,
    assign_topic_ids,
    chunked,
)
from app.config import settings
from app.database import (
    get_question_papers_collection,
    get_questions_collection,
    get_syllabi_collection,
)
from app.local_classification_service.classify import classify_batch
from app.schemas import DocumentStatus

logger = logging.getLogger(__name__)

CLASSIFICATION_TIMEOUT_SECONDS = 600

_running_tasks: set[asyncio.Task] = set()


def _schedule(coro) -> None:
    task = asyncio.create_task(coro)
    _running_tasks.add(task)
    task.add_done_callback(_running_tasks.discard)


async def _set_status(collection, doc_id: ObjectId, doc_status: DocumentStatus, error: str | None = None) -> None:
    update = {"status": doc_status.value, "updated_at": datetime.now(timezone.utc)}
    if error is not None:
        update["error"] = error
    await collection.update_one({"_id": doc_id}, {"$set": update})


async def _syllabi_ready(project_id: str) -> bool:
    """All syllabi in the project must have finished processing
    """
    syllabi = get_syllabi_collection()
    total = await syllabi.count_documents({"project_id": project_id})
    if total == 0:
        return False
    completed = await syllabi.count_documents(
        {"project_id": project_id, "status": DocumentStatus.COMPLETED.value}
    )
    return completed == total


async def maybe_start_classification(project_id: str) -> None:
    """Looks for question papers in this project waiting on classification

    Meant to be called both right after a question paper finishes
    extraction and right after a syllabus finishes processing
    """
    if not await _syllabi_ready(project_id):
        return

    collection = get_question_papers_collection()
    cursor = collection.find(
        {
            "project_id": project_id,
            "status": DocumentStatus.CLASSIFYING.value,
            "classification_claimed_at": None,
        },
        {"_id": 1},
    )
    async for doc in cursor:
        claimed = await collection.find_one_and_update(
            {
                "_id": doc["_id"],
                "status": DocumentStatus.CLASSIFYING.value,
                "classification_claimed_at": None,
            },
            {"$set": {"classification_claimed_at": datetime.now(timezone.utc)}},
        )
        if claimed is not None:
            _schedule(classify_question_paper(doc["_id"], project_id))


async def _classify_batch_safe(
    batch: list[dict], topics_and_subtopics: list[dict], doc_id: ObjectId
) -> list[dict]:
    """Runs one batch through the local Qwen model (via vLLM), turning any
    failure (timeout, connection error, malformed response) into an empty
    result instead of raising
    """
    try:
        return await asyncio.wait_for(
            classify_batch(topics_and_subtopics, batch),
            timeout=CLASSIFICATION_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.error(
            "Classification batch timed out after %ss -- falling back to default "
            "(no topics assigned) for this batch: doc_id=%s batch_size=%d "
            "topics_count=%d questions=%s",
            CLASSIFICATION_TIMEOUT_SECONDS, doc_id, len(batch),
            len(topics_and_subtopics), batch,
        )
    except Exception:
        logger.exception(
            "Classification batch failed -- falling back to default (no topics "
            "assigned) for this batch: doc_id=%s batch_size=%d topics_count=%d "
            "questions=%s",
            doc_id, len(batch), len(topics_and_subtopics), batch,
        )
    return []


async def classify_question_paper(doc_id: ObjectId, project_id: str) -> None:
    """Runs the classification stage for one exam paper: maps each of its
    questions to syllabus topics/subtopics in concurrent batches, and 
    writes the results onto each question's `topic` field.

    """
    logger.info("Classification started: doc_id=%s", doc_id)
    question_papers = get_question_papers_collection()
    questions_collection = get_questions_collection()

    try:
        syllabi_docs = [
            doc
            async for doc in get_syllabi_collection().find(
                {"project_id": project_id, "status": DocumentStatus.COMPLETED.value}
            )
        ]
        topics_and_subtopics, topic_lookup, subtopic_lookup = assign_topic_ids(syllabi_docs)

        question_docs = [
            doc
            async for doc in questions_collection.find(
                {"question_paper_id": str(doc_id)}
            )
        ]

        if not topics_and_subtopics or not question_docs:
            logger.warning(
                "Nothing to classify: doc_id=%s topics=%d questions=%d",
                doc_id, len(topics_and_subtopics), len(question_docs),
            )
            await _set_status(question_papers, doc_id, DocumentStatus.COMPLETED)
            return

        prompt_questions, id_map = assign_question_ids(question_docs)
        batches = chunked(prompt_questions, settings.classification_batch_size)

        batch_results = await asyncio.gather(
            *(
                _classify_batch_safe(batch, topics_and_subtopics, doc_id)
                for batch in batches
            )
        )

        updates = []
        seen_ids: set[str] = set()
        for llm_results in batch_results:
            resolved = resolve_question_mappings(llm_results, topic_lookup, subtopic_lookup, doc_id)
            for temp_id, topics_out in resolved.items():
                mongo_id = id_map.get(temp_id)
                if mongo_id is None:
                    logger.error(
                        "doc_id=%s hallucinated question_id=%r ignored (mapped "
                        "topics discarded: %s)",
                        doc_id, temp_id, topics_out,
                    )
                    continue
                seen_ids.add(temp_id)
                if topics_out:
                    updates.append(UpdateOne({"_id": mongo_id}, {"$set": {"topic": topics_out}}))

        missed = set(id_map) - seen_ids
        if missed:
            logger.warning(
                "doc_id=%s LLM skipped %d of %d question(s) -- these keep their "
                "default (no topic assigned): missing_question_ids=%s",
                doc_id, len(missed), len(id_map), sorted(missed),
            )

        if updates:
            await questions_collection.bulk_write(updates, ordered=False)

        await _set_status(question_papers, doc_id, DocumentStatus.COMPLETED)
        logger.info("Classification completed: doc_id=%s", doc_id)
    except Exception as exc:
        logger.exception(
            "Classification failed: doc_id=%s project_id=%s", doc_id, project_id
        )
        await _set_status(question_papers, doc_id, DocumentStatus.FAILED, error=str(exc))
