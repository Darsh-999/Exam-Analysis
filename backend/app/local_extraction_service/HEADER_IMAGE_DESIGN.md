# Header composite image design

## Problem

The exam paper's header metadata (`degree`, `subject_name`, `subject_code`,
`exam_date`, `semester`, `total_marks`) only ever appears near the top of page 1, but
DocLayout has already split that region into several small boxes (institute name,
subject line, date/semester line, marks line, etc). Sending Qwen 20 tiny separate
images for one small, cheap extraction task is wasteful: each image carries its own
fixed per-image token overhead in the vLLM/Qwen vision encoder regardless of how small
it is, and vLLM counts each one as a separate image slot against `--max-model-len`.

The fix is to **join several small boxes into one composite image** before sending
them, so a handful of tiny crops become one (or a few) images instead of twenty.

## How boxes become composite images

1. Only the first `header_bbox_limit` boxes (default `20`) are considered — headers
   never appear later than that, and this is exactly where DocLayout's box ordering
   (top-to-bottom, left-to-right, continuous across the document) puts them.
2. Those boxes are grouped consecutively into chunks of `header_boxes_per_image`
   (default `4`), giving `20 / 4 = 5` composite images.
3. Each chunk is joined with `image_compose.stack_vertically()`:
   - Crops are stacked **top-to-bottom in their original order** — this preserves the
     natural reading order of a page header (institute name, then subject/code line,
     then date/semester/marks line, ...), so the model reads them the same way a human
     would scan down the page.
   - Each crop keeps its own width; the canvas width is the widest crop, and narrower
     crops are left-aligned with white space to their right (same idea as the
     existing `_stack_vertically` helper in `app/services/cropping.py`, reused for
     consistency).
   - A thin gray rule (4px) plus white padding (12px) separates consecutive crops, so
     the model doesn't misread the bottom of one crop as flowing into the top of the
     next — important since two unrelated header lines can otherwise sit right next
     to each other with no visual gap.
4. All 5 composite images are sent together in **one** Qwen request (one message, 5
   image blocks, in order), asking only for the 6 metadata fields — never questions.

## Why no per-crop ID captions here

Question-batch images (`questions.py`) are captioned with `ImageID: <id>` text blocks
because Qwen needs to report back *which* image a question came from
(`image_ids`). Headers don't need that traceability — there's nothing to attribute an
extracted field back to a specific box for — so the composite images are left
uncluttered: just the stacked crops and a short "Header image N of 5" caption to tell
the model these are sequential parts of the same header block.

## What's configurable

- `settings.header_bbox_limit` — how many of the leading boxes are considered at all.
- `settings.header_boxes_per_image` — how many boxes get joined into one composite
  image.

Both live in `app/config.py` alongside the rest of the local-extraction settings.

## What's deliberately left simple

No dynamic resizing, no grid layout, no cropping the composite down further — DocLayout
crops from page 1 headers are small to begin with, so a single vertical stack per group
stays a modest image size without extra logic. If header extraction quality turns out
to need it later (e.g. very tall composites on unusually dense first pages), the two
settings above are the first things to try tuning before changing the compositing
logic itself.
