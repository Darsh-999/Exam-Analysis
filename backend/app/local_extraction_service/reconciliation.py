from app.local_extraction_service.schemas import BoxRecord


async def reconcile_incomplete_questions(
    content: list[dict], boxes: list[BoxRecord]
) -> list[dict]:
    """Placeholder for a future re-extraction pass.

    Every entry in `content` with `incomplete_info: True` carries an
    `incomplete_reason` list (e.g. `"refers_diagram"`) and the `image_ids` it
    was built from. The eventual implementation will group these by reason,
    build one follow-up Qwen call per group with a different prompt/image set
    (e.g. every box in `boxes` whose `content_type == "diagram"` for
    `"refers_diagram"`), and merge the resolved `image_ids`/text back onto
    the matching question.

    Not implemented yet -- returns `content` unchanged.
    """
    return content
