Extract all questions from this exam PDF following the schema and rules in your system instructions.

## Metadata Extraction

Extract the following from the PDF only — no external reference data is provided or needed.

- `degree`: raw degree text exactly as seen on the paper header (exclude semester or other info). Not found → `""`.
- `subject_name`: raw subject name exactly as seen in the first-page header/title. Not found → `""`.
- `subject_code`: raw subject code exactly as seen in the first-page header/title. Not found → `""`.
- `exam_date`: convert to `YYYY/MM/DD`. Not found → `""`.
- `semester`: integer 1–24. Convert Roman numerals ("III" → 3) and text variants ("Third Semester" → 3) to a number. Not found → `0`.
- `total_marks`: from "Total Marks" / "Maximum Marks" / "Max. Marks". Not found → `0`.

## Question Detection

Scan every page, start to finish. Questions are marked by numbers/letters ("1.", "Q.1", "(a)", "1(a)", "1(a)(i)") and often carry marks ("(7 marks)", "[4]", "CO2 [3]").

Every distinct numbered/lettered item — MCQ, fill-in-the-blank, true/false, match-the-following, short answer, long answer, or numerical/problem-solving — is an INDEPENDENT question with its own entry in `content[]`, its own `question_number`, and its own `bbox`.

## Extracting `question_number`

Capture the question's identifying label exactly as printed, whatever form it takes:
- Pure serial numbers: `"1"`, `"2"`, `"12"`
- Pure alphabetic/roman sub-labels: `"a"`, `"b"`, `"iii"`
- Combined labels: `"1(a)"`, `"2(b)(ii)"`, `"Q.3"`

Do not invent or renumber. If no label is visibly printed for an item, use `""`.

## Extracting `question`

- Strip the label (e.g. "Q.1", "(a)") out of the `question` text — it belongs only in `question_number`.
- Transcribe in **plain text** — no LaTeX, no MathJax, no `$...$` delimiters, no markup of any kind. Reproduce mathematical notation using ordinary characters/Unicode as printed (e.g. `x^2`, `dy/dx`, `∫`, `√x`) rather than converting it.
- For MCQs, include all options: `"(A) ... (B) ... (C) ... (D) ..."`.
- For fill-in-the-blanks, preserve the blank as `___` or as printed.
- Exclude diagrams, complex tables, and mark indicators (those belong in `bbox` and `mark`).

## Marks Extraction

- Pull from patterns like "(7 marks)", "[4]", "7M", "CO2 [3]".
- If sub-questions share a stated total, split evenly (e.g. "Q1 (14 marks)" with (a)/(b) → 7 each).
- Not specified → `mark: 0`.

## Bounding Boxes

- `box_2d`: `[ymin, xmin, ymax, xmax]`, integers normalized to 0–1000.
- One tight box per question per page; no ghost boxes over blank space, margins, headers, footers, or page numbers.
- Sub-questions get separate, non-overlapping boxes — (b)'s `ymin` starts where (b)'s text starts, not at (a)'s.
- Multi-column pages: box only the column the question is in; don't span columns unless content genuinely spans them (on a 1000-scale page: left column ≈ xmin 50–100 / xmax 480–500; right column ≈ xmin 520–550 / xmax 950–980).
- Follow the **sandwich rule** (system instructions) for text/diagram/table sequences and for questions spanning multiple pages.

## Page Processing

Work page by page, 0 to N−1, extracting metadata from page 0 and questions from every page. Do not stop early — a PDF with N pages should produce `bbox` entries with `page_index` covering the full range 0 to N−1.

## Output

Return a single valid JSON object matching the schema — no preamble, no explanation, no extra keys, every question from every page present in `content[]`.

### Example

PDF:
```
Q.1 (a) Define solenoidal vector field. Find constant a such that (x+3)i + (y-2z)j + (x+az)k is solenoidal. (3 marks)
Q.1 (b) Verify Green's theorem for ∮C (xy²-2xy)dx + (x²y+3)dy (4 marks)
```

Output:
```json
{
  "content": [
    {
      "question_number": "1(a)",
      "question": "Define solenoidal vector field. Find constant a such that (x+3)i + (y-2z)j + (x+az)k is solenoidal.",
      "mark": 3,
      "bbox": [{"page_index": 0, "box_2d": [100, 50, 180, 500]}]
    },
    {
      "question_number": "1(b)",
      "question": "Verify Green's theorem for ∮C (xy²-2xy)dx + (x²y+3)dy",
      "mark": 4,
      "bbox": [{"page_index": 0, "box_2d": [190, 50, 270, 500]}]
    }
  ]
}
```