import base64
from io import BytesIO

from PIL import Image, ImageDraw

# Visual separation between crops joined into one composite image -- see
# HEADER_IMAGE_DESIGN.md for why.
PADDING = 12
SEPARATOR_HEIGHT = 4
SEPARATOR_COLOR = (200, 200, 200)

JPEG_QUALITY = 90


def decode_base64_image(image_base64: str) -> Image.Image:
    return Image.open(BytesIO(base64.b64decode(image_base64)))


def encode_base64_jpeg(image: Image.Image) -> str:
    buffer = BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=JPEG_QUALITY)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def stack_vertically(images: list[Image.Image]) -> Image.Image:
    """Joins crops into one image, top-to-bottom in the given order,
    left-aligned on a common white canvas, with padding around each crop and
    a thin gray rule between consecutive crops so the model doesn't read
    across a crop boundary as continuous content.
    """
    if len(images) == 1:
        return images[0]

    width = max(image.width for image in images)
    height = (
        sum(image.height for image in images)
        + PADDING * 2 * len(images)
        + SEPARATOR_HEIGHT * (len(images) - 1)
    )

    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)

    y = 0
    for i, image in enumerate(images):
        y += PADDING
        canvas.paste(image, (0, y))
        y += image.height + PADDING
        if i < len(images) - 1:
            draw.rectangle([(0, y), (width, y + SEPARATOR_HEIGHT)], fill=SEPARATOR_COLOR)
            y += SEPARATOR_HEIGHT

    return canvas
