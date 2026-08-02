import asyncio
import logging

from app.local_extraction_service.doclayout import run_doclayout
from app.local_extraction_service.headers import extract_headers
from app.local_extraction_service.questions import extract_questions
from app.local_extraction_service.reconciliation import reconcile_incomplete_questions
from app.local_extraction_service.schemas import BoxRecord, Question

logger = logging.getLogger(__name__)


def _assemble_content(
    questions: list[Question], box_lookup: dict[str, BoxRecord]
) -> list[dict]:
    """Renames Qwen's per-question fields onto the same shape
    `app.extraction_service.extract.ExamData.content[]` uses
    (`question_number`, `question`, `mark`, `bbox: [{page_index, box_2d}]`),
    plus additive fields (`image_ids`, `incomplete_info`, `incomplete_reason`,
    `confidence`) that ride along unused until they're needed -- see
    `app.local_extraction_service.reconciliation`.
    """
    content = []
    for question in questions:
        bbox = [
            {
                "page_index": box_lookup[image_id].page_index,
                "box_2d": box_lookup[image_id].box_2d,
            }
            for image_id in question.image_ids
            if image_id in box_lookup
        ]
        content.append(
            {
                "question_number": question.question_number,
                "question": question.text,
                "mark": question.marks,
                "bbox": bbox,
                "image_ids": question.image_ids,
                "incomplete_info": question.incomplete_info,
                "incomplete_reason": question.incomplete_reason,
                "confidence": question.confidence,
            }
        )
    return content


async def process_pdf(pdf_bytes: bytes) -> dict:
    """Runs the full DocLayout + Qwen pipeline on one exam paper PDF.

    Returns a dict shaped exactly like
    `app.extraction_service.extract.ExamData.model_dump()`
    (`degree`, `subject_name`, `subject_code`, `exam_date`, `semester`,
    `total_marks`, `content: [{question_number, question, mark, bbox}]`),
    plus additive fields the Gemini pipeline doesn't produce: each `content`
    entry also carries `image_ids`/`incomplete_info`/`incomplete_reason`/
    `confidence`, and a top-level `boxes` list carries every detected box's
    `image_base64` and classified `content_type`/`label`.

    This is the intended swap-in point for
    `app.extraction_service.extract.process_pdf` -- same signature, same
    required output shape.
    """
    boxes = await run_doclayout(pdf_bytes)

    headers, (image_types, raw_questions) = await asyncio.gather(
        extract_headers(boxes), extract_questions(boxes)
    )

    for box in boxes:
        classified = image_types.get(box.temp_id)
        if classified is not None:
            box.content_type = classified.content_type
            box.label = classified.label

    box_lookup = {box.temp_id: box for box in boxes}
    content = _assemble_content(raw_questions, box_lookup)
    content = await reconcile_incomplete_questions(content, boxes)

    return {
        **headers.model_dump(),
        "content": content,
        "boxes": [box.model_dump() for box in boxes],
    }
