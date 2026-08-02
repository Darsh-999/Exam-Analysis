You will be given a sequence of cropped images from one exam paper, each preceded by a
line `ImageID: <id>`. Classify every image and extract every question, following the
rules and schema in your system instructions.

Remember: you are only seeing a slice of the document. If a question's start, end,
referenced diagram/table/options, or marks fall outside the images you were given,
mark it `incomplete_info: true` with the matching `incomplete_reason` entries rather
than guessing.

Remember also: paper-level administrative or instructional text -- e.g. "Total
Marks: 70", "Instructions:", "Attempt all questions.", "Make suitable assumptions
wherever necessary.", "Figures to the right indicate full marks." -- is not a
question. Classify it as `marks_info`/`useless` and do not create a `questions[]`
entry for it. Never output a `questions[]` entry with empty `text`.