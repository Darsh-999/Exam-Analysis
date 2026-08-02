You will be given a sequence of cropped images from one exam paper, each preceded by a
line `ImageID: <id>`. Classify every image and extract every question, following the
rules and schema in your system instructions.

Remember: you are only seeing a slice of the document. If a question's start, end,
referenced diagram/table/options, or marks fall outside the images you were given,
mark it `incomplete_info: true` with the matching `incomplete_reason` entries rather
than guessing.
