import json
import logging
from pathlib import Path

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)


class BoundingBox(BaseModel):
    page_index: int = Field(
        description="The index of the page where the question is located."
    )
    box_2d: list[int] = Field(
        description="Bounding box coordinates [y_min, x_min, y_max, x_max] or similar.",
        min_length=4,
        max_length=4,
    )


class QuestionContent(BaseModel):
    question_number: str = Field(description="The question identifier, e.g., '1(a)'.")
    question: str = Field(description="plain text, no LaTeX")
    mark: float = Field(description="The marks allocated for the question.")
    bbox: list[BoundingBox] = Field(
        description="List of bounding boxes specifying where this question appears."
    )


class ExamData(BaseModel):
    degree: str = Field(
        description='raw text as seen, no semester info; "" if not determined'
    )
    subject_name: str = Field(description='raw text as seen; "" if not determined')
    subject_code: str = Field(description='raw text as seen; "" if not determined')
    exam_date: str = Field(description='YYYY/MM/DD; "" if not determined')
    semester: int = Field(description="The semester number as an integer.")
    total_marks: int = Field(description="The total marks for the exam.")
    content: list[QuestionContent] = Field(
        description="A list containing all the extracted questions."
    )


MODEL_NAME = "gemini-3.5-flash"
TEMPERATURE = 0.2

THINKING_LEVEL = "low"

PROMPT_PATH = Path(__file__).parent / "prompt.md"
SYSTEM_INSTRUCTION_PATH = Path(__file__).parent / "sys_instruct.md"

client = genai.Client(api_key=settings.gemini_api_key)


def _load_prompts() -> tuple[str, str]:
    """Read the system instruction and user prompt."""
    sys_instruct_text = SYSTEM_INSTRUCTION_PATH.read_text(encoding="utf-8")
    prompt_text = PROMPT_PATH.read_text(encoding="utf-8")

    return sys_instruct_text.strip(), prompt_text.strip()


SYSTEM_INSTRUCTION, USER_PROMPT = _load_prompts()


async def process_pdf(pdf_bytes: bytes) -> dict:
    """
    Sends one PDF to Gemini inline and returns the parsed structured JSON output.
    """
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=TEMPERATURE,
        response_mime_type="application/json",
        response_schema=ExamData,
    )

    pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")

    logger.info("Sending exam paper PDF to Gemini (%d bytes)", len(pdf_bytes))

    response = await client.aio.models.generate_content(
        model=MODEL_NAME,
        contents=[pdf_part, USER_PROMPT],
        config=config,
    )

    logger.info("Received Gemini response for exam paper PDF")

    if response.parsed:
        return response.parsed.model_dump()

    logger.warning(
        "Gemini response had no parsed output; falling back to raw JSON parse"
    )
    return json.loads(response.text)
