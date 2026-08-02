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
    output (like the OpenAI API it mirrors) requires an object at the
    schema root, not a bare array.
    """

    results: list[QuestionMapping]


PROMPTS_DIR = Path(__file__).parent / "prompts"
SYSTEM_INSTRUCTION = (PROMPTS_DIR / "sys_instruct.md").read_text(encoding="utf-8").strip()
USER_PROMPT_TEMPLATE = (PROMPTS_DIR / "prompt.md").read_text(encoding="utf-8").strip()

MAX_TOKENS = 3000


def _strip_subtopics(topics_and_subtopics: list[dict]) -> list[dict]:
    """Returns a copy of `topics_and_subtopics` with every topic's subtopics
    zeroed out, so the model only ever sees topics to allocate against.

    Built as a fresh copy (not an in-place mutation) because the caller
    shares one `topics_and_subtopics` list across all batches of a document,
    running concurrently via asyncio.gather.
    """
    return [
        {
            **subject,
            "content": [
                {**topic, "subtopics": []} for topic in subject.get("content", [])
            ],
        }
        for subject in topics_and_subtopics
    ]


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
    """Sends one batch of questions plus the full syllabus.

    Subtopics are stripped from the syllabus before it's sent -- the model
    is only asked to allocate topics, not subtopics.
    """
    topics_only = _strip_subtopics(topics_and_subtopics)
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": _build_prompt(topics_only, questions_batch)},
    ]

    logger.info(
        "Sending classification batch to Qwen (%d questions)", len(questions_batch)
    )
    logger.debug(
        "Classification request payload: topics_and_subtopics=%s questions_batch=%s",
        topics_only, questions_batch,
    )
    result = await call_structured(messages, ClassificationBatchResult, MAX_TOKENS)
    logger.info("Received Qwen response for classification batch")

    return [mapping.model_dump() for mapping in result.results]
