import uuid
from pathlib import Path

import fitz
from fastapi import UploadFile

from app.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".json"}


def is_allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


async def save_upload(project_id: str, file: UploadFile) -> str:
    project_dir = Path(settings.upload_dir) / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = project_dir / stored_name

    contents = await file.read()
    file_path.write_bytes(contents)

    return str(file_path)


def save_pdf_pages(project_id: str, doc_id: str, pdf_path: str) -> list[str]:
    """Renders each page of a PDF to a PNG file and returns their paths.

    Runs synchronously (PyMuPDF is CPU-bound) — call via asyncio.to_thread.
    """
    pages_dir = Path(settings.upload_dir) / project_id / "pages" / doc_id
    pages_dir.mkdir(parents=True, exist_ok=True)

    page_paths = []
    with fitz.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf):
            page_path = pages_dir / f"{page_index}.png"
            page.get_pixmap().save(page_path)
            page_paths.append(str(page_path))

    return page_paths
