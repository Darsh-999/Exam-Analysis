import json
import logging
from pathlib import Path

from pydantic import BaseModel, Field

from app.local_extraction_service.qwen_client import call_structured

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


class ClassificationBatchResult(BaseModel):
    """Wraps the per-question mappings in an object -- vLLM's structured
    output (like the OpenAI API it mirrors) requires an object at the schema
    root, not a bare array, unlike the Gemini `response_schema` this service
    replaces.
    """

    results: list[QuestionMapping]


PROMPTS_DIR = Path(__file__).parent / "prompts"
SYSTEM_INSTRUCTION = (PROMPTS_DIR / "sys_instruct.md").read_text(encoding="utf-8").strip()
USER_PROMPT_TEMPLATE = (PROMPTS_DIR / "prompt.md").read_text(encoding="utf-8").strip()

MAX_TOKENS = 3000


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
    """Sends one batch of questions plus the full syllabus """
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": _build_prompt(topics_and_subtopics, questions_batch)},
    ]

    logger.info(
        "Sending classification batch to Qwen (%d questions)", len(questions_batch)
    )
    result = await call_structured(messages, ClassificationBatchResult, MAX_TOKENS)
    logger.info("Received Qwen response for classification batch")

    return [mapping.model_dump() for mapping in result.results]
