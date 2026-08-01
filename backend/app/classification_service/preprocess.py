from bson import ObjectId

TopicLookup = dict[str, dict]
SubtopicLookup = dict[str, str]


def assign_topic_ids(
    syllabi_docs: list[dict],
) -> tuple[list[dict], TopicLookup, SubtopicLookup]:
    """Builds the prompt-ready `topics_and_subtopics` array (short, globally
    unique IDs in place of names) plus lookup tables to resolve those IDs
    back to their original names afterwards.

    Topic IDs are assigned as a single running counter across every syllabus
    in the project, so no ID repeats anywhere in the output. Subtopic IDs are
    `"{topic_id}-{n}"`, which stay unique for the same reason.
    """
    topics_and_subtopics: list[dict] = []
    topic_lookup: TopicLookup = {}
    subtopic_lookup: SubtopicLookup = {}
    topic_counter = 0

    for syllabus in syllabi_docs:
        extracted = syllabus.get("extracted_data") or {}
        subject_name = extracted.get("subject_name", "")
        content_out = []

        for module in extracted.get("content", []):
            topic_counter += 1
            topic_id = str(topic_counter)
            topic_name = module.get("topic", "")

            subtopics_out = []
            for i, subtopic_name in enumerate(module.get("subtopics", []), start=1):
                subtopic_id = f"{topic_id}-{i}"
                subtopics_out.append({subtopic_id: subtopic_name})
                subtopic_lookup[subtopic_id] = subtopic_name

            content_out.append(
                {"topic": topic_name, "topic_id": topic_id, "subtopics": subtopics_out}
            )
            topic_lookup[topic_id] = {"subject_name": subject_name, "topic": topic_name}

        topics_and_subtopics.append({"subject_name": subject_name, "content": content_out})

    return topics_and_subtopics, topic_lookup, subtopic_lookup


def assign_question_ids(question_docs: list[dict]) -> tuple[list[dict], dict[str, ObjectId]]:
    """Builds the prompt-ready question list (short, sequential IDs in place
    of Mongo ObjectIds, which are too complex and invite LLM hallucination)
    plus a lookup to map those IDs back to the originating Mongo `_id`.
    """
    prompt_questions: list[dict] = []
    id_map: dict[str, ObjectId] = {}

    for i, question in enumerate(question_docs, start=1):
        temp_id = str(i)
        prompt_questions.append({"question_id": temp_id, "question": question["question"]})
        id_map[temp_id] = question["_id"]

    return prompt_questions, id_map


def chunked(items: list[dict], size: int) -> list[list[dict]]:
    return [items[i : i + size] for i in range(0, len(items), size)]
