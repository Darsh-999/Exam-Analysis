import json
import logging
from pathlib import Path

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)


class ModuleContent(BaseModel):
    topic: str = Field(description="Name of the Unit/Module, no trailing punctuation")
    subtopics: list[str] = Field(
        description="List of individual topics/strings covered in this module"
    )
    weightage: int = Field(description="Weightage or marks allocated to this module")
    hours: int = Field(description="Number of hours allocated to this module")


class SyllabusSchema(BaseModel):
    degree: str = Field(
        description="Degree name. Must be from a predefined list, or 'Other', or 'Not Mentioned'"
    )
    subject_name: str = Field(description="Name of the subject")
    subject_code: str = Field(description="Official code for the subject")
    semester: int = Field(description="Semester number")
    total_marks: int = Field(description="Total maximum marks for the subject")
    content: list[ModuleContent] = Field(
        description="List of units/modules that make up the syllabus content"
    )


MODEL_NAME = "gemini-3.5-flash"
TEMPERATURE = 0.2

THINKING_LEVEL = "low"

SYSTEM_INSTRUCTION_PATH = Path(__file__).parent / "sys_instruct.md"

client = genai.Client(api_key=settings.gemini_api_key)


def _load_prompts() -> tuple[str, str]:
    """Read the system instruction and user prompt."""
    sys_instruct_text = SYSTEM_INSTRUCTION_PATH.read_text(encoding="utf-8")

    return sys_instruct_text.strip()


SYSTEM_INSTRUCTION = _load_prompts()


async def process_pdf(pdf_bytes: bytes) -> dict:
    """
    Sends one PDF to Gemini inline and returns the parsed structured JSON output.
    """

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=TEMPERATURE,
        response_mime_type="application/json",
        response_schema=SyllabusSchema,
    )

    pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")

    logger.info("Sending syllabus PDF to Gemini (%d bytes)", len(pdf_bytes))

    response = await client.aio.models.generate_content(
        model=MODEL_NAME,
        contents=[pdf_part],
        config=config,
    )

    logger.info("Received Gemini response for syllabus PDF")

    if response.parsed:
        return response.parsed.model_dump()

    logger.warning(
        "Gemini response had no parsed output; falling back to raw JSON parse"
    )
    return json.loads(response.text)
