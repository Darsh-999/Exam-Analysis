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
