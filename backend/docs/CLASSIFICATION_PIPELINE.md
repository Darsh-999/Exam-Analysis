# Question Paper Extraction & Classification Pipeline

This document explains, in plain language, everything that happens from the
moment a user uploads a PDF to the moment each question has topics and
subtopics attached to it. It also explains *why* things were built the way
they were, so future debugging doesn't require re-reading all the code from
scratch.

Every extraction and classification call in this pipeline runs against a
**local Qwen model served by vLLM** — there is no external LLM API involved
anywhere in this flow. (An earlier version of this pipeline used Gemini; that
code has been fully removed from the codebase, not just disconnected.)

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

Multiple files can be uploaded in one request, and every file is scheduled
as its own concurrent background task — see the concurrency note in
[section 4](#4-stage-2--extraction) before assuming timeouts scale linearly.

---

## 4. Stage 2 — Extraction

Both extraction paths funnel every model call through one shared client,
`app/local_extraction_service/qwen_client.py::call_structured()`, which
talks to vLLM's OpenAI-compatible endpoint (`settings.vllm_base_url`). It:

- Uses **structured/guided JSON decoding** (`response_format: {"type":
  "json_schema", ..., "strict": true}`) against a Pydantic schema, so the
  model is constrained to return valid, on-schema JSON rather than being
  asked nicely to.
- Is throttled by one **global semaphore**, `settings.qwen_max_concurrency`
  (default **8**) — this caps how many Qwen requests are in flight at once
  *across the whole app*: every syllabus, every question paper's headers and
  question batches, and every classification batch share this one limit.
- Has its own per-request timeout, `settings.vllm_request_timeout_seconds`
  (default 120s).

This is a meaningful difference from calling a hosted API like Gemini:
Gemini scaled elastically and was rate-limited by Google, not by us. vLLM
here is one fixed local GPU resource with a hard concurrency ceiling — see
the concurrency limitation in
[section 13](#13-known-limitations--things-to-revisit).

### Syllabus extraction

**`app/local_topic_extraction_service/extract.py`**

1. Every page's embedded text layer is pulled out with PyMuPDF
   (`pdf_text.py`) — no OCR, no images sent to the model, just the PDF's
   real text content, joined with `--- Page N ---` markers so the model can
   reason about cross-page continuity. A page with almost no extractable
   text logs a warning (likely a scanned/image-only page whose content will
   be missed) but doesn't stop the run.
2. The whole document's text goes to the local Qwen model in **one**
   `call_structured()` call, constrained to the `SyllabusExtraction` schema.
3. Returns `{degree, subject_name, subject_code, semester, total_marks,
   content: [{topic, subtopics, weightage, hours}]}`. Saved as
   `extracted_data` on the syllabus row, status becomes `completed`.

### Question paper extraction

**`app/local_extraction_service/extract.py`** — a multi-stage local
pipeline, since (unlike the syllabus text path) exam papers are extracted
from page *images*, not just text:

1. **DocLayout** (`doclayout.py`): a YOLO model detects every content region
   on every page and crops it out, producing an ordered list of
   `BoxRecord`s (top-to-bottom, left-to-right per page, continuous
   numbering across the whole document) — each with a base64 JPEG crop and
   a normalized `box_2d`. Runs on a background thread, serialized by
   `settings.doclayout_gpu_concurrency` (default **1**) since the model
   shares a GPU with vLLM and isn't safe to call from multiple threads at
   once.
2. **Headers and questions extract concurrently** (`asyncio.gather`):
   - **Headers** (`headers.py`): the first `settings.header_bbox_limit`
     boxes (where header metadata always lives) are grouped into a handful
     of composite images (small crops stacked into one image with visible
     separators — see `image_compose.py`) and sent as **one** Qwen call
     constrained to the `ExamHeaders` schema. If this call fails for any
     reason, it falls back to empty headers instead of taking the whole
     document down with it (see the extraction error table below).
   - **Questions** (`questions.py`): *every* box (not just the header ones)
     is chunked into batches of `settings.question_batch_size` (default
     **5**) consecutive boxes. Each batch is its own Qwen call — every image
     in the batch, each tagged with its `ImageID` — constrained to the
     `BatchExtraction` schema, which both classifies every image
     (`question` / `question_continuation` / `diagram` / `table` / `mcq` /
     `marks_info` / `useless`) and extracts the actual question text, marks,
     and a confidence/`incomplete_info` flag for anything that looks
     cut off relative to what that batch could see. Batches run
     concurrently and each is independently resilient — a failed batch just
     contributes zero questions for that slice, others unaffected.
3. Results are merged into the `content[]` shape used everywhere downstream
   (`question_number`, `question`, `mark`, `bbox`), plus additive fields
   (`image_ids`, `incomplete_info`, `incomplete_reason`, `confidence`) that
   ride along unused for now.
4. `reconciliation.py` is a **placeholder** for a future pass that would
   re-extract questions flagged `incomplete_info: true` with a wider
   image context — currently a no-op that returns the content unchanged
   (see [section 13](#13-known-limitations--things-to-revisit)).

Then, same as before (`app/services/processing.py::_save_questions`):
- each question is cropped out of its page image (a crop failure for one
  question no longer aborts the rest — it just saves with
  `cropped_image: ""` and logs a warning),
- **one row per question is inserted into the `questions` collection**
  (a single `insert_many`, not one `insert_one` per question, so a failure
  partway through can't leave some questions committed and others lost),
  with `topic: []`,
- the question paper's status becomes `classifying`.

### Extraction edge cases

| Scenario | What happens | Where it's logged | End state |
|---|---|---|---|
| DocLayout hits a CUDA out-of-memory error | GPU cache freed, re-raised as a plain `RuntimeError` | propagates to `processing.py`'s handler | whole PDF marked `failed` |
| One question-extraction image batch fails (timeout, malformed response) | That batch contributes zero questions; other batches unaffected | `logger.exception` in `questions.py` | those questions are simply missing from `content[]` — nothing to retry them yet |
| Header extraction fails | Falls back to empty headers (`""` / `0` for every field) | `logger.exception` in `headers.py` | `degree`/`subject_name`/`exam_date`/etc. saved empty; questions unaffected |
| A question's page-image crop fails (missing/corrupt rendered page) | That one question saves with `cropped_image: ""`; the rest of the document is unaffected | `logger.exception` in `processing.py` | question has text/marks/topic as normal, just no image |
| The whole PDF processing call exceeds `EXTRACTION_TIMEOUT_SECONDS` (180s) | The task is cancelled | `logger.error` in `processing.py` | document marked `failed` with a timeout message |

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
[Known limitations](#13-known-limitations--things-to-revisit) if you want to
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

## 6. Stage 4 — Preprocessing (before we ever call the model)

This happens inside `classify_question_paper()` in
`app/services/classification.py`, using helpers from
`app/classification_service/preprocess.py`. This part is model-agnostic —
it built the same request shape when the classifier was Gemini and still
does now that it's local Qwen.

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
sent to the model) so we can translate IDs back to real names later:

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
`.env` / `app/config.py`). Example: 50 questions → 3 calls (20, 20, 10).
**The full topic list is resent with every single batch call** — only the
slice of questions changes. This matters more for a local, fixed-context
model than it did for Gemini — see the context-window note in
[section 7](#7-stage-5--calling-qwen-via-vllm).

---

## 7. Stage 5 — Calling Qwen (via vLLM)

**`app/local_classification_service/classify.py`** does the actual model
call for one batch. It has its own `prompts/prompt.md` and
`prompts/sys_instruct.md` — copies of the original prompts, adapted for one
concrete reason (see below); the mapping rules themselves are unchanged.

1. Loads `prompts/sys_instruct.md` and `prompts/prompt.md` (the input/output
   format and mapping rules — e.g. "don't invent IDs", "empty
   `subtopic_ids` is fine", "don't force a weak match").
2. Fills in `prompt.md`'s placeholders (`{{ topics_and_subtopics }}`,
   `{{ id_to_que_map }}`, `{{ nque }}`) with the actual JSON for this batch.
3. Sends one `call_structured()` request (system + user messages) to the
   local Qwen model, constrained to the `ClassificationBatchResult` schema.

### Why the output is wrapped in `{"results": [...]}`

Gemini's SDK accepted `response_schema=list[QuestionMapping]` — a bare JSON
array at the schema root. vLLM's structured-output endpoint mirrors the
OpenAI API, which requires an **object** at the schema root, not a bare
array. So the local prompts ask for:

```json
{
  "results": [
    { "question_id": "1", "mappings": [{ "topic_id": "1", "subtopic_ids": ["1-1", "2-3"] }] }
  ]
}
```

`classify_batch()` unwraps `.results` before returning, so its return shape
(`list[dict]`, one entry per question) is identical to what the Gemini
version returned — nothing in preprocessing or postprocessing needed to
change for the swap.

### Concurrency and timeouts

All batches for one question paper still run **concurrently**
(`asyncio.gather` in `classify_question_paper`), each wrapped with its own
outer timeout (`CLASSIFICATION_TIMEOUT_SECONDS = 120`, in
`app/services/classification.py`) on top of `call_structured()`'s own
per-request timeout. If a batch times out or the call raises any error,
`_classify_batch_safe()` catches it, logs it, and returns an empty list for
that batch instead of crashing the whole paper's classification.

Unlike Gemini, these batches now compete for the **same shared
`qwen_max_concurrency` semaphore** as extraction (see
[section 4](#4-stage-2--extraction)) — under heavy concurrent load (many
papers extracting/classifying at once), later batches can spend real time
just queued for a GPU slot before their timeout clock has any chance to
reflect that. See [section 13](#13-known-limitations--things-to-revisit).

### The context-window trap (already hit once — watch for it again)

vLLM's context window is a **fixed input+output token budget**, unlike
calling a hosted API where the effective limit is enormous. During testing,
`MAX_TOKENS` was initially set to `6000` without checking this — with a
20-question batch and one syllabus, the request came back as a hard `400`:
`"maximum context length is 8192 tokens... your prompt contains at least
2193 input tokens... total of at least 8193"`. `MAX_TOKENS` was lowered to
`3000`, which fixed it (2193 + 3000 = 5193, comfortable margin).

This is a moving target, not a one-time fix: the **full syllabus is resent
as input on every batch call regardless of batch size**, so if a project's
combined syllabus content (multiple subjects, many topics) ever grows large
enough that input tokens alone approach the context window, lowering
`MAX_TOKENS` further or shrinking `classification_batch_size` won't help —
the syllabus portion of the input doesn't shrink with either. At that point
the real fix is raising vLLM's `--max-model-len` at server launch (GPU
memory permitting), not app-level tuning.

---

## 8. Stage 6 — Postprocessing (turning IDs back into names)

`resolve_question_mappings()` in `app/classification_service/postprocess.py`
takes one batch's raw model response plus the `topic_lookup` /
`subtopic_lookup` built earlier, and converts it into the shape that
actually gets saved to the database. This is the same function, unchanged,
regardless of which model produced the response:

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
   throws. That's a bug or infrastructure issue, not "the model didn't find
   a topic," so it's treated differently (see the table below).

---

## 10. What happens when things go wrong (classification edge cases)

| Scenario | What happens | Where it's logged | End state in DB |
|---|---|---|---|
| Question doesn't match any topic | Model returns `"mappings": []` for it | nothing (expected outcome) | `topic: []` |
| Model hallucinates a `topic_id` | That mapping is dropped | `logger.error` in `postprocess.py` | `topic` list just excludes that mapping |
| Model hallucinates a `subtopic_id` | Just that subtopic name is dropped, topic itself kept if valid | `logger.error` in `postprocess.py` | topic kept, subtopic missing |
| Model hallucinates a `question_id` (one not in our batch) | Result for that fake ID is ignored | `logger.error` in `classification.py` | no effect — not a real question |
| Model silently skips a real question (doesn't include it in the response at all) | Detected by comparing input IDs to returned IDs | `logger.warning`, count of skipped questions | `topic: []` (its default, never touched) |
| One batch's Qwen/vLLM call times out, errors, or the response blows past the context window | That batch contributes zero mappings; other batches unaffected | `logger.error`/`logger.exception` in `classification.py` | all questions in that batch stay `topic: []` |
| Model repeats the same `topic_id` twice for one question | Merged into a single topic entry | none (silently handled) | one topic entry, subtopics combined |
| Project has zero syllabi, or none are `completed` | Classification doesn't start yet | nothing (this is just "not ready") | question paper stays `classifying` |
| A syllabus in the project is `failed` | Classification is blocked indefinitely for that project | nothing automatic — needs a human to notice | question paper stuck in `classifying` until the syllabus is fixed/re-uploaded |
| Question paper has zero questions, or project has zero topics at all | Nothing to classify — skips straight to done | `logger.warning` in `classification.py` | status → `completed` immediately |
| Two triggers fire near-simultaneously (race) | Only one wins the atomic claim; the other no-ops | none needed — this is the expected, safe outcome | classified exactly once |
| The classification trigger check itself throws (e.g. a transient DB error) right after extraction succeeded | The extraction's own success is **not** overwritten with `failed` | `logger.exception` ("Failed to check/start classification") | status stays `classifying`, waiting for the next trigger (or stuck if there won't be one — see limitations) |
| A truly unexpected/systemic error during classification (e.g. DB read fails) | The whole classification run is aborted | `logger.exception` in `classification.py` | status → `failed`, with the error message stored |

---

## 11. Where the code lives

| File | Purpose |
|---|---|
| `app/local_topic_extraction_service/` | Syllabus extraction: PyMuPDF text extraction (`pdf_text.py`) + one `call_structured()` call against the `SyllabusExtraction` schema (`extract.py`, `schemas.py`). |
| `app/local_extraction_service/` | Question paper extraction: DocLayout box detection (`doclayout.py`), header extraction (`headers.py`), batched question extraction (`questions.py`), the shared vLLM client every Qwen call goes through (`qwen_client.py`), and the reconciliation placeholder (`reconciliation.py`). |
| `app/classification_service/preprocess.py` | Assigns short IDs to topics/subtopics/questions; batches the question list. Model-agnostic. |
| `app/classification_service/postprocess.py` | Converts the model's ID-based response back into names; handles hallucinated IDs. Model-agnostic. |
| `app/local_classification_service/` | The actual classification call: builds the prompt, calls the local Qwen model via `call_structured()`, unwraps the response (`classify.py` + its own `prompts/`). |
| `app/services/classification.py` | The orchestrator: checks if syllabi are ready, claims papers atomically, runs batches concurrently, writes results, sets final status. |
| `app/services/processing.py` | The extraction orchestrator: runs `local_extraction_service`/`local_topic_extraction_service`, saves questions, triggers `maybe_start_classification()`. |
| `app/routers/documents.py` | Upload endpoint — saves files, seeds documents with `status: "extracting"` (and `classification_claimed_at: null` for question papers), schedules background processing. |
| `app/config.py` | All tunables: `vllm_base_url`/`vllm_model_name`/`vllm_request_timeout_seconds`, `qwen_max_concurrency`, `doclayout_model_path`/`doclayout_gpu_concurrency`, `header_bbox_limit`/`header_boxes_per_image`, `question_batch_size`, `classification_batch_size`, `bbox_expansion`. |

Gemini has been **fully removed**, not just disconnected: `app/extraction_service/`,
`app/topic_extraction_service/`, and `app/classification_service/classify.py`
(plus its `prompt.md`/`sys_instruct.md`) no longer exist in the codebase,
and `gemini_api_key` is no longer a setting. `google-genai` is no longer a
dependency.

---

## 12. How to debug this in practice

- **Follow one document through the logs**: every log line in
  `classification.py` and `processing.py` includes `doc_id=...`, so
  searching your logs for a specific question paper's ID shows its whole
  journey (extraction started → classifying → classification started →
  batch results → completed/failed).
- **Everything failing immediately, across every document?** Check that the
  vLLM server is actually up and reachable at `settings.vllm_base_url`, and
  that the DocLayout model weights exist at `settings.doclayout_model_path`
  — these are now local runtime dependencies (a GPU process, a model file
  on disk) rather than just an API key, so "is the service up" is worth
  ruling out first.
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
  (genuinely no match, or the model skipped it) or an `error`/`warning` line
  explaining a hallucinated ID, a context-window overflow, or a batch
  failure.
- **A `BadRequestError` mentioning "maximum context length"**: this is the
  context-window trap from [section 7](#7-stage-5--calling-qwen-via-vllm) —
  check `MAX_TOKENS` in `local_classification_service/classify.py` against
  how big the project's syllabus has grown, not just the batch size.

---

## 13. Known limitations / things to revisit

These are conscious trade-offs or known-but-not-yet-fixed gaps, flagged here
so they're easy to revisit later:

- **A crashed process leaves in-progress documents stuck.** For
  classification, `classification_claimed_at` stays set forever with no
  automatic retry/timeout. Extraction has no claim step at all (it's kicked
  off directly at upload), but the same risk applies — a killed process
  mid-extraction just leaves the document in `extracting` status forever.
  Fine for a single-process setup; would need a proper job queue (or a
  "claimed/started more than N minutes ago and still not completed" sweep)
  for unattended production robustness.
- **A `failed` syllabus blocks its project's classification forever**,
  by design (see [section 5](#5-stage-3--who-is-allowed-to-classify-and-when)).
  There's no way to say "ignore the failed one, classify against what's
  there" — that would need a small change to `_syllabi_ready()`.
- **No manual "force classify" endpoint.** Everything is automatic, so if
  the two trigger points somehow never fire again for a stuck paper, there's
  currently no button to press — only the manual DB fix above.
- **GPU concurrency is a hard shared ceiling, and timeouts don't account for
  queueing.** Extraction and classification share one global Qwen semaphore
  (`qwen_max_concurrency`, default 8) plus DocLayout's own GPU semaphore
  (`doclayout_gpu_concurrency`, default 1). The upload endpoint explicitly
  supports uploading many files in one request, each scheduled as a
  concurrent task. Under that kind of concurrent load, a batch/document can
  spend a meaningful chunk of its fixed timeout budget (`EXTRACTION_TIMEOUT_SECONDS`,
  `CLASSIFICATION_TIMEOUT_SECONDS`, `vllm_request_timeout_seconds`) just
  queued for a GPU slot, and then get killed shortly after it finally
  starts — which looks like a model failure but is really queue congestion.
  Not yet fixed; worth watching for under real concurrent upload volume.
- **The full syllabus is resent on every classification batch call, with no
  cap.** Fine today, but see the context-window note in
  [section 7](#7-stage-5--calling-qwen-via-vllm) — this doesn't scale
  indefinitely as a project's syllabus content grows, and the eventual fix
  is server-side (`--max-model-len`), not app-level.
- **The reconciliation pass isn't implemented.** `local_extraction_service/reconciliation.py`
  is a documented no-op. Questions the model flags `incomplete_info: true`
  (cut off across a batch boundary, references a diagram/table/mcq outside
  what that batch could see) are saved as-is, incomplete, with no follow-up
  re-extraction pass yet.
