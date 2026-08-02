import logging
from pathlib import Path

from app.config import settings
from app.local_extraction_service.image_compose import (
    decode_base64_image,
    encode_base64_jpeg,
    stack_vertically,
)
from app.local_extraction_service.qwen_client import call_structured
from app.local_extraction_service.schemas import BoxRecord, ExamHeaders

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
SYSTEM_INSTRUCTION = (PROMPTS_DIR / "header_sys_instruct.md").read_text(encoding="utf-8").strip()
USER_PROMPT = (PROMPTS_DIR / "header_prompt.md").read_text(encoding="utf-8").strip()

MAX_TOKENS = 300

EMPTY_HEADERS = ExamHeaders(
    degree="", subject_name="", subject_code="", exam_date="", semester=0, total_marks=0
)


def _build_composite_images(boxes: list[BoxRecord]) -> list[str]:
    """Groups boxes into chunks of `settings.header_boxes_per_image` and joins
    each chunk into one composite image (see HEADER_IMAGE_DESIGN.md). Returns
    each composite as base64 JPEG, in order.
    """
    chunk_size = settings.header_boxes_per_image
    composites = []
    for i in range(0, len(boxes), chunk_size):
        chunk = boxes[i : i + chunk_size]
        images = [decode_base64_image(box.image_base64) for box in chunk]
        composites.append(encode_base64_jpeg(stack_vertically(images)))
    return composites


async def extract_headers(boxes: list[BoxRecord]) -> ExamHeaders:
    """Extracts page-header metadata (degree, subject, exam date, ...) from
    the first `settings.header_bbox_limit` boxes, which is where this
    information always lives on the first page.
    """
    header_boxes = boxes[: settings.header_bbox_limit]
    if not header_boxes:
        return EMPTY_HEADERS

    composite_images = _build_composite_images(header_boxes)

    content = [{"type": "text", "text": USER_PROMPT}]
    for i, image_b64 in enumerate(composite_images, start=1):
        content.append(
            {"type": "text", "text": f"Header image {i} of {len(composite_images)}"}
        )
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
            }
        )

    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": content},
    ]

    logger.info(
        "Sending header extraction request to Qwen (%d composite image(s))",
        len(composite_images),
    )
    try:
        return await call_structured(messages, ExamHeaders, MAX_TOKENS)
    except Exception:
        # Mirrors extract_questions' per-batch resilience: a failed header
        # call (timeout, malformed JSON, ...) must not take down the whole
        # PDF's extraction along with it -- the questions themselves are
        # extracted independently and are worth keeping.
        logger.exception("Header extraction failed -- falling back to empty headers")
        return EMPTY_HEADERS
