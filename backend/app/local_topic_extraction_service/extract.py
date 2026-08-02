import asyncio
import logging
from pathlib import Path

from app.local_extraction_service.qwen_client import call_structured
from app.local_topic_extraction_service.pdf_text import build_document_text, extract_page_texts
from app.local_topic_extraction_service.schemas import SyllabusExtraction

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    (Path(__file__).parent / "prompts" / "sys_instruct.md").read_text(encoding="utf-8").strip()
)

# Syllabi can have many units; give the model room to finish.
MAX_TOKENS = 4096


async def process_pdf(pdf_bytes: bytes) -> dict:
    """Runs the text-based Qwen pipeline on one syllabus PDF.

    Returns a dict with `degree`, `subject_name`, `subject_code`,
    `semester`, `total_marks`, and
    `content: [{topic, subtopics, weightage, hours}]`. Raises on any failure
    (no extractable text, vLLM timeout/error, malformed output) -- the
    caller's existing extraction-failure handling marks the syllabus
    `failed` instead of crashing the whole process.
    """
    # PyMuPDF is a synchronous C extension -- run it off the event loop so one
    # PDF's parsing can't stall every other concurrent request/task.
    page_texts = await asyncio.to_thread(extract_page_texts, pdf_bytes)
    if not page_texts:
        raise ValueError("No pages found in syllabus PDF")

    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": build_document_text(page_texts)},
    ]

    logger.info("Sending syllabus PDF to Qwen (%d page(s))", len(page_texts))
    result = await call_structured(messages, SyllabusExtraction, MAX_TOKENS)
    logger.info("Received Qwen response for syllabus PDF")

    return result.model_dump()
