BBOX_MIN = 0
BBOX_MAX = 1000


def expand_bbox(box_2d: list[int], amount: int) -> list[int]:
    """Expands a normalized `[ymin, xmin, ymax, xmax]` box by `amount` on
    every side, clamped to the valid 0-1000 range.
    """
    ymin, xmin, ymax, xmax = box_2d
    return [
        max(BBOX_MIN, ymin - amount),
        max(BBOX_MIN, xmin - amount),
        min(BBOX_MAX, ymax + amount),
        min(BBOX_MAX, xmax + amount),
    ]


def expand_content_bboxes(content: list[dict], amount: int) -> None:
    """Expands every box_2d in an extracted `content` list, in place."""
    for question in content:
        for box in question["bbox"]:
            box["box_2d"] = expand_bbox(box["box_2d"], amount)
