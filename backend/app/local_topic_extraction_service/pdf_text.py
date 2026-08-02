import logging
import re

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# If a page yields fewer than this many characters of text, it's likely a
# scanned/image-only page with no real text layer -- warn rather than fail,
# since silently dropping a unit's content is worse than a loud warning.
MIN_CHARS_PER_PAGE_WARNING = 20

# A line repeated on at least this many pages is almost certainly a
# header/footer (institution name, page number, running title) rather than
# syllabus content -- it's dead weight on the token budget, so it's stripped
# before the text ever reaches the model.
MIN_PAGES_FOR_BOILERPLATE_LINE = 3

_WHITESPACE_RUN = re.compile(r"[ \t]{2,}")
_BLANK_LINE_RUN = re.compile(r"\n{3,}")


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


def _strip_repeated_boilerplate(page_texts: list[str]) -> list[str]:
    """Drops lines that recur verbatim across many pages (headers, footers,
    running titles). These carry no per-unit information but get re-sent to
    the model once per page, so removing them is a pure token-budget win.
    """
    if len(page_texts) < MIN_PAGES_FOR_BOILERPLATE_LINE:
        return page_texts

    line_page_counts: dict[str, int] = {}
    for text in page_texts:
        for line in {ln.strip() for ln in text.splitlines() if ln.strip()}:
            line_page_counts[line] = line_page_counts.get(line, 0) + 1

    boilerplate = {
        line
        for line, count in line_page_counts.items()
        if count >= MIN_PAGES_FOR_BOILERPLATE_LINE
    }
    if not boilerplate:
        return page_texts

    return [
        "\n".join(ln for ln in text.splitlines() if ln.strip() not in boilerplate)
        for text in page_texts
    ]


def _collapse_whitespace(text: str) -> str:
    """Collapses runs of spaces/tabs and excess blank lines left over from
    column-based layouts. The model already parses table-like content "by
    proximity and context, not exact alignment", so this loses no signal.
    """
    text = _WHITESPACE_RUN.sub(" ", text)
    return _BLANK_LINE_RUN.sub("\n\n", text)


def build_document_text(page_texts: list[str]) -> str:
    """Joins page texts with explicit page markers so the model can reason
    about ordering and cross-page continuity.
    """
    page_texts = _strip_repeated_boilerplate(page_texts)
    labeled_pages = [
        f"--- Page {i} ---\n{_collapse_whitespace(text)}"
        for i, text in enumerate(page_texts, start=1)
    ]
    return "\n\n".join(labeled_pages)
