import base64
from io import BytesIO

from PIL import Image

# White gap between stacked crops when a question spans multiple boxes/pages.
STACK_PADDING = 10


def build_cropped_image(bbox_list: list[dict], page_paths: list[str]) -> str:
    """Crops each bbox out of its page image and stacks the crops vertically.

    Each bbox's `box_2d` is `[ymin, xmin, ymax, xmax]`, integers normalized to
    0-1000 (as produced by the extraction step). Returns a base64-encoded PNG,
    or "" if no crop could be made (e.g. missing page images).
    """
    crops = []
    for box in bbox_list:
        page_index = box["page_index"]
        if page_index >= len(page_paths):
            continue
        page_image = Image.open(page_paths[page_index])
        crops.append(_crop_normalized(page_image, box["box_2d"]))

    if not crops:
        return ""

    stacked = crops[0] if len(crops) == 1 else _stack_vertically(crops)
    return _to_base64_png(stacked)


def _crop_normalized(image: Image.Image, box_2d: list[int]) -> Image.Image:
    width, height = image.size
    ymin, xmin, ymax, xmax = box_2d
    left = xmin / 1000 * width
    top = ymin / 1000 * height
    right = xmax / 1000 * width
    bottom = ymax / 1000 * height
    return image.crop((left, top, right, bottom))


def _stack_vertically(images: list[Image.Image]) -> Image.Image:
    width = max(image.width for image in images)
    height = sum(image.height for image in images) + STACK_PADDING * (len(images) - 1)

    stacked = Image.new("RGB", (width, height), "white")
    y = 0
    for image in images:
        stacked.paste(image, (0, y))
        y += image.height + STACK_PADDING

    return stacked


def _to_base64_png(image: Image.Image) -> str:
    buffer = BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")
