import logging

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# If a page yields fewer than this many characters of text, it's likely a
# scanned/image-only page with no real text layer -- warn rather than fail,
# since silently dropping a unit's content is worse than a loud warning.
MIN_CHARS_PER_PAGE_WARNING = 20


def extract_page_texts(pdf_bytes: bytes) -> list[str]:
    """Extracts the embedded text layer from every page, in page order."""
    pages = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            pages.append(page.get_text("text").strip())

    for i, text in enumerate(pages, start=1):
        if len(text) < MIN_CHARS_PER_PAGE_WARNING:
            logger.warning(
                "Syllabus page %d has almost no extractable text (%d chars) -- "
                "likely a scanned image rather than real text, so this page's "
                "content will be missed.",
                i,
                len(text),
            )
    return pages


def build_document_text(page_texts: list[str]) -> str:
    """Joins page texts with explicit page markers so the model can reason
    about ordering and cross-page continuity.
    """
    labeled_pages = [
        f"--- Page {i} ---\n{text}" for i, text in enumerate(page_texts, start=1)
    ]
    return "\n\n".join(labeled_pages)
