import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.database import get_question_papers_collection, get_syllabi_collection
from app.extraction_service.extract import process_pdf as extract_question_paper
from app.schemas import DocumentStatus
from app.topic_extraction_service.extract import process_pdf as extract_syllabus

logger = logging.getLogger(__name__)

# Safety net so a hung Gemini call can't leave a document stuck in
# "extracting" forever.
EXTRACTION_TIMEOUT_SECONDS = 180

# Keeps strong references to in-flight processing tasks so they aren't garbage
# collected mid-run, and lets every uploaded file process concurrently instead
# of queueing one after another.
_running_tasks: set[asyncio.Task] = set()


def schedule(coro) -> None:
    task = asyncio.create_task(coro)
    _running_tasks.add(task)
    task.add_done_callback(_running_tasks.discard)


async def _set_status(
    collection: AsyncIOMotorCollection,
    doc_id: ObjectId,
    doc_status: DocumentStatus,
    error: str | None = None,
    **fields,
) -> None:
    update = {
        "status": doc_status.value,
        "updated_at": datetime.now(timezone.utc),
        **fields,
    }
    if error is not None:
        update["error"] = error
    await collection.update_one({"_id": doc_id}, {"$set": update})


async def process_question_paper(doc_id: ObjectId, file_path: str) -> None:
    """Runs the extraction stage for one exam paper PDF via Gemini.

    On success the document moves to "classifying" (extraction done, the
    not-yet-built classification stage comes next) and stores the raw
    extraction result. On any failure it's marked "failed" with the error.
    """
    collection = get_question_papers_collection()
    logger.info("Question paper extraction started: doc_id=%s", doc_id)
    try:
        pdf_bytes = await asyncio.to_thread(Path(file_path).read_bytes)
        extracted_data = await asyncio.wait_for(
            extract_question_paper(pdf_bytes), timeout=EXTRACTION_TIMEOUT_SECONDS
        )
        await _set_status(
            collection,
            doc_id,
            DocumentStatus.CLASSIFYING,
            extracted_data=extracted_data,
        )
        logger.info("Question paper extraction completed: doc_id=%s", doc_id)
    except asyncio.TimeoutError:
        error = f"Extraction timed out after {EXTRACTION_TIMEOUT_SECONDS}s"
        logger.error("Question paper extraction timed out: doc_id=%s", doc_id)
        await _set_status(collection, doc_id, DocumentStatus.FAILED, error=error)
    except Exception as exc:
        logger.exception("Question paper extraction failed: doc_id=%s", doc_id)
        await _set_status(collection, doc_id, DocumentStatus.FAILED, error=str(exc))


async def process_syllabus(doc_id: ObjectId, file_path: str) -> None:
    """Runs the extraction stage for one syllabus PDF via Gemini.

    On success the document is marked "completed" and stores the raw
    extraction result (syllabi have no classification stage). On any
    failure it's marked "failed" with the error.
    """
    collection = get_syllabi_collection()
    logger.info("Syllabus extraction started: doc_id=%s", doc_id)
    try:
        pdf_bytes = await asyncio.to_thread(Path(file_path).read_bytes)
        extracted_data = await asyncio.wait_for(
            extract_syllabus(pdf_bytes), timeout=EXTRACTION_TIMEOUT_SECONDS
        )
        await _set_status(
            collection, doc_id, DocumentStatus.COMPLETED, extracted_data=extracted_data
        )
        logger.info("Syllabus extraction completed: doc_id=%s", doc_id)
    except asyncio.TimeoutError:
        error = f"Extraction timed out after {EXTRACTION_TIMEOUT_SECONDS}s"
        logger.error("Syllabus extraction timed out: doc_id=%s", doc_id)
        await _set_status(collection, doc_id, DocumentStatus.FAILED, error=error)
    except Exception as exc:
        logger.exception("Syllabus extraction failed: doc_id=%s", doc_id)
        await _set_status(collection, doc_id, DocumentStatus.FAILED, error=str(exc))
