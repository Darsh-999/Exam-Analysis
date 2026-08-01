import logging

from app.classification_service.preprocess import SubtopicLookup, TopicLookup

logger = logging.getLogger(__name__)


def resolve_question_mappings(
    llm_results: list[dict],
    topic_lookup: TopicLookup,
    subtopic_lookup: SubtopicLookup,
    doc_id: object,
) -> dict[str, list[dict]]:
    """Converts one batch's raw LLM output (temporary topic/subtopic IDs)
    into the DB-ready `topic` list (subject/topic/subtopic names), keyed by
    the temporary `question_id` used for this classification run.

    Any ID the LLM invents that doesn't exist in the syllabus lookups is
    dropped and logged rather than raised — a hallucinated ID must never
    reach the database, but it also shouldn't discard the rest of an
    otherwise-valid question's mappings.
    """
    resolved: dict[str, list[dict]] = {}

    for item in llm_results:
        question_id = item.get("question_id")
        if question_id is None:
            logger.warning("doc_id=%s classification item missing question_id: %r", doc_id, item)
            continue

        # Keyed by topic_id (not name) so mappings are merged in case the LLM
        # repeats a topic_id across two entries despite being told not to.
        topics_by_id: dict[str, dict] = {}
        for mapping in item.get("mappings", []):
            topic_id = mapping.get("topic_id")
            topic_info = topic_lookup.get(topic_id)
            if topic_info is None:
                logger.error(
                    "doc_id=%s question_id=%s hallucinated topic_id=%r ignored",
                    doc_id, question_id, topic_id,
                )
                continue

            entry = topics_by_id.setdefault(
                topic_id,
                {
                    "subject_name": topic_info["subject_name"],
                    "topic": topic_info["topic"],
                    "subtopics": [],
                },
            )

            for subtopic_id in mapping.get("subtopic_ids", []):
                name = subtopic_lookup.get(subtopic_id)
                if name is None:
                    logger.error(
                        "doc_id=%s question_id=%s hallucinated subtopic_id=%r ignored",
                        doc_id, question_id, subtopic_id,
                    )
                    continue
                if name not in entry["subtopics"]:
                    entry["subtopics"].append(name)

        resolved[question_id] = list(topics_by_id.values())

    return resolved
