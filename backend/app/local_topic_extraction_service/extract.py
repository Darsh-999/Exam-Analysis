import asyncio
import logging
from pathlib import Path

from app.config import settings
from app.local_extraction_service.qwen_client import call_structured
from app.local_topic_extraction_service.pdf_text import build_document_text, extract_page_texts
from app.local_topic_extraction_service.schemas import SyllabusExtraction

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    (Path(__file__).parent / "prompts" / "sys_instruct.md").read_text(encoding="utf-8").strip()
)

# Never request more output than this, even when a tiny syllabus leaves
# plenty of the context window spare.
MAX_TOKENS_CEILING = 6144

# Never request less than this -- below this a syllabus with any real
# content wouldn't have room to finish.
MIN_TOKENS_FLOOR = 512

# vLLM rejects a request outright once prompt + max_tokens exceeds the
# server's context window, and a fixed max_tokens either wastes headroom on
# short syllabi or truncates output on long ones. ~4 chars/token is a rough
# but serviceable estimate for English text -- it only needs to be good
# enough to pick a safe ceiling, not exact.
CHARS_PER_TOKEN_ESTIMATE = 4


def _estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN_ESTIMATE + 1


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

    document_text = build_document_text(page_texts)
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": document_text},
    ]

    prompt_tokens_estimate = _estimate_tokens(SYSTEM_INSTRUCTION) + _estimate_tokens(document_text)
    max_tokens = max(
        MIN_TOKENS_FLOOR,
        min(
            MAX_TOKENS_CEILING,
            settings.vllm_max_context_tokens - prompt_tokens_estimate,
        ),
    )

    logger.info(
        "Sending syllabus PDF to Qwen (%d page(s), ~%d prompt tokens, max_tokens=%d)",
        len(page_texts), prompt_tokens_estimate, max_tokens,
    )
    result = await call_structured(messages, SyllabusExtraction, max_tokens)
    logger.info("Received Qwen response for syllabus PDF")

    return result.model_dump()
