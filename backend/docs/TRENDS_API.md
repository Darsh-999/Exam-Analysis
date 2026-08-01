# Trend Analysis API

Endpoints for the project-level trends/insights screen. All endpoints require
a bearer token (same `get_current_user` auth as the rest of the API) and
return **404** if the referenced project / question paper doesn't exist.

Every response is self-describing: it carries its own `title`,
`chart_type` (a suggestion, not a requirement), and a `description` string
that explains exactly what the numbers mean and any counting rules that
affect how they should be rendered (e.g. "values can add up to more than the
total"). Read `description` before wiring up a chart — it calls out the
specific gotcha for that endpoint.

Two response shapes are reused across most endpoints:

- **`ChartOut`** — a generic single-series chart: `{title, chart_type,
  description, x_label, y_label, data: [{label, value}]}`. Used by 5 of the 8
  endpoints below.
- Bespoke shapes for the three endpoints whose data has real structure
  (marks-per-paper, the heatmap, allocation-health).

## Two counting conventions

Because a question can be mapped to more than one topic (`questions.topic`
is a list), there are two different ways to count it, and different
endpoints deliberately use different ones:

| Convention | Meaning | Used by |
|---|---|---|
| **Attached-to-every-topic** | A question mapped to N topics contributes fully to all N buckets. Values can sum to more than the total question count. | Topic/Subtopic frequency |
| **Primary-topic-only** | A question contributes to exactly one bucket (its first-listed topic, or "Unallocated"). Values always sum exactly to the total. | Marks-per-paper, per-paper pie chart |

The frequency charts use the first convention because the question is
genuinely "about" every topic it matched, and the chart's job is to answer
"what comes up most" — losing that signal to force additivity would be
misleading. The stacked-bar and pie-chart endpoints use the second
convention because those chart types visually require their parts to sum to
a whole.

---

## 1. `GET /projects/{project_id}/trends/questions-per-year`

**What it answers:** How many questions were extracted per exam year.

Groups all of a project's questions by the exam year of their parent paper
(`question_papers.extracted_data.exam_date`). Papers with a missing or
unparseable exam date are grouped under the label `"Undated"`.

**Response:** `ChartOut`

```json
{
  "title": "Questions per Year",
  "chart_type": "bar",
  "x_label": "Year",
  "y_label": "Number of Questions",
  "data": [
    { "label": "2021", "value": 25 },
    { "label": "2022", "value": 40 },
    { "label": "Undated", "value": 3 }
  ]
}
```

**Best display:** Simple vertical bar chart, one bar per `data` entry, in the
order given (already sorted chronologically, `"Undated"` last).

---

## 2. `GET /projects/{project_id}/trends/topic-frequency?metric=count|marks`

**What it answers:** Which topics come up the most (or carry the most
marks).

- `metric=count` (default): ranks topics by number of questions attached.
- `metric=marks`: ranks topics by total marks of the questions attached.

Uses the **attached-to-every-topic** convention — a multi-allocated question
counts fully toward each of its topics.

**Response:** `ChartOut`, already sorted descending by value.

**Best display:** Horizontal bar chart (topic names can be long — a
horizontal layout keeps them readable). Consider truncating to the top
10–15 entries for readability if a project has many topics; the API returns
the full ranked list so the frontend can decide how many to show. Rendering
`metric=count` and `metric=marks` side by side (two panels, same topic
order or independently sorted) is a good way to surface "most asked" vs
"most heavily weighted" in one glance.

---

## 3. `GET /projects/{project_id}/trends/subtopic-frequency?metric=count|marks`

Identical to #2, one level down: ranks **subtopics** instead of topics.
Same `metric` query param, same convention (attached-to-every-topic —
here, attached-to-every-subtopic), same response shape.

**Best display:** Same as #2 — horizontal bar chart, likely shown as a
drill-down or secondary panel once a user picks a topic from chart #2 (the
API doesn't filter subtopics by topic today; that's easy to add later if the
UI wants a "subtopics of this topic" drill-down instead of a flat list).

---

## 4. `GET /question-papers/{question_paper_id}/trends/topic-distribution`

**What it answers:** For one specific question paper, how its questions
split across topics.

Uses the **primary-topic-only** convention so slice values sum exactly to
the paper's total question count. Questions with no mapped topic appear as
an `"Unallocated"` slice — don't filter it out, it's meaningful signal
about classification coverage.

**Response:** `ChartOut` (`x_label`/`y_label` are `null` — not meaningful
for a pie chart).

**Best display:** Pie chart, with a dropdown/select above it to switch
between papers. Populate that dropdown from
`GET /projects/{project_id}/question-papers` (already built — gives
`id` + `filename` + `subject_name`/`subject_code` per paper), then call
this endpoint with the selected paper's `id`.

---

## 5. `GET /projects/{project_id}/trends/marks-per-paper`

**What it answers:** How a project's total marks break down by topic,
paper by paper, across time.

Papers are ordered left-to-right by exam date (undated papers last, by
filename). For each paper, every question's marks are attributed to its
**first-listed** mapped topic only ("Unallocated" if none) — so each bar's
segments sum exactly to that bar's `total_marks`.

**Response:** `MarksPerPaperOut`

```json
{
  "title": "Marks per Paper by Topic",
  "chart_type": "stacked_bar_with_line",
  "x_label": "Question Paper",
  "y_label": "Marks",
  "data": [
    {
      "paper_id": "...",
      "filename": "Summer_2021.pdf",
      "subject_code": "3140705",
      "exam_date": "2021/09/11",
      "total_marks": 119,
      "segments": [
        { "topic": "Exception Handling...", "marks": 25 },
        { "topic": "Object oriented thinking", "marks": 38 },
        { "topic": "Unallocated", "marks": 15 }
      ]
    }
  ]
}
```

**Best display:** Vertical **stacked** bar chart, one bar per paper in
`data` order, each bar's `segments` as the stack (color per topic — reuse
the same topic→color mapping as chart #2/#3 if you're color-coding topics
consistently across the screen). Overlay a **line series** through each
bar's `total_marks` value — since segments are guaranteed additive, the
line will always sit exactly at the top of each stack, giving a clean
"total marks trend across papers" read at a glance. Use `filename` or
`subject_code` + `exam_date` for the x-axis tick labels.

---

## 6. `GET /projects/{project_id}/trends/topic-year-heatmap`

**What it answers:** Which topics are trending up or down over time.

**Response:** `HeatmapOut`

```json
{
  "title": "Topic Popularity by Year",
  "chart_type": "heatmap",
  "x_label": "Year",
  "y_label": "Topic",
  "rows": ["Object oriented thinking", "Exception Handling...", "..."],
  "columns": ["2021", "2022", "Undated"],
  "data": [
    { "row": "Object oriented thinking", "column": "2021", "value": 9 }
  ]
}
```

`rows` (topics, ordered by all-time frequency) and `columns` (years,
chronological, `"Undated"` last) are given explicitly so the frontend can
lay out a full grid without deriving axes itself. **`data` is sparse** —
any `(row, column)` pair not present should be rendered as `0`, not left
blank.

**Best display:** Heatmap/matrix, rows = topics, columns = years, cell
color intensity = `value`. This is the recommended replacement for a raw
date-axis trend chart: exam dates are one-per-paper and irregular, so a true
date-axis timeline reads as sparse, disconnected points. Bucketing by year
gives a denser, more readable trend.

---

## 7. `GET /projects/{project_id}/trends/allocation-health`

**What it answers:** How completely each paper's questions have been
classified — a data-quality/QA view, not an exam-content trend.

Three mutually exclusive, stackable buckets per paper:
`unallocated` (0 topics) + `single_allocated` (exactly 1) +
`multi_allocated` (2+) = `total_questions`.

> Note: this intentionally differs from `total_allocated_questions` in
> `GET /projects/{project_id}/summary` and
> `GET /projects/{project_id}/question-papers`, where "allocated" means
> "≥1 topic" and therefore *includes* multi-allocated questions. Here,
> `single_allocated` and `multi_allocated` are split apart so the three
> buckets can stack cleanly to 100% of a paper's questions.

**Response:** `AllocationHealthOut`

**Best display:** Stacked bar chart (or 100%-stacked, since totals differ
per paper) — one bar per paper, three segments. Could also work as a
donut per paper if shown in a grid rather than a single chart. Suggest a
consistent color convention: green = single_allocated, amber = multi_allocated
(informational, not bad), red/gray = unallocated (the thing to actually
worry about).

---

## 8. `GET /projects/{project_id}/trends/mark-distribution`

**What it answers:** The exam's question-weight structure — how many
questions are worth 1 mark, 2 marks, 5 marks, etc.

**Response:** `ChartOut`, `label` is the mark value as a string (e.g.
`"2"`, `"7.5"`), sorted ascending by mark value.

**Best display:** Bar chart / histogram, x-axis = mark value, y-axis =
question count. Since exam marks are typically a handful of discrete
values rather than a continuous range, a plain bar chart (one bar per
distinct value, as returned) reads better than a binned histogram.

---

## Quick reference

| # | Endpoint | Response | Suggested chart |
|---|---|---|---|
| 1 | `GET /projects/{id}/trends/questions-per-year` | `ChartOut` | Bar |
| 2 | `GET /projects/{id}/trends/topic-frequency` | `ChartOut` | Horizontal bar |
| 3 | `GET /projects/{id}/trends/subtopic-frequency` | `ChartOut` | Horizontal bar |
| 4 | `GET /question-papers/{id}/trends/topic-distribution` | `ChartOut` | Pie (+ paper dropdown) |
| 5 | `GET /projects/{id}/trends/marks-per-paper` | `MarksPerPaperOut` | Stacked bar + line |
| 6 | `GET /projects/{id}/trends/topic-year-heatmap` | `HeatmapOut` | Heatmap |
| 7 | `GET /projects/{id}/trends/allocation-health` | `AllocationHealthOut` | Stacked bar |
| 8 | `GET /projects/{id}/trends/mark-distribution` | `ChartOut` | Bar / histogram |

All schemas are defined in `app/schemas.py`; all aggregation logic lives in
`app/services/analytics.py` (shared with the non-trend listing/summary
endpoints where applicable).
