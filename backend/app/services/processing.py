import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.config import settings
from app.database import (
    get_question_papers_collection,
    get_questions_collection,
    get_syllabi_collection,
)
from app.extraction_service.extract import process_pdf as extract_question_paper
from app.schemas import DocumentStatus
from app.services.classification import maybe_start_classification
from app.services.bbox import expand_content_bboxes
from app.services.cropping import build_cropped_image
from app.topic_extraction_service.extract import process_pdf as extract_syllabus

logger = logging.getLogger(__name__)

# Safety net so a hung call can't leave a document stuck in
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


async def _save_questions(
    project_id: str, doc_id: ObjectId, page_paths: list[str], content: list[dict]
) -> None:
    """Inserts one `questions` doc per extracted question and stamps each
    entry in `content` with the new question's id, for cross-referencing.
    """
    questions_collection = get_questions_collection()
    for question in content:
        cropped_image = await asyncio.to_thread(
            build_cropped_image, question["bbox"], page_paths
        )
        question_doc = {
            "project_id": project_id,
            "question_paper_id": str(doc_id),
            "question_number": question["question_number"],
            "question": question["question"],
            "mark": question["mark"],
            "bbox": question["bbox"],
            "cropped_image": cropped_image,
            "topic": [],
            "created_at": datetime.now(timezone.utc),
        }
        result = await questions_collection.insert_one(question_doc)
        question["question_id"] = str(result.inserted_id)


async def process_question_paper(
    doc_id: ObjectId, file_path: str, project_id: str, page_paths: list[str]
) -> None:
    """Runs the extraction stage for one exam paper PDF.

    On success, each extracted question is saved as its own doc in the
    `questions` collection (with its cropped image), the document moves to
    "classifying", and the raw extraction result is stored too. Classification
    is then kicked off immediately if every syllabus in the project has
    already finished processing; otherwise it stays "classifying" until the
    last syllabus completes and triggers it from the other end (see
    `process_syllabus`). On any extraction failure the document is marked
    "failed" with the error.
    """
    collection = get_question_papers_collection()
    logger.info("Question paper extraction started: doc_id=%s", doc_id)
    try:
        pdf_bytes = await asyncio.to_thread(Path(file_path).read_bytes)
        extracted_data = await asyncio.wait_for(
            extract_question_paper(pdf_bytes), timeout=EXTRACTION_TIMEOUT_SECONDS
        )
        expand_content_bboxes(extracted_data["content"], settings.bbox_expansion)
        await _save_questions(project_id, doc_id, page_paths, extracted_data["content"])
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
        return
    except Exception as exc:
        logger.exception("Question paper extraction failed: doc_id=%s", doc_id)
        await _set_status(collection, doc_id, DocumentStatus.FAILED, error=str(exc))
        return

    # Extraction succeeded and the document is already "classifying" at this
    # point; a failure here (e.g. a transient DB error) must not be allowed
    # to overwrite that with "failed" -- it's logged and left for the next
    # trigger (a syllabus completing) to retry instead.
    try:
        await maybe_start_classification(project_id)
    except Exception:
        logger.exception("Failed to check/start classification: doc_id=%s", doc_id)


async def process_syllabus(doc_id: ObjectId, file_path: str, project_id: str) -> None:
    """Runs the extraction stage for one syllabus PDF.

    On success the document is marked "completed" and stores the raw
    extraction result (syllabi have no classification stage of their own).
    Since every syllabus in the project must be "completed" before any
    question paper can be classified, this also checks whether this was the
    last syllabus the project was waiting on and, if so, kicks off
    classification for any question papers left pending (see
    `process_question_paper`). On any failure the document is marked
    "failed" with the error.
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
        return
    except Exception as exc:
        logger.exception("Syllabus extraction failed: doc_id=%s", doc_id)
        await _set_status(collection, doc_id, DocumentStatus.FAILED, error=str(exc))
        return

    try:
        await maybe_start_classification(project_id)
    except Exception:
        logger.exception("Failed to check/start classification: doc_id=%s", doc_id)
