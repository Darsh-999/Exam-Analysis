import asyncio
import logging
from pathlib import Path

from app.config import settings
from app.local_extraction_service.qwen_client import call_structured
from app.local_extraction_service.schemas import BatchExtraction, BoxRecord, ImageRecord, Question

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
SYSTEM_INSTRUCTION = (PROMPTS_DIR / "question_sys_instruct.md").read_text(encoding="utf-8").strip()
USER_PROMPT = (PROMPTS_DIR / "question_prompt.md").read_text(encoding="utf-8").strip()

MAX_TOKENS = 3000

EMPTY_BATCH = BatchExtraction(images=[], questions=[])


def _chunk(boxes: list[BoxRecord], size: int) -> list[list[BoxRecord]]:
    return [boxes[i : i + size] for i in range(0, len(boxes), size)]


def _build_messages(batch: list[BoxRecord]) -> list[dict]:
    content = [{"type": "text", "text": USER_PROMPT}]
    for box in batch:
        content.append({"type": "text", "text": f"ImageID: {box.temp_id}"})
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{box.image_base64}"},
            }
        )
    return [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": content},
    ]


async def _extract_batch_safe(batch: list[BoxRecord]) -> BatchExtraction:
    """Runs one batch of boxes through Qwen, turning any failure (timeout,
    connection error, malformed response) into an empty result instead of
    raising, so one bad batch can't stop the rest of the PDF's questions
    from being extracted.
    """
    try:
        return await call_structured(_build_messages(batch), BatchExtraction, MAX_TOKENS)
    except Exception:
        logger.exception(
            "Question batch failed (image_ids=%s)", [box.temp_id for box in batch]
        )
        return EMPTY_BATCH


async def extract_questions(
    boxes: list[BoxRecord],
) -> tuple[dict[str, ImageRecord], list[Question]]:
    """Extracts every question across the whole ordered box list, in
    concurrent batches of `settings.question_batch_size` consecutive boxes.

    Returns a `temp_id -> ImageRecord` lookup (every box's classified
    content_type/label) plus the flattened list of questions found, in batch
    order.
    """
    batches = _chunk(boxes, settings.question_batch_size)

    logger.info(
        "Extracting questions in %d batch(es) of up to %d boxes",
        len(batches),
        settings.question_batch_size,
    )
    results = await asyncio.gather(*(_extract_batch_safe(batch) for batch in batches))

    image_lookup: dict[str, ImageRecord] = {}
    questions: list[Question] = []
    for result in results:
        for image in result.images:
            image_lookup[image.image_id] = image
        questions.extend(result.questions)

    return image_lookup, questions
