# Frontend Design Specification — Exam Analysis Platform

This document describes every screen of the demo web app in enough visual and
functional detail that it can be drawn on paper or built directly from this
file, without opening the backend code. Where a detail depends on how the API
actually behaves (async processing, per-syllabus topics, etc.) that is called
out explicitly in an **API note**, so the build doesn't quietly assume the
wrong thing.

The brief: simple, clean, easy to build, demo-quality — not a production SaaS
polish pass. Every screen below is deliberately boring in structure (top nav +
stat cards + a table) so it can be built with plain components and no exotic
layout work.

---

## 0. Visual Language

This is the shared design system every screen below draws from. Colors and
composition are inspired by the three reference screenshots supplied
(dark charcoal chrome, warm orange→amber gradient as the single accent,
cream/off-white content surfaces, thin left-accent-bar stat cards).

### 0.1 Color palette (UI chrome)

| Role | Light mode | Usage |
|---|---|---|
| Page background | `#F9F7F2` (warm off-white/cream) | Body background behind cards/tables |
| Surface / card background | `#FFFFFF` | Cards, table rows, modal body |
| Header / nav background | `#141414` (near-black charcoal) | Top navigation bar, footer of modals if used |
| Primary accent | Gradient `#EA5B2E → #F5A623` (orange → amber) | Primary buttons, active nav item, progress bars, highlighted stat borders |
| Primary accent (solid fallback) | `#EA5B2E` | Icons, links, focus rings, badges where a gradient is impractical |
| Primary text | `#171512` | Headings, body copy on light surfaces |
| Secondary text | `#6E6B64` | Helper text, table secondary lines, timestamps |
| Muted text / placeholder | `#A6A39B` | Empty states, disabled labels |
| Divider / border | `#E7E3DA` | Card borders, table row dividers |
| Success (status: completed) | `#0CA30C` | "Completed" badge |
| Warning (status: extracting / classifying) | `#F5A623` | "Extracting" / "Classifying" badge |
| Critical (status: failed) | `#D03B3B` | "Failed" badge |

Dark-chrome elements (top nav, hero/header bands) always use white text on
`#141414`. Everything else is the light cream/white surface described above —
this app does not need a full dark-mode theme for the demo; one consistent
light theme with a dark nav bar is enough to read as "on brand" without
doubling the build effort.

### 0.2 Typography

One typeface family throughout: system sans-serif stack (`-apple-system,
"Segoe UI", Roboto, sans-serif`). No serif, no display font.

- Page titles: 28–32px, semi-bold, primary text color.
- Section headings: 18–20px, semi-bold.
- Stat card numbers: 32–36px, bold, tabular figures (numbers align if stacked).
- Stat card labels: 12–13px, uppercase, letter-spacing 0.04em, secondary text color.
- Body / table text: 14px regular.
- Helper / meta text: 12–13px, secondary or muted text color.

### 0.3 Spacing, radius, elevation

- Base spacing unit: 8px (use multiples: 8, 16, 24, 32).
- Card corner radius: 10px. Buttons and input fields: 8px. Modals: 12px.
- Cards sit on a very light shadow (`0 1px 3px rgba(0,0,0,0.06)`), not a hard
  border, except a 3–4px solid accent bar on the **left edge** of stat cards
  (this is the single most recognizable motif borrowed from the reference
  screenshots — reuse it everywhere a "stat card" appears).
- Max content width: ~1280px, centered, with 24–32px side padding on smaller
  viewports.

### 0.4 Core components (reused across every screen)

**Top navigation bar** — dark charcoal (`#141414`) strip, 64px tall, sticky.
Left: small logo mark + wordmark ("ExamInsight" or similar) in white. Center/
left-of-center: breadcrumb trail once inside a project (e.g. `Projects  /
Data Structures 2024`), rendered in muted white/gray with the current page
name in full white. Right: the logged-in user's email, and a small "Log out"
text button. No other chrome — no sidebar, no hamburger menu. This one bar is
present on every authenticated screen and is the only persistent navigation
element in the app.

**Stat card** — white rounded rectangle, ~140px min-height, 4px accent bar on
the left in the orange→amber gradient. Inside: a big bold number top, an
uppercase gray label underneath, optionally a small icon top-right (outline
style, single color, orange). Stat cards are laid out in a responsive grid
(auto-fit, min width ~180px) so they wrap cleanly from 6-across on desktop to
2-across on a narrow window — never horizontally scrollable.

**Status badge** — small pill, 12px text, icon + label (never color alone,
per accessibility best practice):
- `extracting` → amber pill, spinner/hourglass icon, "Extracting"
- `classifying` → amber pill, spinner icon, "Classifying"
- `completed` → green pill, checkmark icon, "Completed"
- `failed` → red pill, alert icon, "Failed" (hover/click reveals the error
  message string returned by the API)

**Data table** — plain white table, no zebra striping, 1px hairline row
dividers (`#E7E3DA`), column headers in uppercase secondary-gray 12px, row
height ~56px, whole row is a click target when the row navigates somewhere
(cursor: pointer, subtle hover background `#F9F7F2`). No inline row actions
unless stated.

**Primary button** — orange→amber gradient fill, white bold text, 8px radius,
40–44px tall. Used for the one primary action per screen ("+ New Project",
"Analyze", "Log In").

**Secondary button** — white background, 1px border `#E7E3DA`, dark text.
Used for "Cancel", tab-like toggles, filters.

**Modal** — centered overlay, white panel, 12px radius, drop shadow, dark
scrim behind (`rgba(0,0,0,0.5)`). Always has a small "×" close icon in the
top-right corner, ~16px from each edge.

**Empty state** — centered inside whatever table/panel is empty: a muted
outline icon, one line of gray text ("No question papers yet"), and, where
relevant, the primary action that would fill it.

---

## 1. Screen — Login

The simplest screen in the app, intentionally. Full-viewport, centered
single-column layout — no split-screen hero image, no marketing copy.

**Layout:** Page background is the dark charcoal (`#141414`) — the one place
in the app where the dark chrome color fills the whole viewport, giving the
login screen a distinct, branded "gateway" feel before the user gets to the
cream-colored app. Centered in the middle of the screen is a white card,
~400px wide, 12px radius, generous padding (40px). Inside the card, top to
bottom:

1. Small logo mark, centered.
2. Title: "Log In" or the product name, 22px semi-bold, centered.
3. Email field — labeled "Email", full width, 44px tall input, 8px radius.
4. Password field — labeled "Password", same styling, masked input, no
   show/hide toggle needed for a demo.
5. Primary gradient button, full width, label "Log In".
6. Space reserved directly under the button for an inline error message in
   red 13px text (e.g. "Invalid email or password") — only appears after a
   failed attempt; otherwise this space is empty so the layout doesn't jump.

That's the entire screen. **No** "Create account", **no** "Forgot password?",
**no** social login, **no** footer links — exactly as specified. On successful
login, redirect straight to the Project Management screen.

*API note: this hits `POST /auth/login` with `{email, password}` and stores
the returned bearer token (e.g. in `localStorage`) for all subsequent
requests. A stored valid token should skip this screen entirely on next
visit. A signup endpoint exists on the backend but is intentionally not
exposed anywhere in this UI.*

---

## 2. Screen — Project Management (Dashboard)

This is the landing screen after login. Standard top nav (breadcrumb shows
just "Projects" as the current page, no deeper path).

**Header row:** page title "Projects" on the left, primary button "+ New
Project" on the right, same row.

**Stat card strip:** six stat cards in a single responsive row directly under
the header, in this order:

1. Total Projects
2. Total Question Papers
3. Total Syllabi
4. Total Subjects
5. Total Questions
6. Total Topics

*(These map 1:1 to a single global-counts API call — no per-project
aggregation needed for this row.)*

**Toolbar:** below the stat cards, a light toolbar row with a search input
("Search projects...") that filters the table below by project name as the
user types (client-side filtering is fine at demo scale — no need for a
backend search endpoint). This is a small addition beyond your original spec
but costs almost nothing to build and keeps the table usable once there are
more than a handful of projects.

**Projects table:** full-width table below the toolbar, one row per project,
columns exactly as you specified:

| Project Name | Description | Created By | Created On | Question Papers | Syllabi | Subjects | Questions |
|---|---|---|---|---|---|---|---|

- Project Name renders bold/primary text; Description renders truncated to
  one line with an ellipsis if long (full text on hover via title tooltip).
- Created By shows a short username (not the raw email).
- Created On shows a relative-friendly date, e.g. "Aug 2, 2026".
- The four count columns are right-aligned numbers.
- Clicking anywhere on a row navigates to that project's Individual Project
  screen.
- Rows are sorted newest-first by default; clicking a numeric column header
  toggles sort by that column (nice-to-have, skip if time-constrained).

If there are zero projects, the table area is replaced by the empty state
described in §0.4, with its call-to-action button opening the same "New
Project" modal.

*API note: the projects list endpoint returns name/description/owner/date
but not the four count columns — populate those by fetching each project's
summary alongside the list (fine at demo scale; consider lazy-loading counts
only for visible rows if a real dataset ever gets large).*

### 2.1 "New Project" modal

Triggered by the "+ New Project" button. Standard modal per §0.4, ~560px
wide, close "×" top-right.

Top to bottom inside the modal:

1. Title: "New Project".
2. **Project Name** — text input, required, red asterisk or "Required" hint,
   inline validation message if left empty on submit attempt.
3. **Description** — multi-line textarea, 3 rows, labeled "Optional".
4. **Question Papers** — a dashed-border drop zone, ~120px tall, centered
   upload-cloud icon + text "Drag files here or click to browse" + small
   helper text "PDF, TXT or JSON — multiple files allowed". Once files are
   chosen, they render as a wrapped list of small file chips below the zone
   (filename + size + a small "×" to remove before submitting).
5. **Syllabus / Topic List** — identical drop zone, same accepted file types,
   labeled "Syllabus / Topic List", independent file list.
6. Footer row: secondary "Cancel" button + primary "Analyze" button.

**Validation:** "Analyze" is disabled until the Project Name is non-empty
**and** at least one file has been added to either upload zone (the pipeline
needs something to process — a project with a name but zero files can't be
analyzed). A short inline hint under the buttons communicates this
("Add at least one file to continue") rather than a blocking alert.

**On clicking Analyze:** the button shows a brief inline spinner, the project
is created and the files are uploaded, then the modal closes and the app
navigates immediately to that project's **Individual Project screen**.

*API note — important for correct UX: document processing is asynchronous.
The upload call returns immediately (HTTP 202) and extraction/classification
continues in the background per file. So "Analyze" does not block until the
pipeline finishes — it kicks the pipeline off and takes the user straight to
the (mostly empty-looking) project screen, where uploaded documents appear
with an "Extracting" or "Classifying" status badge and the screen polls for
updates until every document reaches "Completed" or "Failed" (see §3). Set
expectations with a small transient banner on arrival: "Processing N
document(s)... this page will update automatically."*

---

## 3. Screen — Individual Project

Reached by clicking a project row, or landing here right after "Analyze".
Top nav breadcrumb: `Projects / <Project Name>`.

**Header block:** project name as the page title (28px bold), description
directly underneath in secondary gray (if present), and a small meta line
below that: "Created by `<username>` on `<date>`". Top-right of this header
block: a secondary "Upload More" button that reopens the same two-drop-zone
upload flow as §2.1 (minus the name/description fields) so more question
papers or syllabi can be added to an existing project without creating a new
one — a small, cheap reuse of the modal component.

**Stat card strip:** seven stat cards, same visual style as §0.4:

1. Question Papers
2. Syllabi
3. Subjects
4. Questions
5. Topics
6. Allocated Questions
7. Unallocated Questions

Consider rendering cards 6–7 as one combined card instead of two plain
numbers: a thin horizontal stacked bar showing the allocated/unallocated
split at a glance (green segment = allocated, gray segment = unallocated),
with the two numbers as a caption underneath. This directly echoes the small
percentage-bar stat tiles in the reference screenshots and turns a QA metric
into something scannable in one glance rather than two separate raw counts.

**Action row:** three secondary-style buttons in a row below the stat cards,
visually slightly larger than a normal button (roughly button + icon,
48px tall) since these are the three primary navigation actions off this
screen:

- **View All Questions** → Questions screen
- **View All Topics** → Topics screen
- **Trend Analysis** → Trend & Insights screen (give this one the primary
  gradient treatment instead of secondary styling — it's the screen you most
  want people clicking into)

**Question Papers table:** section heading "Question Papers", full-width
table, one row per uploaded question paper:

| Document | Status | Subject | Questions | Total Marks | Allocated | Unallocated | Multi-allocated |
|---|---|---|---|---|---|---|---|

- Document column shows the filename.
- Status uses the status badge component (§0.4); a paper stuck in
  "Extracting"/"Classifying" shows its other numeric columns as an em-dash
  or "—" since they aren't meaningful yet.
- Subject renders as "`<name>` (`<code>`)" on one line, or "—" if not yet
  extracted.
- While any paper in this table is still processing, the table (and the stat
  cards above it) auto-refresh on a short interval (e.g. every 3–5 seconds)
  until every row reaches Completed/Failed, then polling stops.

**Syllabus table:** section heading "Syllabus", directly below or side-by-
side with the Question Papers table if screen width allows (stack vertically
on narrower viewports), one row per uploaded syllabus document:

| Document | Status | Topics | Subtopics |
|---|---|---|---|

Same status badge treatment (this table only ever shows Extracting,
Completed, or Failed — there's no classification step for syllabi). Clicking
a row jumps to the Topics screen with that syllabus pre-selected.

---

## 4. Screen — Questions

Reached via "View All Questions". Top nav breadcrumb: `Projects / <Project
Name> / Questions`.

**Filter bar:** a single row of controls above the results, all optional and
combinable:

- **Subject** — dropdown listing the distinct subjects present in this
  project (label shows "`<name>` (`<code>`)"), default "All Subjects".
- **Topic** — searchable dropdown of topic names, default "All Topics".
- **Allocation** — a small 4-way segmented control: All / Allocated /
  Unallocated / Multi-allocated.
- **Keyword** — a plain text box that filters the currently-loaded questions
  by matching against question text client-side (not a backend search — fine
  for a demo dataset; note this filters only what's currently loaded, so pair
  it with the other filters rather than relying on it alone for a huge
  dataset).

Below the filter bar, a small result-count line: "Showing 42 questions".

**Results — card grid, not a dense table.** Each question includes a cropped
image of the original question (not just text), so a table row would waste
that. Use a responsive grid of question cards (roughly 3–4 columns on
desktop, collapsing to 1 on narrow widths). Each card:

- Top: the cropped question image, shown at a fixed thumbnail height with
  `object-fit: contain` on a light gray backdrop; clicking it opens a
  lightbox with the full-size image.
- A small top-right badge with the question number (e.g. "Q1(a)") and the
  mark value (e.g. "3 marks") as a secondary pill.
- Below the image: the question text (2–3 line clamp, full text on hover/
  click), then a line of meta text: subject name, subject code, exam date.
- A row of small topic/subtopic chips at the bottom — one chip per mapped
  topic, showing the topic name; hovering a chip could reveal its subtopics
  as a tooltip. A question with zero chips renders a single muted
  "Unallocated" chip instead, so the empty case is still visibly labeled
  rather than looking broken.
- If a question has two or more topic chips, add a tiny "multi-allocated"
  indicator (a small dot or "×2" badge) so the coverage/QA signal from §3 is
  visible at the individual-question level too, not just in aggregate.

Empty state ("No questions match these filters") replaces the grid when
filters return nothing.

---

## 5. Screen — Topics

Reached via "View All Topics" (or a syllabus row on the project screen, which
pre-selects that document). Top nav breadcrumb: `Projects / <Project Name> /
Topics`.

*API note: topics are extracted per syllabus document, not merged across a
whole project — there's no single "all topics in this project" list. So this
screen is naturally organized around the project's syllabus documents:*

**Document selector:** if the project has more than one syllabus document, a
row of tabs (or a dropdown if there are many) across the top lets the user
pick which syllabus to view, labeled with each document's filename. If there
is exactly one syllabus, skip the selector entirely and just show its
content — don't make the user pick from a list of one.

**Summary line:** directly under the selector, a small line: "`<N>` topics ·
`<N>` subtopics" for the currently-selected syllabus.

**Topic list:** a vertical stack of expandable topic cards (accordion
style), one per topic, each showing when collapsed:

- Topic name (bold, 16px)
- Two small meta chips: weightage (e.g. "15%") and hours (e.g. "6 hrs")
- A muted count on the right: "4 subtopics"

Expanding a card reveals its subtopics as a simple bulleted or chip list
indented beneath the topic name, making the topic→subtopic hierarchy
visually obvious (this satisfies your requirement that subtopics render
nested inside their parent topic, not as a flat mixed list). Default state:
all topics collapsed except the first, to avoid an overwhelming wall of text
on load.

---

## 6. Screen — Trend & Insights

**This is the most important screen in the app** — it's where every chart
from the analytics API surfaces. Reached via the "Trend Analysis" button.
Top nav breadcrumb: `Projects / <Project Name> / Trends`.

### 6.1 Layout shell

A single scrollable page (no tab-switching state to manage — keeps the build
simple) divided into four clearly-labeled sections in a fixed order. A thin
sticky sub-header directly below the main nav bar holds four quick-jump
links — **Content Trends · Papers · Coverage · Exam Structure** — that
smooth-scroll to each section's anchor; this is pure convenience navigation
on top of a normal long page, not real routing, so it's cheap to add and easy
to skip if time is short.

Each section is its own white card/panel (full-width, generous internal
padding) with a section title, and each individual chart within a section
carries the chart's own `title` and `description` text exactly as returned
by its API call, rendered as a small muted caption under the chart title —
the API deliberately hands back human-readable framing for every chart
(including the specific counting-convention gotchas), so surface it rather
than re-deriving your own captions.

### 6.2 Section 1 — Content Trends

The "what does this exam actually test, and how has it shifted" section.
Contains, top to bottom:

**a) Questions per Year** — a plain vertical bar chart, full width, modest
height (~240px). One bar per year in the order returned (chronological,
"Undated" last if present). This is the section's headline chart — put it
first, it's the simplest orientation point before the denser charts below.

**b) Topic & Subtopic Frequency** — a two-panel row, side by side on desktop
(stacked on narrow widths): left panel "Most Tested Topics", right panel
"Most Tested Subtopics". Each is a horizontal bar chart (topic/subtopic names
are long — horizontal keeps them legible), sorted descending, capped to the
top 12 entries with a small "+N more" note if the full list is longer (the
API returns everything; the UI decides how much to show). Above each panel, a
small two-option toggle switches its ranking between **Count** and **Marks**
— i.e. "most asked" vs. "most heavily weighted" is one click apart, not two
separate permanent charts.

**c) Topic-Year Heatmap** — full width, directly below the frequency panels.
Rows = topics (already ordered most-tested-first by the API), columns =
years (chronological, "Undated" last). Cell color intensity encodes question
count for that topic in that year using a single-hue sequential ramp
(light = few/zero, dark = many) — never a multi-hue "rainbow" scale. Any
(topic, year) pair absent from the API response renders as the lightest
step (zero), not a blank cell. If there are many topics, cap the visible rows
to roughly the top 15 by default with a "Show all topics" toggle, and make
the whole grid horizontally scrollable within its own card if there are many
years, rather than letting it stretch the page. A hover tooltip on any cell
shows the exact topic, year, and count.

### 6.3 Section 2 — Papers

The "trend across individual exam sittings" section.

**a) Topic Distribution for a Paper** — a pie/donut chart with a paper-picker
dropdown directly above it (options built from the project's question paper
list, labeled by filename + subject code). Selecting a paper fetches and
renders that paper's topic breakdown. Include the "Unallocated" slice as a
distinct muted-gray wedge rather than hiding it — it's meaningful
classification-coverage signal, not a rendering artifact. Default selection:
the most recently uploaded paper.

**b) Marks per Paper by Topic** — the section's centerpiece: a stacked
vertical bar chart, one bar per paper ordered left-to-right by exam date
(undated last), each bar segmented by topic with segment height = marks
contributed, plus a line drawn through the top of each stack connecting
`total_marks` across papers so the overall marks trend reads at a glance even
though it's layered on a bar chart. Reuse the *same* topic→color mapping
here as in the topic-frequency bars above, so a topic is visually the same
color everywhere it appears on this page — this consistency is worth more
than any single chart's polish. If there are many papers, this chart scrolls
horizontally within its card rather than shrinking bars to illegibility.
x-axis tick labels use filename or subject code + exam date, whichever is
shorter/cleaner to render.

### 6.4 Section 3 — Coverage (data quality)

Deliberately styled with a slightly more neutral/muted panel background than
the two content sections above (e.g. a light gray card instead of pure
white) — a small visual cue that this section is "is the data trustworthy",
not "what does the exam test", and shouldn't be read with the same
excitement as a content insight.

**Allocation Health** — a 100%-stacked horizontal or vertical bar per paper
(pick vertical to stay visually consistent with the marks-per-paper chart
above it), three segments per bar: unallocated / single-allocated / multi-
allocated. Use the status-style color convention suggested by the API docs
themselves: green = single-allocated (good), amber = multi-allocated
(informational, not bad), red/gray = unallocated (the thing actually worth
worrying about) — this is a status encoding, not a categorical one, so it
intentionally does **not** reuse the topic color palette from the sections
above. A one-line caption under the chart states the exact bucket
definitions so nobody misreads "multi-allocated" as an error state.

### 6.5 Section 4 — Exam Structure

**Mark Distribution** — a simple bar chart/histogram, x-axis = distinct mark
values (as returned, e.g. "1", "2", "5", "7.5"), y-axis = question count.
Closes out the page on a simple, easy note after the denser charts above.

### 6.6 Chart color system

To keep every chart on this screen visually coherent (and to avoid the
classic "rainbow dashboard" problem), use one small, fixed set of rules
across the whole screen rather than choosing colors chart-by-chart:

- **Single-series charts** (Questions per Year, Mark Distribution) — one
  solid brand color per bar, using the app's orange accent (`#EB6834`
  family). No per-bar color variation; color here doesn't encode anything,
  it's just the brand showing through.
- **Multi-series / categorical charts** (topic frequency, subtopic
  frequency, marks-per-paper stack segments) — an 8-color, fixed-order,
  colorblind-safe categorical palette, assigned to topics **by identity, not
  by rank**, and reused consistently in that same order everywhere a topic
  needs a color on this page:
  `#2a78d6` (blue) → `#eb6834` (orange) → `#1baf7a` (aqua) → `#eda100`
  (yellow) → `#e87ba4` (magenta) → `#008300` (green) → `#4a3aa7` (violet) →
  `#e34948` (red). Beyond 8 distinct topics on one chart, fold the remainder
  into a muted "Other" bucket rather than generating a 9th hue. A legend is
  always shown wherever 2+ series appear on one chart; identity is never
  color-alone (topic names are always available on hover/label, not just
  inferred from color).
- **Sequential (magnitude) charts** — the heatmap only. One hue, light→dark,
  independent of the categorical palette above (blue works well and reads
  clearly as "just intensity" rather than "another topic").
- **Status charts** — Allocation Health only, as described in §6.4: a
  reserved green/amber/red trio, never reused for anything else on the page.

---

## 7. Navigation map

```
Login
  └─ (on success) → Project Management
                        ├─ "+ New Project" → [New Project modal] → Individual Project (new)
                        └─ click project row → Individual Project
                                                  ├─ "Upload More" → [Upload modal]
                                                  ├─ "View All Questions" → Questions
                                                  ├─ "View All Topics" → Topics
                                                  ├─ "Trend Analysis" → Trend & Insights
                                                  └─ click syllabus row → Topics (pre-selected doc)
```

Every screen past Login keeps the same dark top nav bar with a breadcrumb
back to Projects and, once inside a project, back to that project's overview
— that's the only "back" affordance needed; no separate back-button chrome.

---

## 8. Notes for whoever builds this

- The app needs exactly one protected-route guard: no valid token → Login.
  Everything else is behind it.
- Polling (project screen while documents process; see §3) is the only
  "real-time-ish" behavior in the app — plain interval-based refetching is
  enough, no need for websockets/SSE for a demo.
- The Projects table's count columns require an extra per-project summary
  call today (see the API note in §2) — acceptable at demo scale; flag it if
  the project list ever needs to handle hundreds of rows.
- Nothing in this spec requires a component library beyond basic building
  blocks (button, input, modal, tabs/accordion, table, tooltip) — plain CSS
  or any lightweight utility framework (e.g. Tailwind) is enough to hit the
  look described here.

If anything above should be merged, cut, or reshuffled, treat this as a
starting draft, not a locked spec — flag it and it's easy to adjust before
any component gets built.
