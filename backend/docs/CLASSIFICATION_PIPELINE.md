# Question Paper Classification Pipeline

This document explains, in plain language, everything that happens from the
moment a user uploads a PDF to the moment each question has topics and
subtopics attached to it. It also explains *why* things were built the way
they were, so future debugging doesn't require re-reading all the code from
scratch.

It is written for the classification stage specifically (the part built in
this session), but it walks through the whole pipeline since classification
only makes sense in that context.

---

## 1. The big picture

There are two kinds of documents a user uploads into a project:

- **Syllabus PDFs** — list topics and subtopics for a subject.
- **Question paper PDFs** — contain exam questions.

Both go through the same shape of pipeline: **upload → extract → (classify,
question papers only) → completed**. Every document (syllabus or question
paper) has a `status` field that tracks where it is in that pipeline:

```
extracting  →  classifying  →  completed
                  (question papers only)
      ↓ (any stage)
   failed
```

Syllabi skip the "classifying" step entirely — extracting a syllabus's
topics doesn't require classification, so a syllabus goes straight from
`extracting` to `completed`.

Question papers need one more thing before they can move from `classifying`
to `completed`: **every syllabus in the project must already be
`completed`**. That's because classification needs the full topic list to
match questions against — it can't run with half a syllabus.

---

## 2. Where things live (collections)

| Collection        | What it stores                                                                 |
|--------------------|----------------------------------------------------------------------------------|
| `projects`         | One row per project.                                                             |
| `syllabi`          | One row per uploaded syllabus PDF, its status, and its extracted topics.         |
| `question_papers`  | One row per uploaded question paper PDF, its status, and the raw extracted data. |
| `questions`        | One row **per question** (not per paper) — this is what classification updates. |

A `questions` row looks roughly like this:

```json
{
  "_id": "...",
  "project_id": "...",
  "question_paper_id": "...",
  "question_number": "1(a)",
  "question": "What is supervised learning?",
  "mark": 5,
  "bbox": [...],
  "cropped_image": "...",
  "topic": []   // <-- classification fills this in
}
```

`topic` starts as an empty list when the question is first saved (right
after extraction), and classification is the only thing that ever writes to
it.

---

## 3. Stage 1 — Upload

**Endpoint:** `POST /projects/{project_id}/documents`
(`app/routers/documents.py`)

For every uploaded file:

1. The file is saved to disk (`app/storage.py`).
2. A row is inserted into `question_papers` or `syllabi` with
   `status = "extracting"`.
3. If it's a PDF, each page is rendered to an image (needed later for
   cropping question images out of the page).
4. A background task is scheduled (fire-and-forget, via `asyncio.create_task`
   — see `schedule()` in `app/services/processing.py`) to actually process
   the file. The HTTP request returns immediately (`202 Accepted`); the user
   polls `GET /projects/{project_id}/documents/status` to see progress.

Question papers also get a `classification_claimed_at: null` field at this
point — explained in [section 5](#5-stage-3--who-is-allowed-to-classify-and-when).

---

## 4. Stage 2 — Extraction

This part already existed before this session; summarized here for context.

- **Syllabus** (`app/topic_extraction_service/extract.py`): sends the PDF to
  Gemini, gets back a structured `SyllabusSchema` (subject name, and a list
  of `{topic, subtopics: [...], weightage, hours}`). This is saved as
  `extracted_data` on the syllabus row, and the status becomes `completed`.

- **Question paper** (`app/extraction_service/extract.py`): sends the PDF to
  Gemini, gets back a structured `ExamData` (subject info, and a list of
  questions with their text, marks, and bounding boxes). Then
  (`app/services/processing.py::_save_questions`):
  - each question is cropped out of its page image,
  - **one row per question is inserted into the `questions` collection**,
    with `topic: []`,
  - the question paper's status becomes `classifying`.

This is the handoff point into the part built in this session.

---

## 5. Stage 3 — Who is allowed to classify, and when

Classification for a question paper can only start once **every syllabus in
that project** has `status = "completed"`. This is checked by
`_syllabi_ready()` in `app/services/classification.py`:

```python
total syllabi in project == 0        -> not ready (nothing to classify against)
completed syllabi != total syllabi   -> not ready (some still extracting, or failed)
otherwise                            -> ready
```

**Important:** a syllabus that ended up `failed` blocks classification
**forever** for that project, until it's fixed/re-uploaded. This was a
deliberate choice matching "every syllabus must be completed" — see
[Known limitations](#8-known-limitations--things-to-revisit) if you want to
relax this later (e.g. to only require non-failed syllabi to be completed).

### Two trigger points

Because uploads happen concurrently, we don't know in advance whether the
question paper or the syllabus will finish extracting first. So the
"should I start classifying now?" check (`maybe_start_classification`) is
called from **both** places:

1. **After a question paper finishes extraction** (`process_question_paper`)
   — in case all syllabi are already done.
2. **After a syllabus finishes extraction** (`process_syllabus`) — in case
   this was the *last* syllabus the project was waiting on, unlocking any
   question papers that were sitting in `classifying`.

```
Scenario A: syllabus finishes first
  syllabus -> completed -> checks: any question papers waiting? no -> nothing happens
  question paper -> classifying -> checks: all syllabi completed? yes -> classify now

Scenario B: question paper finishes first
  question paper -> classifying -> checks: all syllabi completed? no -> wait
  syllabus -> completed -> checks: all syllabi completed now? yes -> classify the waiting paper
```

### Avoiding double classification (the "claim")

Both trigger points call the same `maybe_start_classification(project_id)`
function, which looks for question papers with `status = "classifying"`.
If two triggers fire at almost the same time (e.g. two syllabi finish
seconds apart), they could both see the same waiting question paper and try
to classify it twice.

To prevent that, before scheduling classification we **atomically claim**
the document:

```python
collection.find_one_and_update(
    {"_id": doc_id, "status": "classifying", "classification_claimed_at": None},
    {"$set": {"classification_claimed_at": now}},
)
```

Only the caller that actually flips `classification_claimed_at` from `None`
to a timestamp gets to schedule the job. The other caller sees the filter no
longer match (because it's not `None` anymore) and does nothing. This is why
every question paper document has a `classification_claimed_at` field.

---

## 6. Stage 4 — Preprocessing (before we ever call Gemini)

This happens inside `classify_question_paper()` in
`app/services/classification.py`, using helpers from
`app/classification_service/preprocess.py`.

### Why not just use Mongo's IDs?

Mongo `ObjectId`s look like `"66f1a2b3c4d5e6f7a8b9c0d1"` — long, meaningless
strings. Handing 50+ of these to an LLM in a big JSON blob and asking it to
copy them back *exactly* invites mistakes (a flipped character, a
truncated ID, or the model just making one up — "hallucinating"). Short,
simple IDs are much less error-prone for the model to copy around.

### Topic / subtopic IDs

`assign_topic_ids()` takes every **completed** syllabus in the project and
gives each topic a short numeric ID, and each subtopic an ID built from its
topic's ID:

```json
[
  {
    "subject_name": "Algorithm-1",
    "content": [
      { "topic": "String",  "topic_id": "1", "subtopics": [{"1-1": "Pattern matching"}, {"1-2": "KMP"}] },
      { "topic": "Sorting", "topic_id": "2", "subtopics": [{"2-1": "Quicksort"}, {"2-2": "Mergesort"}] }
    ]
  },
  {
    "subject_name": "Physics-1",
    "content": [
      { "topic": "Thermo", "topic_id": "3", "subtopics": [{"3-1": "Heat"}, {"3-2": "Entropy"}] }
    ]
  }
]
```

The topic counter (`1, 2, 3, ...`) runs **across every subject in the
project**, not restarting per subject — that's what guarantees no ID ever
repeats anywhere in the array, even with multiple syllabi. Subtopic IDs
(`"1-1"`, `"1-2"`, ...) are unique for the same reason: they're built from an
already-unique topic ID.

Two lookup tables are built at the same time (kept in memory only, never
sent to Gemini) so we can translate IDs back to real names later:

- `topic_lookup`: `"1"` → `{"subject_name": "Algorithm-1", "topic": "String"}`
- `subtopic_lookup`: `"1-1"` → `"Pattern matching"`

### Question IDs

`assign_question_ids()` does the same thing for questions — just sequential
numbers, `"1"`, `"2"`, `"3"`, ... — and builds a lookup from that temporary
ID back to the question's real Mongo `_id`, so results can be written to the
right row afterwards.

### Batching

`chunked()` splits the question list into groups of
`settings.classification_batch_size` (default **20**, configurable in
`.env` / `app/config.py`). Example: 50 questions → 3 API calls (20, 20, 10).
The **same full topic list** is sent with every batch — only the slice of
questions changes.

---

## 7. Stage 5 — Calling Gemini

`classify_batch()` in `app/classification_service/classify.py` does the
actual API call for one batch:

1. Loads `prompt.md` and `sys_instruct.md` (the instructions describing the
   input/output format and the mapping rules — e.g. "don't invent IDs",
   "empty `subtopic_ids` is fine", "don't force a weak match").
2. Fills in `prompt.md`'s placeholders (`{{ topics_and_subtopics }}`,
   `{{ id_to_que_map }}`, `{{ nque }}`) with the actual JSON for this batch.
3. Asks Gemini for a **structured JSON response** matching
   `list[QuestionMapping]` (a Pydantic model — Gemini's SDK turns this into
   a JSON schema and validates the response against it automatically).

All batches for one question paper run **concurrently**
(`asyncio.gather` in `classify_question_paper`), each with its own timeout
(`CLASSIFICATION_TIMEOUT_SECONDS = 120`, in
`app/services/classification.py`). If a batch times out or the API call
raises any error, `_classify_batch_safe()` catches it, logs it, and returns
an empty list for that batch instead of crashing the whole paper's
classification — see the error table below.

The expected shape coming back from Gemini, per batch:

```json
[
  {
    "question_id": "1",
    "mappings": [
      { "topic_id": "1", "subtopic_ids": ["1-1", "2-3"] }
    ]
  }
]
```

---

## 8. Stage 6 — Postprocessing (turning IDs back into names)

`resolve_question_mappings()` in `app/classification_service/postprocess.py`
takes one batch's raw Gemini response plus the `topic_lookup` /
`subtopic_lookup` built earlier, and converts it into the shape that
actually gets saved to the database:

```json
[
  {
    "subject_name": "Algorithm-1",
    "topic": "String",
    "subtopics": ["Pattern matching", "KMP"]
  }
]
```

Notice that **only names are stored** — the temporary IDs never touch the
database. They only exist for the duration of one classification run, in
memory.

While resolving, every ID is checked against the lookup tables:

- A `topic_id` that isn't in `topic_lookup` → that mapping is **dropped**
  and an error is logged (this is a hallucinated ID — see the table below).
- A `subtopic_id` that isn't in `subtopic_lookup` → just that subtopic is
  dropped and logged; the rest of the topic's subtopics are kept.
- If the LLM repeats the same `topic_id` in two separate mapping entries for
  one question (it's told not to, but might anyway), they're merged into one
  entry instead of creating a duplicate topic in the output.

---

## 9. Stage 7 — Saving results and finishing up

Back in `classify_question_paper()`:

1. Every batch's resolved results are collected. For each question that
   ended up with a non-empty topic list, an `UpdateOne` is queued.
2. All queued updates are written in a single `bulk_write()` call (one
   round-trip instead of one per question).
3. Questions that got an **empty** list are simply left alone — they already
   default to `topic: []`, so there's nothing to write.
4. The question paper's status is set to `completed` — **always**, whether
   every question matched, none did, or a batch failed outright. A partial
   or empty result is a valid outcome, not a pipeline failure.
5. The **only** way a question paper ends up `failed` at this stage is a
   systemic problem — e.g. the database read for syllabi/questions itself
   throws. That's a bug or infrastructure issue, not "the LLM didn't find a
   topic," so it's treated differently (see the table below).

---

## 10. What happens when things go wrong (edge cases)

| Scenario | What happens | Where it's logged | End state in DB |
|---|---|---|---|
| Question doesn't match any topic | LLM returns `"mappings": []` for it | nothing (expected outcome) | `topic: []` |
| LLM hallucinates a `topic_id` | That mapping is dropped | `logger.error` in `postprocess.py` | `topic` list just excludes that mapping |
| LLM hallucinates a `subtopic_id` | Just that subtopic name is dropped, topic itself kept if valid | `logger.error` in `postprocess.py` | topic kept, subtopic missing |
| LLM hallucinates a `question_id` (one not in our batch) | Result for that fake ID is ignored | `logger.error` in `classification.py` | no effect — not a real question |
| LLM silently skips a real question (doesn't include it in the response at all) | Detected by comparing input IDs to returned IDs | `logger.warning`, count of skipped questions | `topic: []` (its default, never touched) |
| One batch's Gemini call times out or errors | That batch contributes zero mappings; other batches unaffected | `logger.error`/`logger.exception` in `classification.py` | all questions in that batch stay `topic: []` |
| LLM repeats the same `topic_id` twice for one question | Merged into a single topic entry | none (silently handled) | one topic entry, subtopics combined |
| Project has zero syllabi, or none are `completed` | Classification doesn't start yet | nothing (this is just "not ready") | question paper stays `classifying` |
| A syllabus in the project is `failed` | Classification is blocked indefinitely for that project | nothing automatic — needs a human to notice | question paper stuck in `classifying` until the syllabus is fixed/re-uploaded |
| Question paper has zero questions, or project has zero topics at all | Nothing to classify — skips straight to done | `logger.warning` in `classification.py` | status → `completed` immediately |
| Two triggers fire near-simultaneously (race) | Only one wins the atomic claim; the other no-ops | none needed — this is the expected, safe outcome | classified exactly once |
| The classification trigger check itself throws (e.g. a transient DB error) right after extraction succeeded | The extraction's own success is **not** overwritten with `failed` | `logger.exception` ("Failed to check/start classification") | status stays `classifying`, waiting for the next trigger (or stuck if there won't be one — see limitations) |
| A truly unexpected/systemic error during classification (e.g. DB read fails) | The whole classification run is aborted | `logger.exception` in `classification.py` | status → `failed`, with the error message stored |

---

## 11. Files added or changed in this session

| File | Purpose |
|---|---|
| `app/classification_service/preprocess.py` **(new)** | Assigns short IDs to topics/subtopics/questions; batches the question list. |
| `app/classification_service/postprocess.py` **(new)** | Converts Gemini's ID-based response back into names; handles hallucinated IDs. |
| `app/classification_service/classify.py` **(rewritten)** | Was PDF-input only; now builds the text prompt for one batch and calls Gemini with a `list[QuestionMapping]` structured response schema. |
| `app/services/classification.py` **(new)** | The orchestrator: checks if syllabi are ready, claims papers atomically, runs batches concurrently, writes results, sets final status. |
| `app/services/processing.py` **(edited)** | Calls `maybe_start_classification()` after a question paper reaches `classifying` and after a syllabus reaches `completed`. `process_syllabus` now takes `project_id` as a parameter. |
| `app/routers/documents.py` **(edited)** | Passes `project_id` through to `process_syllabus`; seeds `classification_claimed_at: null` on new question paper documents. |
| `app/config.py` **(edited)** | Added `classification_batch_size` (default 20). |

`app/classification_service/prompt.md` and `sys_instruct.md` already existed
before this session and were not changed — `classify.py` reads and fills
them in as described in [section 7](#7-stage-5--calling-gemini).

---

## 12. How to debug this in practice

- **Follow one document through the logs**: every log line in
  `classification.py` and `processing.py` includes `doc_id=...`, so
  searching your logs for a specific question paper's ID shows its whole
  journey (extraction started → classifying → classification started →
  batch results → completed/failed).
- **Check why a paper isn't classifying**: look at its `status` and
  `classification_claimed_at` in the `question_papers` collection, and
  compare against the `status` of every `syllabi` row with the same
  `project_id`. If any syllabus isn't `completed`, that's why it's stuck.
- **A paper is stuck `classifying` with `classification_claimed_at` set,
  but nothing is happening**: this means the process was restarted (or
  crashed) mid-classification — see the limitation below. Manually reset it
  to retry:
  ```python
  await get_question_papers_collection().update_one(
      {"_id": doc_id},
      {"$set": {"status": "classifying", "classification_claimed_at": None}},
  )
  await maybe_start_classification(project_id)
  ```
- **A question has an empty `topic` list and you want to know why**: check
  the logs for that question paper's `doc_id` — you'll either see nothing
  (genuinely no match, or the LLM skipped it) or an `error`/`warning` line
  explaining a hallucinated ID or a batch failure.

---

## 13. Known limitations / things to revisit

These were conscious simplicity trade-offs, not oversights — flagged here so
they're easy to revisit later if they become a real problem:

- **A crashed process leaves claimed papers stuck.** If the server restarts
  while a paper is mid-classification, `classification_claimed_at` stays set
  but nothing will ever finish the job — there's no automatic retry/timeout
  for this. Fine for a single-process dev setup; would need a proper
  job queue (or a "claimed more than N minutes ago and still not completed"
  sweep) for production robustness.
- **A `failed` syllabus blocks its project's classification forever**,
  by design (see [section 5](#5-stage-3--who-is-allowed-to-classify-and-when)).
  There's no way to say "ignore the failed one, classify against what's
  there" — that would need a small change to `_syllabi_ready()`.
- **No manual "force classify" endpoint.** Everything is automatic, so if
  the two trigger points somehow never fire again for a stuck paper, there's
  currently no button to press — only the manual DB fix above.
- **Batch concurrency is unbounded.** All batches for one question paper run
  at once via `asyncio.gather` — for a huge question paper this could mean
  many simultaneous Gemini calls. Batch *size* is configurable
  (`classification_batch_size`), but there's no cap on how many batches run
  in parallel. Only worth adding if you start seeing rate-limit errors.
