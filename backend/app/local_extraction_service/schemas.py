from typing import Literal

from pydantic import BaseModel, Field

# -- DocLayout output (internal, never sent through guided_json) --


class BoxRecord(BaseModel):
    """One cropped region detected by DocLayout, in whole-document reading
    order (top-to-bottom, left-to-right per page, continuous across pages).
    """

    temp_id: str
    page_index: int
    box_2d: list[int] = Field(min_length=4, max_length=4)
    image_base64: str

    # Filled in after the question-extraction pass classifies every image;
    # "" until then.
    content_type: str = ""
    label: str = ""


# -- Header extraction --


class ExamHeaders(BaseModel):
    degree: str = Field(
        description='raw text as seen, no semester info; "" if not determined'
    )
    subject_name: str = Field(description='raw text as seen; "" if not determined')
    subject_code: str = Field(description='raw text as seen; "" if not determined')
    exam_date: str = Field(description='YYYY/MM/DD; "" if not determined')
    semester: int = Field(description="integer 1-24; 0 if not determined")
    total_marks: int = Field(description="0 if not determined")


# -- Question extraction (adapted from Qwen.py) --

ContentType = Literal[
    "question", "question_continuation", "diagram",
    "table", "mcq", "marks_info", "useless",
]

IncompleteReason = Literal[
    "que_start_missing", "que_end_missing", "refers_diagram",
    "refers_table", "refers_mcq", "no_marks",
]


class ImageRecord(BaseModel):
    image_id: str
    content_type: ContentType
    label: str = ""


class Question(BaseModel):
    question_number: str
    text: str
    marks: float = 0
    image_ids: list[str]
    incomplete_info: bool = False
    incomplete_reason: list[IncompleteReason] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class BatchExtraction(BaseModel):
    images: list[ImageRecord]
    questions: list[Question]
