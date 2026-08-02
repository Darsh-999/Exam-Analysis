import asyncio
import base64
import gc
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import cv2
import fitz  # PyMuPDF
import numpy as np
import torch

from app.config import settings
from app.local_extraction_service.schemas import BoxRecord

logger = logging.getLogger(__name__)

# DocLayout tuning constants, carried over from the DocLayout.py prototype.
DPI = 150
ROW_THRESHOLD = 10                 # pixels; boxes within this y-distance count as one row
WIDTH_EXPANSION_THRESHOLD = 0.3    # fraction of page width -- wide boxes snap to margins
PAGE_MARGIN = 30                   # pixels
DETECTION_CONFIDENCE = 0.2
JPEG_QUALITY = 90

BACKEND_ROOT = Path(__file__).resolve().parents[2]

# Caps concurrent GPU inferences across every PDF being processed at once.
# DocLayout shares its GPU with vLLM, and the underlying model instance isn't
# safe to call from multiple threads concurrently regardless.
_semaphore = asyncio.Semaphore(settings.doclayout_gpu_concurrency)
_model = None
_model_lock = asyncio.Lock()


@dataclass
class _DetBox:
    page: int
    x1: float
    y1: float
    x2: float
    y2: float


def _load_model():
    import doclayout_yolo_slim

    sys.modules.setdefault("doclayout_yolo", doclayout_yolo_slim)
    from doclayout_yolo_slim.models import YOLOv10

    model_path = Path(settings.doclayout_model_path)
    if not model_path.is_absolute():
        model_path = BACKEND_ROOT / model_path
    if not model_path.exists():
        raise FileNotFoundError(f"DocLayout model weights not found at {model_path}")

    logger.info("Loading DocLayout model from %s", model_path)
    model = YOLOv10(model=str(model_path))
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    for m in model.model.modules():
        if hasattr(m, "anchors"):
            m.anchors = m.anchors.to(device)
        if hasattr(m, "strides"):
            m.strides = m.strides.to(device)

    logger.info("DocLayout model loaded on %s", device)
    return model, device


async def _get_model():
    global _model
    if _model is None:
        async with _model_lock:
            if _model is None:
                _model = await asyncio.to_thread(_load_model)
    return _model


def _assign_box_ids(boxes: list[_DetBox]) -> list[tuple[int, _DetBox]]:
    """Orders boxes top-to-bottom, left-to-right per page, with one
    continuous ID counter across the whole document. Adapted unchanged from
    DocLayout.py's `assign_box_ids`.
    """
    pages: dict[int, list[_DetBox]] = {}
    for b in boxes:
        pages.setdefault(b.page, []).append(b)

    ordered: list[tuple[int, _DetBox]] = []
    idx = 1

    for page in sorted(pages.keys()):
        page_boxes = sorted(pages[page], key=lambda b: b.y1)
        rows = []

        for box in page_boxes:
            placed = False
            for row in rows:
                if abs(box.y1 - row["y"]) <= ROW_THRESHOLD:
                    row["boxes"].append(box)
                    n = len(row["boxes"])
                    row["y"] = ((row["y"] * (n - 1)) + box.y1) / n
                    placed = True
                    break
            if not placed:
                rows.append({"y": box.y1, "boxes": [box]})

        rows.sort(key=lambda r: r["y"])

        for row in rows:
            row["boxes"].sort(key=lambda b: b.x1)
            for box in row["boxes"]:
                ordered.append((idx, box))
                idx += 1

    return ordered


def _rasterize_pages(pdf_bytes: bytes) -> list[np.ndarray]:
    page_images = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            pix = page.get_pixmap(dpi=DPI)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR if pix.n == 4 else cv2.COLOR_RGB2BGR)
            page_images.append(img)
    return page_images


def _detect_boxes(model, device, page_images: list[np.ndarray]) -> list[_DetBox]:
    all_boxes: list[_DetBox] = []

    for page_idx, img in enumerate(page_images):
        img_h, img_w = img.shape[:2]
        threshold = img_w * WIDTH_EXPANSION_THRESHOLD

        results = model.predict(
            img, device=device, conf=DETECTION_CONFIDENCE, half=True, verbose=False
        )

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                if (x2 - x1) >= threshold:
                    x1 = PAGE_MARGIN
                    x2 = img_w - PAGE_MARGIN

                # Upper bounds clamp to img_w/img_h (not -1): x2/y2 feed a
                # half-open slice (img[y1:y2, x1:x2]), so clamping to the
                # last valid index would always cut off the final row/column.
                x1 = max(0, min(img_w, x1))
                x2 = max(0, min(img_w, x2))
                y1 = max(0, min(img_h, y1))
                y2 = max(0, min(img_h, y2))

                all_boxes.append(_DetBox(page=page_idx, x1=x1, y1=y1, x2=x2, y2=y2))

    return all_boxes


def _normalize_box_2d(box: _DetBox, img_w: int, img_h: int) -> list[int]:
    """[ymin, xmin, ymax, xmax], integers normalized 0-1000 -- the same
    convention used by app/services/bbox.py and app/services/cropping.py.
    """
    return [
        round(box.y1 / img_h * 1000),
        round(box.x1 / img_w * 1000),
        round(box.y2 / img_h * 1000),
        round(box.x2 / img_w * 1000),
    ]


def _run_sync(model, device, pdf_bytes: bytes) -> list[BoxRecord]:
    page_images = _rasterize_pages(pdf_bytes)

    try:
        all_boxes = _detect_boxes(model, device, page_images)
    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        gc.collect()
        raise RuntimeError("DocLayout GPU out of memory") from None

    ordered = _assign_box_ids(all_boxes)

    records = []
    for idx, box in ordered:
        img = page_images[box.page]
        img_h, img_w = img.shape[:2]
        x1, y1, x2, y2 = map(int, [box.x1, box.y1, box.x2, box.y2])

        crop = img[y1:y2, x1:x2]
        if crop.size == 0:
            continue

        ok, buffer = cv2.imencode(".jpg", crop, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
        if not ok:
            continue

        records.append(
            BoxRecord(
                temp_id=str(idx),
                page_index=box.page,
                box_2d=_normalize_box_2d(box, img_w, img_h),
                image_base64=base64.b64encode(buffer).decode("ascii"),
            )
        )

    return records


async def run_doclayout(pdf_bytes: bytes) -> list[BoxRecord]:
    """Detects and crops every content region in the PDF via DocLayout YOLO,
    returning them in whole-document reading order (top-to-bottom,
    left-to-right per page, continuous across pages) with a stable
    `temp_id` per box.

    Runs on a background thread, serialized by `doclayout_gpu_concurrency`
    since the model shares a GPU with vLLM and isn't safe to call from
    multiple threads at once. Raises a plain `RuntimeError` on GPU OOM (after
    freeing what it can) -- the caller's existing extraction-failure handling
    marks the PDF `failed` instead of crashing the whole process.
    """
    model, device = await _get_model()
    async with _semaphore:
        return await asyncio.to_thread(_run_sync, model, device, pdf_bytes)
