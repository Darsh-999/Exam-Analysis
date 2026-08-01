from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class ProjectOut(BaseModel):
    id: str
    name: str
    description: str | None = None
    owner_id: str
    owner_email: EmailStr
    created_at: datetime
    is_owner: bool


class DocumentType(str, Enum):
    QUESTION_PAPER = "question_paper"
    SYLLABUS = "syllabus"


class DocumentStatus(str, Enum):
    EXTRACTING = "extracting"
    CLASSIFYING = "classifying"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentOut(BaseModel):
    id: str
    project_id: str
    filename: str
    doc_type: DocumentType
    status: DocumentStatus
    error: str | None = None
    uploaded_at: datetime
    updated_at: datetime


class DocumentUploadResult(BaseModel):
    id: str
    filename: str
    doc_type: DocumentType


class DocumentUploadResponse(BaseModel):
    message: str
    documents: list[DocumentUploadResult]


class GlobalCountsOut(BaseModel):
    total_projects: int
    total_question_papers: int
    total_syllabi: int
    total_subjects: int
    total_questions: int
    total_topics: int


class ProjectSummaryOut(BaseModel):
    id: str
    name: str
    description: str | None = None
    created_by: str
    created_at: datetime
    total_question_papers: int
    total_syllabi: int
    total_subjects: int
    total_questions: int
    total_topics: int
    total_subtopics: int
    total_allocated_questions: int
    total_unallocated_questions: int
    total_multi_allocated_questions: int


class SyllabusSummaryOut(BaseModel):
    id: str
    filename: str
    status: DocumentStatus
    total_topics: int
    total_subtopics: int


class SyllabusTopicOut(BaseModel):
    topic: str
    subtopics: list[str]
    weightage: int
    hours: int


class SyllabusContentOut(BaseModel):
    syllabus_id: str
    filename: str
    content: list[SyllabusTopicOut]


class QuestionPaperSummaryOut(BaseModel):
    id: str
    filename: str
    status: DocumentStatus
    subject_name: str | None = None
    subject_code: str | None = None
    total_questions: int
    total_marks: int | None = None
    total_allocated_questions: int
    total_unallocated_questions: int
    total_multi_allocated_questions: int


class QuestionTopicOut(BaseModel):
    subject_name: str
    topic: str
    subtopics: list[str]


class QuestionOut(BaseModel):
    question_id: str
    subject_name: str | None = None
    subject_code: str | None = None
    exam_date: str | None = None
    question_number: str
    question: str
    mark: float
    cropped_image: str
    topic: list[QuestionTopicOut]


class AllocationStatus(str, Enum):
    ALLOCATED = "allocated"
    UNALLOCATED = "unallocated"
    MULTI_ALLOCATED = "multi_allocated"
