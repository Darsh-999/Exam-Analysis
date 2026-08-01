import json
import logging
from pathlib import Path

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)


class TopicMapping(BaseModel):
    topic_id: str = Field(
        description="The short ID string representing the main topic."
    )
    subtopic_ids: list[str] = Field(
        description="A list of short ID strings representing the subtopics."
    )


class QuestionMapping(BaseModel):
    question_id: str = Field(
        description="The short ID string representing the question."
    )
    mappings: list[TopicMapping] = Field(
        description="A list of topic and subtopic mappings associated with this question."
    )


MODEL_NAME = "gemini-3.5-flash"
TEMPERATURE = 0.2

THINKING_LEVEL = "low"

PROMPT_PATH = Path(__file__).parent / "prompt.md"
SYSTEM_INSTRUCTION_PATH = Path(__file__).parent / "sys_instruct.md"

client = genai.Client(api_key=settings.gemini_api_key)


def _load_prompts() -> tuple[str, str]:
    """Read the system instruction and user prompt templates."""
    sys_instruct_text = SYSTEM_INSTRUCTION_PATH.read_text(encoding="utf-8")
    prompt_text = PROMPT_PATH.read_text(encoding="utf-8")

    return sys_instruct_text.strip(), prompt_text.strip()


SYSTEM_INSTRUCTION, USER_PROMPT_TEMPLATE = _load_prompts()


def _build_prompt(topics_and_subtopics: list[dict], questions_batch: list[dict]) -> str:
    return (
        USER_PROMPT_TEMPLATE.replace(
            "{{ topics_and_subtopics }}",
            json.dumps(topics_and_subtopics, ensure_ascii=False),
        )
        .replace(
            "{{ id_to_que_map }}", json.dumps(questions_batch, ensure_ascii=False)
        )
        .replace("{{ nque }}", str(len(questions_batch)))
    )


async def classify_batch(
    topics_and_subtopics: list[dict], questions_batch: list[dict]
) -> list[dict]:
    """Sends one batch of questions plus the full syllabus (topics/subtopics,
    all with short temporary IDs) to Gemini and returns the raw per-question
    topic/subtopic ID mappings, in the same shape as `QuestionMapping`.
    """
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=TEMPERATURE,
        response_mime_type="application/json",
        response_schema=list[QuestionMapping],
    )

    prompt = _build_prompt(topics_and_subtopics, questions_batch)

    logger.info("Sending classification batch to Gemini (%d questions)", len(questions_batch))

    response = await client.aio.models.generate_content(
        model=MODEL_NAME,
        contents=[prompt],
        config=config,
    )

    logger.info("Received Gemini response for classification batch")

    if response.parsed is not None:
        return [mapping.model_dump() for mapping in response.parsed]

    logger.warning(
        "Gemini response had no parsed output; falling back to raw JSON parse"
    )
    return json.loads(response.text)
